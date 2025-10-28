import os
import requests
import re # 必要に応じて
from typing import Dict, Any, List, Optional

# .envから都営地下鉄用のトークンを読み込む
API_TOKEN = os.getenv('ODPT_TOKEN_TOEI')
# 都営地下鉄用のAPIエンドポイント
API_ENDPOINT = "https://api.odpt.org/api/v4/odpt:Train" # JRと同じURLでOK

# --- 辞書定義 (都営地下鉄用に調整) ---
# 駅名辞書はJRと共通のものを使うか、必要なら都営専用を追加
STATION_DICT = {
    # --- 都営三田線 ---
    'Mita': '三田', 'Shibakoen': '芝公園', 'Onarimon': '御成門', 'Uchisaiwaicho': '内幸町',
    'Hibiya': '日比谷', 'Otemachi': '大手町', 'Jimbocho': '神保町', 'Suidobashi': '水道橋',
    'Kasuga': '春日', 'Hakusan': '白山', 'Sengoku': '千石', 'Sugamo': '巣鴨',
    'NishiSugamo': '西巣鴨', 'ShinItabashi': '新板橋', 'ItabashiKuyakushomae': '板橋区役所前',
    'Itabashihoncho': '板橋本町', 'Motosunuma': '本蓮沼', 'ShimuraSakaue': '志村坂上',
    'ShimuraSanchome': '志村三丁目', 'Hasune': '蓮根', 'Nishidai': '西台',
    'Takashimadaira': '高島平', 'NishiTakashimadaira': '西高島平',

    # --- 東京メトロ南北線 ---
    'Shirokanedai': '白金台', 'ShirokaneTakanawa': '白金高輪', 'Meguro': '目黒',

    # --- 東急目黒線・東急新横浜線 ---
    'FudoMae': '不動前', 'MusashiKoyama': '武蔵小山', 'NishiKoyama': '西小山',
    'Senzoku': '洗足', 'Okurayama': '大倉山', 'Okusawa': '奥沢', 'DenEnChofu': '田園調布',
    'Tamagawa': '多摩川', 'ShinMaruko': '新丸子', 'Motosumiyoshi': '元住吉',
    'MusashiKosugi': '武蔵小杉', 'Hiyoshi': '日吉', 'ShinTsunashima': '新綱島', 'ShinYokohama': '新横浜',

    # --- 相鉄新横浜線・相鉄本線・相鉄いずみ野線 ---
    'HazawaYokohamaKokudai': '羽沢横浜国大', 'Nishiya': '西谷', 'Tsurugamine': '鶴ヶ峰',
    'Futamatagawa': '二俣川', 'Kibogaoka': '希望ヶ丘', 'Yamato': '大和', 'Kashiwadai': 'かしわ台',
    'Ebina': '海老名', 'MinamiMakigahara': '南万騎が原', 'RyokuenToshi': '緑園都市', 'IzumiChuo': 'いずみ中央',
    'Izumino': 'いずみ野', 'Yumegaoka': 'ゆめが丘', 'Shonandai': '湘南台',

    # --- 都営新宿線 ---
    'Shinjuku': '新宿', 'ShinjukuSanchome': '新宿三丁目', 'Akebonobashi': '曙橋',
    'Ichigaya': '市ヶ谷', 'Kudanshita': '九段下', 'Jimbocho': '神保町', 'Ogawamachi': '小川町',
    'Iwamotocho': '岩本町', 'BakuroYokoyama': '馬喰横山', 'Hamacho': '浜町', 'Morishita': '森下',
    'Kikukawa': '菊川', 'Sumiyoshi': '住吉', 'NishiOjima': '西大島', 'Ojima': '大島',
    'HigashiOjima': '東大島', 'Funabori': '船堀', 'Ichinoe': '一之江', 'Mizue': '瑞江',
    'Shinozaki': '篠崎', 'Motoyawata': '本八幡',

    # --- 京王新線・京王線 ---
    'Hatsudai': '初台', 'Hatagaya': '幡ヶ谷', 'Sasazuka': '笹塚', 'Daitabashi': '代田橋',
    'Meidaimae': '明大前', 'Sakurajosui': '桜上水', 'ChitoseKarasuyama': '千歳烏山',
    'Tsutsujigaoka': 'つつじヶ丘', 'Chofu': '調布', 'Fuchu': '府中',
    'Takahatafudo': '高幡不動', 'Kitano': '北野', 'KeioHachioji': '京王八王子',
    'Takaosanguchi': '高尾山口', 'Inagi': '稲城', 'Wakabadai': '若葉台', 'KeioNagayama': '京王永山',
    'KeioTamaCenter': '京王多摩センター', 'MinamiOsawa': '南大沢', 'Hashimoto': '橋本',

    # --- 都営大江戸線 ---
    'Tochomae': '都庁前', 'ShinjukuNishiguchi': '新宿西口', 'HigashiShinjuku': '東新宿',
    'WakamatsuKawada': '若松河田', 'UshigomeYanagicho': '牛込柳町', 'UshigomeKagurazaka': '牛込神楽坂',
    'Iidabashi': '飯田橋', 'Kasuga': '春日', 'HongoSanchome': '本郷三丁目', 'UenoOkachimachi': '上野御徒町',
    'ShinOkachimachi': '新御徒町', 'Kuramae': '蔵前', 'Ryogoku': '両国', 'Morishita': '森下',
    'KiyosumiShirakawa': '清澄白河', 'MonzenNakacho': '門前仲町', 'Tsukishima': '月島',
    'Kachidoki': '勝どき', 'Tsukijishijo': '築地市場', 'Shiodome': '汐留', 'Daimon': '大門',
    'Akabanebashi': '赤羽橋', 'AzabuJuban': '麻布十番', 'Roppongi': '六本木', 'AoyamaItchome': '青山一丁目',
    'KokuritsuKyogijo': '国立競技場', 'Yoyogi': '代々木', 'Shinjuku': '新宿',
    'NishiShinjukuGochome': '西新宿五丁目', 'NakanoSakaue': '中野坂上', 'HigashiNakano': '東中野',
    'Nakai': '中井', 'OchiaiMinamiNagasaki': '落合南長崎', 'ShinEgota': '新江古田',
    'Nerima': '練馬', 'Toshimaen': '豊島園', 'NerimaKasugacho': '練馬春日町', 'Hikarigaoka': '光が丘',

    # --- 都営浅草線 ---
    'NishiMagome': '西馬込', 'Magome': '馬込', 'Nakanobu': '中延', 'Togoshi': '戸越',
    'Gotanda': '五反田', 'Takanawadai': '高輪台', 'Sengakuji': '泉岳寺', 'Mita': '三田',
    'Daimon': '大門', 'Shimbashi': '新橋', 'HigashiGinza': '東銀座', 'Takaracho': '宝町',
    'Nihombashi': '日本橋', 'Ningyocho': '人形町', 'HigashiNihombashi': '東日本橋',
    'Asakusabashi': '浅草橋', 'Kuramae': '蔵前', 'Asakusa': '浅草', 'HonjoAzumabashi': '本所吾妻橋',
    'Oshiage': '押上',

    # --- [直通先] 京急線 ---
    'Shinagawa': '品川', 'KeikyuKamata': '京急蒲田', 'HanedaAirportTerminal1and2': '羽田空港',
    'KeikyuKawasaki': '京急川崎', 'KanagawaShimmachi': '神奈川新町', 'Yokohama': '横浜',
    'Kamiooka': '上大岡', 'KanazawaBunko': '金沢文庫', 'ZushiHayama': '逗子・葉山',
    'Hemmi': '逸見', 'Horinouchi': '堀ノ内', 'Uraga': '浦賀', 'KeikyuKurihama': '京急久里浜',
    'Miurakaigan': '三浦海岸', 'Misakiguchi': '三崎口',

    # --- [直通先] 京成線・北総線・芝山鉄道線 ---
    'Yahiro': '八広', 'Aoto': '青砥', 'KeiseiTakasago': '京成高砂', 'KeiseiKoiwa': '京成小岩',
    'Ichikawamama': '市川真間', 'HigashiNakayama': '東中山', 'KeiseiFunabashi': '京成船橋',
    'Funabashikeibajo': '船橋競馬場', 'KeiseiTsudanuma': '京成津田沼', 'Yachiyodai': '八千代台',
    'KeiseiOwada': '京成大和田', 'KeiseiUsui': '京成臼井', 'KeiseiSakura': '京成佐倉', 
    'Sogosando': '宗吾参道',
    'KeiseiNarita': '京成成田', 'HigashiNarita': '東成田', 'NaritaAirportTerminal2and3': '空港第２ビル',
    'NaritaAirportTerminal1': '成田空港', 'Yagiri': '矢切', 'HigashiMatsudo': '東松戸',
    'ShinKamagaya': '新鎌ヶ谷', 'NishiShiroi': '西白井', 'ChibaNewtownChuo': '千葉ニュータウン中央',
    'InzaiMakinohara': '印西牧の原', 'ImbaNihonIdai': '印旛日本医大', 'NaritaYukawa': '成田湯川',
}

