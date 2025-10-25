import os
import requests
import re
from typing import Dict, Any, List, Optional

# --- 基本設定 ---
API_TOKEN = os.getenv('ODPT_TOKEN_TOEI')
API_ENDPOINT = "https://api.odpt.org/api/v4/odpt:TrainInformation"

# --- 駅名と折り返し可能駅のリスト
GINZA_LINE_STATIONS = [
    '渋谷', '表参道', '外苑前', '青山一丁目', '赤坂見附', '溜池山王', '虎ノ門', 
    '新橋', '銀座', '京橋', '日本橋', '三越前', '神田', '末広町', '上野広小路', 
    '上野', '稲荷町', '田原町', '浅草'
]
GINZA_LINE_TURNING_STATIONS = {'渋谷', '表参道', '青山一丁目', '溜池山王', '銀座', '三越前', '上野', 
                               '浅草'}

MARUNOUCHI_MAIN_STATIONS = [
    '荻窪', '南阿佐ケ谷', '新高円寺', '東高円寺', '新中野', '中野坂上', '西新宿', '新宿', 
    '新宿三丁目', '新宿御苑前', '四谷三丁目', '四ツ谷', '赤坂見附', '国会議事堂前', '霞ケ関', 
    '銀座', '東京', '大手町', '淡路町', '御茶ノ水', '本郷三丁目', '後楽園', '茗荷谷', '新大塚', '池袋'
]
MARUNOUCHI_BRANCH_STATIONS = ['方南町', '中野富士見町', '中野新橋', '中野坂上']
MARUNOUCHI_TURNING_STATIONS = { '池袋', '茗荷谷', '御茶ノ水','銀座','四谷三丁目','新宿三丁目','新宿',
                               '中野坂上','新中野','中野富士見町','方南町'}

HIBIYA_LINE_STATIONS = [
    '中目黒', '恵比寿', '広尾', '六本木', '神谷町', '霞ケ関', '日比谷', '銀座', '東銀座', '築地', 
    '八丁堀', '茅場町', '人形町', '小伝馬町', '秋葉原', '仲御徒町', '上野', '入谷', '三ノ輪', 
    '南千住', '北千住', '東武スカイツリーライン内' 
]
HIBIYA_TURNING_STATIONS = {
    '中目黒', '恵比寿', '広尾', '六本木', '霞ケ関', '東銀座', '八丁堀', '人形町','仲御徒町','上野', '南千住', '北千住'
}

TOZAI_LINE_STATIONS = [
    'JR中央線内', '中野', '落合', '高田馬場', '早稲田', '神楽坂', '飯田橋', '九段下', '竹橋',
    '大手町', '日本橋', '茅場町', '門前仲町', '木場', '東陽町', '南砂町',
    '西葛西', '葛西', '浦安', '南行徳', '行徳', '妙典', '原木中山', '西船橋'
]
TOZAI_TURNING_STATIONS = {
    '中野', '高田馬場', '飯田橋', '九段下', '茅場町', '東陽町', '葛西','妙典', '西船橋'
}

CHIYODA_STATIONS = [
    '代々木上原', '代々木公園', '明治神宮前', '表参道', '乃木坂', '赤坂', '国会議事堂前',
    '霞ケ関', '日比谷', '二重橋前', '大手町', '新御茶ノ水', '湯島', '根津', '千駄木',
    '西日暮里', '町屋', '北千住', '綾瀬', '常磐線内'
]
CHIYODA_TURNING_STATIONS = {
    '代々木上原', '代々木公園', '表参道', '霞ケ関', '大手町', '湯島', '北千住', '綾瀬' 
}

YURAKUCHO_LINE_STATIONS = [
    '和光市', '地下鉄成増', '地下鉄赤塚', '平和台', '氷川台', '小竹向原', '千川',
    '要町', '池袋', '東池袋', '護国寺', '江戸川橋', '飯田橋', '市ケ谷', '麹町',
    '永田町', '桜田門', '有楽町', '銀座一丁目', '新富町', '月島', '豊洲', '辰巳', '新木場'
]
YURAKUCHO_TURNING_STATIONS = {
    '和光市', '地下鉄成増','小竹向原','池袋','市ケ谷','有楽町','銀座一丁目','豊洲','新木場'
}

