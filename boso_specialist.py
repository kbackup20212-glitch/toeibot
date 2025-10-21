import re

# --- この専門家だけが知っている、総武快速線のルールブック ---
LIMITED_EXPRESS_REGULAR_DESTINATIONS = {
    "特急あずさ": {'Matsumoto', 'Chiba'},
    "特急NEX": {'Shinjuku','Ofuna', 'NaritaAirportTerminal1'},
    "特急しおさい": {'Choshi', 'Sakura', 'Naruto', 'Tokyo'},
    "特急新宿さざなみ": {'Shinjuku', 'Tateyama'},
    "特急新宿わかしお": {'Shinjuku', 'Awakamogawa'},
    "特急さざなみ": {'Tokyo', 'Tateyama'},
    "特急わかしお": {'Tokyo', 'KazusaIchinomiya', 'Awakamogawa'},
    "特急開運成田山初詣": {},
    "特急": {}, 
}
RAPID_REGULAR_DESTINATIONS = {
    "快速": {'Kimitsu','Sakura','KazusaIchinomiya','Narita','NaritaAirportTerminal1',
            'Chiba','Tsudanuma','Tokyo','Shinagawa','Ofuna','Yokosuka','Zushi','Kurihama'},
    "快速B.B.BASE": {},
    "快速B.B.BASE佐倉・銚子": {},
    "快速B.B.BASE手賀沼": {},
}

# --- この専門家だけが使う、特殊な道具 ---
def _get_boso_rapid_nickname(train_number_str):
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

def _get_boso_limited_express_nickname(train_number_str):
    match = re.search(r'\d+', train_number_str)
    if not match: 
        return "特急"
    num = int(match.group(0))
    if num in [5003, 5004]: 
        return "特急あずさ"
    if (1001 <= num <= 1050): 
        return "特急さざなみ"
    if (1051 <= num <= 2000) or (9072 <= num <= 9099) or (9201 <= num <= 9209): 
        return "特急わかしお"
    if (2001 <= num <= 2099) or (2201 <= num <= 2299): 
        return "特急NEX"
    if (4001 <= num <= 4199) or (9301 <= num <= 9309): 
        return "特急しおさい"
    if (9040 <= num <= 9049) or (9111 <= num <= 9119): 
        return "特急新宿さざなみ"
    if (9050 <= num <= 9059): 
        return "特急新宿わかしお"
    if num in [9433, 9434]:
        return "特急開運成田山初詣" 
    return "特急"

# --- この専門家が、現場監督に提供する唯一の報告機能 ---
def check_boso_train(train, general_regular_trips, general_train_type_names):

    train_type_id = train["odpt:trainType"]
    dest_station_en = train["odpt:destinationStation"][-1].split('.')[-1].strip()
    train_number = train["odpt:trainNumber"]

    # 【特急の場合】
    if train_type_id == 'odpt.TrainType:JR-East.LimitedExpress':
        nickname = _get_boso_limited_express_nickname(train_number)
        if nickname in LIMITED_EXPRESS_REGULAR_DESTINATIONS:
            allowed_dests = LIMITED_EXPRESS_REGULAR_DESTINATIONS[nickname]
            is_irregular = dest_station_en not in allowed_dests
            return is_irregular, nickname
    
       # 【快速の場合】
    if train_type_id == 'odpt.TrainType:JR-East.rapid':
        rapid_type = _get_boso_rapid_nickname(train_number)
        allowed_dests = RAPID_REGULAR_DESTINATIONS.get(rapid_type, set())
        is_irregular = dest_station_en not in allowed_dests
        return is_irregular, rapid_type

    # 【快速・特快・愛称なし特急など、その他すべての場合】
    # 専門家は、自分の専門外のことは、現場監督から渡された標準ルールブックで判定する
    current_trip = (train_type_id, dest_station_en)
    is_allowed = current_trip in general_regular_trips
    return not is_allowed, general_train_type_names.get(train_type_id, train_type_id)