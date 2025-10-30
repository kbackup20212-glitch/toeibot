import os
import requests
import re
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta # ★ 曜日と日付の確認に必要
import traceback

# --- 共通データのインポート ---
try:
    from jr_east_detector import STATION_DICT, TRAIN_TYPE_NAMES
except ImportError:
    print("--- [DEST PRED] WARNING: jr_east_detector.py から辞書をインポートできませんでした。 ---", flush=True)
    STATION_DICT = {'Otsuki': '大月', 'Shiotsu': '四方津'} # 仮定義
    TRAIN_TYPE_NAMES = {'odpt.TrainType:JR-East.Rapid': '快速'} # 仮定義

API_TOKEN = os.getenv('ODPT_TOKEN_CHALLENGE')
API_ENDPOINT = "https://api-challenge.odpt.org/api/v4/odpt:Train" # 在線情報のエンドポイント
JST = timezone(timedelta(hours=+9)) # 日本時間

# --- 予測済みの通知を記録する辞書 ---
# キー: "列車番号_日付" (例: "1971T_2025-10-28")
# 値: UNIXタイムスタンプ (古い記録を掃除するため)
notified_predictions: Dict[str, float] = {}

# --- 設定値 ---
PREDICTION_DELAY_THRESHOLD = 30 * 60 # 30分 (1800秒)

# --- メイン関数 ---
# --- メイン関数 (お試しルール追加版) ---
def check_destination_predictions() -> Optional[List[str]]:
    """
    特定の条件を満たした列車の行先変更を予測し、通知メッセージのリストを返す。
    """
    global notified_predictions
    notification_messages: List[str] = []
    current_time = time.time()
    
    # --- 曜日と日付を取得 ---
    now_jst = datetime.now(JST)
    today_weekday = now_jst.weekday() # 0=月, 1=火, ..., 5=土, 6=日
    today_date_str = now_jst.strftime('%Y-%m-%d')
    
    # 平日(0-4)か、休日(5-6)かを判断
    is_weekday = today_weekday <= 4
    is_holiday = today_weekday >= 5

    try:
        # 1. 中央線快速の在線データを取得
        params = {"odpt:railway": "odpt.Railway:JR-East.ChuoRapid", "acl:consumerKey": API_TOKEN}
        response = requests.get(API_ENDPOINT, params=params, timeout=45)
        response.raise_for_status()
        train_data = response.json()
        if not isinstance(train_data, list): return None

        for train in train_data:
            train_number: Optional[str] = train.get("odpt:trainNumber")
            current_delay: int = train.get("odpt:delay", 0)
            dest_station_id_list: Optional[List[str]] = train.get("odpt:destinationStation")
            
            if not all([train_number, dest_station_id_list]): continue
            
            dest_station_en = dest_station_id_list[-1].split('.')[-1].strip()
            
            # --- 2. ルールブックと照合 ---
            prediction_key: Optional[str] = None
            new_destination_jp: str = ""
            
            # (1) 平日・特定列車ルール
            if is_weekday and train_number == "1971T" and dest_station_en == "Otsuki" and current_delay >= PREDICTION_DELAY_THRESHOLD:
                prediction_key = f"{train_number}_{today_date_str}"
                new_destination_jp = "四方津" # 変更後の行先
            
            # (2) 休日・特定列車ルール
            elif is_holiday and train_number == "1727H" and dest_station_en == "Otsuki" and current_delay >= PREDICTION_DELAY_THRESHOLD:
                prediction_key = f"{train_number}_{today_date_str}"
                new_destination_jp = "四方津"

            # ▼▼▼▼▼ ここからが君の「お試し」ルール ▼▼▼▼▼
            # (3) その他の列車（列番指定なし）の30分遅延ルール
            elif dest_station_en == "Otsuki" and current_delay >= PREDICTION_DELAY_THRESHOLD:
                print(f"--- [DEST PRED] General Otsuki rule triggered for {train_number}", flush=True)
                prediction_key = f"{train_number}_{today_date_str}"
                new_destination_jp = "四方津"
            # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

            # --- 3. 通知作成 ---
            if prediction_key and prediction_key not in notified_predictions:
                try:
                    # (メッセージ作成ロジックは変更なし)
                    line_name_jp = "🟧中央快速線"
                    train_type_id = train.get("odpt:trainType")
                    train_type_jp = TRAIN_TYPE_NAMES.get(train_type_id, train_type_id)
                    original_dest_jp = STATION_DICT.get(dest_station_en, dest_station_en)
                    
                    location_text = ""
                    from_station_id = train.get("odpt:fromStation")
                    to_station_id = train.get("odpt:toStation")
                    if to_station_id and from_station_id:
                        from_jp = STATION_DICT.get(from_station_id.split('.')[-1], '?')
                        to_jp = STATION_DICT.get(to_station_id.split('.')[-1], '?')
                        location_text = f"{from_jp}→{to_jp}を走行中"
                    elif from_station_id:
                        from_jp = STATION_DICT.get(from_station_id.split('.')[-1], '?')
                        location_text = f"{from_jp}に停車中"
                    
                    delay_minutes = int(current_delay / 60)

                    message_line1 = f"[{line_name_jp}] 早期行先変更予測"
                    message_line2 = f"{train_type_jp} {original_dest_jp}行き (→ {new_destination_jp}行きに変更の可能性)"
                    message_line3 = f"{location_text} (遅延:{delay_minutes}分)"
                    message_line4 = f"列番:{train_number}"
                    message_line5 = f"なお、行先変更が実施されない場合もあります。"
                    
                    final_message = f"{message_line1}\n{message_line2}\n{message_line3}\n{message_line4}\n{message_line5}"
                    notification_messages.append(final_message)
                    
                    notified_predictions[prediction_key] = current_time
                    print(f"--- [DEST PRED] !!! PREDICTION NOTICE SENT for Train {train_number} !!!", flush=True)

                except Exception as e:
                    print(f"--- [DEST PRED] ERROR creating message for {train_number}: {e}", flush=True)

        # --- 4. 古い通知記録を掃除 (例: 1日以上経過したもの) ---
        keys_to_remove = [
            key for key, timestamp in notified_predictions.items()
            if current_time - timestamp > (24 * 60 * 60)
        ]
        for key in keys_to_remove:
            del notified_predictions[key]

        return notification_messages

    except requests.exceptions.RequestException as req_err:
        print(f"--- [DEST PRED] ERROR: Network error: {req_err}", flush=True)
        return None
    except Exception as e:
        print(f"--- [DEST PRED] ERROR: Unexpected error: {e}", flush=True)
        traceback.print_exc()
        return None