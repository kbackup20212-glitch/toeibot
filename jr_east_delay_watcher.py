import os
import requests
import re
import time
import traceback # エラーの詳細表示のためにインポート
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta

# --- 共通データのインポート ---
try:
    from jr_east_detector import STATION_DICT, JR_LINES_TO_MONITOR
    JR_LINE_NAMES = {line.get("id"): line.get("name", line.get("id", "").split('.')[-1])
                     for line in JR_LINES_TO_MONITOR if line.get("id")}
except ImportError:
    STATION_DICT, JR_LINES_TO_MONITOR, JR_LINE_NAMES = {}, [], {}
try:
    from jr_east_info_detector import JR_LINE_PREDICTION_DATA, RAIL_DIRECTION_NAMES
except ImportError:
     JR_LINE_PREDICTION_DATA, RAIL_DIRECTION_NAMES = {}, {}

API_TOKEN = os.getenv('ODPT_TOKEN_CHALLENGE')
API_ENDPOINT = "https://api-challenge.odpt.org/api/v4/odpt:Train"

tracked_delayed_trains: Dict[str, Dict[str, Any]] = {}
line_cooldown_tracker: Dict[str, float] = {}
line_resumption_notified: Dict[str, bool] = {}
line_prediction_cooldown_tracker: Dict[str, float] = {} # ★ 予測通知専用クールダウン
JST = timezone(timedelta(hours=+9)) # ★ JST

# --- 設定値 ---
DELAY_THRESHOLD_SECONDS = 3 * 60
INITIAL_NOTICE_THRESHOLD = 5
ESCALATION_NOTICE_THRESHOLD = 10
GROUP_ANALYSIS_THRESHOLD = 2
GRACE_STATION_COUNT = 4
CLEANUP_THRESHOLD_SECONDS = 15 * 60
COOLDOWN_SECONDS = 30 * 60

