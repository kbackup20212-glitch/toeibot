import os
import requests
import re
import time
import traceback # エラーの詳細表示のためにインポート
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
JST = timezone(timedelta(hours=+9))

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
# ▼▼▼▼▼ この一行が抜けていた ▼▼▼▼▼
line_prediction_cooldown_tracker: Dict[str, float] = {}

# --- 設定値 ---
DELAY_THRESHOLD_SECONDS = 3 * 60  # 3分 (180秒)
INITIAL_NOTICE_THRESHOLD = 5      # 最初の通知を出すカウント
ESCALATION_NOTICE_THRESHOLD = 10 # 再通知を出すカウント
GROUP_ANALYSIS_THRESHOLD = 2 # 集団遅延とみなす最低カウント
GRACE_STATION_COUNT = 4           # 集団遅延判定の「猶予」駅数
CLEANUP_THRESHOLD_SECONDS = 15 * 60 # 15分
COOLDOWN_SECONDS = 30 * 60 # 30分

PREDICTION_TIME_MAP = {
    "シカと衝突": 20,
    "異音の確認": 20,
    "動物と衝突": 20,
    "信号確認": 20,
    "信号装置点検": 20,
    "踏切安全確認": 15,
    "線路に人立入": 15,
    "お客さま救護": 15,
    "ホーム上確認": 15,
    "車内点検": 15,
    "車両点検": 15,
    "濃霧": 10,
    "荷物挟まり": 10,
    "ドア点検": 10,
    "車内トラブル": 10,
}

