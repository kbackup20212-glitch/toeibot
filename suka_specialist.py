import re

# --- この専門家だけが知っている、中央線のルールブック ---
LIMITED_EXPRESS_REGULAR_DESTINATIONS = {
    "特急NEX": {'NaritaAirportTerminal1','Shinjuku','Ofuna'},
    "特急NEX(新宿編成)": {'NaritaAirportTerminal1','Shinjuku','Tokyo'},
    "特急湘南": {'Tokyo'},
    "特急": {},
}


def _get_suka_limited_express_nickname(train_number_str):
    match = re.search(r'\d+', train_number_str)
    if not match: return "特急"
    num = int(match.group(0))
    if (2001 <= num <= 2099): 
        return "特急NEX"
    if (2201 <= num <= 2299):
        return "特急NEX(新宿編成)"
    if (3078 <= num <= 3080): 
        return "特急湘南"
    return "特急"

# --- この専門家が、現場監督に提供する唯一の報告機能 ---
def check_suka_line_train(train, general_regular_trips, general_train_type_names):
    """
    横須賀線の列車を専門的に判定する。
    戻り値: (is_irregular: bool, train_type_jp: str)
    """
    train_type_id = train["odpt:trainType"]
    dest_station_en = train["odpt:destinationStation"][-1].split('.')[-1].strip()
    train_number = train["odpt:trainNumber"]

    # 【特急の場合】
    if train_type_id == 'odpt.TrainType:JR-East.LimitedExpress':
        nickname = _get_suka_limited_express_nickname(train_number)
        if nickname in LIMITED_EXPRESS_REGULAR_DESTINATIONS:
            allowed_dests = LIMITED_EXPRESS_REGULAR_DESTINATIONS[nickname]
            is_irregular = dest_station_en not in allowed_dests
            return is_irregular, nickname

    # 【快速・特快・愛称なし特急など、その他すべての場合】
    # 専門家は、自分の専門外のことは、現場監督から渡された標準ルールブックで判定する
    current_trip = (train_type_id, dest_station_en)
    is_allowed = current_trip in general_regular_trips
    return not is_allowed, general_train_type_names.get(train_type_id, train_type_id)