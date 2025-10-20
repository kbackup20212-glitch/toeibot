import os
import requests
import time
from typing import Dict, Any, List, Optional

# --- jr_east_detector.py から共通データをインポート ---
try:
    from jr_east_detector import STATION_DICT, JR_LINES_TO_MONITOR
    # JR_LINES_TO_MONITOR から路線IDと日本語名の辞書を作成
    JR_LINE_NAMES = {line.get("id"): line.get("name", line.get("id", "").split('.')[-1])
                     for line in JR_LINES_TO_MONITOR if line.get("id")}
except ImportError:
    print("--- [DELAY WATCH] WARNING: jr_east_detector.py から共通データをインポートできませんでした。 ---", flush=True)
    # フォールバック (もしインポートに失敗した場合の最小限の定義)
    STATION_DICT = {'Tokyo': '東京', 'Shinjuku': '新宿'}
    JR_LINES_TO_MONITOR = []
    JR_LINE_NAMES = {}

API_TOKEN = os.getenv('ODPT_TOKEN_CHALLENGE')
API_ENDPOINT = "https://api-challenge.odpt.org/api/v4/odpt:Train" # 在線情報のエンドポイント

# --- 監視対象の列車情報を保持する辞書 ---
tracked_delayed_trains: Dict[str, Dict[str, Any]] = {}

# --- 設定値 ---
DELAY_THRESHOLD_SECONDS = 3 * 60
INCREASE_COUNT_THRESHOLD = 5
CLEANUP_THRESHOLD_SECONDS = 15 * 60

# --- メイン関数 ---
def check_delay_increase() -> Optional[List[str]]:
    global tracked_delayed_trains
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

            if not all([train_number, line_id, current_location_id]): continue
            if train_number is None: continue

            trains_found_this_cycle.add(train_number)

            if train_number in tracked_delayed_trains:
                tracking_info = tracked_delayed_trains[train_number]

                # ▼▼▼▼▼ ここからリセット条件を修正 ▼▼▼▼▼
                # 条件①：場所が変わったか？
                moved = current_location_id != tracking_info["last_location_id"]
                # 条件②：遅延が閾値未満に回復したか？
                recovered = current_delay < DELAY_THRESHOLD_SECONDS

                if moved or recovered:
                    # 場所が変わったか、遅延が回復したらリセット
                    if moved: print(f"--- [DELAY WATCH] Train {train_number}: Reset (moved).", flush=True)
                    if recovered: print(f"--- [DELAY WATCH] Train {train_number}: Reset (delay recovered).", flush=True)
                    del tracked_delayed_trains[train_number]
                
                # 条件③：場所は同じで遅延が増加したか？ (横ばいや微減は無視)
                elif current_delay > tracking_info["last_delay"]:
                    tracking_info["consecutive_increase_count"] += 1
                    tracking_info["last_delay"] = current_delay
                    tracking_info["last_seen_time"] = current_time # 最終確認時刻は常に更新
                    
                    print(f"--- [DELAY WATCH] Train {train_number}: Count {tracking_info['consecutive_increase_count']}/{INCREASE_COUNT_THRESHOLD} at {current_location_id}", flush=True)

                    if tracking_info["consecutive_increase_count"] >= INCREASE_COUNT_THRESHOLD:
                        # インポートした辞書を使う
                        line_name_jp = JR_LINE_NAMES.get(line_id, line_id.split('.')[-1])
                        location_name_en = current_location_id.split('.')[-1]
                        location_name_jp = STATION_DICT.get(location_name_en, location_name_en)
                        
                        message = (
                            f"[{line_name_jp} 運転見合わせの可能性あり]\n"
                            f"{line_name_jp}は{location_name_jp}駅付近で何らかのトラブルが発生した可能性があります。"
                            f"今後の運行情報にご注意ください。"
                        )
                        notification_messages.append(message)
                        del tracked_delayed_trains[train_number] # 通知したら削除
                        print(f"--- [DELAY WATCH] !!! NOTIFICATION SENT for Train {train_number} !!!", flush=True)
                
                else: # 場所は同じで、遅延が横ばい or 微減の場合
                    # 何もしない (追跡を継続)
                    tracking_info["last_seen_time"] = current_time # 最終確認時刻だけ更新
                    print(f"--- [DELAY WATCH] Train {train_number}: Condition stable/slightly decreased at {current_location_id}. Continuing track.", flush=True)
                # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

            elif current_delay >= DELAY_THRESHOLD_SECONDS: # 新規追跡
                 print(f"--- [DELAY WATCH] Train {train_number}: Start tracking (Delay={current_delay}s at {current_location_id}).", flush=True)
                 tracked_delayed_trains[train_number] = {
                     "line_id": line_id,
                     "last_location_id": current_location_id,
                     "last_delay": current_delay,
                     "consecutive_increase_count": 1,
                     "last_seen_time": current_time
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