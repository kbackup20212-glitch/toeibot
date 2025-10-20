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
    },
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
        "odpt.Railway:JR-East.Itsukaichi": {
        "name": "五日市線",
        "stations":['武蔵五日市','武蔵増戸','武蔵引田','秋川','東秋留','熊川','拝島','拝島・立川方面'],
        "turning_stations":{'武蔵五日市','武蔵引田','拝島'}
    },
        "odpt.Railway:JR-East.Sotobo": {
        "name": "外房線",
        "stations":['千葉方面','千葉','本千葉','蘇我','鎌取','誉田','土気','大網','永田','本納',
                    '新茂原','茂原','八積','上総一ノ宮','東浪見','太東','長者町','三門','大原','浪花',
                    '御宿','勝浦','鵜原','上総興津','行川アイランド','安房小湊','安房天津','安房鴨川',
                    '安房鴨川・内房線方面'],
        "turning_stations":{'千葉','誉田','大網','本納','茂原','上総一ノ宮','大原','勝浦','安房鴨川'}
    },
        "odpt.Railway:JR-East.Uchibo": {
        "name": "内房線",
        "stations":['千葉方面','千葉','本千葉','蘇我','浜野','八幡宿','五井','姉ケ崎','長浦','袖ヶ浦',
                    '巌根','木更津','君津','青堀','大貫','佐貫町','上総湊','竹岡','浜金谷','保田',
                    '安房勝山','岩井','富浦','那古船形','館山','九重','千倉','千歳','南三原','和田浦',
                    '江見','太海','安房鴨川','安房鴨川・外房線方面'],
        "turning_stations":{'千葉','姉ケ崎','木更津','君津','佐貫町','上総湊','保田','岩井','富浦',
                            '館山','千倉','安房鴨川'}
    },
        "odpt.Railway:JR-East.Chuo": {
        "name": "中央本線",
        "stations":['高尾方面','高尾','相模湖','藤野','上野原','四方津','梁川','鳥沢','猿橋','大月',
                    '初狩','笹子','甲斐大和','勝沼ぶどう郷','塩山','東山梨','山梨市','春日居町',
                    '石和温泉','酒折','甲府','竜王','塩崎','韮崎','新府','穴山','日野春','長坂','小淵沢',
                    '信濃境','富士見','すずらんの里','青柳','茅野','上諏訪','下諏訪','岡谷','岡谷・松本方面'],
        "turning_stations":{'高尾','相模湖','四方津','大月','甲斐大和','塩山','山梨市','酒折','甲府','竜王',
                            '韮崎','日野春','小淵沢','富士見','青柳','茅野','上諏訪','下諏訪','岡谷'}
    },
    "odpt.Railway:JR-East.Yamanote": {"name": "山手線"},
    "odpt.Railway:JR-East.ShonanShinjuku": {"name": "湘南新宿ライン"},
    "odpt.Railway:JR-East.ChuoSobuLocal": {"name": "中央総武線"},
    }

last_jr_east_statuses = {}

