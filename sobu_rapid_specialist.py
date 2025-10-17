import re

# --- この専門家だけが知っている、総武快速線のルールブック ---
LIMITED_EXPRESS_REGULAR_DESTINATIONS = {
    "特急あずさ": {'Matsumoto', 'Chiba'},
    "特急NEX": {'Ofuna', 'NaritaAirportTerminal1'},
    "特急しおさい": {'Choshi', 'Sakura', 'Naruto', 'Tokyo'},
    "特急新宿さざなみ": {'Shinjuku', 'Tateyama'},
    "特急新宿わかしお": {'Shinjuku', 'Awakamogawa'},
    "特急": {}, 
}
RAPID_REGULAR_DESTINATIONS = {
    "快速": {'Tokyo','Mitaka','MusashiKoganei','Kokubunji', 'Tachikawa','Ome',
           'Toyoda','Hachioji','Takao','Otsuki'},
    "快速ｻｳﾝﾄﾞｺﾆﾌｧｰ": {},
}

# --- この専門家だけが使う、特殊な道具 ---
def _get_chuo_rapid_nickname(train_number_str):
    match = re.search(r'\d+', train_number_str)
    if not match: 
        return "快速"
    num = int(match.group(0))
    if num in [9131, 9132, 9231, 9232]: 
        return "快速B.B.BASE"
    if num in [9331, 9332]: 
        return "快速B.B.BASE佐倉・銚子"
    if num in [9441, 9442]: 
        return "快速B.B.BASE手賀沼"
    return "快速"

def _get_chuo_limited_express_nickname(train_number_str):
    match = re.search(r'\d+', train_number_str)
    if not match: 
        return "特急"
    num = int(match.group(0))
    if (5001 <= num <= 5099): 
        return "特急あずさ"
    if (2001 <= num <= 2099): 
        return "特急NEX"
    if (4001 <= num <= 4199): 
        return "特急しおさい"
    if (9040 <= num <= 9049): 
        return "特急新宿さざなみ"
    if (9050 <= num <= 9059): 
        return "特急新宿わかしお"
    return "特急"

# --- この専門家が、現場監督に提供する唯一の報告機能 ---
def check_chuo_line_train(train, general_regular_trips, general_train_type_names):

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
        allowed_dests = RAPID_REGULAR_DESTINATIONS.get(rapid_type, set())
        is_irregular = dest_station_en not in allowed_dests
        return is_irregular, rapid_type

    # 【快速・特快・愛称なし特急など、その他すべての場合】
    # 専門家は、自分の専門外のことは、現場監督から渡された標準ルールブックで判定する
    current_trip = (train_type_id, dest_station_en)
    is_allowed = current_trip in general_regular_trips
    return not is_allowed, general_train_type_names.get(train_type_id, train_type_id)