import os
import requests
import time
from typing import Dict, Any, List, Optional

# --- jr_east_detector.py から共通データをインポート ---
try:
    from jr_east_detector import STATION_DICT, JR_LINES_TO_MONITOR
    JR_LINE_NAMES = {line.get("id"): line.get("name", line.get("id", "").split('.')[-1])
                     for line in JR_LINES_TO_MONITOR if line.get("id")}
except ImportError:
    print("--- [DELAY WATCH] WARNING: jr_east_detector.py から共通データをインポートできませんでした。 ---", flush=True)
    STATION_DICT = {'Tokyo': '東京', 'Shinjuku': '新宿'}
    JR_LINES_TO_MONITOR = []
    JR_LINE_NAMES = {}


# --- jr_east_info_detector.py からカルテ棚をインポート ---
try:
    from jr_east_info_detector import JR_LINE_PREDICTION_DATA
    JR_LINE_NAMES = {line.get("id"): line.get("name", line.get("id", "").split('.')[-1])
                     for line in JR_LINES_TO_MONITOR if line.get("id")}
except ImportError:
    print("--- [DELAY WATCH] WARNING: jr_east_info_detector.py からカルテをインポートできませんでした。 ---", flush=True)
    JR_LINE_PREDICTION_DATA = {}

try:
    from jr_east_info_detector import JR_LINE_PREDICTION_DATA
    # ★★★ 方向辞書をインポート ★★★
    from jr_east_info_detector import RAIL_DIRECTION_NAMES
except ImportError:
     JR_LINE_PREDICTION_DATA = {}
     RAIL_DIRECTION_NAMES = {} # ★ 空の辞書を定義



API_TOKEN = os.getenv('ODPT_TOKEN_CHALLENGE')
API_ENDPOINT = "https://api-challenge.odpt.org/api/v4/odpt:Train"

tracked_delayed_trains: Dict[str, Dict[str, Any]] = {}
line_cooldown_tracker: Dict[str, float] = {}


# --- 設定値 ---
DELAY_THRESHOLD_SECONDS = 3 * 60
INCREASE_COUNT_THRESHOLD = 5     # ★★★ 最初の通知を出すカウント ★★★
ESCALATION_NOTICE_THRESHOLD = 10 # ★★★ 再通知を出すカウント ★★★
GROUP_ANALYSIS_THRESHOLD = 2
CLEANUP_THRESHOLD_SECONDS = 15 * 60
COOLDOWN_SECONDS = 30 * 60

# --- ★★★ 新しい分析官（ヘルパー関数） ★★★ ---
def _analyze_group_delay(line_id: str, line_name_jp: str) -> Optional[str]:
    """
    指定された路線の集団遅延を分析し、通知メッセージを作成する。
    """
    global tracked_delayed_trains
    
    # 1. 容疑者リストの作成
    suspicious_trains = []
    for train_num, info in tracked_delayed_trains.items():
        if info["line_id"] == line_id and info["consecutive_increase_count"] >= GROUP_ANALYSIS_THRESHOLD:
            suspicious_trains.append(info)

    if not suspicious_trains:
        return None # 分析対象なし

    # 2. 方向と範囲の特定
    directions_set: set = set()
    affected_locations: set = set()
    for train in suspicious_trains:
        if train.get("direction"): # 記録された方向を追加
            directions_set.add(train["direction"])
        affected_locations.add(train["last_location_id"]) # 止まっている場所を追加

    # 3. 方向の日本語を決定
    direction_text = ""
    
    # 特殊なペアをチェック
    if "odpt.RailDirection:Inbound" in directions_set and "odpt.RailDirection:Outbound" in directions_set:
        direction_text = "上下線"
    elif "odpt.RailDirection:Northbound" in directions_set and "odpt.RailDirection:Southbound" in directions_set:
        direction_text = "南北両方向"
    elif "odpt.RailDirection:InnerLoop" in directions_set and "odpt.RailDirection:OuterLoop" in directions_set:
        direction_text = "内外回り"
    
    # 特殊なペアがなかった場合、個別に翻訳して結合
    else:
        found_directions = []
        for direction_id in directions_set:
            direction_name = RAIL_DIRECTION_NAMES.get(direction_id, "不明")
            if direction_name not in found_directions:
                found_directions.append(direction_name)
        
        if found_directions:
            direction_text = "・".join(found_directions)
        else:
            direction_text = "上下線" # 方向が何もわからなければ、安全のために「上下線」

    # 4. 範囲の特定
    line_map_data = JR_LINE_PREDICTION_DATA.get(line_id, {})
    station_list = line_map_data.get("stations", [])
    
    range_text = "広範囲" # デフォルト
    if station_list:
        min_index = len(station_list)
        max_index = -1
        found_on_map = False
        for location_id in affected_locations:
            station_en = location_id.split('.')[-1]
            station_jp = STATION_DICT.get(station_en, station_en)
            if station_jp in station_list:
                idx = station_list.index(station_jp)
                if idx < min_index: min_index = idx
                if idx > max_index: max_index = idx
                found_on_map = True
        
        if found_on_map:
            if min_index == max_index: # 1駅だけ
                range_text = f"{station_list[min_index]}駅付近"
            else: # 複数駅
                range_text = f"{station_list[min_index]}～{station_list[max_index]}駅間"
    
    # 5. 総合報告メッセージ作成
    message = (
        f"[{line_name_jp} 運転見合わせの可能性あり]\n"
        f"{line_name_jp}は、{range_text}の{direction_text}で何らかのトラブルが発生した可能性があります。"
        f"今後の運行情報にご注意ください。"
    )
    
    # 6. 容疑者全員に「通知済み」フラグを立てる
    for train in suspicious_trains:
        train["notified_initial"] = True

    return message

