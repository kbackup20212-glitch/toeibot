import os
import requests
import time
from typing import Dict, Any, List, Optional

# --- toei_detector.py から共通データをインポート ---
try:
    # 駅名辞書をインポート
    from toei_detector import STATION_DICT 
    # 監視対象リストから路線IDと日本語名の辞書を作成
    from toei_detector import TOEI_LINES_TO_MONITOR
    TOEI_LINE_NAMES = {line.get("id"): line.get("name", line.get("id", "").split('.')[-1])
                       for line in TOEI_LINES_TO_MONITOR if line.get("id")}
except ImportError:
    print("--- [TOEI DELAY WATCH] WARNING: toei_detector.py から共通データをインポートできませんでした。 ---", flush=True)
    # フォールバック (最小限の定義)
    STATION_DICT = {'Shinjuku': '新宿', 'Otemachi': '大手町'}
    TOEI_LINE_NAMES = {}

# 都営地下鉄用のトークン
API_TOKEN = os.getenv('ODPT_TOKEN_TOEI')
# 在線情報のエンドポイント (JRと同じ)
API_ENDPOINT = "https://api.odpt.org/api/v4/odpt:Train" 

# --- 監視対象の列車情報を保持する辞書 ---
tracked_delayed_trains: Dict[str, Dict[str, Any]] = {}
# --- 路線ごとの通知クールダウン用辞書 ---
line_cooldown_tracker: Dict[str, float] = {}

# --- 設定値 (JR版と同じ値を流用) ---
DELAY_THRESHOLD_SECONDS = 3 * 60  # 3分 (180秒)
INCREASE_COUNT_THRESHOLD = 5      # 5回連続
ESCALATION_NOTICE_THRESHOLD = 10 
CLEANUP_THRESHOLD_SECONDS = 15 * 60 # 15分
COOLDOWN_SECONDS = 30 * 60 # 30分

