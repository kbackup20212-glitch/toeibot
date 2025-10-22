import re

# --- この専門家だけが知っている、高崎・宇都宮線のルールブック ---
LIMITED_EXPRESS_REGULAR_DESTINATIONS = {
    "特急水上": {},
    "特急ほくほく十日町雪まつり": {},
    "特急ｽﾍﾟｰｼｱ日光": {'Shinjuku', 'TobuNikko'},
    "特急きぬがわ": {'Shinjuku', 'KinugawaOnsen'},
    "特急日光": {},
    "特急草津四万": {'Ueno','Naganoharakusatsuguchi'},
    "特急あかぎ": {'Ueno','Shinjuku','Konosu','Honjo','Takasaki'},
    "特急": {},
}

def _get_tohoku_limited_express_nickname(train_number_str):
    match = re.search(r'\d+', train_number_str)
    if not match: 
        return "特急"
    num = int(match.group(0))
    if num in [9090, 9091]: 
        return "特急水上"
    elif num in [9005, 9006]: 
        return "特急ほくほく十日町雪まつり"
    elif num in [1091, 1094, 8111, 8114]: 
        return "特急ｽﾍﾟｰｼｱ日光"
    elif num in [1082, 1083, 8112, 8113]: 
        return "特急きぬがわ"
    elif (8121 <= num <= 8124):
        return "特急日光"
    elif (3001 <= num <= 3199) or (9061 <= num <= 9082): 
        return "特急草津四万"
    elif (4001 <= num <= 4199) or (8081 <= num <= 8082): 
        return "特急あかぎ"
    return "特急"

# --- この専門家が、現場監督に提供する唯一の報告機能 ---
def check_tohoku_train(train, general_regular_trips, general_train_type_names):

    train_type_id = train["odpt:trainType"]
    dest_station_en = train["odpt:destinationStation"][-1].split('.')[-1].strip()
    train_number = train["odpt:trainNumber"]

    # 【特急の場合】
    if train_type_id == 'odpt.TrainType:JR-East.LimitedExpress':
        nickname = _get_tohoku_limited_express_nickname(train_number)
        if nickname in LIMITED_EXPRESS_REGULAR_DESTINATIONS:
            allowed_dests = LIMITED_EXPRESS_REGULAR_DESTINATIONS[nickname]
            is_irregular = dest_station_en not in allowed_dests
            return is_irregular, nickname
    

    # 【快速・特快・愛称なし特急など、その他すべての場合】
    # 専門家は、自分の専門外のことは、現場監督から渡された標準ルールブックで判定する
    current_trip = (train_type_id, dest_station_en)
    is_allowed = current_trip in general_regular_trips
    return not is_allowed, general_train_type_names.get(train_type_id, train_type_id)