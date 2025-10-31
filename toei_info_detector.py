import os
import requests
import re
import unicodedata # ★ 全角数字を半角にするため
from typing import Dict, Any, List, Optional
from datetime import datetime

# --- 基本設定 ---
API_TOKEN = os.getenv('ODPT_TOKEN_TOEI') # ★ 都営用のトークン
API_ENDPOINT = "https://api.odpt.org/api/v4/odpt:TrainInformation"

# ---------------------------------------------------------------
# ▼▼▼ 路線ごとの「カルテ棚」エリア ▼▼▼
# ---------------------------------------------------------------
# (駅名は、他のファイルと共通の STATIONS_DICT を使うのが理想だけど、
#  ひとまずこのファイル専用のカルテ棚として定義するね)

TOEI_LINE_PREDICTION_DATA = {
    "odpt.Railway:Toei.Mita": {
        "name": "都営三田線",
        "stations": [
            '目黒', '白金台', '白金高輪', '三田', '芝公園', '御成門', '内幸町', '日比谷', 
            '大手町', '神保町', '水道橋', '春日', '白山', '千石', '巣鴨', '西巣鴨', 
            '新板橋', '板橋区役所前', '板橋本町', '本蓮沼', '志村坂上', '志村三丁目', 
            '蓮根', '西台', '高島平', '新高島平', '西高島平'
        ],
        "turning_stations": {
            '目黒', '白金高輪', '三田', '御成門', '日比谷', '水道橋', '巣鴨', '新板橋', '本蓮沼',
            '高島平', '西高島平'
        }
    },
    "odpt.Railway:Toei.Asakusa": {
        "name": "都営浅草線",
        "stations": [
            '西馬込', '馬込', '中延', '戸越', '五反田', '高輪台', '泉岳寺', '三田', 
            '大門', '新橋', '東銀座', '宝町', '日本橋', '人形町', '東日本橋', '浅草橋', 
            '蔵前', '浅草', '本所吾妻橋', '押上'
        ],
        "turning_stations": {
            '西馬込', '泉岳寺', '浅草橋', '浅草橋', '押上'
        }
    },
    "odpt.Railway:Toei.Shinjuku": {
        "name": "都営新宿線",
        "stations": [
            '京王線方面', '新宿', '新宿三丁目', '曙橋', '市ケ谷', '九段下', '神保町', '小川町', 
            '岩本町', '馬喰横山', '浜町', '森下', '菊川', '住吉', '西大島', '大島', 
            '東大島', '船堀', '一之江', '瑞江', '篠崎', '本八幡'
        ],
        "turning_stations": {
            '新宿', '市ケ谷', '岩本町', '大島', '瑞江', '本八幡'
        }
    },
    "odpt.Railway:Toei.Oedo": {
        "name": "都営大江戸線",
        # ★ 丸ノ内線と同じ「本線・支線」方式
        "main_stations": [ # ループ部 (都庁前から反時計回り)
            '都庁前', '新宿西口', '東新宿', '若松河田', '牛込柳町', '牛込神楽坂', 
            '飯田橋', '春日', '本郷三丁目', '上野御徒町', '新御徒町', '蔵前', '両国', 
            '森下', '清澄白河', '門前仲町', '月島', '勝どき', '築地市場', '汐留', 
            '大門', '赤羽橋', '麻布十番', '六本木', '青山一丁目', '国立競技場', 
            '代々木', '新宿', '都庁前' # ループの終点
        ],
        "branch_stations": [ # 光が丘方面
            '光が丘', '練馬春日町', '豊島園', '練馬', '新江古田', '落合南長崎', 
            '中井', '東中野', '中野坂上', '西新宿五丁目', '都庁前'
        ],
        "turning_stations": {
            '光が丘', '練馬', '都庁前', '牛込神楽坂', '新御徒町', '清澄白河', '築地市場', 
            '赤羽橋', '国立競技場'
        }
    },
    "odpt.Railway:Toei.Arakawa": {
        "name": "都電荒川線",
        "stations": [
            '三ノ輪橋', '荒川一中前', '荒川区役所前', '荒川二丁目', '荒川七丁目', '町屋駅前', '町屋二丁目', 
            '東尾久三丁目', '熊野前', '宮ノ前', '小台', '荒川遊園地前', '荒川車庫前', '梶原', '栄町', 
            '王子駅前', '飛鳥山', '滝野川一丁目', '西ヶ原四丁目', '新庚申塚', '庚申塚', '巣鴨新田', 
            '大塚駅前', '向原', '東池袋四丁目', '都電雑司ヶ谷', '鬼子母神前', '学習院下', '面影橋',
            '早稲田', 
        ],
        "turning_stations": {
            '三ノ輪橋', '町屋駅前', '荒川車庫前', '王子駅前', '大塚駅前', '早稲田'
        }
    },
}