# --- ★★★ 分析官（ヘルパー関数） ★★★ ---
def _analyze_group_delay(line_id: str, line_name_jp: str, all_trains_on_line: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    集団遅延を分析し、「生データ」の辞書を返す。
    「主犯」の列車番号も特定する。
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

    # 3. 最大クラスターの分析 (★ 主犯特定ロジックを追加)
    main_cluster = max(clusters, key=lambda c: len(c["trains"]))
    directions_set: set = set()
    max_delay: int = 0
    main_culprit_count: int = -1
    main_culprit_train_number: Optional[str] = None # ★ 主犯の列車番号
    cause_location_id: Optional[str] = None
    suspicious_train_numbers: List[str] = [] # ★ 集団全員の列車番号

    for train in main_cluster["trains"]:
        if train.get("odpt:railDirection"): directions_set.add(train["odpt:railDirection"])
        if train.get("odpt:delay", 0) > max_delay: max_delay = train.get("odpt:delay", 0)
        train_number = train.get("odpt:trainNumber")
        if train_number in tracked_delayed_trains:
            count = tracked_delayed_trains[train_number]["consecutive_increase_count"]
            if count >= GROUP_ANALYSIS_THRESHOLD:
                 suspicious_train_numbers.append(train_number) # ★ 集団のメンバーとして追加
            if count > main_culprit_count:
                main_culprit_count = count
                main_culprit_train_number = train_number # ★ 主犯を特定
                cause_location_id = train.get("odpt:toStation") or train.get("odpt:fromStation")

    # 4. 方向の日本語決定
    direction_text = "上下線"
    if "odpt.RailDirection:Inbound" in directions_set and "odpt.RailDirection:Outbound" in directions_set: direction_text = "上下線"
    elif "odpt.RailDirection:Northbound" in directions_set and "odpt.RailDirection:Southbound" in directions_set: direction_text = "上下線"
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

    # 6. 分析結果を辞書で返す (★ 返す中身を変更)
    return {
        "range_text": range_text,
        "direction_text": direction_text,
        "max_delay_minutes": int(max_delay / 60),
        "cause_station_jp": cause_station_jp,
        "main_culprit_train_number": main_culprit_train_number, # ★ 主犯の番号
        "suspicious_train_numbers": suspicious_train_numbers # ★ 集団全員の番号
    }

# --- ★★★ 予測時刻計算（ヘルパー関数） ★★★ ---
def _get_resume_prediction_text(line_id: str, line_info: Dict[str, Any], max_delay_seconds: int, current_time: float) -> str:
    global line_prediction_cooldown_tracker
    
    
    print(f"--- [PREDICTION DEBUG @ {line_id}] ---", flush=True) # ★ログ追加
    
    official_cause = line_info.get("odpt:trainInformationCause", {}).get("ja")
    if not official_cause: 
        print(f"  > FAILED: Official cause is missing (None).", flush=True) # ★ログ追加
        return ""

    target_delay_seconds = 0
    found_cause_keyword = "" # ★見つけたキーワードを記録
    for cause_keyword, duration_minutes in PREDICTION_TIME_MAP.items():
        if cause_keyword in official_cause:
            target_delay_seconds = duration_minutes * 60
            found_cause_keyword = cause_keyword # ★記録
            break
    
    if not target_delay_seconds: 
        print(f"  > FAILED: Cause '{official_cause}' is not in PREDICTION_TIME_MAP.", flush=True) # ★ログ追加
        return ""

    print(f"  > Check 1: Cause '{found_cause_keyword}' found. Rule is {target_delay_seconds // 60} mins.", flush=True) # ★ログ追加
    
    # 条件: 0 < 最大遅延 < ルール時間
    if not (0 < max_delay_seconds < target_delay_seconds):
        print(f"  > FAILED: Max delay ({max_delay_seconds}s) is not within the rule range (0 ~ {target_delay_seconds}s).", flush=True) # ★ログ追加
        return ""
    
    print(f"  > Check 2: Delay ({max_delay_seconds}s) is within range. OK.", flush=True) # ★ログ追加
    
    last_prediction_time = line_prediction_cooldown_tracker.get(line_id, 0)
    if not (current_time - last_prediction_time > COOLDOWN_SECONDS):
        print(f"  > FAILED: Line is still in prediction cooldown.", flush=True) # ★ログ追加
        return ""
    
    print(f"  > Check 3: Cooldown check passed. OK.", flush=True) # ★ログ追加

    # すべてのチェックを通過
    seconds_to_reach_target = target_delay_seconds - max_delay_seconds
    predicted_time_dt = datetime.fromtimestamp(current_time + seconds_to_reach_target, JST)
    predicted_time_str = predicted_time_dt.strftime('%H:%M')
    line_prediction_cooldown_tracker[line_id] = current_time
    print(f"--- [DELAY WATCH] !!! RESUME PREDICTION SENT for {line_id} ({predicted_time_str}) !!!", flush=True)
    return f"\nなお、運転再開は{predicted_time_str}頃になると予測しています。"

# --- メイン関数 (バグ修正・完全版) ---
def check_delay_increase(official_info: Dict[str, Dict[str, Any]]) -> Optional[List[str]]:
    global tracked_delayed_trains, line_cooldown_tracker, line_resumption_notified
    notification_messages: List[str] = []
    current_time = time.time()
    trains_found_this_cycle: set = set()

    # 1. 列車在線データを取得
    try:
        params = {"odpt:operator": "odpt.Operator:JR-East", "acl:consumerKey": API_TOKEN}
        response = requests.get(API_ENDPOINT, params=params, timeout=45)
        response.raise_for_status()
        train_data = response.json()
        if not isinstance(train_data, list): return None

        # 2. 路線ごとの全列車リストと、最大遅延を集計
        all_trains_by_line: Dict[str, List[Dict[str, Any]]] = {}
        max_delay_by_line: Dict[str, int] = {} # ★ 箱は用意されてるけど...
        for train in train_data:
            line_id = train.get("odpt:railway")
            if not line_id: continue
            if line_id not in all_trains_by_line: all_trains_by_line[line_id] = []
            all_trains_by_line[line_id].append(train)
            
            # ★★★ ここの計算が正しいか？ ★★★
            current_delay = train.get("odpt:delay", 0)
            if current_delay > max_delay_by_line.get(line_id, 0):
                max_delay_by_line[line_id] = current_delay

        # 4. 既存の「不審遅延」ロジック (追跡リスト更新)
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

                # ▼▼▼ リセット処理 (★君のアイデアで、ロジックを大幅に簡略化) ▼▼▼
                if moved or recovered:
                    
                    # ★ 1. 動いたのが「主犯」で、かつ「路線再開」がまだ未通知か？
                    if tracking_info.get("is_main_culprit", False) and not line_resumption_notified.get(line_id, False):
                        line_name_jp = JR_LINE_NAMES.get(line_id, line_id.split('.')[-1])
                        range_text = STATION_DICT.get(tracking_info["last_location_id"].split('.')[-1], "不明な場所")
                        
                        # ★ 2. もう「一部再開」は気にせず、「完全再開」通知だけを送る
                        message = (
                            f"【{line_name_jp} 運転再開】\n"
                            f"{range_text}駅付近のトラブルは解消した模様です。運転を順次再開しました。(最大{int(current_delay / 60)}分遅れ)"
                        )
                        notification_messages.append(message)
                        line_resumption_notified[line_id] = True # ★ 3. 路線再開フラグを立てる
                        print(f"--- [DELAY WATCH] !!! MAIN CULPRIT MOVED. FULL RESUMPTION NOTICE SENT for line {line_name_jp} !!!", flush=True)

                    # ★ 4. 「主犯」じゃなかったら、ログだけ出して静かに消す
                    if moved: print(f"--- [DELAY WATCH] Train {train_number}: Reset (moved).", flush=True)
                    if recovered: print(f"--- [DELAY WATCH] Train {train_number}: Reset (delay recovered).", flush=True)
                    del tracked_delayed_trains[train_number]
                # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
                
                # ▼▼▼ 遅延増加処理 ▼▼▼
                elif current_delay > tracking_info["last_delay"]:
                    tracking_info["consecutive_increase_count"] += 1
                    tracking_info["last_delay"] = current_delay
                    tracking_info["last_seen_time"] = current_time
                    if current_direction: tracking_info["direction"] = current_direction
                    count = tracking_info["consecutive_increase_count"]
                    print(f"--- [DELAY WATCH] Train {train_number}: Count {count} at {current_location_id}", flush=True)
                    
                    line_name_jp = JR_LINE_NAMES.get(line_id, line_id.split('.')[-1])
                    location_name_en = current_location_id.split('.')[-1]
                    location_name_jp = STATION_DICT.get(location_name_en, location_name_en)

                    # --- 最初の通知判定 (カウント5) ---
                    if count >= INITIAL_NOTICE_THRESHOLD and not tracking_info.get("notified_initial", False):
                        line_info = official_info.get(line_id, {})
                        current_official_status = line_info.get("odpt:trainInformationStatus", {}).get("ja")
                        
                        if current_official_status == "運転見合わせ":
                            print(f"--- [DELAY WATCH] Train {train_number}: Skipping initial notice (Official status is '運転見合わせ').", flush=True)
                            tracking_info["notified_initial"] = True # ★公式発表済みなら、旗1だけ立てる
                        else:
                            cooldown_key = line_id
                            if line_id == "odpt.Railway:JR-East.Chuo":
                                cooldown_key = "JR-East.Chuo.Takao" if location_name_jp == "高尾" else "JR-East.Chuo.Other"
                            
                            last_notification_time = line_cooldown_tracker.get(cooldown_key, 0)
                            if current_time - last_notification_time > COOLDOWN_SECONDS:
                                line_train_list = all_trains_by_line.get(line_id, [])
                                analysis_result = _analyze_group_delay(line_id, line_name_jp, line_train_list)
                                
                                # ▼▼▼▼▼ ここが修正箇所 ▼▼▼▼▼
                                # ★ まず、分析失敗時の「代わりの範囲」を用意
                                range_text = f"{location_name_jp}駅付近"
                                
                                if analysis_result:
                                    # ▼▼▼▼▼ ここからが修正箇所 ▼▼▼▼▼
                                    line_info = official_info.get(line_id, {}) # (この行はたぶんもうある)
                                    status_to_check = line_info.get("odpt:trainInformationText", {}).get("ja", "")

                                    # ★ 1. まず「公式原因」を最優先で取得
                                    official_cause_text = line_info.get("odpt:trainInformationCause", {}).get("ja")
                                    cause_text = official_cause_text if official_cause_text else "何らかの事象" # 取得できなければ「何らか」

                                    # ★ 2. 次に「場所」を正規表現で探す
                                    location_text = analysis_result['cause_station_jp'] # デフォルトは分析官の推測
                                    reason_match = re.search(r'(.+?(?:駅|駅間))で(?:の)?', status_to_check) # 「影響で」まで見ない
                                    if reason_match:
                                        location_part = reason_match.group(1).strip()
                                        actual_location = re.split(r'[、\s]', location_part)[-1] if location_part else location_part
                                        location_text = f"{actual_location}での" # 「での」を付ける
                                    
                                    # ▼▼▼▼▼ 発生時刻を計算 ▼▼▼▼▼
                                    event_time_str = ""
                                    # 監視開始時刻 (Count 1) から3分引いて、事故発生時刻(Count 0)を推測
                                    tracking_start_time = tracking_info.get("tracking_start_time")
                                    if tracking_start_time:
                                        event_timestamp = tracking_start_time - 180 # 3分(180秒)前と仮定
                                        event_time_dt = datetime.fromtimestamp(event_timestamp, JST)
                                        event_time_str = event_time_dt.strftime('%H:%M頃、') # 「、」も付ける
                                    
                                    message = (
                                        f"【{line_name_jp} 運転見合わせ】\n"
                                        f"{event_time_str}{location_text}{cause_text}の影響で、" # ★ 時刻と原因と場所を合体
                                        f"{analysis_result['range_text']}の{analysis_result['direction_text']}で運転を見合わせています。"
                                        f"(最大{analysis_result['max_delay_minutes']}分遅れ)"
                                    )
                                
                                notification_messages.append(message)
                                line_cooldown_tracker[cooldown_key] = current_time
                                line_resumption_notified[line_id] = False
                                
                                # ★★★ 旗1（集団）と 旗2（主犯）を立てる ★★★
                                if analysis_result:
                                    main_culprit_num = analysis_result["main_culprit_train_number"]
                                    for train_num in analysis_result["suspicious_train_numbers"]:
                                        if train_num in tracked_delayed_trains:
                                            tracked_delayed_trains[train_num]["notified_initial"] = True # 旗1
                                            if train_num == main_culprit_num:
                                                tracked_delayed_trains[train_num]["is_main_culprit"] = True # 旗2
                                                print(f"--- [DELAY WATCH] Train {train_num} is now MAIN CULPRIT.", flush=True)
                                else:
                                    tracking_info["notified_initial"] = True # 分析失敗でも、トリガーになったやつには旗1を立てる

                                print(f"--- [DELAY WATCH] !!! GROUP NOTICE SENT for {cooldown_key} !!!", flush=True)
                            
                            else: # クールダウン中
                                print(f"--- [DELAY WATCH] Train {train_number}: Initial threshold reached, but area {cooldown_key} is in cooldown.", flush=True)
                                # ★ クールダウンなら旗は立てない
                        
                    else: # 公式が運転見合わせ
                        print(f"--- [DELAY WATCH] Train {train_number}: Skipping initial notice (Official status is '運転見合わせ').", flush=True)
                            # ★ 公式見合わせでも、旗は立てない (再開通知は公式情報に任せる)
                    
                    # --- 再通知 (カウント10) ---
                    # ★★★「主犯」だけが継続通知をトリガーする ★★★
                    if count >= ESCALATION_NOTICE_THRESHOLD and tracking_info.get("is_main_culprit", False) and not tracking_info.get("notified_escalated", False):
                         line_info = official_info.get(line_id, {})
                         current_official_status = line_info.get("odpt:trainInformationStatus", {}).get("ja")

                         # もし公式が「運転見合わせ」と発表していたら、[継続]通知はスキップ
                         if current_official_status == "運転見合わせ":
                             print(f"--- [DELAY WATCH] Train {train_number}: Skipping escalation notice (Official status is already '運転見合わせ').", flush=True)
                             tracking_info["notified_escalated"] = True # フラグだけ立てる
                         
                         else: # 公式が「遅延」などの場合のみ、[継続]通知を出す
                             line_train_list = all_trains_by_line.get(line_id, [])
                             analysis_result = _analyze_group_delay(line_id, line_name_jp, all_trains_by_line.get(line_id, []))
                             
                             # ▼▼▼▼▼ ここが修正箇所 ▼▼▼▼▼
                             # ★ まず、分析失敗時の「代わりの範囲」を用意
                             range_text = f"{location_name_jp}駅付近での"
                             
                             if analysis_result:
                                 # (原因特定ロジックは変更なし)
                                 line_info = official_info.get(line_id, {})
                                 status_to_check = line_info.get("odpt:trainInformationText", {}).get("ja", "")

                                 # ▼▼▼▼▼ ここも同じように修正 ▼▼▼▼▼
                                 # ★ 1. まず「公式原因」を最優先で取得
                                 official_cause_text = line_info.get("odpt:trainInformationCause", {}).get("ja")
                                 cause_text = official_cause_text if official_cause_text else "何らかの事象"
                                 
                                 # ★ 2. 次に「場所」を正規表現で探す
                                 location_text = analysis_result['cause_station_jp'] # デフォルト
                                 reason_match = re.search(r'(.+?(?:駅|駅間))で(?:の)?', status_to_check)
                                 if reason_match:
                                     location_part = reason_match.group(1).strip()
                                     actual_location = re.split(r'[、\s]', location_part)[-1] if location_part else location_part
                                     location_text = f"{actual_location}での"
                                
                                 event_time_str = ""
                                 tracking_start_time = tracking_info.get("tracking_start_time")
                                 if tracking_start_time:
                                     event_timestamp = tracking_start_time - 180 
                                     event_time_dt = datetime.fromtimestamp(event_timestamp, JST)
                                     event_time_str = event_time_dt.strftime('%H:%M頃、')
                                 
                                 message = (
                                     f"【{line_name_jp} 運転見合わせ[継続]】\n"
                                     f"{event_time_str}{location_text}{cause_text}の対処が長引いている影響で、" # ★ 合体
                                     f"{analysis_result['range_text']}の{analysis_result['direction_text']}で運転を見合わせています。"
                                     f"(最大{analysis_result['max_delay_minutes']}分遅れ)"
                                 )
                             else:
                                 # ★ 分析失敗したら、デフォルトの本文を使う
                                 message_body = f"{line_name_jp}は、{range_text}でのトラブル対応が長引いている可能性があります。(最大{int(current_delay / 60)}分遅れ)"

                             # --- 予測時刻を計算 ---
                             max_delay_seconds = 0 # まず初期化
                             if analysis_result:
                                    # ★ 分析結果（例: 20分）を秒に直して使う
                                max_delay_seconds = analysis_result['max_delay_minutes'] * 60
                             else:
                                    # ★ 分析失敗なら、その列車の遅延を使う
                                max_delay_seconds = current_delay 
                                
                             prediction_text = _get_resume_prediction_text(line_id, line_info, max_delay_seconds, current_time)
                             
                             # --- メッセージを組み立て ---
                             message = f"【{line_name_jp} 運転見合わせ[継続]】\n{message_body}{prediction_text}"
                             
                             notification_messages.append(message)
                             tracking_info["notified_escalated"] = True # ★ 主犯に「再通知済み」の旗を立てる
                             print(f"--- [DELAY WATCH] !!! ESCALATION NOTICE SENT for line {line_name_jp} !!!", flush=True)

                else: # 遅延が横ばい or 微減
                    tracking_info["last_seen_time"] = current_time
                    
            
            # ▼▼▼ 新規追跡処理 ▼▼▼
            elif current_delay >= DELAY_THRESHOLD_SECONDS:
                 tracked_delayed_trains[train_number] = {
                     "line_id": line_id, "last_location_id": current_location_id,
                     "last_delay": current_delay, "consecutive_increase_count": 1,
                     "last_seen_time": current_time, "direction": current_direction,
                     "notified_initial": False, # 旗1
                     "is_main_culprit": False,  # ★ 旗2
                     "notified_escalated": False,
                     "notified_resumed": False 
                 }
        
        # --- 4. 古い記録の掃除 ---
        trains_to_remove = [
            train_num for train_num, info in tracked_delayed_trains.items()
            if train_num not in trains_found_this_cycle and current_time - info["last_seen_time"] > CLEANUP_THRESHOLD_SECONDS
        ]
        for train_num in trains_to_remove:
            info = tracked_delayed_trains[train_num]
            if info.get("is_main_culprit", False) and not line_resumption_notified.get(info["line_id"], False):
                line_id = info["line_id"]
                line_name_jp = JR_LINE_NAMES.get(line_id, line_id.split('.')[-1])
                location_name_jp = STATION_DICT.get(info["last_location_id"].split('.')[-1], info["last_location_id"].split('.')[-1])
                
                message = f"【{line_name_jp} 運転再開】\n{location_name_jp}駅付近で停止していた列車の情報が更新されなくなりました。運転を再開した可能性があります。"
                notification_messages.append(message)
                line_resumption_notified[line_id] = True
            
            
            del tracked_delayed_trains[train_num]


        return notification_messages

    except requests.exceptions.RequestException as req_err:
        print(f"--- [DELAY WATCH] ERROR: Network error: {req_err}", flush=True)
        return None
    except Exception as e:
        print(f"--- [DELAY WATCH] ERROR: Unexpected error: {e}", flush=True)
        traceback.print_exc()
        return None