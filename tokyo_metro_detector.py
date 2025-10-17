import os
import requests
import re

# 多摩モノレールと同じトークンを使用
API_TOKEN = os.getenv('ODPT_TOKEN_TOEI')
API_ENDPOINT = "https://api.odpt.org/api/v4/odpt:TrainInformation"

# --- 銀座線の路線データ ---
GINZA_LINE_STATIONS = [
    '渋谷', '表参道', '外苑前', '青山一丁目', '赤坂見附', '溜池山王', '虎ノ門', 
    '新橋', '銀座', '京橋', '日本橋', '三越前', '神田', '末広町', '上野広小路', 
    '上野', '稲荷町', '田原町', '浅草'
]
# 折り返し設備がある駅のリスト
GINZA_LINE_TURNING_STATIONS = {
    '渋谷', '溜池山王', '銀座', '三越前', '上野', '浅草'
}
# --- 丸ノ内線データ ---
MARUNOUCHI_MAIN_STATIONS = [
    '荻窪', '南阿佐ケ谷', '新高円寺', '東高円寺', '新中野', '中野坂上', '西新宿', '新宿', 
    '新宿三丁目', '新宿御苑前', '四谷三丁目', '四ツ谷', '赤坂見附', '国会議事堂前', '霞ケ関', 
    '銀座', '東京', '大手町', '淡路町', '御茶ノ水', '本郷三丁目', '後楽園', '茗荷谷', '新大塚', '池袋'
]
MARUNOUCHI_BRANCH_STATIONS = ['方南町', '中野富士見町', '中野新橋', '中野坂上']
MARUNOUCHI_TURNING_STATIONS = { 
    '池袋', '茗荷谷', '御茶ノ水', '銀座', '四谷三丁目', '新宿三丁目', '新宿', 
    '中野坂上', '新中野', '荻窪', '中野富士見町', '方南町'
}
# --- 千代田線データ ---
CHIYODA_STATIONS = [ # 本線
    '代々木上原', '代々木公園', '明治神宮前', '表参道', '乃木坂', '赤坂', '国会議事堂前',
    '霞ケ関', '日比谷', '二重橋前', '大手町', '新御茶ノ水', '湯島', '根津', '千駄木',
    '西日暮里', '町屋', '北千住', '綾瀬', 'JR常磐線内'
]
CHIYODA_TURNING_STATIONS = {
    '代々木上原', '代々木公園', '明治神宮前', '表参道', '霞ケ関', '大手町', '湯島', '北千住', '綾瀬', 'JR常磐線内'
}
last_metro_statuses = {}

# 折り返し可能な最寄り駅を探すヘルパー関数
def _find_nearest_turning_station(station_list, turning_stations, start_index, direction):
    """
    指定された駅リストを、指定された方向に探索し、折り返し可能な最寄り駅を探す
    """
    current_index = start_index
    while 0 <= current_index < len(station_list):
        station_name = station_list[current_index]
        if station_name in turning_stations:
            return station_name # 見つかったらその駅名を返す
        current_index += direction
    return None # 見つからなかった場合

# --- 3. メイン関数 ---
def check_tokyo_metro_info():
    global last_metro_statuses
    notification_messages = []

    try:
        params = {"odpt:operator": "odpt.Operator:TokyoMetro", "acl:consumerKey": API_TOKEN}
        response = requests.get(API_ENDPOINT, params=params, timeout=30)
        response.raise_for_status()
        info_data = response.json()

        for line_info in info_data:
            line_id = line_info.get("odpt:railway")
            current_status = line_info.get("odpt:trainInformationText", {}).get("ja")
            if not line_id or not current_status: continue
            
            if current_status != last_metro_statuses.get(line_id):
                last_metro_statuses[line_id] = current_status
                
                if "運転を見合わせています" not in current_status: continue

                line_name_jp = ""
                station_list = []
                turning_stations = set()
                is_branch_line = False

                if line_id == "odpt.Railway:TokyoMetro.Ginza":
                    line_name_jp = "銀座線"
                    station_list = GINZA_LINE_STATIONS
                    turning_stations = GINZA_LINE_TURNING_STATIONS
                
                elif line_id == "odpt.Railway:TokyoMetro.Chiyoda":
                    line_name_jp = "千代田線"
                    station_list = CHIYODA_STATIONS
                    turning_stations = CHIYODA_TURNING_STATIONS
                
                elif line_id == "odpt.Railway:TokyoMetro.Marunouchi":
                    line_name_jp = "丸ノ内線"
                    turning_stations = MARUNOUCHI_TURNING_STATIONS
                    
                    match_between = re.search(r'(.+?)駅～(.+?)駅', current_status)
                    match_at = re.search(r'(.+?)駅で', current_status)
                    stop_station = ""
                    if match_between: stop_station = match_between.group(1)
                    elif match_at: stop_station = match_at.group(1)

                    if stop_station in MARUNOUCHI_BRANCH_STATIONS:
                        station_list = MARUNOUCHI_BRANCH_STATIONS
                        is_branch_line = True
                    else:
                        station_list = MARUNOUCHI_MAIN_STATIONS
                
                else:
                    continue

                turn_back_1, turn_back_2 = None, None
                match_between = re.search(r'(.+?)駅～(.+?)駅', current_status)
                match_at = re.search(r'(.+?)駅で', current_status)

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

                # ▼▼▼▼▼ ここからが新しい通知作成ロジック ▼▼▼▼▼
                
                # 1. タイトルを作成
                message_title = f"【{line_name_jp} 折返し区間予測】"
                
                running_sections = []
                if is_branch_line:
                    line_start, line_end = station_list[0], station_list[-1]
                else:
                    line_start, line_end = station_list[0], station_list[-1]

                if turn_back_1 and turn_back_1 != line_start:
                    running_sections.append(f"・{line_start}～{turn_back_1}")
                if turn_back_2 and turn_back_2 != line_end:
                    running_sections.append(f"・{turn_back_2}～{line_end}")

                reason_text = ""
                reason_match = re.search(r'頃、(.+?)のため', current_status)
                if reason_match:
                    reason = reason_match.group(1)
                    reason_text = f"\nこれは{reason}の影響です。"

                disclaimer = "\n状況により折返し運転が実施されない場合があります。"

                final_message = message_title
                if running_sections:
                    sections_text = "\n".join(running_sections)
                    final_message += f"\n{sections_text}"
                
                final_message += reason_text
                final_message += disclaimer
                
                notification_messages.append(final_message)

        return notification_messages

    except Exception as e:
        print(f"--- [METRO] ERROR: {e} ---", flush=True)
        return None