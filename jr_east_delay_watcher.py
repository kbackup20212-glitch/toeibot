import os
import requests
import time
from typing import Dict, Any, List, Optional

# --- 共通データのインポート ---
try:
    from jr_east_detector import STATION_DICT, JR_LINES_TO_MONITOR
    # JR_LINES_TO_MONITOR から路線IDと日本語名の辞書を作成
    JR_LINE_NAMES = {line.get("id"): line.get("name", line.get("id", "").split('.')[-1])
                     for line in JR_LINES_TO_MONITOR if line.get("id")}
except ImportError:
    print("--- [DELAY WATCH] WARNING: jr_east_detector.py から共通データをインポートできませんでした。 ---", flush=True)
    STATION_DICT = {'Tokyo': '東京', 'Shinjuku': '新宿'}
    JR_LINES_TO_MONITOR = []
    JR_LINE_NAMES = {}

try:
    # jr_east_info_detector からカルテ棚と「方向辞書」をインポート
    from jr_east_info_detector import JR_LINE_PREDICTION_DATA, RAIL_DIRECTION_NAMES
except ImportError:
     print("--- [DELAY WATCH] WARNING: jr_east_info_detector.py からカルテと方向辞書をインポートできませんでした。 ---", flush=True)
     JR_LINE_PREDICTION_DATA = {}
     RAIL_DIRECTION_NAMES = {}

API_TOKEN = os.getenv('ODPT_TOKEN_CHALLENGE')
API_ENDPOINT = "https://api-challenge.odpt.org/api/v4/odpt:Train" # 在線情報のエンドポイント

# --- 監視対象の列車情報を保持する辞書 ---
tracked_delayed_trains: Dict[str, Dict[str, Any]] = {}
# --- 路線ごとの通知クールダウン用辞書 ---
line_cooldown_tracker: Dict[str, float] = {}
# --- 路線ごとの「再開通知済み」フラグ ---
line_resumption_notified: Dict[str, bool] = {}

# --- 設定値 ---
DELAY_THRESHOLD_SECONDS = 3 * 60  # 3分 (180秒)
INITIAL_NOTICE_THRESHOLD = 5      # 最初の通知を出すカウント
ESCALATION_NOTICE_THRESHOLD = 10 # 再通知を出すカウント
GROUP_ANALYSIS_THRESHOLD = 2 # 集団遅延とみなす最低カウント
GRACE_STATION_COUNT = 4           # 集団遅延判定の「猶予」駅数
CLEANUP_THRESHOLD_SECONDS = 15 * 60 # 15分
COOLDOWN_SECONDS = 30 * 60 # 30分

