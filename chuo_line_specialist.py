import re

# --- この専門家だけが知っている、中央線のルールブック ---
LIMITED_EXPRESS_REGULAR_DESTINATIONS = {
    "特急あずさ": {'Matsumoto', 'Hakuba', 'Shinjuku', 'Tokyo', 'Chiba'},
    "特急かいじ": {'Ryuo', 'Kofu', 'Shinjuku', 'Tokyo'},
    "特急富士回遊": {'Kawaguchiko', 'Shinjuku'},
    "特急新宿さざなみ": {'Shinjuku', 'Tateyama'},
    "特急新宿わかしお": {'Shinjuku', 'AwaKamogawa'},
    "特急アルプス": {},
}
CHUO_RAPID_REGULAR_DESTINATIONS = {
    "快速": {'Tokyo','Mitaka','MusashiKoganei','Kokubunji', 'Tachikawa','Ome',
           'Toyoda','Hachioji','Takao','Otsuki'},
    "快速ｻｳﾝﾄﾞｺﾆﾌｧｰ": {},
}
CHUO_LOCAL_REGULAR_DESTINATIONS = {
    "各停": {'Tokyo', 'MusashiKoganei','Kokubunji', 'Tachikawa','Toyoda','Hachioji','Takao','Otsuki','Ome'},
    "普通むさしの号": {'Hachioji', 'Omiya'},
    "普通": {'Tachikawa','Takao', 'Otsuki','Kawaguchiko',
           'Kofu', 'Kobuchizawa', 'Matsumoto','Nirasaki','Enzan', 'Nagano'},
}

# --- この専門家だけが使う、特殊な道具 ---
def _get_chuo_local_type_name(train_number_str):
    if not train_number_str.endswith('M'): return "各停"
    if re.match(r'^26\d{2}M$', train_number_str): return "普通むさしの号"
    return "普通"

def _get_chuo_rapid_nickname(train_number_str):
    match = re.search(r'\d+', train_number_str)
    if not match: return "快速"
    num = int(match.group(0))
    if (9876 <= num <= 9879): return "快速ｻｳﾝﾄﾞｺﾆﾌｧｰ"
    return "快速"

def _get_chuo_limited_express_nickname(train_number_str):
    match = re.search(r'\d+', train_number_str)
    if not match: return "特急"
    num = int(match.group(0))
    if (8190 <= num <= 8199) or (9190 <= num <= 9199): return "特急富士回遊"
    if num in [9095, 9096]: return "特急アルプス"
    if (9040 <= num <= 9049): return "特急新宿さざなみ"
    if (9050 <= num <= 9059): return "特急新宿わかしお"
    if (1 <= num <= 99) or (5001 <= num <= 5099) or (8070 <= num <= 8099) or (9070 <= num <= 9094): return "特急あずさ"
    if (3100 <= num <= 3199) or (5100 <= num <= 5199) or (8100 <= num <= 8189) or (9100 <= num <= 9189): return "特急かいじ"
    return "特急"

# --- この専門家が、現場監督に提供する唯一の報告機能 ---
def check_chuo_line_train(train, general_regular_trips, general_train_type_names):
    """
    中央線の列車を専門的に判定する。
    戻り値: (is_irregular: bool, train_type_jp: str)
    """
    train_type_id = train["odpt:trainType"]
    dest_station_en = train["odpt:destinationStation"][-1].split('.')[-1].strip()
    train_number = train["odpt:trainNumber"]

    # 【特急の場合】
    if train_type_id == 'odpt.TrainType:JR-East.LimitedExpress':
        nickname = _get_chuo_limited_express_nickname(train_number)
        if nickname in LIMITED_EXPRESS_REGULAR_DESTINATIONS:
            allowed_dests = LIMITED_EXPRESS_REGULAR_DESTINATIONS[nickname]
            is_irregular = dest_station_en not in allowed_dests
            return is_irregular, nickname
    
       # 【快速の場合】
    if train_type_id == 'odpt.TrainType:JR-East.rapid':
        rapid_type = _get_chuo_rapid_nickname(train_number)
        allowed_dests = CHUO_RAPID_REGULAR_DESTINATIONS.get(rapid_type, set())
        is_irregular = dest_station_en not in allowed_dests
        return is_irregular, rapid_type
    
    # 【各停・普通の場合】
    if train_type_id == 'odpt.TrainType:JR-East.Local':
        local_type = _get_chuo_local_type_name(train_number)
        allowed_dests = CHUO_LOCAL_REGULAR_DESTINATIONS.get(local_type, set())
        is_irregular = dest_station_en not in allowed_dests
        return is_irregular, local_type

    # 【快速・特快・愛称なし特急など、その他すべての場合】
    # 専門家は、自分の専門外のことは、現場監督から渡された標準ルールブックで判定する
    current_trip = (train_type_id, dest_station_en)
    is_allowed = current_trip in general_regular_trips
    return not is_allowed, general_train_type_names.get(train_type_id, train_type_id)