# --- メイン関数 ---
def check_delay_increase(official_statuses: Dict[str, Optional[str]]) -> Optional[List[str]]:
    global tracked_delayed_trains, line_cooldown_tracker
    notification_messages: List[str] = []
    current_time = time.time()
    trains_found_this_cycle: set = set()

    try:
        params = {"odpt:operator": "odpt.Operator:JR-East", "acl:consumerKey": API_TOKEN}
        response = requests.get(API_ENDPOINT, params=params, timeout=45)
        response.raise_for_status()
        train_data = response.json()
        if not isinstance(train_data, list): return None

        for train in train_data:
            train_number: Optional[str] = train.get("odpt:trainNumber")
            current_delay: int = train.get("odpt:delay", 0)
            line_id: Optional[str] = train.get("odpt:railway")
            current_location_id: Optional[str] = train.get("odpt:toStation") or train.get("odpt:fromStation")
            # ★★★ 1. 方向も取得 ★★★
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
                    if tracking_info.get("notified_initial", False) and not tracking_info.get("notified_resumed", False):
                        line_name_jp = JR_LINE_NAMES.get(line_id, line_id.split('.')[-1])
                        location_name_en = tracking_info["last_location_id"].split('.')[-1] # ★動く前の場所を使う
                        location_name_jp = STATION_DICT.get(location_name_en, location_name_en)
                        
                        reason = "運転再開を確認" if moved else "遅延が回復"
                        message = f"【{line_name_jp} 運転再開】\n{location_name_jp}駅付近で停止していた列車の{reason}しました。(遅延: {int(current_delay / 60)}分)"
                        notification_messages.append(message)
                        print(f"--- [DELAY WATCH] !!! RESUMPTION NOTICE for Train {train_number} !!! Reason: {reason}", flush=True)

                    # 理由に関わらず追跡解除
                    if moved: print(f"--- [DELAY WATCH] Train {train_number}: Reset (moved).", flush=True)
                    if recovered: print(f"--- [DELAY WATCH] Train {train_number}: Reset (delay recovered).", flush=True)
                    tracking_info["notified_resumed"] = True
                    del tracked_delayed_trains[train_number]
                
                # ▼▼▼ 遅延増加処理 (通知判定を修正) ▼▼▼
                elif current_delay > tracking_info["last_delay"]:
                    tracking_info["consecutive_increase_count"] += 1
                    tracking_info["last_delay"] = current_delay
                    tracking_info["last_seen_time"] = current_time
                    if current_direction: # ★方向も更新
                        tracking_info["direction"] = current_direction
                    count = tracking_info["consecutive_increase_count"]
                    
                    print(f"--- [DELAY WATCH] Train {train_number}: Count {count} at {current_location_id}", flush=True)

                    line_name_jp = JR_LINE_NAMES.get(line_id, line_id.split('.')[-1])

                    # --- 最初の通知判定 (カウント5) ---
                    if count >= INCREASE_COUNT_THRESHOLD and not tracking_info.get("notified_initial", False):
                        # ★★★ 2. ここで分析官を呼ぶ ★★★
                        current_official_status = official_statuses.get(line_id)
                        if current_official_status == "運転見合わせ":
                            tracking_info["notified_initial"] = True # フラグだけ立てる
                        else:
                            last_notification_time = line_cooldown_tracker.get(line_id, 0)
                            if current_time - last_notification_time > COOLDOWN_SECONDS:
                                # ★★★ 3. 分析官を呼び出し ★★★
                                message = _analyze_group_delay(line_id, line_name_jp)
                                if message:
                                    notification_messages.append(message)
                                    line_cooldown_tracker[line_id] = current_time
                                    print(f"--- [DELAY WATCH] !!! GROUP NOTICE SENT for line {line_name_jp} !!!", flush=True)
                                # (notified_initialフラグは分析官が立てる)
                            else:
                                print(f"--- [DELAY WATCH] Train {train_number}: Initial threshold reached, but line {line_name_jp} in cooldown.", flush=True)
                            
                    # --- 再通知（エスカレーション）判定 ---
                    if count >= ESCALATION_NOTICE_THRESHOLD and tracking_info.get("notified_initial", False) and not tracking_info.get("notified_escalated", False):
                         message = (
                             f"【{line_name_jp} 運転見合わせ継続中】\n"
                             f"{location_name_jp}駅付近でのトラブル対応が長引いている可能性があります。"
                             f"(遅延: {int(current_delay / 60)}分)" 
                         )
                         notification_messages.append(message)
                         tracking_info["notified_escalated"] = True # ★再通知フラグを立てる
                         print(f"--- [DELAY WATCH] !!! ESCALATION NOTICE SENT for Train {train_number} !!!", flush=True)
                
                else: # 遅延が横ばい or 微減
                    tracking_info["last_seen_time"] = current_time
            
            # ▼▼▼ 新規追跡処理 (notifiedフラグの初期値を追加) ▼▼▼
            elif current_delay >= DELAY_THRESHOLD_SECONDS:
                 print(f"--- [DELAY WATCH] Train {train_number}: Start tracking (Delay={current_delay}s at {current_location_id}).", flush=True)
                 tracked_delayed_trains[train_number] = {
                     "line_id": line_id,
                     "last_location_id": current_location_id,
                     "last_delay": current_delay,
                     "consecutive_increase_count": 1,
                     "last_seen_time": current_time,
                     "direction": current_direction, # ★方向も記録
                     "notified_initial": False, "notified_escalated": False,
                     "notified_resumed": False # ★再開フラグ
                 }

        # 古い記録の掃除
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