HANZOMON_LINE_STATIONS = [
    '東急田園都市線内', '渋谷', '表参道', '青山一丁目', '永田町', '半蔵門', '九段下', '神保町', '大手町',
    '三越前', '水天宮前', '清澄白河', '住吉', '錦糸町', '押上'
]
HANZOMON_TURNING_STATIONS = {
    '渋谷', '半蔵門','九段下','神保町','水天宮前','清澄白河','住吉？','錦糸町''押上'
}

NAMBOKU_LINE_STATIONS = [
    '東急目黒線内', '目黒', '白金台', '白金高輪', '麻布十番', '六本木一丁目', '溜池山王', '永田町',
    '四ツ谷', '市ケ谷', '飯田橋', '後楽園', '東大前', '本駒込', '駒込', '西ケ原',
    '王子', '王子神谷', '志茂', '赤羽岩淵', '埼玉高速鉄道線内' 
]
NAMBOKU_TURNING_STATIONS = {
    '目黒', '白金高輪', '麻布十番','溜池山王','市ケ谷','駒込','赤羽岩淵'
}

FUKUTOSHIN_STATIONS = [ 
    '和光市', '地下鉄成増', '地下鉄赤塚', '平和台', '氷川台', '小竹向原', '千川', '要町', '池袋', 
    '雑司が谷', '西早稲田', '東新宿', '新宿三丁目', '北参道', '明治神宮前', '渋谷', '東急線方面' 
]
FUKUTOSHIN_TURNING_STATIONS = {
    '和光市', '地下鉄成増', '小竹向原', '池袋', '新宿三丁目', '渋谷'
}

METRO_LINE_PREDICTION_DATA = {
    "odpt.Railway:TokyoMetro.Ginza": {
        "name": "銀座線",
        "stations": GINZA_LINE_STATIONS,
        "turning_stations": GINZA_LINE_TURNING_STATIONS
    },
    "odpt.Railway:TokyoMetro.Marunouchi": {
        "name": "丸ノ内線",
        "main_stations": MARUNOUCHI_MAIN_STATIONS, # 本線と支線を区別
        "branch_stations": MARUNOUCHI_BRANCH_STATIONS,
        "turning_stations": MARUNOUCHI_TURNING_STATIONS
    },
    "odpt.Railway:TokyoMetro.Chiyoda": {
        "name": "日比谷線",
        "stations": CHIYODA_STATIONS,
        "turning_stations": CHIYODA_TURNING_STATIONS
    },
    "odpt.Railway:TokyoMetro.Chiyoda": {
        "name": "東西線",
        "stations": TOZAI_LINE_STATIONS,
        "turning_stations": TOZAI_TURNING_STATIONS
    },
    "odpt.Railway:TokyoMetro.Chiyoda": {
        "name": "千代田線",
        "stations": CHIYODA_STATIONS,
        "turning_stations": CHIYODA_TURNING_STATIONS
    },
    "odpt.Railway:TokyoMetro.Chiyoda": {
        "name": "有楽町線",
        "stations": YURAKUCHO_LINE_STATIONS,
        "turning_stations": YURAKUCHO_TURNING_STATIONS
    },
    "odpt.Railway:TokyoMetro.Chiyoda": {
        "name": "半蔵門線",
        "stations": HANZOMON_LINE_STATIONS,
        "turning_stations": HANZOMON_TURNING_STATIONS
    },
    "odpt.Railway:TokyoMetro.Chiyoda": {
        "name": "南北線",
        "stations": NAMBOKU_LINE_STATIONS,
        "turning_stations": NAMBOKU_TURNING_STATIONS
    },
    'odpt.Railway:TokyoMetro.Fukutoshin': {
        "name": "副都心線",
        "stations": FUKUTOSHIN_STATIONS,
        "turning_stations": FUKUTOSHIN_TURNING_STATIONS
    },
}



# --- 状態保存用 ---
last_metro_statuses: Dict[str, str] = {}

# --- ヘルパー関数 (ログ出力付きの、唯一の正しい定義) ---
def _find_nearest_turning_station(station_list: List[str], turning_stations: set, start_index: int, direction: int) -> Optional[str]:
    print(f"\n--- [HELPER INTERROGATION] ---", flush=True)
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

# (メトロでは _find_nearest_hub は不要なので削除)

