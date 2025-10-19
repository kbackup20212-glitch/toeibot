import os
import requests
import re
from typing import Dict, Any, List, Optional

API_TOKEN = os.getenv('ODPT_TOKEN_CHALLENGE')
API_ENDPOINT = "https://api-challenge.odpt.org/api/v4/odpt:TrainInformation"

# ---------------------------------------------------------------
# ▼▼▼ 路線ごとの「カルテ棚」エリア ▼▼▼
# ---------------------------------------------------------------
JR_LINE_PREDICTION_DATA = {
    "odpt.Railway:JR-East.ChuoRapid": {
        "name": "中央快速線",
        "stations": [
            '東京', '神田', '御茶ノ水', '水道橋', '飯田橋', '市ケ谷', '四ツ谷', '信濃町', '千駄ケ谷', 
            '代々木', '新宿', '大久保', '東中野', '中野', '高円寺', '阿佐ケ谷', '荻窪', '西荻窪', 
            '吉祥寺', '三鷹', '国分寺', '西国分寺', '国立', '立川', '日野', '豊田', '八王子', 
            '西八王子', '高尾'
        ],
        "turning_stations": {
            '東京', '新宿', '中野', '三鷹', '武蔵小金井', '国分寺', '国立', '立川', '豊田', '八王子', 
            '高尾'
        }
    }
    },
{
    "odpt.Railway:JR-East.SaikyoKawagoe": {
        "name": "埼京線",
        "stations": [
            'りんかい線内', '大崎','五反田','目黒', '恵比寿', '渋谷','原宿','代々木', '新宿', 
            '新大久保', '高田馬場', '目白','池袋', '板橋', '十条', '赤羽', 
            '北赤羽', '浮間舟渡', '戸田公園', '戸田', '北戸田', '武蔵浦和', '中浦和', 
            '南与野', '与野本町', '北与野', '大宮', '日進', '西大宮', '指扇', '南古谷', '川越'
        ],
        "turning_stations": {
            'りんかい線内', '大崎', '新宿', '池袋', '赤羽', '武蔵浦和', '大宮'
        },
        "hubs": { 
            'りんかい線内', '大宮', '川越'
        }  
    },
    "odpt.Railway:JR-East.Takasaki": {
        "name": "高崎線",
        "stations": [
            '上野', '尾久', '上中里', '東十条', '赤羽', '川口', '西川口', '蕨', '南浦和', 
            '浦和', '北浦和', '与野', 'さいたま新都心', '大宮', '宮原', '上尾', 
            '北上尾', '桶川', '北本', '鴻巣', '北鴻巣', '吹上', '行田', '熊谷', 
            '籠原', '深谷', '岡部', '本庄', '神保原', '新町', '倉賀野', '高崎'
        ],
        "turning_stations": {
            '上野', '大宮','宮原', '上尾', '桶川', '北本', '鴻巣', '吹上', '熊谷', '籠原', 
            '深谷','本庄','神保原','高崎'
        }
    },
    "odpt.Railway:JR-East.Utsunomiya": {
        "name": "宇都宮線",
        "stations": [
            '上野', '尾久', '上中里', '東十条', '赤羽', '川口', '西川口', '蕨', '南浦和', 
            '浦和', '北浦和', '与野', 'さいたま新都心', '大宮', '土呂', '東大宮', 
            '蓮田', '白岡', '新白岡', '久喜', '東鷲宮', '栗橋', '古河', '野木', 
            '間々田', '小山', '小金井', '自治医大', '石橋', '雀宮', '宇都宮', 
            '岡本', '宝積寺', '氏家', '蒲須坂', '片岡', '矢板', '野崎', '西那須野', 
            '那須塩原', '黒磯'
        ],
        "turning_stations": {
            '上野', '大宮', '蓮田', '白岡', '古河', '小山', '小金井', '宇都宮', 
            '宝積寺', '氏家', '矢板', '那須塩原', '黒磯'
        },
        "hubs": { # ★★★ 新しい「ハブ空港」の定義 ★★★
            '上野', '宇都宮', '黒磯'
        }        
    },
    "odpt.Railway:JR-East.KeihinTohokuNegishi": {
        "name": "京浜東北線",
        "stations": [
            '大宮', 'さいたま新都心', '与野', '北浦和', '浦和', '南浦和', '蕨', '西川口', 
            '川口', '赤羽', '東十条', '王子', '上中里', '田端', '西日暮里', '日暮里', 
            '鶯谷', '上野', '御徒町', '秋葉原', '神田', '東京', '有楽町', '新橋', 
            '浜松町', '田町', '高輪ゲートウェイ', '品川', '大井町', '大森', '蒲田', 
            '川崎', '鶴見', '新子安', '東神奈川', '横浜', '桜木町', '関内', '石川町', 
            '山手', '根岸', '磯子', '新杉田', '洋光台', '港南台', '本郷台', '大船'
        ],
        "turning_stations": {
            # 主要な折り返し設備のある駅
            '大宮', '南浦和', '赤羽', '東十条', '上野', '品川', '蒲田', '鶴見', '東神奈川', '桜木町',
            '磯子', '大船'
        }
    },
        "odpt.Railway:JR-East.Narita": {
        "name": "成田線",
        "stations_main": ['千葉方面', '佐倉', '酒々井', '成田', '久住', '滑河', '下総神崎', '大戸', '佐原', '香取', '水郷', '小見川', '笹川', '下総橘', '下総豊里', '椎柴', '松岸', '銚子'], 
        "stations_abiko": ['我孫子・常磐線方面', '我孫子', '東我孫子', '湖北', '新木', '布佐', '木下', '小林', '安食', '下総松崎', '成田'],
        "stations_airport": ['成田', '空港第２ビル', '成田空港'], # 空港支線
        "turning_stations": {'我孫子', '湖北', '布佐', '木下', '安食', '成田','佐原','銚子'}, # 折り返し可能駅
        "hubs": {'成田', '銚子'} # 主要な接続駅
    },
    "odpt.Railway:JR-East.Yamanote": {"name": "山手線"},
    "odpt.Railway:JR-East.ShonanShinjuku": {"name": "湘南新宿ライン"},
    "odpt.Railway:JR-East.ChuoSobuLocal": {"name": "中央・総武線各駅停車"},
    }