NORMAL_STATUS_KEYWORDS = ["平常", "遅れ", "運転を再開", "運休します"]
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

    # ▼▼▼▼▼ ここからがシミュレーションコード ▼▼▼▼▼
    # Trueにすると、指定した路線の事故を強制的に発生させる
    SIMULATE_ACCIDENTS = False
    SIMULATION_DATA = {
    "odpt.Railway:JR-East.ChuoRapid": "中央線快速電車は、中央・総武各駅停車での人身事故の影響で、上下線で運転を見合わせています。運転再開は９時２０分頃を見込んでいます。",
    "odpt.Railway:JR-East.ChuoSobuLocal": "中央・総武各駅停車は、荻窪駅での人身事故の影響で、上下線で運転を見合わせています。運転再開は９時２０分頃を見込んでいます。",
    # 他のテストしたい路線とテキストをここに追加
}
    # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
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
        found_unexpected_item = False # 異物が見つかったかのフラグ
        
        for item_index, item in enumerate(info_data): # インデックスも取得
             is_valid_dict = False # まずは無効と仮定
             reason = "Unknown format" # 無効な理由

             if isinstance(item, dict):
                 line_id_val = item.get("odpt:railway")
                 info_text_val = item.get("odpt:trainInformationText")
                 ja_text_val = None
                 if isinstance(info_text_val, dict):
                      ja_text_val = info_text_val.get("ja")

                 if line_id_val and ja_text_val:
                      is_valid_dict = True # 必要なものが全て揃っていれば有効
                 else:
                      reason = "Missing required keys (railway or ja_text)"
             else:
                  reason = f"Not a dictionary (type: {type(item)})"

             if is_valid_dict:
                 # line_id_val が None でないことは上で保証済み
                 info_dict[line_id_val] = item 
             else:
                 # 予期せぬ形式のデータは、その正体をログに出力！
                 print(f"--- [JR INFO] WARNING: Skipping unexpected item at index {item_index} ---", flush=True)
                 print(f"    -> Reason: {reason}", flush=True)
                 print(f"    -> Raw Item Data: {repr(item)}", flush=True) # repr()で生の姿を表示
                 found_unexpected_item = True
        
        # もし異物が見つかっていたら、ここで一度処理を止めてユーザーに知らせる (デバッグ用)
        if found_unexpected_item:
             print("--- [JR INFO] Unexpect item detected. Stopping further processing for this cycle. ---", flush=True)
             # return None # 必要ならここで処理を中断しても良い
        # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

        # === ここからが正しい処理ループ ===
        for line_id, line_info in info_dict.items():
            if line_id not in JR_LINE_PREDICTION_DATA:
                continue
            current_status: str = line_info["odpt:trainInformationText"]["ja"]
            if not current_status: continue

            if SIMULATE_ACCIDENTS and line_id in SIMULATION_DATA:
                print(f"--- [SIMULATION] Injecting accident info for {line_id} ---", flush=True)
                # 辞書から対応するテキストを取得して上書き
                current_status = SIMULATION_DATA[line_id]
                last_jr_east_statuses[line_id] = "dummy_status_to_force_update"

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
                        match_between = re.search(r'、\s*([^\s～、]+?)駅～([^\s～、]+?)駅間(?:の)?', status_to_check)
                        match_at = re.search(r'、\s*([^\s、]+?)駅で(?:の)?', status_to_check)
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
                        linked_line_id = "odpt.Railway:JR-East.ChuoSobuLocal"
                        linked_status_raw = None
                        # ★★★ シミュレーションモードを優先 ★★★
                        if SIMULATE_ACCIDENTS and linked_line_id in SIMULATION_DATA:
                            linked_status_raw = SIMULATION_DATA[linked_line_id]
                            print(f"--- [JR INFO] ChuoRapid: Using SIMULATED Sobu status ---", flush=True)
                        # シミュレーションでなければ、現実世界の情報を参照
                        elif linked_line_id in info_dict:
                             linked_status_raw = info_dict[linked_line_id].get("odpt:trainInformationText", {}).get("ja")
                             print(f"--- [JR INFO] ChuoRapid: Using REAL Sobu status ---", flush=True)

                        if linked_status_raw:
                            status_to_check = linked_status_raw.strip()
                        else:
                             print(f"--- [JR INFO] ChuoRapid: Linked Sobu status was empty. Using original status.", flush=True)
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
                    if not skip_prediction:
                        turn_back_1, turn_back_2 = None, None
                        try:
                            # 1回目の正規表現 (あえて不完全なまま)
                            match_between = re.search(r'(.+?)駅～(.+?)駅間', status_to_check)
                            match_at = re.search(r'(.+?)駅で', status_to_check)

                            station_to_compare = ""
                            station1, station2, station = None, None, None

                            if match_between:
                                station1_raw = match_between.group(1)
                                station2_raw = match_between.group(2)
                                station1 = re.split(r'[、\s]', station1_raw)[-1].strip()
                                station2 = re.split(r'[、\s]', station2_raw)[-1].strip()
                                station_to_compare = station1
                                print(f"  > Initial Regex (between): '{station1}', '{station2}'", flush=True)
                            elif match_at:
                                station_raw = match_at.group(1)
                                station = re.split(r'[、\s]', station_raw)[-1].strip()
                                station_to_compare = station
                                print(f"  > Initial Regex (at): '{station}'", flush=True)

                            # ▼▼▼▼▼ 逆転の発想チェック ▼▼▼▼▼
                            if line_id == "odpt.Railway:JR-East.ChuoRapid" and station_to_compare and station_to_compare.startswith("中央・総武各"):
                                print(f"--- [JR INFO] ChuoRapid: Detected ambiguous station '{station_to_compare}'. Switching to Sobu status. ---", flush=True)
                                linked_line_id = "odpt.Railway:JR-East.ChuoSobuLocal"
                                linked_status_raw = None
                                if SIMULATE_ACCIDENTS and linked_line_id in SIMULATION_DATA:
                                    linked_status_raw = SIMULATION_DATA[linked_line_id]
                                elif linked_line_id in info_dict:
                                     linked_status_raw = info_dict[linked_line_id].get("odpt:trainInformationText", {}).get("ja")

                                if linked_status_raw:
                                    status_to_check = linked_status_raw.strip() # ★★★ ここで情報を上書き ★★★
                                    print(f"--- [JR INFO] Now checking Sobu status: '{status_to_check}'", flush=True)
                                    # ★★★ もう一度、正規表現をかけ直す ★★★
                                    match_between = re.search(r'([^\s～、]+?)駅～([^\s～、]+?)駅間(?:の)?', status_to_check)
                                    match_at = re.search(r'([^\s、]+?)駅で(?:の)?', status_to_check)
                                    station1, station2, station = None, None, None # 再初期化
                                    if match_between:
                                        station1 = match_between.group(1).strip()
                                        station2 = match_between.group(2).strip()
                                        station_to_compare = station1
                                        print(f"  > Second Regex (between): '{station1}', '{station2}'", flush=True)
                                    elif match_at:
                                        station = match_at.group(1).strip()
                                        station_to_compare = station
                                        print(f"  > Second Regex (at): '{station}'", flush=True)
                                else:
                                    print(f"--- [JR INFO] Could not find Sobu status to switch.", flush=True)
                                    station_to_compare = "" # 駅名不明として扱う
                            # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

                            if station_to_compare:
                                # 生のリストと駅名を表示
                                list_repr = [repr(s) for s in station_list]
                                print(f"  > Station List (raw): {list_repr[:5]}...", flush=True)
                                station_repr = repr(station_to_compare)
                                print(f"  > Station to Check (raw): {station_repr}", flush=True)

                                is_in_list = station_to_compare in station_list
                                print(f"  > Is Station in List?: {is_in_list}", flush=True)
                                
                                if is_in_list:
                                    if match_between:
                                        idx1, idx2 = station_list.index(station1), station_list.index(station2)
                                        b_idx1, b_idx2 = min(idx1, idx2), max(idx1, idx2)
                                        print(f"  > Index Found (between): {b_idx1}, {b_idx2}", flush=True)
                                        s_before, s_after = station_list[b_idx1], station_list[b_idx2]
                                        # 境界駅チェック
                                        if s_before in turning_stations: turn_back_1 = s_before
                                        else: turn_back_1 = _find_nearest_turning_station(station_list, turning_stations, b_idx1 - 1, -1)
                                        if s_after in turning_stations: turn_back_2 = s_after
                                        else: turn_back_2 = _find_nearest_turning_station(station_list, turning_stations, b_idx2 + 1, 1)
                                        print(f"  > Calculated Turnbacks (between): 1='{turn_back_1}', 2='{turn_back_2}'", flush=True)
                                    elif match_at:
                                        idx = station_list.index(station)
                                        print(f"  > Index Found (at): {idx}", flush=True)
                                        turn_back_1 = _find_nearest_turning_station(station_list, turning_stations, idx - 1, -1)
                                        turn_back_2 = _find_nearest_turning_station(station_list, turning_stations, idx + 1, 1)
                                        print(f"  > Calculated Turnbacks (at): 1='{turn_back_1}', 2='{turn_back_2}'", flush=True)
                                else:
                                     print(f"  > Station NOT FOUND in list. Skipping calculation.", flush=True)
                            else:
                                print(f"  > No valid station extracted. Skipping calculation.", flush=True)

                            print(f"--- [Prediction Calculation END] ---\n", flush=True)

                        except ValueError as e:
                            print(f"--- [JR WARNING] Failed to find index. Station: '{station_to_compare}'. Error: {e}", flush=True)
                            pass
                        except Exception as find_err:
                            print(f"--- [JR WARNING] Error during turning station search for {line_name_jp}: {find_err}", flush=True)
                            pass
                        
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
                        # まず、全体の構造「(場所)での(原因)の影響で」を探す
                        reason_match = re.search(r'(.+?(?:駅|駅間))で(?:の)?(.+?)の影響で', status_to_check)

                        if reason_match:
                            location_part = reason_match.group(1).strip() # 「駅」または「駅間」までの部分全体
                            cause = reason_match.group(2).strip() # 原因の部分

                            # location_part から、最後の単語（＝駅名や区間名）だけを抜き出す
                            # 例：「中央線快速電車は、西国分寺駅」→「西国分寺駅」
                            # 例：「中央線快速電車は、 西国分寺～国立駅間」→「西国分寺～国立駅間」
                            location_elements = re.split(r'[、\s]', location_part) # 読点や空白で区切る
                            actual_location = location_elements[-1] if location_elements else location_part # 最後の要素を取得

                            reason_text = f"\nこれは、{actual_location}での{cause}の影響です。"
                        # 一致しない場合は、シンプルな抽出 (これは変更なし)
                        elif not reason_text:
                            reason_match_simple = re.search(r'頃\s*(.+?)の影響で', current_status)
                            if reason_match_simple:
                                reason_text = f"\nこれは{reason_match_simple.group(1)}です。"

                        disclaimer = "\n状況により折返し運転が実施されない場合があります。"
                        
                        final_message = message_title
                        if running_sections: final_message += f"\n" + "\n".join(running_sections)
                        final_message += reason_text
                        final_message += disclaimer
                        notification_messages.append(final_message)
                        prediction_made = True
                
                # ▼▼▼ 通常の運行情報通知 ▼▼▼
                if not prediction_made:
                    if not any(keyword in current_status for keyword in NORMAL_STATUS_KEYWORDS):
                        line_name_jp = JR_LINE_PREDICTION_DATA.get(line_id, {}).get("name", line_id)
                        message = f"【{line_name_jp} 運行情報】\n{current_status}"
                        notification_messages.append(message)
                    else:
                        # 平常運転の場合はログにだけ記録（デバッグ用、不要なら消してもOK）
                        print(f"--- [JR INFO] Skipping notification for {line_id} (Normal operation) ---", flush=True)
        
        return notification_messages

    except requests.exceptions.RequestException as req_err:
        print(f"--- [JR INFO] ERROR: Network error during API request: {req_err}", flush=True)
        return None
    except Exception as e:
        # ▼▼▼▼▼ ここからが最後の尋問コード ▼▼▼▼▼
        # エラーの種類と、それが起きた正確な場所を特定する
        import traceback
        print(f"--- [JR INFO] DETAILED ERROR REPORT ---", flush=True)
        print(f"  > Error Type: {type(e).__name__}", flush=True)
        print(f"  > Error Message: {e}", flush=True)
        print(f"  > Traceback:", flush=True)
        traceback.print_exc() # エラーが発生した場所までの詳細な経路を出力
        print(f"------------------------------------", flush=True)
        # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
        return None # エラーが起きたらNoneを返すのは変わらない