# --- メイン関数 ---
def check_toei_delay_increase() -> Optional[List[str]]:
    """
    都営地下鉄の全列車を監視し、遅延が同一箇所で増加し続けている
    運転見合わせの可能性のある列車を検知して通知メッセージを返す。
    """
    global tracked_delayed_trains, line_cooldown_tracker
    notification_messages: List[str] = []
    current_time = time.time()
    trains_found_this_cycle: set = set()

    try:
        # 1. 全列車データを取得 (OperatorをToeiに指定)
        params = {"odpt:operator": "odpt.Operator:Toei", "acl:consumerKey": API_TOKEN}
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

            # 2. 遅延列車を記録・更新
            if train_number in tracked_delayed_trains:
                tracking_info = tracked_delayed_trains[train_number]
                moved = current_location_id != tracking_info["last_location_id"]
                recovered = current_delay < DELAY_THRESHOLD_SECONDS

                # ▼▼▼ リセット処理 (再開通知) ▼▼▼
                if moved or recovered:
                    if tracking_info.get("notified_initial", False):
                        line_name_jp = TOEI_LINE_NAMES.get(line_id, line_id.split('.')[-1])
                        location_name_en = tracking_info["last_location_id"].split('.')[-1]
                        location_name_jp = STATION_DICT.get(location_name_en, location_name_en)
                        reason = "運転再開を確認" if moved else "遅延が回復"
                        message = f"【{line_name_jp} 運転再開】\n{location_name_jp}駅付近で停止していた列車の{reason}しました。(遅延: {int(current_delay / 60)}分)"
                        notification_messages.append(message)
                        print(f"--- [TOEI DELAY WATCH] !!! RESUMPTION NOTICE for Train {train_number} !!! Reason: {reason}", flush=True)
                    if moved: print(f"--- [TOEI DELAY WATCH] Train {train_number}: Reset (moved).", flush=True)
                    if recovered: print(f"--- [TOEI DELAY WATCH] Train {train_number}: Reset (delay recovered).", flush=True)
                    del tracked_delayed_trains[train_number]
                
                # ▼▼▼ 遅延増加処理 (通知判定) ▼▼▼
                elif current_delay > tracking_info["last_delay"]:
                    tracking_info["consecutive_increase_count"] += 1
                    tracking_info["last_delay"] = current_delay
                    tracking_info["last_seen_time"] = current_time
                    count = tracking_info["consecutive_increase_count"]
                    print(f"--- [TOEI DELAY WATCH] Train {train_number}: Count {count}/{INCREASE_COUNT_THRESHOLD} at {current_location_id}", flush=True)

                    line_name_jp = TOEI_LINE_NAMES.get(line_id, line_id.split('.')[-1])
                    location_name_en = current_location_id.split('.')[-1]
                    location_name_jp = STATION_DICT.get(location_name_en, location_name_en)

                    # --- 最初の通知判定 ---
                    if count >= INCREASE_COUNT_THRESHOLD and not tracking_info.get("notified_initial", False):
                        last_notification_time = line_cooldown_tracker.get(line_id, 0)
                        if current_time - last_notification_time > COOLDOWN_SECONDS:
                            message = (
                                f"【{line_name_jp} 運転見合わせ】\n"
                                f"{line_name_jp}は{location_name_jp}駅付近で何らかのトラブルが発生した可能性があります。"
                                f"今後の情報にご注意ください。(現在遅延: {int(current_delay / 60)}分)"
                            )
                            notification_messages.append(message)
                            line_cooldown_tracker[line_id] = current_time
                            tracking_info["notified_initial"] = True
                            print(f"--- [TOEI DELAY WATCH] !!! INITIAL NOTICE SENT for Train {train_number} !!!", flush=True)
                        else:
                            print(f"--- [TOEI DELAY WATCH] Train {train_number}: Initial threshold reached, but line {line_name_jp} in cooldown.", flush=True)
                    
                    # --- 再通知（エスカレーション）判定 ---
                    elif count >= ESCALATION_NOTICE_THRESHOLD and tracking_info.get("notified_initial", False) and not tracking_info.get("notified_escalated", False):
                         message = (
                             f"【{line_name_jp} 運転見合わせ継続中】\n"
                             f"{location_name_jp}駅付近でのトラブル対応が長引いている可能性があります。"
                             f"(遅延: {int(current_delay / 60)}分)" # 遅延時間も追加
                         )
                         notification_messages.append(message)
                         tracking_info["notified_escalated"] = True # ★再通知フラグを立てる
                         print(f"--- [DELAY WATCH] !!! ESCALATION NOTICE SENT for Train {train_number} !!!", flush=True)
                 

                else: # 遅延が横ばい or 微減
                    tracking_info["last_seen_time"] = current_time
            
            # ▼▼▼ 新規追跡処理 ▼▼▼
            elif current_delay >= DELAY_THRESHOLD_SECONDS:
                 print(f"--- [TOEI DELAY WATCH] Train {train_number}: Start tracking (Delay={current_delay}s at {current_location_id}).", flush=True)
                 tracked_delayed_trains[train_number] = {
                     "line_id": line_id, "last_location_id": current_location_id,
                     "last_delay": current_delay, "consecutive_increase_count": 1,
                     "last_seen_time": current_time,
                     "notified_initial": False, "notified_escalated": False
                 }

        # 4. 古い記録の掃除
        trains_to_remove = [
            train_num for train_num, info in tracked_delayed_trains.items()
            if train_num not in trains_found_this_cycle and current_time - info["last_seen_time"] > CLEANUP_THRESHOLD_SECONDS
        ]
        for train_num in trains_to_remove:
            del tracked_delayed_trains[train_num]
            print(f"--- [TOEI DELAY WATCH] Train {train_num}: Removing track (timeout).", flush=True)

        return notification_messages

    except requests.exceptions.RequestException as req_err:
        print(f"--- [TOEI DELAY WATCH] ERROR: Network error: {req_err}", flush=True)
        return None
    except Exception as e:
        import traceback
        print(f"--- [TOEI DELAY WATCH] ERROR: Unexpected error: {e}", flush=True)
        traceback.print_exc()
        return None