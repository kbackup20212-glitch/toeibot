import os
import requests
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

API_TOKEN = os.getenv('ODPT_TOKEN_CHALLENGE')
API_ENDPOINT = "https://api-challenge.odpt.org/api/v4/odpt:TrainInformation"


RAIL_DIRECTION_NAMES = {
    "odpt.RailDirection:Inbound": "上り線",
    "odpt.RailDirection:Outbound": "下り線",
    "odpt.RailDirection:Northbound": "北行",
    "odpt.RailDirection:Southbound": "南行",
    "odpt.RailDirection:Eastbound": "東行",
    "odpt.RailDirection:Westbound": "西行",
    "odpt.RailDirection:InnerLoop": "内回り",
    "odpt.RailDirection:OuterLoop": "外回り",
}

# ---------------------------------------------------------------
# ▼▼▼ 路線ごとの「カルテ棚」エリア ▼▼▼
# ---------------------------------------------------------------
JR_LINE_PREDICTION_DATA = {
    "odpt.Railway:JR-East.ChuoRapid": {
        "name": "🟧中央快速線",
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
        "name": "🟩埼京線",
        "stations": [
            'りんかい線方面', '大崎','五反田','目黒', '恵比寿', '渋谷','原宿','代々木', '新宿', 
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
    "odpt.Railway:JR-East.SotetsuDirect": {
        "name": "🟩相鉄直通線",
        "stations": [
            '相鉄線方面', '羽沢横浜国大', '武蔵小杉', '西大井', '大崎','五反田','目黒', '恵比寿', 
            '渋谷','原宿','代々木', '新宿'],
        "turning_stations": {
            'りんかい線内', '大崎', '新宿', '池袋', '赤羽', '武蔵浦和', '大宮'
        },  
    },
    "odpt.Railway:JR-East.Takasaki": {
        "name": "🟧高崎線",
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
        "name": "🟧宇都宮線",
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
        "name": "🟦京浜東北線",
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
        "odpt.Railway:JR-East.NaritaAbikoBranch": {
        "name": "🟩成田線",
        "stations": ['常磐快速線上野・品川方面', '我孫子', '東我孫子', '湖北', '新木', '布佐', '木下', '小林', '安食', '下総松崎', '成田'],
        "turning_stations": {'我孫子', '湖北', '布佐', '木下', '安食', '成田'}, # 折り返し可能駅
        "hubs": {} # 主要な接続駅
    },
        "odpt.Railway:JR-East.Itsukaichi": {
        "name": "🟧五日市線",
        "stations":['武蔵五日市','武蔵増戸','武蔵引田','秋川','東秋留','熊川','拝島','立川方面'],
        "turning_stations":{'武蔵五日市','武蔵引田','拝島'}
    },
        "odpt.Railway:JR-East.Sotobo": {
        "name": "🟥外房線",
        "stations":['千葉','本千葉','蘇我','鎌取','誉田','土気','大網','永田','本納',
                    '新茂原','茂原','八積','上総一ノ宮','東浪見','太東','長者町','三門','大原','浪花',
                    '御宿','勝浦','鵜原','上総興津','行川アイランド','安房小湊','安房天津','安房鴨川',
                    '内房線方面'],
        "turning_stations":{'千葉','誉田','大網','本納','茂原','上総一ノ宮','大原','勝浦','安房小湊',
                            '安房鴨川'}
    },
        "odpt.Railway:JR-East.Uchibo": {
        "name": "🟦内房線",
        "stations":['千葉','本千葉','蘇我','浜野','八幡宿','五井','姉ケ崎','長浦','袖ヶ浦',
                    '巌根','木更津','君津','青堀','大貫','佐貫町','上総湊','竹岡','浜金谷','保田',
                    '安房勝山','岩井','富浦','那古船形','館山','九重','千倉','千歳','南三原','和田浦',
                    '江見','太海','安房鴨川','外房線方面'],
        "turning_stations":{'千葉','姉ケ崎','木更津','君津','佐貫町','上総湊','保田','岩井','富浦',
                            '館山','千倉','安房鴨川'}
    },
        "odpt.Railway:JR-East.Chuo": {
        "name": "🟦中央本線",
        "stations":['立川方面','高尾','相模湖','藤野','上野原','四方津','梁川','鳥沢','猿橋','大月',
                    '初狩','笹子','甲斐大和','勝沼ぶどう郷','塩山','東山梨','山梨市','春日居町',
                    '石和温泉','酒折','甲府','竜王','塩崎','韮崎','新府','穴山','日野春','長坂','小淵沢',
                    '信濃境','富士見','すずらんの里','青柳','茅野','上諏訪','下諏訪','岡谷','岡谷・松本方面'],
        "turning_stations":{'高尾','相模湖','四方津','大月','甲斐大和','塩山','山梨市','酒折','甲府','竜王',
                            '韮崎','日野春','小淵沢','富士見','青柳','茅野','上諏訪','下諏訪','岡谷'}
    },
    "odpt.Railway:JR-East.ChuoSobuLocal": {
        "name": "🟨中央総武線",
        "stations":['千葉','西千葉','稲毛','新検見川','幕張','幕張本郷','津田沼','東船橋','船橋',
                    '西船橋','下総中山','本八幡','市川','小岩','新小岩','平井','亀戸','錦糸町','両国',
                    '浅草橋','秋葉原','御茶ノ水', '水道橋', '飯田橋', '市ケ谷', '四ツ谷', '信濃町', 
                    '千駄ケ谷', '代々木', '新宿', '大久保', '東中野', '中野', '高円寺', '阿佐ケ谷', 
                    '荻窪', '西荻窪', '吉祥寺','三鷹'],
        "turning_stations":{'千葉','幕張','津田沼','西船橋','御茶ノ水','水道橋','中野','三鷹'}
    },
    "odpt.Railway:JR-East.SobuRapid": {
        "name": "🟦総武快速線",
        "stations":['千葉','西千葉','稲毛','新検見川','幕張','幕張本郷','津田沼','東船橋','船橋',
                    '西船橋','下総中山','本八幡','市川','小岩','新小岩','平井','亀戸','錦糸町',
                    '馬喰町','新日本橋','東京','横須賀線方面'],
        "turning_stations":{'千葉','津田沼','東京'}
    },
    "odpt.Railway:JR-East.Kashima": {
        "name": "🟫鹿島線",
        "stations":['佐原','香取','十二橋','潮来','延方','鹿島神宮',
                    '鹿島サッカースタジアム','大洗鹿島線方面'],
        "turning_stations":{'佐原','香取','潮来','鹿島神宮'},
        "hubs": {'鹿島神宮'}
    },
    "odpt.Railway:JR-East.Nambu": {
        "name": "🟨南武線",
        "stations":['立川','西国立','矢川','谷保','西府','分倍河原','府中本町','南多摩','稲城長沼',
                    '矢野口','稲田堤','中野島','登戸','宿河原','久地','津田山','武蔵溝ノ口',
                    '武蔵新城','武蔵中原','武蔵小杉','向河原','平間','鹿島田','矢向','尻手','川崎'],
        "turning_stations":{'立川','稲城長沼','登戸','武蔵溝ノ口','武蔵中原','矢向','川崎'}
    },
    "odpt.Railway:JR-East.Yokohama": {
        "name": "🟩横浜線",
        "stations":['八王子','片倉','八王子みなみ野','相原','橋本','相模原','矢部','淵野辺','古淵',
                    '町田','成瀬','長津田','十日市場','中山','鴨居','小机','新横浜','菊名','大口',
                    '東神奈川','横浜・桜木町方面'],
        "turning_stations":{'八王子','橋本','町田','中山','小机','東神奈川'}
    },
    "odpt.Railway:JR-East.Hachiko": {
        "name": "⬜八高線",
        "stations":['八王子','北八王子','小宮','拝島','東福生','箱根ケ崎','金子','東飯能','高麗川',
                    '毛呂','越生','明覚','小川町','竹沢','折原','寄居','用土','松久','児玉','丹荘',
                    '群馬藤岡','北藤岡','倉賀野','高崎'],
        "turning_stations":{'八王子','拝島','箱根ケ崎','東飯能','高麗川','小川町','寄居','児玉',
                            '群馬藤岡','北藤岡','高崎'},
        "hubs": {'高麗川'}
    },
    "odpt.Railway:JR-East.Keiyo": {
        "name": "🟥京葉線",
        "stations":['東京', '八丁堀', '越中島', '潮見', '新木場', '葛西臨海公園', '舞浜', '新浦安', 
                    '市川塩浜', '二俣新町', '南船橋', '新習志野', '幕張豊砂', '海浜幕張', '検見川浜', 
                    '稲毛海岸', '千葉みなと', '蘇我'],
"turning_stations":{'東京','新木場','南船橋','新習志野','海浜幕張','千葉みなと','蘇我'},
    },
    "odpt.Railway:JR-East.Musashino": {
        "name": "🟧武蔵野線",
        "stations":['府中本町', '北府中', '西国分寺', '新小平', '新秋津', '東所沢', '新座', '北朝霞', 
                    '西浦和', '武蔵浦和', '南浦和', '東浦和', '東川口', '南越谷', '越谷レイクタウン', 
                    '吉川', '吉川美南', '新三郷', '三郷', '南流山', '新松戸', '新八柱', '東松戸', 
                    '市川大野', '船橋法典', '西船橋','京葉線方面'],
        "turning_stations":{'府中本町','東所沢','吉川美南','西船橋'},
    },
    "odpt.Railway:JR-East.JobanRapid": {
        "name": "🟩常磐快速線",
        "stations":['品川方面','上野','日暮里','三河島','南千住','北千住','綾瀬','亀有','金町','松戸',
                    '北松戸','馬橋','新松戸','北小金','南柏','柏','北柏','我孫子','天王台','取手',
                    '土浦方面'],
        "turning_stations":{'上野','北千住','松戸','我孫子','取手'},
    },
    "odpt.Railway:JR-East.JobanLocal": {
        "name": "⬜常磐緩行線",
        "stations":['千代田線方面','綾瀬','亀有','金町','松戸','北松戸','馬橋','新松戸','北小金','南柏',
                    '柏','北柏','我孫子','天王台','取手'],
        "turning_stations":{'綾瀬','松戸','柏','我孫子','取手'},
    },
    "odpt.Railway:JR-East.Joban": {
        "name": "🟦常磐線",
        "stations":['上り方面','取手','藤代','龍ケ崎市','牛久','ひたち野うしく','荒川沖','土浦',
                    '神立','高浜','石岡','羽鳥','岩間','友部','内原','赤塚','偕楽園','水戸','勝田'
                    '佐和','東海','大甕','常陸多賀','日立','小木津','十王','高萩',
                    '南仲郷','磯原','大津港','勿来','植田','泉','湯本','内郷','いわき',
                    '草野','四ツ倉','久ノ浜','末続','広野','Jヴィレッジ','木戸','竜田','富岡',
                    '夜ノ森','大野','双葉','浪江','桃内','小高','磐城太田','原ノ町',
                    '鹿島','日立木','相馬','駒ケ嶺','新地','坂元','山下','浜吉田','亘理','逢隈','岩沼',
                    '下り方面'],
        "turning_stations":{'取手','龍ケ崎市','土浦','友部','水戸','勝田','東海','大津港','いわき'
                            '久ノ浜','富岡','原ノ町','岩沼'},
    },
    "odpt.Railway:JR-East.ShonanShinjuku": {
        "name": "🟧湘南新宿ﾗｲﾝ",
        "stations":['高崎・宇都宮方面','大宮','さいたま新都心', '与野', '北浦和', '浦和', '南浦和', 
                    '蕨', '西川口', '川口', '赤羽', '東十条', '王子', '上中里', '田端','駒込','巣鴨',
                    '大塚','池袋','目白','高田馬場','新大久保','新宿','代々木','原宿','渋谷','恵比寿',
                    '目黒','五反田','大崎','西大井','武蔵小杉','新川崎','横浜','逗子・平塚方面'],
        "turning_stations":{'大宮','池袋','新宿','大崎','横浜'},
    },
    "odpt.Railway:JR-East.Yokosuka": {
        "name": "🟦横須賀線",
        "stations":['東京','新橋','品川','西大井','武蔵小杉','新川崎','横浜','保土ヶ谷','東戸塚',
                    '戸塚','大船','北鎌倉','鎌倉','逗子','東逗子','田浦','横須賀','衣笠','久里浜'],
        "turning_stations":{'東京','品川','横浜','大船','逗子','横須賀','久里浜'},
    },

    "odpt.Railway:JR-East.Yamanote": {"name": "🟩山手線"},
    "odpt.Railway:JR-East.NaritaAirportBranch": {"name": "🟦成田線"},
    "odpt.Railway:JR-East.Echigo": {"name": "🟩越後線"},
    }

# ▼▼▼ 2つのグローバル変数の名前を変更 ▼▼▼
last_jr_east_statuses = {}
current_official_info: Dict[str, Dict[str, Any]] = {} # ★名前変更 (statuses -> info)

NORMAL_STATUS_KEYWORDS = ["平常", "遅れ", "運転を再開", "運休します","お知らせ","昼間"]
# ---------------------------------------------------------------

current_official_statuses: Dict[str, Optional[str]] = {}

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
    global last_jr_east_statuses, current_official_info
    notification_messages: List[str] = []
    current_official_info = {}
    
    try:
        params = {"odpt:operator": "odpt.Operator:jre-is", "acl:consumerKey": API_TOKEN}
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
            if line_id not in JR_LINE_PREDICTION_DATA: continue

            current_status_text: str = line_info["odpt:trainInformationText"]["ja"]
            current_info_status: Optional[str] = line_info.get("odpt:trainInformationStatus", {}).get("ja")
            current_official_info[line_id] = line_info # ★公式情報を丸ごと保存
            
            if not current_status_text: continue

            if current_status_text != last_jr_east_statuses.get(line_id):
                last_jr_east_statuses[line_id] = current_status_text
                prediction_made = False
                skip_prediction = False

                # ▼▼▼ 予測処理ブロック ▼▼▼
                if "運転を見合わせています" in current_status_text and \
                   (current_info_status is None or (current_info_status != "運転再開見込" and "運転再開" not in current_info_status)):
                    
                    # --- ★★★ ここで変数を無条件に定義 ★★★ ---
                    line_data = JR_LINE_PREDICTION_DATA[line_id]
                    line_name_jp = line_data.get("name", line_id)
                    station_list: List[str] = []
                    turning_stations = line_data.get("turning_stations", set())
                    hubs = line_data.get("hubs", set())
                    is_branch_line = False # (丸ノ内線用、JRでは使わないが一応)
                    # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

                    status_to_check: str = current_status_text
                    forced_station = None
                    linked_line_name: Optional[str] = None

                    # --- 路線ごとの駅リスト設定 & 路線連携 ---
                    if line_id == "odpt.Railway:JR-East.Narita":
                        match_between = re.search(r'([^\s～]+?)駅～([^\s～]+?)駅', status_to_check)
                        match_at = re.search(r'([^\s]+?)駅で', status_to_check)
                        stop_station = ""
                        if match_between: stop_station = match_between.group(1).strip()
                        elif match_at: stop_station = match_at.group(1).strip()
                        if stop_station:
                            if stop_station in line_data.get("stations_main", []): station_list = line_data["stations_main"]
                            elif stop_station in line_data.get("stations_abiko", []): station_list = line_data["stations_abiko"]
                            elif stop_station in line_data.get("stations_airport", []): skip_prediction = True
                            else: skip_prediction = True
                        else: skip_prediction = True
                    else:
                        station_list = line_data.get("stations", [])
                    
                    if not station_list: skip_prediction = True

                if line_id == "odpt.Railway:JR-East.ChuoRapid" and "中央・総武各駅停車での" in current_status_text:
                    linked_line_id_str = "odpt.Railway:JR-East.ChuoSobuLocal"
                    sobu_info = info_dict.get(linked_line_id_str, {})
                    sobu_status = sobu_info.get("odpt:trainInformationText", {}).get("ja")
                    if sobu_status:
                        status_to_check = sobu_status
                        linked_line_name = JR_LINE_PREDICTION_DATA.get(linked_line_id_str, {}).get("name", "中央・総武線各駅停車")

                elif line_id == "odpt.Railway:JR-East.Saikyo":
                    linked_line_id_str = None
                    if "山手線内での" in current_status_text: linked_line_id_str = "odpt.Railway:JR-East.Yamanote"
                    elif "湘南新宿ライン内での" in current_status_text: linked_line_id_str = "odpt.Railway:JR-East.ShonanShinjuku"
                    
                    if linked_line_id_str:
                        linked_info = info_dict.get(linked_line_id_str, {})
                        linked_status = linked_info.get("odpt:trainInformationText", {}).get("ja")
                        if linked_status:
                            status_to_check = linked_status
                            linked_line_name = JR_LINE_PREDICTION_DATA.get(linked_line_id_str, {}).get("name", linked_line_id_str.split('.')[-1])
                    
                    elif "東海道線内での" in current_status_text or "横須賀線内での" in current_status_text:
                        forced_station = "大崎"
                    elif "線内での" in current_status_text:
                        skip_prediction = True
                elif line_id == "odpt.Railway:JR-East.ChuoSobuLocal":
                    if "中央線快速電車での" in current_status_text:
                        ChuoRapid_status = info_dict.get("odpt.Railway:JR-East.ChuoRapid", {}).get("odpt:trainInformationText", {}).get("ja")
                        if ChuoRapid_status: status_to_check = ChuoRapid_status
                        linked_line_id_str = "odpt.Railway:JR-East.ChuoRapid"
                    elif "総武快速線内での" in current_status_text:
                        SobuRapid_status = info_dict.get("odpt.Railway:JR-East.SobuRapid", {}).get("odpt:trainInformationText", {}).get("ja")
                        if SobuRapid_status: status_to_check = SobuRapid_status
                        linked_line_id_str = "odpt.Railway:JR-East.SobuRapid"
                    elif "山手線内での" in current_status_text:
                        yamanote_status = info_dict.get("odpt.Railway:JR-East.Yamanote", {}).get("odpt:trainInformationText", {}).get("ja")
                        if yamanote_status: status_to_check = yamanote_status
                        linked_line_id_str = "odpt.Railway:JR-East.Yamanote"
                    
                    # --- 予測実行 ---
                    if not skip_prediction:
                        turn_back_1, turn_back_2 = None, None
                        try:
                            match_between = re.search(r'([^\s～]+?)\s*駅?\s*～\s*([^\s、。～]+?)\s*駅間', status_to_check)
                            match_at = re.search(r'([^\s、。～]+?)\s*駅\s*で', status_to_check)
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
                        
                        # --- メッセージ作成 ---
                        message_title = f"【{line_name_jp} 折返し区間予測】"
                        running_sections = []
                        if hubs:
                            if turn_back_1:
                                hub_1 = _find_nearest_hub(station_list, hubs, station_list.index(turn_back_1), -1)
                                if hub_1 and hub_1 != turn_back_1: running_sections.append(f"・{hub_1}～{turn_back_1}")
                            if turn_back_2:
                                hub_2 = _find_nearest_hub(station_list, hubs, station_list.index(turn_back_2), 1)
                                if hub_2 and hub_2 != turn_back_2: running_sections.append(f"・{turn_back_2}～{hub_2}")
                        else:
                            line_start, line_end = station_list[0], station_list[-1]
                            if turn_back_1 and turn_back_1 != line_start: running_sections.append(f"・{line_start}～{turn_back_1}")
                            if turn_back_2 and turn_back_2 != line_end: running_sections.append(f"・{turn_back_2}～{line_end}")
                        
                        reason_text = ""
                        reason_match = re.search(r'(.+?(?:駅|駅間))で(?:の)?(.+?)の影響で', status_to_check)
                        if reason_match:
                            location_part = reason_match.group(1).strip(); cause = reason_match.group(2).strip()
                            actual_location = re.split(r'[、\s]', location_part)[-1] if location_part else location_part
                            if linked_line_name: reason_text = f"\nこれは、{linked_line_name} {actual_location}での{cause}の影響です。"
                            else: reason_text = f"\nこれは、{actual_location}での{cause}の影響です。"
                        elif not reason_text:
                            reason_match_simple = re.search(r'頃\s*(.+?)の影響で', current_status_text)
                            if reason_match_simple: reason_text = f"\nこれは{reason_match_simple.group(1)}です。"
                        
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
                        line_name_jp = JR_LINE_PREDICTION_DATA.get(line_id, {}).get("name", line_id) # ★ここで line_name_jp が決まる
                        title = f"【{line_name_jp} {current_info_status}】"
                        
                        resume_estimate_time_str = line_info.get("odpt:resumeEstimate")
                        if resume_estimate_time_str:
                            try:
                                resume_time = datetime.fromisoformat(resume_estimate_time_str).strftime('%H:%M')
                                title = f"【{line_name_jp} {current_info_status} {resume_time}】"
                                last_status_full = last_jr_east_statuses.get(line_id)
                                if last_status_full:
                                    last_resume_match = re.search(r'(\d{1,2}時\d{1,2}分)', last_status_full)
                                    if last_resume_match and last_resume_match.group(1) != resume_time.replace(':', '時') + '分': title += "(変更)"
                                    elif "変更" in last_status_full: title += "(変更)"
                            except (ValueError, TypeError): pass

                        reason_text = ""
                        reason_match = re.search(r'(.+?(?:駅|駅間))で(?:の)?(.+?)の影響で', status_to_check)
                        if reason_match:
                            location_part = reason_match.group(1).strip(); cause = reason_match.group(2).strip()
                            actual_location = re.split(r'[、\s]', location_part)[-1] if location_part else location_part
                            if linked_line_name: reason_text = f"{linked_line_name} {actual_location}での{cause}のため、{current_info_status}となっています。"
                            else: reason_text = f"{actual_location}での{cause}のため、{current_info_status}となっています。"
                        elif not reason_text:
                            current_info_cause = line_info.get("odpt:trainInformationCause", {}).get("ja")
                            if current_info_cause: reason_text = f"{current_info_cause}のため、{current_info_status}となっています。"
                            else: reason_text = current_status_text.split('。')[0] + "。"
                        
                        final_message = f"{title}\n{reason_text}"
                        notification_messages.append(final_message)
        
        return notification_messages

    except requests.exceptions.RequestException as req_err: return None
    except Exception as e:
        import traceback
        print(f"--- [JR INFO] ERROR: An unexpected error occurred in check_jr_east_info: {e}", flush=True)
        traceback.print_exc()
        return None

# --- 遅延検知にステータスを渡すための関数 ---
def get_current_official_info() -> Dict[str, Dict[str, Any]]:
    return current_official_info
