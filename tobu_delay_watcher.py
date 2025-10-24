import os
import requests
import time
from typing import Dict, Any, List, Optional

API_TOKEN = os.getenv('ODPT_TOKEN_CHALLENGE') # JRと同じトークン
API_ENDPOINT = "https://api-challenge.odpt.org/api/v4/odpt:Train" # JRと同じエンドポイント

# --- 東武線用の「駅名」と「路線名」辞書 ---
# ★★★ 今は仮で主要駅しか入ってないから、君の旧Botデータや知識で追加してね！ ★★★
TOBU_STATION_DICT = {
    'Ikebukuro': '池袋', 'KitaIkebukuro': '北池袋', 'ShimoItabashi': '下板橋', 'Oyama': '大山', 
    'NakaItabashi': '中板橋', 'Tokiwadai': 'ときわ台', 'KamiItabashi': '上板橋', 
    'TobuNerima': '東武練馬', 'ShimoAkatsuka': '下赤塚', 'Narimasu': '成増', 'Wakoshi': '和光市', 
    'Asaka': '朝霞', 'Asakadai': '朝霞台', 'Shiki': '志木', 'Yanasegawa': '柳瀬川', 
    'Mizuhodai': 'みずほ台', 'Tsuruse': '鶴瀬', 'Fujimino': 'ふじみ野', 'KamiFukuoka': '上福岡', 
    'Shingashi': '新河岸', 'Kawagoe': '川越', 'Kawagoeshi': '川越市', 'Kasumigaseki': '霞ヶ関', 
    'Tsurugashima': '鶴ヶ島', 'Wakaba': '若葉', 'Sakado': '坂戸', 'KitaSakado': '北坂戸', 
    'Takasaka': '高坂', 'HigashiMatsuyama': '東松山', 'ShinrinKoen': '森林公園', 
    'Tsukinowa': 'つきのわ', 'MusashiRanzan': '武蔵嵐山', 'Ogawamachi': '小川町', 
    'TobuTakezawa': '東武竹沢', 'Obusuma': '男衾', 'MinamiYorii': 'みなみ寄居', 'Hachigata': '鉢形', 
    'Tamayodo': '玉淀', 'Yorii': '寄居', 'Ipponmatsu': '一本松', 'NishiOya': '西大家',
    'Kawakado': '川角', 'BushuNagase': '武州長瀬', 'HigashiMoro': '東毛呂', 'BushuKarasawa': '武州唐沢',
    'Ogose': '越生',
    'Asakusa': '浅草', 'TokyoSkytree': 'とうきょうスカイツリー', 'Oshiage': '押上', 'Hikifune': '曳舟',
    'HigashiMukojima': '東向島', 'Kanegafuchi': '鐘ヶ淵', 'Horikiri': '堀切', 'Ushida': '牛田',
    'KitaSenju': '北千住', 'Kosuge': '小菅', 'Gotanno': '五反野', 'Umejima': '梅島',
    'Nishiarai': '西新井', 'Takenotsuka': '竹ノ塚', 'Yatsuka': '谷塚', 'Soka': '草加', 
    'DokkyoDaigakumae': '獨協大学前', 'Shinden': '新田', 'Gamo': '蒲生', 'ShinKoshigaya': '新越谷',
    'Koshigaya': '越谷', 'KitaKoshigaya': '北越谷', 'Obukuro': '大袋', 'Sengendai': 'せんげん台',
    'Takesato': '武里', 'Ichinowari': '一ノ割', 'Kasukabe': '春日部', 'KitaKasukabe': '北春日部',
    'Himemiya': '姫宮', 'TobuDobutsuKoen': '東武動物公園', 'Wado': '和戸', 'Kuki': '久喜',
    'Washinomiya': '鷲宮', 'Hanasaki': '花崎', 'Kazo': '加須', 'MinamiHanyu': '南羽生',
    'Hanyu': '羽生', 'Kawamata': '川俣', 'Morinjimae': '茂林寺前',
    'SugitoTakanodai': '杉戸高野台', 'Satte': '幸手', 'MinamiKurihashi': '南栗橋',
    'Kurihashi': '栗橋', 'ItakuraToyodaimae': '板倉東洋大前', 'Fujioka': '藤岡', 'Shizuwa': '静和',
    'ShinOshira': '新大平下', 'ShinKoga': '新古河', 'Tochigi': '栃木',
    'Omiya': '大宮', 'KitaOmiya': '北大宮', 'Omiyakoen': '大宮公園', 'Owada': '大和田',
    'Nanasato': '七里', 'Iwatsuki': '岩槻', 'HigashiIwatsuki': '東岩槻', 'Toyoharu': '豊春',
    'Yagisaki': '八木崎', 'Kasukabe': '春日部', 'Fujinoushijima': '藤の牛島', 
    'MinamiSakurai': '南桜井', 'Kawama': '川間', 'Nanakodai': '七光台', 'Shimizukoen': '清水公園',
    'Atago': '愛宕', 'Nodashi': '野田市', 'Umesato': '梅郷', 'Unga': '運河', 'Edogawadai': '江戸川台',
    'Hatsuoi': '初石', 'NagareyamaOtakanomori': '流山おおたかの森', 'Toyoshiki': '豊四季',
    'Kashiwa': '柏', 'ShinKashiwa': '新柏', 'Masuo': '増尾', 'Sakasai': '逆井', 
    'Takayanagi': '高柳', 'Mutsumi': '六実', 'ShinKamagaya': '新鎌ヶ谷', 'Magomezawa': '馬込沢',
    'Tsukada': '塚田', 'ShinFunabashi': '新船橋', 'Funabashi': '船橋',
    'Daishimae': '大師前', 'Omurai': '小村井', 'HigashiAzuma': '東あずま',
    'KameidoSuijin': '亀戸水神', 'Kameido': '亀戸',
    
}

