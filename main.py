import os
import re
import asyncio
import urllib.request
from flask import Flask
from threading import Thread
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, RPCError

# --- FLASK KEEP-ALIVE SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot 2 status: FULLY ACTIVE 24/7"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask, daemon=True).start()

# --- HARDENED SELF-PING SYSTEM ---
def self_ping():
    import time
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "")
    while True:
        time.sleep(120)
        if render_url:
            try:
                urllib.request.urlopen(render_url, timeout=10)
            except Exception:
                pass

Thread(target=self_ping, daemon=True).start()

# --- CONFIGURATION (SECOND BOT UPDATED) ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
STRING_SESSION = os.environ.get("STRING_SESSION", "")

# 1. Updated Source Channel
SOURCE_CHAT = "@crypto_dmfirstofficiall"  

# 2. Destination Channel
DESTINATION_CHAT = "@predictionmasterhindi"

# 3. Updated Game / Referral Link
MY_NEW_LINK = "https://www.dmfirst13.com/#/register?invitationCode=52199550527"

client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

def process_text(text):
    if not text:
        return ""
    # Replace external links with new referral link
    text = re.sub(r'https?://[^\s]+', MY_NEW_LINK, text)
    # Replace telegram handles with destination channel
    text = re.sub(r't\.me/[^\s]+', DESTINATION_CHAT, text)
    return text

album_cache = {}

@client.on(events.NewMessage(chats=SOURCE_CHAT))
async def handler(event):
    try:
        # Multi-photo / Album Handling
        if event.grouped_id:
            if event.grouped_id not in album_cache:
                album_cache[event.grouped_id] = True
                await asyncio.sleep(2.5)
                
                messages = await client.get_messages(SOURCE_CHAT, limit=10)
                group = [m for m in messages if m.grouped_id == event.grouped_id]
                
                media_list = []
                caption_text = ""
                for msg in reversed(group):
                    if msg.media:
                        media_list.append(msg.media)
                    if msg.raw_text and not caption_text:
                        caption_text = process_text(msg.raw_text)

                if media_list:
                    await client.send_file(DESTINATION_CHAT, media_list, caption=caption_text)
            return

        # Single Photo / Video / Text Handling
        updated_text = process_text(event.raw_text)
        if event.media:
            await client.send_file(DESTINATION_CHAT, event.media, caption=updated_text)
        else:
            if updated_text:
                await client.send_message(DESTINATION_CHAT, updated_text)

    except FloodWaitError as fwe:
        await asyncio.sleep(fwe.seconds + 2)
    except Exception as err:
        print(f"[ERROR] Handler issue: {err}")

async def main():
    while True:
        try:
            print("[STATUS] Listening for messages on Bot 2...")
            await client.start()
            await client.run_until_disconnected()
        except Exception as crash_err:
            await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())