last_jr_east_statuses = {}
# ---------------------------------------------------------------

# --- ヘルパー関数 ---
def _find_nearest_turning_station(station_list, turning_stations, start_index, direction):
    current_index = start_index
    while 0 <= current_index < len(station_list):
        station_name = station_list[current_index]
        if station_name in turning_stations: return station_name
        current_index += direction
    return None
def _find_nearest_hub(station_list, hubs, start_index, direction):
    current_index = start_index
    while 0 <= current_index < len(station_list):
        station_name = station_list[current_index]
        if station_name in hubs: return station_name
        current_index += direction
    return None

# --- メイン関数 (構造修正・最終完成版) ---
def check_jr_east_info() -> Optional[List[str]]:
    global last_jr_east_statuses
    notification_messages: List[str] = []
    try:
        params = {"odpt:operator": "odpt.Operator:jre-is", "acl:consumerKey": API_TOKEN}
        response = requests.get(API_ENDPOINT, params=params, timeout=30)
        response.raise_for_status()
        try:
            info_data: Any = response.json()
        except requests.exceptions.JSONDecodeError as json_err:
            print(f"--- [JR INFO] ERROR: Failed to decode API response as JSON. Error: {json_err}", flush=True)
            return None
        if not isinstance(info_data, list):
             print(f"--- [JR INFO] ERROR: API response is not a list, but {type(info_data)} ---", flush=True)
             return None

        info_dict: Dict[str, Dict[str, Any]] = {}
        for item in info_data:
             if isinstance(item, dict) and \
                item.get("odpt:railway") and \
                isinstance(item.get("odpt:trainInformationText"), dict) and \
                item.get("odpt:trainInformationText", {}).get("ja"):
                 line_id: str = item["odpt:railway"]
                 info_dict[line_id] = item
             else:
                 print(f"--- [JR INFO] WARNING: Skipping unexpected/incomplete item in API response: {item} ---", flush=True)

        # === ここからが正しい処理ループ ===
        for line_id, line_info in info_dict.items():
            current_status: str = line_info["odpt:trainInformationText"]["ja"]

            if current_status != last_jr_east_statuses.get(line_id):
                last_jr_east_statuses[line_id] = current_status
                prediction_made = False
                skip_prediction = False

                # ▼▼▼ 予測処理ブロック ▼▼▼
                if line_id in JR_LINE_PREDICTION_DATA and "運転を見合わせています" in current_status:
                    # このブロックで初めて line_data などを定義する
                    line_data = JR_LINE_PREDICTION_DATA[line_id]
                    line_name_jp = line_data.get("name", line_id)
                    # 成田線は支線があるので、station_listの決定が特殊
                    if line_id == "odpt.Railway:JR-East.Narita":
                        station_list = [] # まず空で初期化
                        match_between = re.search(r'(.+?)～(.+?)駅間での', current_status)
                        match_at = re.search(r'(.+?)駅での', current_status)
                        stop_station = ""
                        if match_between: stop_station = match_between.group(1)
                        elif match_at: stop_station = match_at.group(1)
                        if stop_station:
                            if stop_station in line_data.get("stations_main", []): station_list = line_data["stations_main"]
                            elif stop_station in line_data.get("stations_abiko", []): station_list = line_data["stations_abiko"]
                            elif stop_station in line_data.get("stations_airport", []): skip_prediction = True
                            else: skip_prediction = True
                        else: skip_prediction = True
                    else: # 他の路線はシンプル
                        station_list = line_data.get("stations", [])
                    
                    turning_stations = line_data.get("turning_stations", set())
                    hubs = line_data.get("hubs", set())
                    
                    if not station_list: skip_prediction = True # 駅リストがなければ予測不能

                    status_to_check = current_status
                    forced_station = None

                    # --- 路線連携ロジック ---
                    if line_id == "odpt.Railway:JR-East.ChuoRapid" and "中央・総武各駅停車での" in current_status:
                        sobu_status = info_dict.get("odpt.Railway:JR-East.ChuoSobuLocal", {}).get("odpt:trainInformationText", {}).get("ja")
                        if sobu_status: status_to_check = sobu_status
                    elif line_id == "odpt.Railway:JR-East.Saikyo":
                        if "山手線内での" in current_status:
                            yamanote_status = info_dict.get("odpt.Railway:JR-East.Yamanote", {}).get("odpt:trainInformationText", {}).get("ja")
                            if yamanote_status: status_to_check = yamanote_status
                        elif "湘南新宿ライン内での" in current_status:
                            shonan_status = info_dict.get("odpt.Railway:JR-East.ShonanShinjuku", {}).get("odpt:trainInformationText", {}).get("ja")
                            if shonan_status: status_to_check = shonan_status
                        elif "東海道線内での" in current_status or "横須賀線内での" in current_status:
                            forced_station = "大崎"
                        elif "線内での" in current_status:
                            skip_prediction = True
                    
                    # --- 予測実行 ---
                    if not skip_prediction and station_list:
                        turn_back_1, turn_back_2 = None, None
                        try:
                            if forced_station: # 「みなし処理」の場合
                                if forced_station in station_list:
                                    idx = station_list.index(forced_station)
                                    # この場合も境界（forced_station）は使えないので外側を探索
                                    turn_back_1 = _find_nearest_turning_station(station_list, turning_stations, idx - 1, -1)
                                    turn_back_2 = _find_nearest_turning_station(station_list, turning_stations, idx + 1, 1)
                            else:
                                match_between = re.search(r'(.+?)～(.+?)駅間での', status_to_check)
                                match_at = re.search(r'(.+?)駅での', status_to_check)

                                # ▼▼▼▼▼ ここからが新しい境界駅チェック ▼▼▼▼▼
                                if match_between:
                                    station1, station2 = match_between.groups()
                                    if station1 in station_list and station2 in station_list:
                                        idx1, idx2 = station_list.index(station1), station_list.index(station2)
                                        # 境界駅のインデックス
                                        boundary_idx_1 = min(idx1, idx2)
                                        boundary_idx_2 = max(idx1, idx2)
                                        
                                        # 境界駅(手前側)自体が折り返し可能かチェック
                                        station_before = station_list[boundary_idx_1]
                                        if station_before in turning_stations:
                                            turn_back_1 = station_before
                                        else: # ダメなら外側を探索
                                            turn_back_1 = _find_nearest_turning_station(station_list, turning_stations, boundary_idx_1 - 1, -1)
                                            
                                        # 境界駅(奥側)自体が折り返し可能かチェック
                                        station_after = station_list[boundary_idx_2]
                                        if station_after in turning_stations:
                                            turn_back_2 = station_after
                                        else: # ダメなら外側を探索
                                            turn_back_2 = _find_nearest_turning_station(station_list, turning_stations, boundary_idx_2 + 1, 1)

                                elif match_at:
                                    station = match_at.group(1)
                                    if station in station_list:
                                        idx = station_list.index(station)
                                        # 駅で事故の場合は、その駅では折り返せないので、必ず外側を探索
                                        turn_back_1 = _find_nearest_turning_station(station_list, turning_stations, idx - 1, -1)
                                        turn_back_2 = _find_nearest_turning_station(station_list, turning_stations, idx + 1, 1)
                                # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

                        except ValueError: pass
                        
                        # --- メッセージ作成 ---
                        message_title = f"【{line_name_jp} 折返し区間予測】"
                        running_sections = []
                        if hubs:
                            if turn_back_1:
                                hub_1 = _find_nearest_hub(station_list, hubs, station_list.index(turn_back_1), -1)
                                if hub_1: running_sections.append(f"・{hub_1}～{turn_back_1}")
                            if turn_back_2:
                                hub_2 = _find_nearest_hub(station_list, hubs, station_list.index(turn_back_2), 1)
                                if hub_2: running_sections.append(f"・{turn_back_2}～{hub_2}")
                        else:
                            line_start, line_end = station_list[0], station_list[-1]
                            if turn_back_1 and turn_back_1 != line_start: running_sections.append(f"・{line_start}～{turn_back_1}")
                            if turn_back_2 and turn_back_2 != line_end: running_sections.append(f"・{turn_back_2}～{line_end}")
                        
                        reason_text = ""
                        reason_match = re.search(r'頃\s*(.+?)の影響で', current_status)
                        if reason_match: reason_text = f"\nこれは{reason_match.group(1)}です。"
                        disclaimer = "\n状況により折返し運転が実施されない場合があります。"
                        
                        final_message = message_title
                        if running_sections: final_message += f"\n" + "\n".join(running_sections)
                        final_message += reason_text
                        final_message += disclaimer
                        notification_messages.append(final_message)
                        prediction_made = True
                
                # ▼▼▼ 通常の運行情報通知 ▼▼▼
                if not prediction_made:
                    # line_name_jpをここで定義する
                    line_name_jp = JR_LINE_PREDICTION_DATA.get(line_id, {}).get("name", line_id) 
                    message = f"【{line_name_jp} 運行情報】\n{current_status}"
                    notification_messages.append(message)
        
        return notification_messages

    except requests.exceptions.RequestException as req_err:
        print(f"--- [JR INFO] ERROR: Network error during API request: {req_err}", flush=True)
        return None
    except Exception as e:
        print(f"--- [JR INFO] ERROR: An unexpected error occurred in check_jr_east_info: {e}", flush=True)
        return None