TOBU_LINE_NAMES = {
    "odpt.Railway:Tobu.Tojo": "東武東上線",
    "odpt.Railway:Tobu.Ogose": "東武越生線",
    "odpt.Railway:Tobu.TobuSkytree": "東武ｽｶｲﾂﾘｰﾗｲﾝ",
    "odpt.Railway:Tobu.Isesaki": "東武伊勢崎線",
    "odpt.Railway:Tobu.Nikko": "東武日光線",
    "odpt.Railway:Tobu.Daishi": "東武大師線",
    "odpt.Railway:Tobu.TobuUrbanPark": "東武ｱｰﾊﾞﾝﾊﾟｰｸﾗｲﾝ",
    "odpt.Railway:Tobu.Kiryu": "東武桐生線",
    "odpt.Railway:Tobu.Kameido": "東武亀戸線",
}
# ★★★★★★★★★★★★★★★★★★★★★★★★

# --- 1. 部品1：東武線の「路線カルテ」を追加 ---
TOBU_LINE_PREDICTION_DATA = {
    "odpt.Railway:Tobu.Tojo": {
        "name": "東武東上線",
        "stations": [ # 例：東上線（池袋～小川町）
            '池袋', '北池袋', '下板橋', '大山', '中板橋', 'ときわ台', '上板橋', '東武練馬', 
            '下赤塚', '成増', '和光市', '朝霞', '朝霞台', '志木', '柳瀬川', 'みずほ台', 
            '鶴瀬', 'ふじみ野', '上福岡', '新河岸', '川越', '川越市', '霞ケ関', 
            '鶴ケ島', '若葉', '坂戸', '北坂戸', '高坂', '東松山', '森林公園', 
            'つきのわ', '武蔵嵐山', '小川町', '東武竹沢', '男衾', 'みなみ寄居', '鉢形', '玉淀', 
            '寄居'],
        "turning_stations": {
            '池袋', '成増', '志木', '上福岡', '川越市', '坂戸', '森林公園', '小川町', '寄居'
        }
    },
    "odpt.Railway:Tobu.TobuSkytree": {
        "name": "東武ｽｶｲﾂﾘｰﾗｲﾝ",
        "stations": [ # 例：東上線（池袋～小川町）
            '浅草','とうきょうスカイツリー','曳舟','東向島','鐘ヶ淵','堀切','牛田','北千住', 
            '小菅','五反野','梅島','西新井','竹ノ塚','谷塚','草加','獨協大学前','新田','蒲生',
            '新越谷','越谷','北越谷','大袋','せんげん台','武里','一ノ割','春日部','北春日部',
            '姫宮','東武動物公園','和戸','久喜',],
        "turning_stations": {
            '浅草','曳舟','北千住','北越谷','春日部','北春日部','東武動物公園','久喜'
        }
    },
    "odpt.Railway:Tobu.Isesaki": {
        "name": "東武伊勢崎線",
        "stations": [ 
            '久喜','鷲宮','花崎','加須','南羽生','羽生','川俣','茂林寺前','館林'],
        "turning_stations": {
            '久喜','加須','羽生','館林'
        }
    },

}

    
# --- 監視対象の列車情報を保持する辞書 ---
tracked_delayed_trains: Dict[str, Dict[str, Any]] = {}
line_cooldown_tracker: Dict[str, float] = {}