# --- メイン関数 (丸ノ内線ロジック復活、ハブロジック削除) ---
def check_tokyo_metro_info() -> Optional[List[str]]:
    global last_metro_statuses
    notification_messages: List[str] = []
    SIMULATE_CHIYODA_ACCIDENT = False # シミュレーションフラグ

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
            current_status: str = line_info["odpt:trainInformationText"]["ja"]

            if SIMULATE_CHIYODA_ACCIDENT and line_id == "odpt.Railway:TokyoMetro.Chiyoda":
                print("--- [SIMULATION] Injecting Chiyoda accident info ---", flush=True)
                current_status = "12時34分頃、代々木公園駅で進路の安全確認のため、運転を見合わせています。"
                last_metro_statuses[line_id] = "dummy"

            if current_status != last_metro_statuses.get(line_id):
                last_metro_statuses[line_id] = current_status
                prediction_made = False # 予測を作ったかのフラグを初期化
                
                # ▼▼▼ 予測処理ブロック ▼▼▼
                if line_id in METRO_LINE_PREDICTION_DATA and "運転を見合わせています" in current_status:
                    line_data = METRO_LINE_PREDICTION_DATA[line_id]
                    line_name_jp = line_data.get("name", line_id)
                    station_list: List[str] = []
                    turning_stations = line_data.get("turning_stations", set())
                    # hubs = line_data.get("hubs", set()) # メトロには不要
                    is_branch_line = False
                    skip_prediction = False

                    # --- 路線ごとの駅リスト設定 ---
                    if line_id == "odpt.Railway:TokyoMetro.Marunouchi":
                        match_between = re.search(r'([^\s～]+?)駅～([^\s～]+?)駅', current_status)
                        match_at = re.search(r'([^\s]+?)駅で', current_status)
                        stop_station = ""
                        if match_between: stop_station = match_between.group(1).strip()
                        elif match_at: stop_station = match_at.group(1).strip()
                        
                        if stop_station in line_data.get("branch_stations", []):
                            print(f"--- [METRO] Marunouchi Branch Line incident detected.", flush=True)
                            station_list = line_data.get("branch_stations", [])
                            is_branch_line = True
                        else:
                            print(f"--- [METRO] Marunouchi Main Line incident detected.", flush=True)
                            station_list = line_data.get("main_stations", [])
                    else:
                        station_list = line_data.get("stations", [])
                    
                    if not station_list: skip_prediction = True

                    # --- 予測実行 ---
                    if not skip_prediction:
                        turn_back_1, turn_back_2 = None, None
                        try:
                            # 修正済みの正規表現
                            match_between = re.search(r'([^\s～、]+?)駅～([^\s～、]+?)駅間(?:の)?', current_status)
                            match_at = re.search(r'([^\s、]+?)駅で(?:の)?', current_status)
                            station_to_compare = ""
                            station1, station2 = "", ""

                            if match_between:
                                station1 = match_between.group(1).strip()
                                station2 = match_between.group(2).strip()
                                station_to_compare = station1
                            elif match_at:
                                station = match_at.group(1).strip()
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

                        # --- メッセージ作成 (ハブロジック削除済み) ---
                        message_title = f"【{line_name_jp} 折返し区間予測】"
                        running_sections = []
                        if is_branch_line: line_start, line_end = station_list[0], station_list[-1]
                        else: line_start, line_end = station_list[0], station_list[-1]
                        
                        if turn_back_1 and turn_back_1 != line_start:
                            running_sections.append(f"・{line_start}～{turn_back_1}")
                        if turn_back_2 and turn_back_2 != line_end:
                            running_sections.append(f"・{turn_back_2}～{line_end}")
                        
                        reason_text = ""
                        reason_match = re.search(r'頃、(.+?)のため', current_status)
                        if reason_match: reason_text = f"\nこれは{reason_match.group(1)}の影響です。"
                        disclaimer = "\n状況により折返し運転が実施されない場合があります。"
                        
                        final_message = message_title
                        if running_sections: final_message += f"\n" + "\n".join(running_sections)
                        else: final_message += "\n(運転区間不明)"
                        final_message += reason_text
                        final_message += disclaimer
                        notification_messages.append(final_message)
                        prediction_made = True # 予測フラグを立てる

                # 通常の運行情報通知は削除済み
        
        return notification_messages

    except requests.exceptions.RequestException as req_err: return None
    except Exception as e:
        print(f"--- [METRO] ERROR: An unexpected error occurred in check_tokyo_metro_info: {e}", flush=True)
        return None