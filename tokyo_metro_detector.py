import os
import requests
import re

# 多摩モノレールと同じトークンを使用
API_TOKEN = os.getenv('ODPT_TOKEN_TOEI')
API_ENDPOINT = "https://api.odpt.org/api/v4/odpt:TrainInformation"

# --- 1. 路線データ：駅の順番を定義する ---
# 銀座線の駅名を、渋谷から浅草の順番でリスト化
GINZA_LINE_STATIONS = [
    '渋谷', '表参道', '外苑前', '青山一丁目', '赤坂見附', '溜池山王', '虎ノ門', 
    '新橋', '銀座', '京橋', '日本橋', '三越前', '神田', '末広町', '上野広小路', 
    '上野', '稲荷町', '田原町', '浅草'
]

# --- 2. 状態を記憶する変数 ---
# 最後に取得した運行情報のテキストを路線ごとに保存しておく
# これと違う情報が来たら「変化あり」と判断
last_metro_statuses = {}

# --- 3. メイン関数 ---
def check_tokyo_metro_info():
    """
    東京メトロの運行情報をチェックし、折り返し運転を推測して通知用メッセージを返す
    """
    global last_metro_statuses
    notification_messages = []

    try:
        params = {"odpt:operator": "odpt.Operator:TokyoMetro", "acl:consumerKey": API_TOKEN}
        response = requests.get(API_ENDPOINT, params=params, timeout=30)
        response.raise_for_status()
        info_data = response.json()

        for line_info in info_data:
            line_id = line_info.get("odpt:railway")
            current_status = line_info.get("odpt:trainInformationText", {}).get("ja")
            
            # 路線IDか情報テキストがなければスキップ
            if not line_id or not current_status:
                continue
            
            # 前回から情報に変化があった場合のみ処理
            if current_status != last_metro_statuses.get(line_id):
                last_metro_statuses[line_id] = current_status # 状態を更新

                # まずは銀座線だけを対象にする
                if line_id == "odpt.Railway:TokyoMetro.Ginza":
                    
                    # 運行情報テキストに「運転を見合わせています」が含まれているかチェック
                    if "運転を見合わせています" in current_status:
                        # 「A駅～B駅」のパターンを正規表現で探す
                        match = re.search(r'(.+?)駅～(.+?)駅間で運転を見合わせています', current_status)
                        
                        if match:
                            station1, station2 = match.groups()
                            
                            try:
                                # 見合わせ区間の駅の、リスト上での位置（インデックス）を探す
                                idx1 = GINZA_LINE_STATIONS.index(station1)
                                idx2 = GINZA_LINE_STATIONS.index(station2)
                                
                                start_idx = min(idx1, idx2)
                                end_idx = max(idx1, idx2)
                                
                                # 折り返し駅を推測
                                turn_back_1 = GINZA_LINE_STATIONS[start_idx - 1] if start_idx > 0 else None
                                turn_back_2 = GINZA_LINE_STATIONS[end_idx + 1] if end_idx < len(GINZA_LINE_STATIONS) - 1 else None

                                # 通知メッセージを作成
                                line_name_jp = "銀座線"
                                message = f"【{line_name_jp} 運転見合わせ】\n{current_status}"
                                
                                if turn_back_1 and turn_back_2:
                                    message += f"\n\n推測：**{turn_back_1}駅**と**{turn_back_2}駅**で折り返し運転の可能性"
                                elif turn_back_1:
                                    message += f"\n\n推測：**{turn_back_1}駅**で折り返し運転の可能性"
                                elif turn_back_2:
                                    message += f"\n\n推測：**{turn_back_2}駅**で折り返し運転の可能性"

                                notification_messages.append(message)

                            except ValueError:
                                # もしリストに駅名が見つからなかった場合は、通常の運行情報だけを通知
                                notification_messages.append(f"【銀座線 運転見合わせ】\n{current_status}")
        
        return notification_messages

    except Exception as e:
        print(f"--- [METRO] ERROR: {e} ---", flush=True)
        return None