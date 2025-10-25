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
from tokyo_metro_detector import check_tokyo_metro_info

from toei_delay_watcher import check_toei_delay_increase
from toei_detector import check_toei_irregularities
from jr_east_info_detector import check_jr_east_info, get_current_official_info
from jr_east_delay_watcher import check_delay_increase
from tobu_delay_watcher import check_tobu_delay_increase



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
        official_info = {}

        # 1. JR東 非定期
        jr_messages = await bot.loop.run_in_executor(None, check_jr_east_irregularities)
        if jr_messages: all_notifications.extend(jr_messages)

        # 2. JR東 運行情報
        jr_info_messages = await bot.loop.run_in_executor(None, check_jr_east_info)
        official_info = await bot.loop.run_in_executor(None, get_current_official_info)
        
        if jr_info_messages:
            all_notifications.extend(jr_info_messages)
        
        # 3. 都営 非定期
        toei_messages = await bot.loop.run_in_executor(None, check_toei_irregularities)
        if toei_messages: all_notifications.extend(toei_messages)

        # 4. 多摩モノ 運行情報
        tama_message = await bot.loop.run_in_executor(None, check_tama_monorail_info)
        if tama_message: all_notifications.append(tama_message)

        # 5. 東京メトロ 運行情報
        metro_messages = await bot.loop.run_in_executor(None, check_tokyo_metro_info)
        if metro_messages: all_notifications.extend(metro_messages)

        # 6. JR東日本 遅延増加監視
        delay_watcher_messages = await bot.loop.run_in_executor(None, check_delay_increase, official_info)
        
        if delay_watcher_messages:
            all_notifications.extend(delay_watcher_messages)
        
        # 7. 都営 遅延増加監視 
        toei_delay_messages = await bot.loop.run_in_executor(None, check_toei_delay_increase)
        if toei_delay_messages:
            all_notifications.extend(toei_delay_messages)

        # 8. 東武 遅延増加監視 ---
        tobu_delay_messages = await bot.loop.run_in_executor(None, check_tobu_delay_increase)
        if tobu_delay_messages:
            all_notifications.extend(tobu_delay_messages)

        if all_notifications:
            for msg in all_notifications:
                await channel.send(msg)
        await asyncio.sleep(20)

# (Botの起動部分は変更なし)
keep_alive()
bot.run(DISCORD_BOT_TOKEN)