# --- ★★★ 分析官（ヘルパー関数） ★★★ ---
def _analyze_group_delay(line_id: str, line_name_jp: str, all_trains_on_line: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    指定された路線の全列車データから、集団遅延の「クラスター」を見つけて分析し、
    「生データ」の辞書を返す。
    """
    global tracked_delayed_trains
    
    line_map_data = JR_LINE_PREDICTION_DATA.get(line_id, {})
    station_list = line_map_data.get("stations", [])
    if not station_list: 
        print(f"--- [DELAY ANALYZE] No station map for {line_name_jp}. Cannot analyze range.", flush=True)
        return None # 駅マップがなければ分析不可

    # 1. 全列車の位置と遅延を駅インデックスにマッピング
    station_delay_map: Dict[int, List[Dict[str, Any]]] = {}
    for train in all_trains_on_line:
        location_id = train.get("odpt:toStation") or train.get("odpt:fromStation")
        if not location_id: continue
        
        station_en = location_id.split('.')[-1]
        station_jp = STATION_DICT.get(station_en, station_en)
        
        if station_jp in station_list:
            try:
                index = station_list.index(station_jp)
                if index not in station_delay_map:
                    station_delay_map[index] = []
                station_delay_map[index].append(train)
            except ValueError:
                pass # 駅リストにない駅は無視

    # 2. 遅延クラスター（小隊）を見つける (猶予カウント方式)
    clusters: List[Dict[str, Any]] = []
    current_cluster: Optional[Dict[str, Any]] = None
    grace_count = 0
    
    for index in range(len(station_list)):
        trains_at_this_station = station_delay_map.get(index, [])
        is_delayed_station = False
        if trains_at_this_station:
            for train in trains_at_this_station:
                train_number = train.get("odpt:trainNumber")
                if train_number in tracked_delayed_trains and \
                   tracked_delayed_trains[train_number]["consecutive_increase_count"] >= GROUP_ANALYSIS_THRESHOLD:
                    is_delayed_station = True
                    break
        
        if is_delayed_station:
            grace_count = 0
            if current_cluster is None:
                current_cluster = {"indices": [index], "trains": trains_at_this_station}
            else:
                current_cluster["indices"].append(index)
                current_cluster["trains"].extend(trains_at_this_station)
        else:
            if current_cluster is not None:
                grace_count += 1
                if grace_count > GRACE_STATION_COUNT:
                    clusters.append(current_cluster)
                    current_cluster = None
                    grace_count = 0
    
    if current_cluster is not None:
        clusters.append(current_cluster)

    if not clusters:
        return None

    # 3. 最大のクラスターを分析
    main_cluster = max(clusters, key=lambda c: len(c["trains"]))

    directions_set: set = set()
    max_delay: int = 0
    main_culprit_count: int = -1
    cause_location_id: Optional[str] = None

    for train in main_cluster["trains"]:
        if train.get("odpt:railDirection"):
            directions_set.add(train["odpt:railDirection"])
        if train.get("odpt:delay", 0) > max_delay:
            max_delay = train.get("odpt:delay", 0)
        train_number = train.get("odpt:trainNumber")
        if train_number in tracked_delayed_trains:
            count = tracked_delayed_trains[train_number]["consecutive_increase_count"]
            if count > main_culprit_count:
                main_culprit_count = count
                cause_location_id = train.get("odpt:toStation") or train.get("odpt:fromStation")

    # 4. 方向の日本語決定
    direction_text = "上下線"
    if "odpt.RailDirection:Inbound" in directions_set and "odpt.RailDirection:Outbound" in directions_set: direction_text = "上下線"
    elif "odpt.RailDirection:Northbound" in directions_set and "odpt.RailDirection:Southbound" in directions_set: direction_text = "上下線"
    elif "odpt.RailDirection:Eastbound" in directions_set and "odpt.RailDirection:Westbound" in directions_set: direction_text = "上下線"
    elif "odpt.RailDirection:InnerLoop" in directions_set and "odpt.RailDirection:OuterLoop" in directions_set: direction_text = "内外回り"
    else:
        found_directions = [RAIL_DIRECTION_NAMES.get(d, "不明") for d in directions_set]
        direction_text = "・".join(set(found_directions)) if found_directions else "上下線"
    
    # 5. 範囲の特定
    min_index = min(main_cluster["indices"])
    max_index = max(main_cluster["indices"])
    range_text = f"{station_list[min_index]}～{station_list[max_index]}"
    if min_index == max_index:
         range_text = f"{station_list[min_index]}駅付近"

    cause_station_jp = range_text
    if cause_location_id:
        cause_station_en = cause_location_id.split('.')[-1]
        cause_station_jp = STATION_DICT.get(cause_station_en, cause_station_en) + "駅付近"

    # 6. 分析結果を辞書で返す
    return {
        "range_text": range_text,
        "direction_text": direction_text,
        "max_delay_minutes": int(max_delay / 60),
        "cause_station_jp": cause_station_jp,
        "suspicious_trains": main_cluster["trains"] # 旗を立てるために使う
    }

# --- メイン関数 (バグ修正・完全版) ---
def check_delay_increase(official_info: Dict[str, Dict[str, Any]]) -> Optional[List[str]]:
    global tracked_delayed_trains, line_cooldown_tracker, line_resumption_notified
    notification_messages: List[str] = []
    current_time = time.time()
    trains_found_this_cycle: set = set()

    try:
        #1 列車在線データを取得
        params = {"odpt:operator": "odpt.Operator:JR-East", "acl:consumerKey": API_TOKEN}
        response = requests.get(API_ENDPOINT, params=params, timeout=45)
        response.raise_for_status()
        train_data = response.json()
        if not isinstance(train_data, list): return None

        #2 路線ごとの全列車リストと、最大遅延を集計
        all_trains_by_line: Dict[str, List[Dict[str, Any]]] = {}
        max_delay_by_line = {}
        for train in train_data:
            line_id = train.get("odpt:railway")
            if not line_id: continue
            if line_id not in all_trains_by_line: all_trains_by_line[line_id] = []
            all_trains_by_line[line_id].append(train)

            current_delay = train.get("odpt:delay", 0)
            if current_delay > max_delay_by_line.get(line_id, 0):
                max_delay_by_line[line_id] = current_delay
        
        #3 運転再開予測
        PREDICTION_CAUSES = {"シカと衝突", "異音の確認", "動物と衝突"} # 「の影響」は含まない
        target_delay_seconds = 20 * 60 # 20分
        
        for line_id, line_info in official_info.items():
            if not line_info: continue
            official_cause = line_info.get("odpt:trainInformationCause", {}).get("ja")
            
            # 条件1 & 2: 公式情報があり、原因が特定のものか
            if official_cause and any(cause in official_cause for cause in PREDICTION_CAUSES):
                # この路線の最大遅延を取得
                max_delay_seconds = max_delay_by_line.get(line_id, 0)
                
                # 条件3 & 4: 遅延が発生しており、20分未満か
                if 0 < max_delay_seconds < target_delay_seconds:
                    # クールダウンチェック
                    last_prediction_time = line_prediction_cooldown_tracker.get(line_id, 0)
                    if current_time - last_prediction_time > COOLDOWN_SECONDS:
                        seconds_to_reach_target = target_delay_seconds - max_delay_seconds
                        predicted_time_timestamp = current_time + seconds_to_reach_target
                        predicted_time_dt = datetime.fromtimestamp(predicted_time_timestamp, JST)
                        predicted_time_str = predicted_time_dt.strftime('%H:%M')
                        
                        line_name_jp = JR_LINE_NAMES.get(line_id, line_id.split('.')[-1])
                        message = f"【{line_name_jp} 運転再開予測】\n運転再開予測 {predicted_time_str}頃"
                        
                        notification_messages.append(message)
                        line_prediction_cooldown_tracker[line_id] = current_time # クールダウン開始
                        print(f"--- [DELAY WATCH] !!! RESUME PREDICTION SENT for {line_name_jp} ({predicted_time_str}) !!!", flush=True)

        #4 既存の不審遅延検知ロジック
        for train in train_data:
            train_number: Optional[str] = train.get("odpt:trainNumber")
            current_delay: int = train.get("odpt:delay", 0)
            line_id: Optional[str] = train.get("odpt:railway")
            current_location_id: Optional[str] = train.get("odpt:toStation") or train.get("odpt:fromStation")
            current_direction: Optional[str] = train.get("odpt:railDirection")
            if not all([train_number, line_id, current_location_id]): continue
            if train_number is None: continue
            trains_found_this_cycle.add(train_number)

            if train_number in tracked_delayed_trains:
                tracking_info = tracked_delayed_trains[train_number]
                moved = current_location_id != tracking_info["last_location_id"]
                recovered = current_delay < DELAY_THRESHOLD_SECONDS

                # ▼▼▼ リセット処理 (再開通知) ▼▼▼
                if moved or recovered:
                    if tracking_info.get("notified_initial", False) and not line_resumption_notified.get(line_id, False):
                        line_name_jp = JR_LINE_NAMES.get(line_id, line_id.split('.')[-1])
                        line_train_list = all_trains_by_line.get(line_id, [])
                        analysis_result = _analyze_group_delay(line_id, line_name_jp, line_train_list)
                        
                        range_text = STATION_DICT.get(tracking_info["last_location_id"].split('.')[-1], "不明な場所")
                        max_delay = int(tracking_info["last_delay"] / 60)
                        
                        if analysis_result: # まだ一部が遅れている
                            message = (
                                f"【{line_name_jp} 一部列車運転再開】\n"
                                f"{STATION_DICT.get(tracking_info['last_location_id'].split('.')[-1], '不明な場所')}駅付近の列車は動き出しましたが、"
                                f"現在も{analysis_result['range_text']}の{analysis_result['direction_text']}で停止中の列車があります。(最大{analysis_result['max_delay_minutes']}分遅れ)"
                            )
                        else: # 完全復旧
                            message = (
                                f"【{line_name_jp} 運転再開】\n"
                                f"{range_text}駅付近のトラブルは解消した模様です。運転を順次再開しました。"
                            )
                        
                        notification_messages.append(message)
                        line_resumption_notified[line_id] = True
                    del tracked_delayed_trains[train_number]
                
                # ▼▼▼ 遅延増加処理 ▼▼▼
                elif current_delay > tracking_info["last_delay"]:
                    tracking_info["consecutive_increase_count"] += 1
                    tracking_info["last_delay"] = current_delay
                    tracking_info["last_seen_time"] = current_time
                    if current_direction: tracking_info["direction"] = current_direction
                    count = tracking_info["consecutive_increase_count"]
                    
                    line_name_jp = JR_LINE_NAMES.get(line_id, line_id.split('.')[-1])

                    # --- 最初の通知判定 (カウント5) ---
                    if count >= INITIAL_NOTICE_THRESHOLD and not tracking_info.get("notified_initial", False):
                        line_info = official_info.get(line_id, {})
                        current_official_status = line_info.get("odpt:trainInformationStatus", {}).get("ja")
                        
                        if current_official_status == "運転見合わせ":
                            print(f"--- [DELAY WATCH] Train {train_number}: Skipping initial notice (Official status is '運転見合わせ').", flush=True)
                            tracking_info["notified_initial"] = True # ★公式発表済みなら、もう通知不要なので旗を立てる
                        else:
                            last_notification_time = line_cooldown_tracker.get(line_id, 0)
                            if current_time - last_notification_time > COOLDOWN_SECONDS:
                                line_train_list = all_trains_by_line.get(line_id, [])
                                analysis_result = _analyze_group_delay(line_id, line_name_jp, line_train_list)
                                if analysis_result:
                                    # ★★★ 司令塔から公式情報を使って「原因」を特定 ★★★
                                    status_to_check = line_info.get("odpt:trainInformationText", {}).get("ja", "")
                                    cause_text = "何らかの事象" # デフォルト
                                    reason_match = re.search(r'(.+?(?:駅|駅間))で(?:の)?(.+?)の影響で', status_to_check)
                                    if reason_match:
                                        location_part = reason_match.group(1).strip(); cause = reason_match.group(2).strip()
                                        actual_location = re.split(r'[、\s]', location_part)[-1] if location_part else location_part
                                        cause_text = f"{actual_location}での{cause}"
                                    else:
                                        official_cause_text = line_info.get("odpt:trainInformationCause", {}).get("ja")
                                        if official_cause_text: cause_text = official_cause_text
                                    
                                    message = (
                                        f"【{line_name_jp} 運転見合わせ】\n"
                                        f"{line_name_jp}は、{cause_text}の影響で、" # ★ 原因を公式に統一
                                        f"{analysis_result['range_text']}の{analysis_result['direction_text']}で運転を見合わせています。"
                                        f"(最大{analysis_result['max_delay_minutes']}分遅れ)"
                                    )
                                    notification_messages.append(message)
                                    line_cooldown_tracker[line_id] = current_time
                                    line_resumption_notified[line_id] = False
                                    # ★ 容疑者全員に旗を立てる
                                    for train_info in analysis_result["suspicious_trains"]:
                                        train_info["notified_initial"] = True
                                    print(f"--- [DELAY WATCH] !!! GROUP NOTICE SENT for line {line_name_jp} !!!", flush=True)
                            else:
                                print(f"--- [DELAY WATCH] Train {train_number}: Initial threshold reached, but line {line_name_jp} in cooldown.", flush=True)
                                # ★ クールダウンでも旗は立てない (バグ修正)
                    
                    # --- 再通知 (カウント10) ---
                    if count >= ESCALATION_NOTICE_THRESHOLD and tracking_info.get("notified_initial", False) and not tracking_info.get("notified_escalated", False):
                         
                         # ▼▼▼▼▼ ここからが修正箇所 ▼▼▼▼▼
                         line_info = official_info.get(line_id, {})
                         current_official_status = line_info.get("odpt:trainInformationStatus", {}).get("ja")

                         # もし公式が「運転見合わせ」と発表していたら、[継続]通知はスキップ
                         if current_official_status == "運転見合わせ":
                             print(f"--- [DELAY WATCH] Train {train_number}: Skipping escalation notice (Official status is already '運転見合わせ').", flush=True)
                             
                             # ただし、再通知は「処理済み」としてフラグだけ立てておく
                             tracking_info["notified_escalated"] = True # ★重要★
                         
                         else: # 公式が「遅延」などの場合のみ、[継続]通知を出す
                             line_train_list = all_trains_by_line.get(line_id, [])
                             analysis_result = _analyze_group_delay(line_id, line_name_jp, line_train_list)
                             if analysis_result:
                                line_info = official_info.get(line_id, {})
                                # ★★★ 継続通知でも公式情報から「原因」を特定 ★★★
                                status_to_check = line_info.get("odpt:trainInformationText", {}).get("ja", "")
                                cause_text = "何らかの事象" # デフォルト
                                reason_match = re.search(r'(.+?(?:駅|駅間))で(?:の)?(.+?)の影響で', status_to_check)
                                if reason_match:
                                    location_part = reason_match.group(1).strip(); cause = reason_match.group(2).strip()
                                    actual_location = re.split(r'[、\s]', location_part)[-1] if location_part else location_part
                                    cause_text = f"{actual_location}での{cause}"
                                else:
                                    official_cause_text = line_info.get("odpt:trainInformationCause", {}).get("ja")
                                    if official_cause_text: cause_text = official_cause_text
                                
                                message = (
                                    f"【{line_name_jp} 運転見合わせ[継続]】\n"
                                    f"{line_name_jp}は、{cause_text}の対処が長引いている影響で、" # ★ 原因を公式に統一
                                    f"{analysis_result['range_text']}の{analysis_result['direction_text']}で運転を見合わせています。"
                                    f"(最大{analysis_result['max_delay_minutes']}分遅れ)"
                                )
                                notification_messages.append(message)
                                
                                for train_info in analysis_result["suspicious_trains"]:
                                    train_info["notified_escalated"] = True
                                print(f"--- [DELAY WATCH] !!! ESCALATION NOTICE SENT for line {line_name_jp} !!!", flush=True)

                else: # 遅延が横ばい or 微減
                    tracking_info["last_seen_time"] = current_time
            
            # ▼▼▼ 新規追跡処理 ▼▼▼
            elif current_delay >= DELAY_THRESHOLD_SECONDS:
                 print(f"--- [DELAY WATCH] Train {train_number}: Start tracking (Delay={current_delay}s at {current_location_id}).", flush=True)
                 tracked_delayed_trains[train_number] = {
                     "line_id": line_id, "last_location_id": current_location_id,
                     "last_delay": current_delay, "consecutive_increase_count": 1,
                     "last_seen_time": current_time, "direction": current_direction,
                     "notified_initial": False, "notified_escalated": False,
                     "notified_resumed": False 
                 }
        
        # --- 4. 古い記録の掃除 ---
        trains_to_remove = [
            train_num for train_num, info in tracked_delayed_trains.items()
            if train_num not in trains_found_this_cycle and current_time - info["last_seen_time"] > CLEANUP_THRESHOLD_SECONDS
        ]
        for train_num in trains_to_remove:
            del tracked_delayed_trains[train_num]
            print(f"--- [DELAY WATCH] Train {train_num}: Removing track (timeout).", flush=True)

        return notification_messages

    except requests.exceptions.RequestException as req_err:
        print(f"--- [DELAY WATCH] ERROR: Network error: {req_err}", flush=True)
        return None
    except Exception as e:
        print(f"--- [DELAY WATCH] ERROR: Unexpected error: {e}", flush=True)
        traceback.print_exc()
        return None