TRAIN_TYPE_NAMES = {
    'odpt.TrainType:Toei.Local': '各停',
    'odpt.TrainType:Toei.Express': '急行',
    'odpt.TrainType:Toei.Rapid': '快速',
    'odpt.TrainType:Toei.LimitedExpress': '特急', 
    'odpt.TrainType:Toei.RapidLimitedExpress': '快特',
    'odpt.TrainType:Toei.AirportRapidLimitedExpress': 'ｴｱﾎﾟｰﾄ快特',
    'odpt.TrainType:Toei.AccessExpress': 'ｱｸｾｽ特急',
    'odpt.TrainType:Toei.CommuterLimitedExpress': '通勤特急',
}

TRAIN_OWNER_NAMES: Dict[str, str] = {
    "odpt.Operator:Toei": "都営車",
    "odpt.Operator:Keio": "京王車",
    "odpt.Operator:Keikyu": "京急車",
    "odpt.Operator:Keisei": "京成車",
    "odpt.Operator:Hokuso": "北総車", 
    "odpt.Operator:Shibayama": "芝山車", 
    "odpt.Operator:Tokyu": "東急車",
    "odpt.Operator:Sotetsu": "相鉄車",
}
# --- 監視対象リスト（都営地下鉄） ---
TOEI_LINES_TO_MONITOR = [
    {
        "id": "odpt.Railway:Toei.Mita",
        "name": "🔵都営三田線",
        "regular_trips": {
            ('odpt.TrainType:Toei.Local', 'NishiTakashimadaira'),
            ('odpt.TrainType:Toei.Local', 'Takashimadaira'),
            ('odpt.TrainType:Toei.Local', 'ShirokaneTakanawa'),
            ('odpt.TrainType:Toei.Local', 'Ebina'),
            ('odpt.TrainType:Toei.Local', 'Shonandai'),
            ('odpt.TrainType:Toei.Local', 'ShinYokohama'),
            ('odpt.TrainType:Toei.Local', 'Yamato'),
            ('odpt.TrainType:Toei.Local', 'Hiyoshi'),
            ('odpt.TrainType:Toei.Local', 'MusashiKosugi'),
            ('odpt.TrainType:Toei.Local', 'Nishiya'),
            ('odpt.TrainType:Toei.Express', 'Ebina'),
            ('odpt.TrainType:Toei.Express', 'Shonandai'),
            ('odpt.TrainType:Toei.Express', 'ShinYokohama'),
            ('odpt.TrainType:Toei.Express', 'Yamato'),
            ('odpt.TrainType:Toei.Express', 'Hiyoshi'),
            ('odpt.TrainType:Toei.Express', 'Nishiya'),
        }
    },
    {
        "id": "odpt.Railway:Toei.Shinjuku",
        "name": "🟢都営新宿線",
        "regular_trips": {
            ('odpt.TrainType:Toei.Local', 'KeioTamaCenter'), 
            ('odpt.TrainType:Toei.Local', 'Hashimoto'),     
            ('odpt.TrainType:Toei.Local', 'Sasazuka'),       
            ('odpt.TrainType:Toei.Local', 'Wakabadai'),      
            ('odpt.TrainType:Toei.Local', 'Shinjuku'),       
            ('odpt.TrainType:Toei.Local', 'Motoyawata'),    
            ('odpt.TrainType:Toei.Local', 'Ojima'),          
            ('odpt.TrainType:Toei.Local', 'Mizue'),          
            ('odpt.TrainType:Toei.Local', 'Iwamotocho'),    
            ('odpt.TrainType:Toei.Express', 'KeioTamaCenter'), 
            ('odpt.TrainType:Toei.Express', 'Hashimoto'),      
            ('odpt.TrainType:Toei.Express', 'Sasazuka'),       
            ('odpt.TrainType:Toei.Express', 'Motoyawata'),     
            ('odpt.TrainType:Toei.Express', 'Ojima'),
        }
    },
    {
        "id": "odpt.Railway:Toei.Oedo",
        "name": "🔴都営大江戸線",
        "regular_trips": {
            ('odpt.TrainType:Toei.Local', 'Hikarigaoka'),      
            ('odpt.TrainType:Toei.Local', 'Tochomae'),        
            ('odpt.TrainType:Toei.Local', 'ShinOkachimachi'), 
            ('odpt.TrainType:Toei.Local', 'Shiodome'),        
            ('odpt.TrainType:Toei.Local', 'KiyosumiShirakawa'),  
        }
    },
    {       
        "id": "odpt.Railway:Toei.Asakusa",
        "name": "🔴都営浅草線",
        "regular_trips": {
            ('odpt.TrainType:Toei.AirportRapidLimitedExpress', 'HanedaAirportTerminal1and2'),
            ('odpt.TrainType:Toei.AirportRapidLimitedExpress', 'NaritaAirportTerminal1'),
            ('odpt.TrainType:Toei.AirportRapidLimitedExpress', 'Sogosando'),
            ('odpt.TrainType:Toei.AirportRapidLimitedExpress', 'KeiseiNarita'),
            ('odpt.TrainType:Toei.RapidLimitedExpress', 'HanedaAirportTerminal1and2'),
            ('odpt.TrainType:Toei.RapidLimitedExpress', 'NaritaAirportTerminal1'),
            ('odpt.TrainType:Toei.RapidLimitedExpress', 'KeiseiNarita'),
            ('odpt.TrainType:Toei.RapidLimitedExpress', 'KeikyuKurihama'),
            ('odpt.TrainType:Toei.RapidLimitedExpress', 'Misakiguchi'),
            ('odpt.TrainType:Toei.RapidLimitedExpress', 'ShibayamaChiyoda'),
            ('odpt.TrainType:Toei.Express', 'HanedaAirportTerminal1and2'), 
            ('odpt.TrainType:Toei.Express', 'ZushiHayama'),
            ('odpt.TrainType:Toei.Local', 'NishiMagome'),
            ('odpt.TrainType:Toei.Local', 'Sengakuji'),
            ('odpt.TrainType:Toei.Local', 'Shinagawa'),
            ('odpt.TrainType:Toei.Local', 'ImbaNihonIdai'),
            ('odpt.TrainType:Toei.Local', 'Asakusabashi'),
            ('odpt.TrainType:Toei.Local', 'InzaiMakinohara'),
            ('odpt.TrainType:Toei.Local', 'Oshiage'),
            ('odpt.TrainType:Toei.Local', 'KeiseiTakasago'),
            ('odpt.TrainType:Toei.Local', 'Aoto'),
            ('odpt.TrainType:Toei.LimitedExpress', 'Misakiguchi'),
            ('odpt.TrainType:Toei.LimitedExpress', 'KeikyuKurihama'),
            ('odpt.TrainType:Toei.LimitedExpress', 'HanedaAirportTerminal1and2'),
            ('odpt.TrainType:Toei.LimitedExpress', 'Miurakaigan'),
            ('odpt.TrainType:Toei.LimitedExpress', 'KanazawaBunko'), 
            ('odpt.TrainType:Toei.LimitedExpress', 'KeiseiTakasago'),
            ('odpt.TrainType:Toei.LimitedExpress', 'Aoto'),
            ('odpt.TrainType:Toei.LimitedExpress', 'NaritaAirportTerminal1'),
            ('odpt.TrainType:Toei.LimitedExpress', 'ShibayamaChiyoda'),
            ('odpt.TrainType:Toei.LimitedExpress', 'KeiseiNarita'),
            ('odpt.TrainType:Toei.LimitedExpress', 'ImbaNihonIdai'),
            ('odpt.TrainType:Toei.LimitedExpress', 'KanagawaShimmachi'),
            ('odpt.TrainType:Toei.AccessExpress', 'NaritaAirportTerminal1'),
            ('odpt.TrainType:Toei.Rapid', 'KeiseiSakura'),
            ('odpt.TrainType:Toei.Rapid', 'NaritaAirportTerminal1'),
            ('odpt.TrainType:Toei.Rapid', 'Aoto'),
            ('odpt.TrainType:Toei.Rapid', 'KeiseiNarita'),
            ('odpt.TrainType:Toei.CommuterLimitedExpress', 'NaritaAirportTerminal1'),  
        }   
    },
]

