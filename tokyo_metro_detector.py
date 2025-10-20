import os
import requests
import re
from typing import Dict, Any, List, Optional

# --- 基本設定 ---
API_TOKEN = os.getenv('ODPT_TOKEN_TOEI')
API_ENDPOINT = "https://api.odpt.org/api/v4/odpt:TrainInformation"

# --- 千代田線データ (これだけ残す) ---
CHIYODA_STATIONS = [
    '代々木上原', '代々木公園', '明治神宮前', '表参道', '乃木坂', '赤坂', '国会議事堂前',
    '霞ケ関', '日比谷', '二重橋前', '大手町', '新御茶ノ水', '湯島', '根津', '千駄木',
    '西日暮里', '町屋', '北千住', '綾瀬', '常磐線内'
]
CHIYODA_TURNING_STATIONS = {
    '代々木上原', '代々木公園', '表参道', '霞ケ関', '大手町', '湯島', '北千住', '綾瀬' # 常磐線内は折り返し不可とする
}

# --- 状態保存用 ---
last_metro_statuses: Dict[str, str] = {}

# --- ヘルパー関数 (折り返し駅探索) ---
def _find_nearest_turning_station(station_list: List[str], turning_stations: set, start_index: int, direction: int) -> Optional[str]:
    """指定された駅リストを、指定された方向に探索し、折り返し可能な最寄り駅を探す"""
    print(f"\n--- [HELPER INTERROGATION] ---", flush=True) # デバッグログ付き
    print(f"  > Task: Find nearest turning station", flush=True)
    print(f"  > Station List Provided (first 5): {station_list[:5]}", flush=True)
    print(f"  > Turning Stations Provided: {turning_stations}", flush=True)
    print(f"  > Start Index: {start_index}", flush=True)
    print(f"  > Search Direction: {direction}", flush=True)

    current_index = start_index
    step_count = 0
    while 0 <= current_index < len(station_list):
        step_count += 1
        station_name = station_list[current_index]
        print(f"  Step {step_count}: Checking index {current_index} ('{station_name}')...", flush=True)
        
        if station_name in turning_stations:
            print(f"    -> FOUND! '{station_name}' is in the turning list.", flush=True)
            print(f"--- [HELPER REPORT] Found: '{station_name}' ---\n", flush=True)
            return station_name
            
        current_index += direction
        if step_count > len(station_list) + 5: # 無限ループ防止
             print(f"    -> ERROR: Too many steps. Aborting search.", flush=True)
             break
             
    print(f"  -> Reached end of list or aborted.", flush=True)
    print(f"--- [HELPER REPORT] Found: None ---\n", flush=True)
    return None