last_toei_statuses: Dict[str, str] = {}
current_official_info: Dict[str, Dict[str, Any]] = {} # ★ 司令塔に渡すための情報

# --- ヘルパー関数 (JR/メトロと共通) ---
def _find_nearest_turning_station(station_list: List[str], turning_stations: set, start_index: int, direction: int) -> Optional[str]:
    current_index = start_index
    while 0 <= current_index < len(station_list):
        station_name = station_list[current_index]
        if station_name in turning_stations: return station_name
        current_index += direction
    return None

# --- メイン関数 (都営版) ---
def check_toei_info() -> Optional[tuple[List[str], Dict[str, Dict[str, Any]]]]:
    global last_toei_statuses, current_official_info
    notification_messages: List[str] = []
    current_official_info = {} # 毎回復活させる
    
    try:
        params = {"odpt:operator": "odpt.Operator:Toei", "acl:consumerKey": API_TOKEN}
        response = requests.get(API_ENDPOINT, params=params, timeout=30)
        response.raise_for_status()
        try: info_data: Any = response.json()
        except requests.exceptions.JSONDecodeError as json_err: return None, {}
        if not isinstance(info_data, list): return None, {}

        info_dict: Dict[str, Dict[str, Any]] = {}
        for item in info_data:
             if isinstance(item, dict) and item.get("odpt:railway") and isinstance(item.get("odpt:trainInformationText"), dict) and item.get("odpt:trainInformationText", {}).get("ja"):
                 info_dict[item["odpt:railway"]] = item

        for line_id, line_info in info_dict.items():
            
            if line_id not in TOEI_LINE_PREDICTION_DATA: continue

            current_status_text: str = line_info["odpt:trainInformationText"]["ja"]
            current_info_status: Optional[str] = line_info.get("odpt:trainInformationStatus", {}).get("ja")
            current_official_info[line_id] = line_info
            
            if not current_status_text: continue

            if current_status_text != last_toei_statuses.get(line_id):
                last_toei_statuses[line_id] = current_status_text
                prediction_made = False
                skip_prediction = False

                # ▼▼▼ 路線連携ロジック (都営は今のところ不要) ▼▼▼
                status_to_check: str = current_status_text
                linked_line_name: Optional[str] = None
                
                # ▼▼▼ 予測処理ブロック ▼▼▼
                if "運転を見合わせています" in current_status_text and \
                   (current_info_status is None or (current_info_status != "運転再開見込" and "運転再開" not in current_info_status)):
                    
                    line_data = TOEI_LINE_PREDICTION_DATA[line_id]
                    line_name_jp = line_data.get("name", line_id)
                    station_list: List[str] = []
                    turning_stations = line_data.get("turning_stations", set())
                    is_branch_line = False

                    # --- ★ 大江戸線の分岐ロジック ---
                    if line_id == "odpt.Railway:Toei.Oedo":
                        match_between = re.search(r'([^\s～]+?)駅～([^\s～]+?)駅', status_to_check)
                        match_at = re.search(r'([^\s]+?)駅で', status_to_check)
                        stop_station = ""
                        if match_between: stop_station = match_between.group(1).strip()
                        elif match_at: stop_station = match_at.group(1).strip()
                        
                        if stop_station in line_data.get("branch_stations", []):
                            print(f"--- [TOEI] Oedo Branch Line incident detected.", flush=True)
                            station_list = line_data.get("branch_stations", [])
                            is_branch_line = True
                        else:
                            print(f"--- [TOEI] Oedo Main Line incident detected.", flush=True)
                            station_list = line_data.get("main_stations", [])
                    else: # 三田線、浅草線、新宿線
                        station_list = line_data.get("stations", [])
                    
                    if not station_list: skip_prediction = True
                    
                    # --- 予測実行 ---
                    if not skip_prediction:
                        turn_back_1, turn_back_2 = None, None
                        try:
                            # (正規表現はJRで完成したものを流用)
                            match_between = re.search(r'([^\s～、]+?)\s*駅?\s*～\s*([^\s、。～〜]+?)\s*駅間', status_to_check)
                            match_at = re.search(r'([^\s、。～〜]+?)\s*駅(?:構内)?\s*で', status_to_check)
                            station_to_compare = ""
                            station1, station2, station = None, None, None

                            if match_between:
                                station1_raw = match_between.group(1); station2_raw = match_between.group(2)
                                station1 = re.split(r'[、\s]', station1_raw)[-1].strip(); station2 = re.split(r'[、\s]', station2_raw)[-1].strip()
                                station_to_compare = station1
                            elif match_at:
                                station_raw = match_at.group(1)
                                station = re.split(r'[、\s]', station_raw)[-1].strip()
                                station_to_compare = station

                            if station_to_compare and station_to_compare in station_list:
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
                        except ValueError as e: pass
                        except Exception as find_err: pass

                        # --- メッセージ作成 (ハブなしのシンプル版) ---
                        message_title = f"【{line_name_jp} 折返し区間予測】"
                        running_sections = []
                        line_start, line_end = station_list[0], station_list[-1]
                        if turn_back_1 and turn_back_1 != line_start: running_sections.append(f"・{line_start}～{turn_back_1}")
                        if turn_back_2 and turn_back_2 != line_end: running_sections.append(f"・{turn_back_2}～{line_end}")
                        
                        reason_text = ""
                        reason_match = re.search(r'(.+?(?:駅|駅間))で(?:の)?(.+?)の影響で', status_to_check)
                        if reason_match:
                            location_part = reason_match.group(1).strip(); cause = reason_match.group(2).strip()
                            actual_location = re.split(r'[、\s]', location_part)[-1] if location_part else location_part
                            reason_text = f"\nこれは、{actual_location}での{cause}の影響です。"
                        elif not reason_text:
                            reason_match_simple = re.search(r'頃\s*(.+?)の影響で', current_status_text)
                            if reason_match_simple:
                                reason_text = f"\nこれは{reason_match_simple.group(1)}です。"
                        
                        disclaimer = "\n状況により折返し運転が実施されない場合があります。"
                        final_message = message_title
                        if running_sections: final_message += f"\n" + "\n".join(running_sections)
                        else: final_message += "\n(運転区間不明)"
                        final_message += reason_text
                        final_message += disclaimer
                        notification_messages.append(final_message)
                        prediction_made = True
                
                # ▼▼▼ 通常の運行情報通知 (賢い要約版) ▼▼▼
                if not prediction_made:
                    NORMAL_STATUS_KEYWORDS = ["平常", "正常", "お知らせ"]
                    
                    if current_info_status and not any(keyword in current_info_status for keyword in NORMAL_STATUS_KEYWORDS):
                        line_name_jp = TOEI_LINE_PREDICTION_DATA.get(line_id, {}).get("name", line_id)
                        
                        # --- 1. タイトルを作成 ---
                        title = f"【{line_name_jp} {current_info_status}】" # 例: 【都営三田線 ダイヤ乱れ】

                        # --- 2. 本文を加工 ---
                        
                        # a) 「三田線は、」や「新宿線は、」の部分を削除
                        body = re.sub(r'^\w+?は、', '', current_status_text).strip()
                        
                        # b) 君のルール1: 「にて発生した」 -> 「での」
                        body = body.replace("にて発生した", "での")
                        
                        # c) 君のルール2: 「○○駅方面行列車の」 -> 「○○方面行きの」
                        body = re.sub(r'([^\s、]+?)駅方面行列車の', r'\1方面行きの', body)
                        
                        # d) 例2のためのルール: 「〇〇駅～××駅間」 -> 「〇〇～××」
                        body = re.sub(r'([^\s～、]+?)駅～([^\s～、]+?)駅間', r'\1～\2', body)
                        
                        # e) 念のため、全角英数記号を半角に（時刻を見やすくするため）
                        body = unicodedata.normalize('NFKC', body)
                        
                        # --- 3. 最終組み立て ---
                        final_message = f"{title}\n{body}"
                        notification_messages.append(final_message)
        
        return notification_messages, current_official_info

    except requests.exceptions.RequestException as req_err: 
        print(f"--- [TOEI INFO] ERROR: Network error: {req_err}", flush=True)
        return None, {}
    except Exception as e:
        import traceback
        print(f"--- [TOEI INFO] ERROR: Unexpected error occurred in check_toei_info: {e}", flush=True)
        traceback.print_exc()
        return None, {}

# --- 遅延検知にステータスを渡すための関数 ---
def get_current_official_info() -> Dict[str, Dict[str, Any]]:
    return current_official_info