# --- 設定値 (JR版と同じ) ---
DELAY_THRESHOLD_SECONDS = 3 * 60
INCREASE_COUNT_THRESHOLD = 5
ESCALATION_NOTICE_THRESHOLD = 10
PREDICTION_THRESHOLD = 12
CLEANUP_THRESHOLD_SECONDS = 15 * 60
COOLDOWN_SECONDS = 30 * 60

# --- 2. 部品2：「予測ツール」を追加 ---
def _find_nearest_turning_station(station_list: List[str], turning_stations: set, start_index: int, direction: int) -> Optional[str]:
    """指定された駅リストを、指定された方向に探索し、折り返し可能な最寄り駅を探す"""
    current_index = start_index
    while 0 <= current_index < len(station_list):
        station_name = station_list[current_index]
        if station_name in turning_stations:
            return station_name
        current_index += direction
    return None

# --- メイン関数 (名前を tobu に変更) ---
def check_tobu_delay_increase() -> Optional[List[str]]:
    global tracked_delayed_trains, line_cooldown_tracker
    notification_messages: List[str] = []
    current_time = time.time()
    trains_found_this_cycle: set = set()

    try:
        # 1. 全列車データを取得 (OperatorをTobuに指定)
        params = {"odpt:operator": "odpt.Operator:Tobu", "acl:consumerKey": API_TOKEN}
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
                moved = current_location_id != tracking_info["last_location_id"]
                recovered = current_delay < DELAY_THRESHOLD_SECONDS

                # ▼▼▼ リセット処理 (再開通知) ▼▼▼
                if moved or recovered:
                    if tracking_info.get("notified_initial", False):
                        line_name_jp = TOBU_LINE_NAMES.get(line_id, line_id.split('.')[-1])
                        location_name_en = tracking_info["last_location_id"].split('.')[-1]
                        location_name_jp = TOBU_STATION_DICT.get(location_name_en, location_name_en)
                        reason = "運転再開を確認" if moved else "遅延が回復"
                        message = f"【{line_name_jp} 運転再開】\n{location_name_jp}駅付近で停止していた列車の{reason}しました。(遅延: {int(current_delay / 60)}分)"
                        notification_messages.append(message)
                        print(f"--- [TOBU DELAY WATCH] !!! RESUMPTION NOTICE for Train {train_number} !!! Reason: {reason}", flush=True)
                    del tracked_delayed_trains[train_number]
                
                # ▼▼▼ 遅延増加処理 (通知判定) ▼▼▼
                elif current_delay > tracking_info["last_delay"]:
                    tracking_info["consecutive_increase_count"] += 1
                    tracking_info["last_delay"] = current_delay
                    tracking_info["last_seen_time"] = current_time
                    count = tracking_info["consecutive_increase_count"]
                    
                    print(f"--- [TOBU DELAY WATCH] Train {train_number}: Count {count} at {current_location_id}", flush=True)

                    line_name_jp = TOBU_LINE_NAMES.get(line_id, line_id.split('.')[-1])
                    location_name_en = current_location_id.split('.')[-1]
                    location_name_jp = TOBU_STATION_DICT.get(location_name_en, location_name_en)

                    # --- 最初の通知判定 (公式情報のチェックはなし) ---
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
                            print(f"--- [TOBU DELAY WATCH] !!! INITIAL NOTICE SENT for Train {train_number} !!!", flush=True)
                        else:
                            print(f"--- [TOBU DELAY WATCH] Train {train_number}: Initial threshold reached, but line {line_name_jp} in cooldown.", flush=True)
                            #tracking_info["notified_initial"] = True # フラグは立てる
                    
                    # --- 再通知（エスカレーション）判定 ---
                    if count >= ESCALATION_NOTICE_THRESHOLD and tracking_info.get("notified_initial", False) and not tracking_info.get("notified_escalated", False):
                         message = (
                             f"【{line_name_jp} 運転見合わせ継続中】\n"
                             f"{location_name_jp}駅付近でのトラブル対応が長引いている可能性があります。"
                             f"(遅延: {int(current_delay / 60)}分)" 
                         )
                         notification_messages.append(message)
                         tracking_info["notified_escalated"] = True
                         print(f"--- [TOBU DELAY WATCH] !!! ESCALATION NOTICE SENT for Train {train_number} !!!", flush=True)

                    #カウント12    
                    if count >= PREDICTION_THRESHOLD and tracking_info.get("notified_initial", False) and not tracking_info.get("notified_predicted", False):
                        
                        # この路線のカルテがあるか確認
                        if line_id in TOBU_LINE_PREDICTION_DATA:
                            line_data = TOBU_LINE_PREDICTION_DATA[line_id]
                            station_list = line_data.get("stations", [])
                            turning_stations = line_data.get("turning_stations", set())

                            if station_list and turning_stations:
                                turn_back_1, turn_back_2 = None, None
                                try:
                                    # 止まっている駅のインデックスを探す
                                    if location_name_jp in station_list:
                                        idx = station_list.index(location_name_jp)
                                        # 両方向に折り返し駅を探す
                                        turn_back_1 = _find_nearest_turning_station(station_list, turning_stations, idx - 1, -1)
                                        turn_back_2 = _find_nearest_turning_station(station_list, turning_stations, idx + 1, 1)
                                
                                    # --- メッセージ作成 ---
                                    message_title = f"【{line_name_jp} 折返し区間予測】"
                                    running_sections = []
                                    line_start, line_end = station_list[0], station_list[-1]

                                    if turn_back_1 and turn_back_1 != line_start:
                                        running_sections.append(f"・{line_start}～{turn_back_1}")
                                    if turn_back_2 and turn_back_2 != line_end:
                                        running_sections.append(f"・{turn_back_2}～{line_end}")

                                    # (原因テキストは遅延検知では特定できないので、簡易版)
                                    reason_text = f"\nこれは、{location_name_jp}駅付近でのトラブルの影響と推測されます。"
                                    disclaimer = "\n状況により折返し運転が実施されない場合があります。"
                                    
                                    final_message = message_title
                                    if running_sections: final_message += f"\n" + "\n".join(running_sections)
                                    else: final_message += "\n(運転区間不明)"
                                    final_message += reason_text
                                    final_message += disclaimer
                                    
                                    notification_messages.append(final_message)
                                    tracking_info["notified_predicted"] = True # 予測通知フラグを立てる
                                    print(f"--- [TOBU DELAY WATCH] !!! PREDICTION NOTICE SENT for Train {train_number} !!!", flush=True)

                                except Exception as e:
                                    print(f"--- [TOBU DELAY WATCH] ERROR during prediction logic: {e}", flush=True)
                        else:
                            print(f"--- [TOBU DELAY WATCH] Prediction threshold reached, but no map found for {line_name_jp}.", flush=True)
                            tracking_info["notified_predicted"] = True
                
                else: # 遅延が横ばい or 微減
                    tracking_info["last_seen_time"] = current_time
            
            # ▼▼▼ 新規追跡処理 ▼▼▼
            elif current_delay >= DELAY_THRESHOLD_SECONDS:
                 print(f"--- [TOBU DELAY WATCH] Train {train_number}: Start tracking (Delay={current_delay}s at {current_location_id}).", flush=True)
                 tracked_delayed_trains[train_number] = {
                     "line_id": line_id, "last_location_id": current_location_id,
                     "last_delay": current_delay, "consecutive_increase_count": 1,
                     "last_seen_time": current_time,
                     "notified_initial": False, "notified_escalated": False,
                     "notified_predicted": False # ★予測フラグの初期値
                 }

        # 4. 古い記録の掃除
        trains_to_remove = [
            train_num for train_num, info in tracked_delayed_trains.items()
            if train_num not in trains_found_this_cycle and current_time - info["last_seen_time"] > CLEANUP_THRESHOLD_SECONDS
        ]
        for train_num in trains_to_remove:
            del tracked_delayed_trains[train_num]
            print(f"--- [DELAY WATCH] Train {train_num}: Removing track (timeout).", flush=True)

        return notification_messages

    except requests.exceptions.RequestException as req_err:
        print(f"--- [TOBU DELAY WATCH] ERROR: Network error: {req_err}", flush=True)
        return None
    except Exception as e:
        import traceback
        print(f"--- [TOBU DELAY WATCH] ERROR: Unexpected error: {e}", flush=True)
        traceback.print_exc()
        return None