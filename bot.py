import os
from dotenv import load_dotenv

# まず、dotenvライブラリをインポートし、
# その直後にload_dotenv()を実行して環境変数を読み込む。
# これを他のどのimportよりも先に行うことが重要。
load_dotenv()

# --- これ以降に、他のimport文を続ける ---
import nextcord as discord
import asyncio
from flask import Flask
from threading import Thread

from jr_east_detector import check_jr_east_irregularities
from tama_monorail_info_detector import check_tama_monorail_info
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
NOTIFICATION_USER_ID = os.getenv('NOTIFICATION_USER_ID')
NOTIFICATION_CHANNEL_ID = int(os.getenv('NOTIFICATION_CHANNEL_ID'))

# Flask (変更なし)
app = Flask('')
@app.route('/')
def home(): return "Bot is alive!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# Intents (変更なし)
intents = discord.Intents.none()
intents.guilds = True
intents.messages = True
bot = discord.Client(intents=intents)

# --- on_ready イベントに目印を追加 ---
@bot.event
async def on_ready():
    print(f"--- [2] EVENT: on_ready - Logged in as {bot.user} ---", flush=True)
    bot.loop.create_task(periodic_check())
    print("--- [3] TASK: periodic_check has been created. ---", flush=True)

# --- periodic_check 関数に目印を追加 ---
async def periodic_check():
    await bot.wait_until_ready()
    channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
    if not channel:
        print(f"エラー: チャンネルID {NOTIFICATION_CHANNEL_ID} が見つかりません。")
        return

    while not bot.is_closed():
        all_notifications = []

        # --- JR東日本の非定期行先をチェック ---
        jr_messages = await bot.loop.run_in_executor(None, check_jr_east_irregularities)
        
        # ▼▼▼▼▼ ここからが最後のテスト ▼▼▼▼▼
        print(f"--- [FINAL REPORT FROM JR DETECTOR] ---", flush=True)
        print(f"    -> Number of reports: {len(jr_messages)}", flush=True)
        if jr_messages:
            print(f"    -> Report contents: {jr_messages}", flush=True)
        print("--------------------------------------", flush=True)
        if jr_messages:
            all_notifications.extend(jr_messages)

        # ★★★ ここから追加 ★★★
        # --- 多摩モノレールの運行情報をチェック ---
        tama_message = await bot.loop.run_in_executor(None, check_tama_monorail_info)
        if tama_message: # メッセージが返ってきたら（変化があったら）リストに追加
            all_notifications.append(tama_message)
        # ★★★ ここまで追加 ★★★

        # 送信すべき通知があれば、まとめて送信
        if all_notifications:
            for msg in all_notifications:
                await channel.send(msg)
        
        await asyncio.sleep(60)

# (Botの起動部分は変更なし)
keep_alive()
bot.run(DISCORD_BOT_TOKEN)