import os
import requests

# .envから都営地下鉄・多摩モノレール用のトークンを読み込む
API_TOKEN = os.getenv('ODPT_TOKEN_TOEI')
# APIエンドポイント（運行情報用）
API_ENDPOINT = "https://api.odpt.org/api/v4/odpt:TrainInformation"

# 最後に取得した運行情報のテキストを保存しておく変数
# これと違う情報が来たら「変化あり」と判断します
last_tama_monorail_status = ""

def check_tama_monorail_info():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    """
    多摩モノレールの運行情報をチェックし、変化があれば通知用メッセージを返す関数
    """
    global last_tama_monorail_status # ファイル内で共通の変数を使うことを宣言

    try:
        # APIリクエストのためのパラメータを設定
        params = {
            "odpt:operator": "odpt.Operator:TamaMonorail",
            "acl:consumerKey": API_TOKEN
        }
        operator_id = "odpt.Operator:TamaMonorail"
        target_url = f"{API_ENDPOINT}?odpt:operator={operator_id}&acl:consumerKey={API_TOKEN}"
        response = requests.get(target_url, headers=headers, timeout=30)
        info_data = response.json()

        # データが空、または情報テキストがない場合は何もしない
        if not info_data or "odpt:trainInformationText" not in info_data[0]:
            return None

        # 現在の運行情報テキスト（日本語）を取得
        current_status_text = info_data[0]["odpt:trainInformationText"]["ja"]

        # 前回取得した情報と、今回取得した情報が異なる場合のみ通知
        if current_status_text != last_tama_monorail_status:
            print(f"--- [TAMA] 運行情報に変化を検知: {current_status_text} ---", flush=True)
            # 状態を更新
            last_tama_monorail_status = current_status_text
            
            # 通知用のメッセージを作成して返す
            message = f"【多摩モノレール 運行情報】\n{current_status_text}"
            return message
        
        # 変化がなければ何も返さない
        return None

    except Exception as e:
        print(f"--- [TAMA] ERROR: {e} ---", flush=True)
        return None