# --- メイン関数 (千代田線特化・デバッグモード) ---
def check_tokyo_metro_info() -> Optional[List[str]]:
    global last_metro_statuses
    notification_messages: List[str] = []
    SIMULATE_CHIYODA_ACCIDENT = False # ★★★ テスト実行時はTrue ★★★

    try:
        params = {"odpt:operator": "odpt.Operator:TokyoMetro", "acl:consumerKey": API_TOKEN}
        response = requests.get(API_ENDPOINT, params=params, timeout=30)
        response.raise_for_status()
        try: info_data: Any = response.json()
        except requests.exceptions.JSONDecodeError as json_err: return None
        if not isinstance(info_data, list): return None

        info_dict: Dict[str, Dict[str, Any]] = {}
        for item in info_data:
             if isinstance(item, dict) and item.get("odpt:railway") and isinstance(item.get("odpt:trainInformationText"), dict) and item.get("odpt:trainInformationText", {}).get("ja"):
                 info_dict[item["odpt:railway"]] = item

        for line_id, line_info in info_dict.items():
            # --- 千代田線以外は完全に無視 ---
            if line_id != "odpt.Railway:TokyoMetro.Chiyoda":
                continue

            current_status: str = line_info["odpt:trainInformationText"]["ja"]

            if SIMULATE_CHIYODA_ACCIDENT:
                print("--- [SIMULATION] Injecting Chiyoda accident info ---", flush=True)
                current_status = "12時34分頃、赤坂駅で(これはテスト文面です)のため、運転を見合わせています。"
                last_metro_statuses[line_id] = "dummy" # 強制更新

            if current_status != last_metro_statuses.get(line_id):
                last_metro_statuses[line_id] = current_status
                
                if "運転を見合わせています" in current_status:
                    line_name_jp = "千代田線"
                    station_list = CHIYODA_STATIONS
                    turning_stations = CHIYODA_TURNING_STATIONS
                    turn_back_1, turn_back_2 = None, None
                    status_to_check: str = current_status

                    try:
                        # --- 最終尋問コード ---
                        print(f"\n--- [FINAL鑑定 @ {line_name_jp}] ---", flush=True)
                        
                        match_between = re.search(r'([^\s～、]+?)駅～([^\s～、]+?)駅間(?:の)?', status_to_check)
                        match_at = re.search(r'([^\s、]+?)駅で(?:の)?', status_to_check) # 読点(、)も除外
                        match_between_result = "Success" if match_between else "Failed"
                        match_at_result = "Success" if match_at else "Failed"
                        print(f"  > Regex Check: match_between={match_between_result}, match_at={match_at_result}", flush=True)

                        station_to_compare = ""
                        station1, station2 = "", ""

                        if match_between:
                            station1 = match_between.group(1).strip()
                            station2 = match_between.group(2).strip()
                            print(f"  > Extracted (between): '{station1}', '{station2}'", flush=True)
                            station_to_compare = station1
                        elif match_at:
                            station = match_at.group(1).strip()
                            print(f"  > Extracted (at): '{station}'", flush=True)
                            station_to_compare = station

                        if station_to_compare:
                            print(f"  > Station List Provided (showing raw representation):", flush=True)
                            list_repr = [repr(s) for s in station_list]
                            print(f"    - {list_repr}", flush=True)
                            station_repr = repr(station_to_compare)
                            print(f"  > Station Name to Compare (raw representation): {station_repr}", flush=True)
                            
                            is_in_list = station_to_compare in station_list
                            print(f"  > FINAL LIST CHECK: Is raw name above found in raw list above? -> {is_in_list}", flush=True)
                            
                            if is_in_list:
                                print(f"    -> Station FOUND in list. Proceeding to find index and turning stations.", flush=True)
                                if match_between:
                                    idx1, idx2 = station_list.index(station1), station_list.index(station2)
                                    b_idx1, b_idx2 = min(idx1, idx2), max(idx1, idx2)
                                    s_before, s_after = station_list[b_idx1], station_list[b_idx2]
                                    if s_before in turning_stations: turn_back_1 = s_before
                                    else: turn_back_1 = _find_nearest_turning_station(station_list, turning_stations, b_idx1 - 1, -1)
                                    if s_after in turning_stations: turn_back_2 = s_after
                                    else: turn_back_2 = _find_nearest_turning_station(station_list, turning_stations, b_idx2 + 1, 1)
                                elif match_at:
                                    idx = station_list.index(station)
                                    turn_back_1 = _find_nearest_turning_station(station_list, turning_stations, idx - 1, -1)
                                    turn_back_2 = _find_nearest_turning_station(station_list, turning_stations, idx + 1, 1)
                            else:
                                 print(f"  > !!! CRITICAL: Station extracted IS NOT FOUND in the station_list. Skipping index search. !!!", flush=True)
                        else:
                            print(f"  > No station name extracted to compare.", flush=True)

                        print(f"--- [FINAL鑑定 END] ---\n", flush=True)

                    except ValueError as e:
                         print(f"--- [METRO WARNING] Failed to find index. Station: '{station_to_compare}'. Error: {e}", flush=True)
                         pass
                    except Exception as find_err:
                         print(f"--- [METRO WARNING] Error during turning station search for {line_name_jp}: {find_err}", flush=True)
                         pass

                    # --- メッセージ作成 ---
                    message_title = f"【{line_name_jp} 折返し区間予測】"
                    print(f"--- [MSG CREATE] Title: {message_title}", flush=True)
                    running_sections = []
                    line_start, line_end = station_list[0], station_list[-1]
                    print(f"--- [MSG CREATE] Turnback Stations: 1='{turn_back_1}', 2='{turn_back_2}'", flush=True)
                    print(f"--- [MSG CREATE] Line Start='{line_start}', Line End='{line_end}'", flush=True)
                    if turn_back_1 and turn_back_1 != line_start:
                        section1 = f"・{line_start}～{turn_back_1}"
                        print(f"--- [MSG CREATE] Calculated Section 1: {section1}", flush=True)
                        running_sections.append(section1)
                    if turn_back_2 and turn_back_2 != line_end:
                        section2 = f"・{turn_back_2}～{line_end}"
                        print(f"--- [MSG CREATE] Calculated Section 2: {section2}", flush=True)
                        running_sections.append(section2)
                    
                    reason_text = ""
                    reason_match = re.search(r'頃、(.+?)のため', current_status)
                    if reason_match:
                        reason = reason_match.group(1)
                        reason_text = f"\nこれは{reason}の影響です。"
                        print(f"--- [MSG CREATE] Extracted Reason: {reason}", flush=True)
                    disclaimer = "\n状況により折返し運転が実施されない場合があります。"
                    
                    final_message = message_title
                    if running_sections:
                        sections_text = "\n".join(running_sections)
                        print(f"--- [MSG CREATE] Joining sections: {sections_text}", flush=True)
                        final_message += f"\n{sections_text}"
                    else:
                        print(f"--- [MSG CREATE] No running sections to add.", flush=True)
                        final_message += "\n(運転区間不明)"
                    final_message += reason_text
                    final_message += disclaimer
                    print(f"--- [MSG CREATE] Final Message Assembled (before append):\n{final_message}\n---", flush=True)
                    notification_messages.append(final_message)
        
        return notification_messages

    except requests.exceptions.RequestException as req_err: return None
    except Exception as e:
        print(f"--- [METRO] ERROR: An unexpected error occurred in check_tokyo_metro_info: {e}", flush=True)
        return None