# --- ★★★ 分析官（ヘルパー関数） ★★★ ---
def _analyze_group_delay(line_id: str, line_name_jp: str, all_trains_on_line: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    指定された路線の全列車データから、集団遅延の「クラスター」を見つけて分析し、
    「生データ」の辞書を返す。
    """
    global tracked_delayed_trains
    
    line_map_data = JR_LINE_PREDICTION_DATA.get(line_id, {})
    station_list = line_map_data.get("stations", [])
    if not station_list: return None # 駅マップがなければ分析不可

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
    grace_count = 0 # 猶予カウント
    
    for index in range(len(station_list)): # 駅リストを順番に走査
        trains_at_this_station = station_delay_map.get(index, [])
        
        is_delayed_station = False # この駅に不審な列車がいるか？
        if trains_at_this_station:
            for train in trains_at_this_station:
                train_number = train.get("odpt:trainNumber")
                if train_number in tracked_delayed_trains and \
                   tracked_delayed_trains[train_number]["consecutive_increase_count"] >= GROUP_ANALYSIS_THRESHOLD:
                    is_delayed_station = True
                    break
        
        if is_delayed_station:
            # 不審な駅を見つけた
            grace_count = 0 # 猶予カウントをリセット
            if current_cluster is None:
                current_cluster = {"indices": [index], "trains": trains_at_this_station}
            else:
                current_cluster["indices"].append(index)
                current_cluster["trains"].extend(trains_at_this_station)
        else:
            # 無遅延の駅を見つけた
            if current_cluster is not None:
                grace_count += 1
                if grace_count > GRACE_STATION_COUNT:
                    clusters.append(current_cluster)
                    current_cluster = None
                    grace_count = 0
    
    if current_cluster is not None: # 最後のクラスターを追加
        clusters.append(current_cluster)

    # 3. 各クラスターを分析 (今は最大のクラスターだけを返す簡易版)
    # TODO: 将来的に複数クラスターを返すようにしても良い
    if not clusters:
        return None

    # 最も多くの列車を含むクラスターを「主犯」とする
    main_cluster = max(clusters, key=lambda c: len(c["trains"]))

    # --- クラスターの分析 ---
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

    # (方向の日本語決定ロジック)
    direction_text = "上下線" # デフォルト
    if "odpt.RailDirection:Inbound" in directions_set and "odpt.RailDirection:Outbound" in directions_set: direction_text = "上下線"
    elif "odpt.RailDirection:Northbound" in directions_set and "odpt.RailDirection:Southbound" in directions_set: direction_text = "上下線"
    elif "odpt.RailDirection:InnerLoop" in directions_set and "odpt.RailDirection:OuterLoop" in directions_set: direction_text = "内外回り"
    else:
        found_directions = [RAIL_DIRECTION_NAMES.get(d, "不明") for d in directions_set]
        direction_text = "・".join(set(found_directions)) if found_directions else "上下線"
    
    # (範囲の特定ロジック)
    min_index = min(main_cluster["indices"])
    max_index = max(main_cluster["indices"])
    range_text = f"{station_list[min_index]}～{station_list[max_index]}"
    if min_index == max_index:
         range_text = f"{station_list[min_index]}駅付近"

    cause_station_jp = range_text # デフォルト
    if cause_location_id:
        cause_station_en = cause_location_id.split('.')[-1]
        cause_station_jp = STATION_DICT.get(cause_station_en, cause_station_en) + "駅付近"

    # 5. 分析結果を辞書で返す
    return {
        "range_text": range_text,
        "direction_text": direction_text,
        "max_delay_minutes": int(max_delay / 60),
        "cause_station_jp": cause_station_jp,
        "suspicious_trains": main_cluster["trains"] # このクラスターに属する列車
    }

# --- メイン関数 (修正版) ---
def check_delay_increase(official_info: Dict[str, Dict[str, Any]]) -> Optional[List[str]]:
    global tracked_delayed_trains, line_cooldown_tracker, line_resumption_notified
    notification_messages: List[str] = []
    current_time = time.time()
    trains_found_this_cycle: set = set()

    try:
        params = {"odpt:operator": "odpt.Operator:JR-East", "acl:consumerKey": API_TOKEN}
        response = requests.get(API_ENDPOINT, params=params, timeout=45)
        response.raise_for_status()
        train_data = response.json()
        if not isinstance(train_data, list): return None

        # --- 1. 全列車を路線ごとに分類 ---
        all_trains_by_line: Dict[str, List[Dict[str, Any]]] = {}
        for train in train_data:
            line_id = train.get("odpt:railway")
            if not line_id: continue
            if line_id not in all_trains_by_line:
                all_trains_by_line[line_id] = []
            all_trains_by_line[line_id].append(train)

        # --- 2. 追跡リストを更新 ---
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
                        direction_text = "上下線"
                        max_delay = int(tracking_info["last_delay"] / 60)
                        
                        if analysis_result: # まだ一部が遅れている場合
                            range_text = analysis_result["range_text"]
                            direction_text = analysis_result["direction_text"]
                            max_delay = analysis_result["max_delay_minutes"]
                            message = (
                                f"【{line_name_jp} 運転再開】\n"
                                f"{STATION_DICT.get(tracking_info['last_location_id'].split('.')[-1], '不明な場所')}駅付近の列車は動き出しましたが、"
                                f"なお、現在も{range_text}の{direction_text}で遅延が継続しています。(最大{max_delay}分遅れ)"
                            )
                        else: # 分析結果が空＝完全復旧
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
                        tracking_info["notified_initial"] = True # ★まず旗を立てる
                        
                        line_info = official_info.get(line_id, {})
                        current_official_status = line_info.get("odpt:trainInformationStatus", {}).get("ja")
                        
                        if current_official_status == "運転見合わせ":
                            print(f"--- [DELAY WATCH] Train {train_number}: Skipping initial notice (Official status is '運転見合わせ').", flush=True)
                        else:
                            last_notification_time = line_cooldown_tracker.get(line_id, 0)
                            if current_time - last_notification_time > COOLDOWN_SECONDS:
                                line_train_list = all_trains_by_line.get(line_id, [])
                                analysis_result = _analyze_group_delay(line_id, line_name_jp, line_train_list)
                                if analysis_result:
                                    official_cause_text = line_info.get("odpt:trainInformationCause", {}).get("ja")
                                    cause_text = f"{official_cause_text}の影響" if official_cause_text else "何らかの事象"
                                    
                                    message = (
                                        f"【{line_name_jp} 運転見合わせ】\n"
                                        f"{line_name_jp}は、{analysis_result['cause_station_jp']}で発生した{cause_text}で、"
                                        f"{analysis_result['range_text']}の{analysis_result['direction_text']}で運転を見合わせています。"
                                        f"(最大{analysis_result['max_delay_minutes']}分遅れ)"
                                    )
                                    notification_messages.append(message)
                                    line_cooldown_tracker[line_id] = current_time
                                    line_resumption_notified[line_id] = False
                                    print(f"--- [DELAY WATCH] !!! GROUP NOTICE SENT for line {line_name_jp} !!!", flush=True)
                            else:
                                print(f"--- [DELAY WATCH] Train {train_number}: Initial threshold reached, but line {line_name_jp} in cooldown.", flush=True)
                    
                    # --- 再通知 (カウント10) ---
                    if count >= ESCALATION_NOTICE_THRESHOLD and tracking_info.get("notified_initial", False) and not tracking_info.get("notified_escalated", False):
                         line_train_list = all_trains_by_line.get(line_id, [])
                         analysis_result = _analyze_group_delay(line_id, line_name_jp, line_train_list)
                         if analysis_result:
                             line_info = official_info.get(line_id, {})
                             official_cause_text = line_info.get("odpt:trainInformationCause", {}).get("ja")
                             cause_text = f"{official_cause_text}の対処が長引いている影響" if official_cause_text else "何らかの事象の対処が長引いている影響"

                             message = (
                                 f"【{line_name_jp} 運転見合わせ[継続]】\n"
                                 f"{line_name_jp}は、{analysis_result['cause_station_jp']}で発生した{cause_text}で、"
                                 f"{analysis_result['range_text']}の{analysis_result['direction_text']}で運転を見合わせています。"
                                 f"(最大{analysis_result['max_delay_minutes']}分遅れ)"
                             )
                             notification_messages.append(message)
                             
                             for train_info in analysis_result["suspicious_trains"]:
                                 train_num = train_info.get("odpt:trainNumber")
                                 if train_num and train_num in tracked_delayed_trains:
                                     tracked_delayed_trains[train_num]["notified_escalated"] = True
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
        import traceback
        print(f"--- [DELAY WATCH] ERROR: Unexpected error: {e}", flush=True)
        traceback.print_exc()
        return None