notified_trains = set() # 通知済みリストは共通

# --- データを取ってくる係 (ほぼJRと同じ) ---
def fetch_toei_train_data(line_config):
    try:
        # operatorではなくrailwayで指定する方が確実
        params = {"odpt:railway": line_config["id"], "acl:consumerKey": API_TOKEN}
        response = requests.get(API_ENDPOINT, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"--- [TOEI FETCH] {line_config['name']} データ取得エラー: {e}", flush=True)
        return None

# --- データを判定する係 (JRのprocess_irregularitiesとほぼ同じ構造) ---
def process_toei_irregularities(train_data: List[Dict[str, Any]], line_config: Dict[str, Any]) -> List[str]:
    irregular_messages: List[str] = []
    
    for train in train_data:
        train_type_id: Optional[str] = train.get("odpt:trainType")
        train_number: Optional[str] = train.get("odpt:trainNumber")
        line_id: str = line_config["id"] # 路線IDを先に取得
        
        if not all([train_type_id, train_number, line_id]): continue
        if train_number is None: continue

        # 行き先リストを取得
        dest_station_id_list: Optional[List[str]] = train.get("odpt:destinationStation")

        is_irregular = False
        train_type_jp: str = "" # まず空で初期化
        dest_station_jp: str = "" # まず空で初期化
        notification_id: str = ""
        dest_station_en: str = "" # 通常ルート用に初期化

        # ▼▼▼▼▼ None行き特別ルート ▼▼▼▼▼
        if dest_station_id_list is None:
            if line_id == "odpt.Railway:Toei.Asakusa":
                print(f"--- [TOEI ROMAN] Train {train_number}: None destination on Asakusa Line. Assuming Keikyu Kamata. ---", flush=True)
                is_irregular = True
                dest_station_jp = "京急蒲田" # 特別表示
                notification_id = f"{train_number}_KeikyuKamata" # 特別ID
            elif line_id == "odpt.Railway:Toei.Mita":
                print(f"--- [TOEI ROMAN] Train {train_number}: None destination on Mita Line. Assuming Meguro Area. ---", flush=True)
                is_irregular = True
                dest_station_jp = "目黒方面" # 特別表示
                notification_id = f"{train_number}_MeguroArea" # 特別ID
            
            # None行きでも対象路線でなければ、通常通り無視 (is_irregular は False のまま)
            if not is_irregular:
                 continue # この列車はスキップ

            # 種別名は通常通り取得
            if line_id == "odpt.Railway:Toei.Oedo" and train_type_id == 'odpt.TrainType:Toei.Local':
                train_type_jp = "" 
            elif line_id == "odpt.Railway:Toei.Asakusa" and train_type_id == 'odpt.TrainType:Toei.Local':
                train_type_jp = "普通"
            else:
                train_type_jp = TRAIN_TYPE_NAMES.get(train_type_id, train_type_id)

        # ▼▼▼ 通常ルート ▼▼▼
        else:
            dest_station_en = dest_station_id_list[-1].split('.')[-1].strip()
            notification_id = f"{train_number}_{dest_station_en}"
            current_trip: tuple = (train_type_id, dest_station_en)
            allowed_trips: set = line_config.get("regular_trips", set())

            if current_trip not in allowed_trips:
                is_irregular = True

            # 通常ルートの種別名設定
            if line_id == "odpt.Railway:Toei.Oedo" and train_type_id == 'odpt.TrainType:Toei.Local':
                train_type_jp = ""
            elif line_id == "odpt.Railway:Toei.Asakusa" and train_type_id == 'odpt.TrainType:Toei.Local':
                train_type_jp = "普通"
            else:
                train_type_jp = TRAIN_TYPE_NAMES.get(train_type_id, train_type_id)
            
            # 通常ルートの行き先名設定
            dest_station_jp = STATION_DICT.get(dest_station_en, dest_station_en)

        # ▼▼▼ メッセージ作成 (None行きと通常ルートが合流) ▼▼▼
        if is_irregular and notification_id and notification_id not in notified_trains:
            try:
                line_name_jp: str = line_config.get("name", "?")
                
                # train_type_jp と dest_station_jp は上で決定済み

                location_text: str = ""
                from_station_id: Optional[str] = train.get("odpt:fromStation")
                to_station_id: Optional[str] = train.get("odpt:toStation")
                if to_station_id and from_station_id:
                    from_jp: str = STATION_DICT.get(from_station_id.split('.')[-1], '?')
                    to_jp: str = STATION_DICT.get(to_station_id.split('.')[-1], '?')
                    location_text = f"{from_jp}→{to_jp}を走行中"
                elif from_station_id:
                    from_jp: str = STATION_DICT.get(from_station_id.split('.')[-1], '?')
                    location_text = f"{from_jp}に停車中"
                
                delay_minutes: int = round(train.get("odpt:delay", 0) / 60)
                delay_text: str = f"遅延:{delay_minutes}分" if delay_minutes > 0 else ""

                owner_id: Optional[str] = train.get("odpt:trainOwner")
                owner_text: str = ""
                if owner_id:
                    owner_name: str = TRAIN_OWNER_NAMES.get(owner_id, "")
                    if owner_name: owner_text = f" ({owner_name})"
                
                message_line1 = f"[{line_name_jp}] {train_type_jp} {dest_station_jp}行き"
                location_text_with_delay = f"{location_text} ({delay_text})" if location_text and delay_text else location_text
                message_line2 = location_text_with_delay
                message_line3 = f"列番:{train_number}{owner_text}"
                
                final_message = f"{message_line1}\n{message_line2}\n{message_line3}" if message_line2 else f"{message_line1}\n{message_line3}"
                
                irregular_messages.append(final_message)
                notified_trains.add(notification_id)
            except Exception as e:
                print(f"--- [TOEI NOTIFICATION ERROR] Train {train_number} メッセージ作成エラー: {e}", flush=True)

    return irregular_messages

# --- 司令塔に提供する、唯一の機能 ---
def check_toei_irregularities() -> List[str]:
    all_irregular_trains: List[str] = []
    for line_config in TOEI_LINES_TO_MONITOR:
        train_data = fetch_toei_train_data(line_config)
        if train_data is not None:
            irregular_list = process_toei_irregularities(train_data, line_config)
            all_irregular_trains.extend(irregular_list)
    return all_irregular_trains