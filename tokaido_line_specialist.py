import re

# --- この専門家だけが知っている、東海道線のルールブック ---
LIMITED_EXPRESS_REGULAR_DESTINATIONS = {
    '寝台特急ｻﾝﾗｲｽﾞ': {'Takamatsu', 'Kotohira', 'Tokyo'},
    '特急ｻﾌｨｰﾙ踊り子': {'Tokyo', 'IzukyuShimoda'},
    '特急踊り子': {'Tokyo', 'IzukyuShimoda', 'Shinjuku','Ikebukuro'},
    '特急湘南': {'Tokyo', 'Shinjuku', 'Hiratsuka', 'Odawara'},
    '特急NEX': {'Ofuna', 'NaritaAirportTerminal1'},
    '特急ときわ': {'Katsuta', 'Tsuchiura', 'Takahagi','Shinagawa'},
    '特急ひたち': {'Sendai','Iwaki','Shinagawa'},
    "特急鎌倉": {},
    "特急": {}, # 愛称なし特急は基本すべて通知対象とする場合
}

# --- 旧botのロジックを基にした、新しい愛称判定関数 ---
def get_tokaido_limited_express_nickname(train_number_str):
    """列車番号の文字列から特急の愛称を返す関数"""
    try:
        # 最後の文字（'M'など）を削ってから数字に変換
        num = int(train_number_str[:-1])
    except (ValueError, IndexError):
        # もし変換に失敗したら、デフォルトの「特急」を返す
        return "特急"

    if (3020 <= num <= 3069) or (4020 <= num <= 4069) or (num in [8001, 8002]) or \
       (8005 <= num <= 8014) or (8016 <= num <= 8040) or (8043 <= num <= 8065) or \
    (8070 <= num <= 8093) or (9020 <= num <= 9090):
        return "特急踊り子"
    elif num in [3001, 3002, 8003, 8004, 8015]:
        return "特急ｻﾌｨｰﾙ踊り子"
    elif (3070 <= num <= 3099) or (num == 6089):
        return "特急湘南"
    elif num in [5031, 5032, 9011, 9012, 8041, 8042]:
        return "寝台特急ｻﾝﾗｲｽﾞ"
    elif 2001 <= num <= 2100:
        return "特急NEX"
    elif 8066 <= num <= 8069:
        return "特急鎌倉"
    elif (51 <= num <= 99) or (9091 <= num <= 9099):
        return "特急ときわ"
    elif (1 <= num <= 50) or (8094 <= num <= 8099):
        return "特急ひたち"
    else:
        return "特急"

# --- この専門家が、現場監督に提供する唯一の報告機能 ---
def check_tokaido_line_train(train, general_regular_trips, general_train_type_names):
    """
    東海道線の列車を専門的に判定する。
    戻り値: (is_irregular: bool, train_type_jp: str, destination_en: str)
    """
    train_type_id = train.get("odpt:trainType")
    dest_station_en = train.get("odpt:destinationStation", [""])[-1].split('.')[-1].strip()
    train_number = train.get("odpt:trainNumber")

    # --- ルール①：「S」で終わる普通列車は、常に非定期な「迂回列車」 ---
    if train_type_id == 'odpt.TrainType:JR-East.Local' and train_number.endswith('S'):
        return True, "[迂回]普通", dest_station_en

    # --- ルール②：特急の判定 ---
    if train_type_id == 'odpt.TrainType:JR-East.LimitedExpress':
        # 新しい愛称判定関数を呼び出す
        nickname = get_tokaido_limited_express_nickname(train_number)

        # --- ルール③：「踊り子」下り14両の特殊判定 ---
        direction = train.get("odpt:railDirection")
        car_composition = train.get("odpt:carComposition", 0)

        if nickname == "特急踊り子" and direction and "Outbound" in direction and car_composition == 14:
            # 定期行先リストを参照
            allowed_dests = LIMITED_EXPRESS_REGULAR_DESTINATIONS.get(nickname, set())
            is_irregular = dest_station_en not in allowed_dests
            # 表示上は「伊豆急下田・修善寺」に変える
            display_dest = "IzukyuShimoda.Shuzenji" if dest_station_en == 'IzukyuShimoda' else dest_station_en
            return is_irregular, nickname, display_dest

        # --- ルール④：「サンライズ」の特殊判定 ---
        if nickname == "寝台特急ｻﾝﾗｲｽﾞ" and direction and "Outbound" in direction and car_composition == 14:
            allowed_dests = LIMITED_EXPRESS_REGULAR_DESTINATIONS.get(nickname, set())
            is_irregular = dest_station_en not in allowed_dests
            # 表示上は「高松・出雲市」に変える
            display_dest = "Takamatsu.Izumoshi" if dest_station_en == 'Takamatsu' else dest_station_en
            return is_irregular, nickname, display_dest

        # その他の特急の判定
        if nickname in LIMITED_EXPRESS_REGULAR_DESTINATIONS:
            allowed_dests = LIMITED_EXPRESS_REGULAR_DESTINATIONS[nickname]
            is_irregular = dest_station_en not in allowed_dests
            return is_irregular, nickname, dest_station_en

    # 【快速・普通など、その他すべての場合】
    current_trip = (train_type_id, dest_station_en)
    is_allowed = current_trip in general_regular_trips
    return not is_allowed, general_train_type_names.get(train_type_id, train_type_id), dest_station_en