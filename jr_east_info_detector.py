import os
import requests
import re

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
        if station_name in turning_stations:
            return station_name
        current_index += direction
    return None

def _find_nearest_hub(station_list, hubs, start_index, direction):
    """指定された方向に、最も近いハブ駅を探す"""
    current_index = start_index
    while 0 <= current_index < len(station_list):
        station_name = station_list[current_index]
        if station_name in hubs:
            return station_name
        current_index += direction
    return None # 見つからなければNone

# --- メイン関数 (共通ロジックに改造) ---
def check_jr_east_info():
    global last_jr_east_statuses
    notification_messages = []

    try:
        params = {"odpt:operator": "odpt.Operator:jre-is", "acl:consumerKey": API_TOKEN}
        response = requests.get(API_ENDPOINT, params=params, timeout=30)
        response.raise_for_status()
        info_data = response.json()

        # ▼▼▼ 1. 全ピースをテーブルに並べる (データの前処理) ▼▼▼
        info_dict = {item['odpt:railway']: item for item in info_data if 'odpt:railway' in item}

        # ▼▼▼ 2. 路線ごとに処理 (テーブルのピースを1枚ずつ見る) ▼▼▼
        for line_id, line_info in info_dict.items():
            current_status = line_info.get("odpt:trainInformationText", {}).get("ja")
            if not current_status: continue

            if current_status != last_jr_east_statuses.get(line_id):
                last_jr_east_statuses[line_id] = current_status
                
                prediction_made = False

                # もし、その路線のカルテがあり、かつ「運転見合わせ」なら、高度な手術を行う
                if line_id in JR_LINE_PREDICTION_DATA and "運転を見合わせています" in current_status:
                    
                    line_data = JR_LINE_PREDICTION_DATA[line_id]
                    line_name_jp = line_data["name"]
                    station_list = line_data["stations"]
                    turning_stations = line_data["turning_stations"]
                    if not station_list: continue

                    # ▼▼▼ 3. ここからが新しい連携ロジック ▼▼▼
                    status_to_check = current_status # デフォルトでは、自路線の情報をチェック
                    forced_station = None
                    skip_prediction = False
                    
                    # もし中央線快速で、原因が曖昧な場合
                    if line_id == "odpt.Railway:JR-East.ChuoRapid" and "中央・総武各駅停車での" in current_status:
                        sobu_info = info_dict.get("odpt.Railway:JR-East.ChuoSobuLocal", {})
                        sobu_status = sobu_info.get("odpt:trainInformationText", {}).get("ja")
                        if sobu_status: status_to_check = sobu_status

                    elif line_id == "odpt.Railway:JR-East.Saikyo":
                        if "山手線内での" in current_status:
                            yamanote_info = info_dict.get("odpt.Railway:JR-East.Yamanote", {})
                            yamanote_status = yamanote_info.get("odpt:trainInformationText", {}).get("ja")
                            if yamanote_status: status_to_check = yamanote_status
                        elif "湘南新宿ライン内での" in current_status:
                            shonan_info = info_dict.get("odpt.Railway:JR-East.ShonanShinjuku", {})
                            shonan_status = shonan_info.get("odpt:trainInformationText", {}).get("ja")
                            if shonan_status: status_to_check = shonan_status
                        elif "東海道線内での" in current_status or "横須賀線内での" in current_status:
                            forced_station = "大崎"
                        # ### ここからが完成した「思考放棄」ルール ###
                        elif "線内での" in current_status:
                            print(f"--- [JR INFO] 埼京線の未知の路線での事象のため、予測をスキップします ---", flush=True)
                            skip_prediction = True
                        # ### ここまで ###
                    elif line_id == "odpt.Railway:JR-East.Narita":
                        match_between = re.search(r'(.+?)～(.+?)駅間での', status_to_check)
                        match_at = re.search(r'(.+?)駅での', status_to_check)
                        stop_station = ""
                        if match_between: stop_station = match_between.group(1) # 区間なら開始駅で判断
                        elif match_at: stop_station = match_at.group(1)

                        if stop_station:
                            if stop_station in line_data.get("stations_main", []):
                                station_list = line_data["stations_main"]
                                print(f"--- [JR INFO] 成田線(本線)で事象発生と判断 ---", flush=True)
                            elif stop_station in line_data.get("stations_abiko", []):
                                station_list = line_data["stations_abiko"]
                                print(f"--- [JR INFO] 成田線(我孫子支線)で事象発生と判断 ---", flush=True)
                            elif stop_station in line_data.get("stations_airport", []):
                                print(f"--- [JR INFO] 成田線(空港支線)での事象のため、予測をスキップ ---", flush=True)
                                skip_prediction = True
                            else: # どのリストにもなければ予測不能
                                skip_prediction = True
                        else: # 駅名が特定できなければ予測不能
                            skip_prediction = True
                    else:
                        # 他の路線は通常のリストを使用
                        station_list = line_data.get("stations", [])
                    
                    # 思考放棄フラグが立っていなければ、予測処理に進む
                    if not skip_prediction:
                        turn_back_1, turn_back_2 = None, None
                    if forced_station:
                            if forced_station in station_list:
                                idx = station_list.index(forced_station)
                                turn_back_1 = _find_nearest_turning_station(station_list, turning_stations, idx - 1, -1)
                                turn_back_2 = _find_nearest_turning_station(station_list, turning_stations, idx + 1, 1)
                    else:    
                        match_between = re.search(r'(.+?)～(.+?)駅間での', status_to_check)
                        match_at = re.search(r'(.+?)駅での', status_to_check)

                    try:
                        if match_between:
                            station1, station2 = match_between.groups()
                            if station1 in station_list and station2 in station_list:
                                idx1, idx2 = station_list.index(station1), station_list.index(station2)
                                start_idx, end_idx = min(idx1, idx2), max(idx1, idx2)
                                turn_back_1 = _find_nearest_turning_station(station_list, turning_stations, start_idx - 1, -1)
                                turn_back_2 = _find_nearest_turning_station(station_list, turning_stations, end_idx + 1, 1)
                        elif match_at:
                            station = match_at.group(1)
                            if station in station_list:
                                idx = station_list.index(station)
                                turn_back_1 = _find_nearest_turning_station(station_list, turning_stations, idx - 1, -1)
                                turn_back_2 = _find_nearest_turning_station(station_list, turning_stations, idx + 1, 1)
                    except ValueError:
                        pass
                    
                    message_title = f"【{line_name_jp} 折返し区間予測】"
                    running_sections = []

                    # もし、その路線に「ハブ」の定義があれば、新しい方式で計算
                    if "hubs" in line_data:
                        hubs = line_data["hubs"]
                        if turn_back_1:
                            hub_1 = _find_nearest_hub(station_list, hubs, station_list.index(turn_back_1), -1)
                            if hub_1: running_sections.append(f"・{hub_1}～{turn_back_1}")
                        if turn_back_2:
                            hub_2 = _find_nearest_hub(station_list, hubs, station_list.index(turn_back_2), 1)
                            if hub_2: running_sections.append(f"・{turn_back_2}～{hub_2}")
                    else: # ハブの定義がなければ、従来通り始点と終点から計算
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
                
                # ▼▼▼ 簡単な処置 ▼▼▼
                if not prediction_made:
                    line_name_jp = JR_LINE_PREDICTION_DATA.get(line_id, {}).get("name", line_id) # カルテにあれば日本語名、なければID
                    message = f"【{line_name_jp} 運行情報】\n{current_status}"
                    notification_messages.append(message)
        
        return notification_messages

    except Exception as e:
        print(f"--- [JR INFO] ERROR: {e} ---", flush=True)
        return None