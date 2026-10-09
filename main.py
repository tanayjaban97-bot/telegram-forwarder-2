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
    return "Bot status: FULLY ACTIVE 24/7"

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

# --- CONFIGURATION FROM RENDER ENV ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
STRING_SESSION = os.environ.get("STRING_SESSION", "")

SOURCE_CHAT = os.environ.get("SOURCE_CHAT", "@Bigsmallmaster11").strip()
DESTINATION_CHAT = os.environ.get("DESTINATION_CHAT", "@SixClubWinningZone").strip()

OLD_LINK = os.environ.get("OLD_LINK", "").strip()
NEW_LINK = os.environ.get("NEW_LINK", "").strip()

DEST_HANDLE = DESTINATION_CHAT.replace("@", "")

client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

def process_text(text):
    if not text:
        return ""
    
    if OLD_LINK and NEW_LINK:
        text = text.replace(OLD_LINK, NEW_LINK)
    elif NEW_LINK:
        text = re.sub(r'https?://[^\s]+', NEW_LINK, text)

    text = re.sub(r't\.me/[a-zA-Z0-9_]+', f't.me/{DEST_HANDLE}', text)
    text = re.sub(r'@[a-zA-Z0-9_]+', DESTINATION_CHAT, text)
    
    return text

# Saved Messages ('me') se latest APK file fetch karne ka function
async def get_my_saved_apk():
    try:
        async for msg in client.iter_messages('me', limit=20):
            if msg.file and msg.file.name and msg.file.name.endswith('.apk'):
                print(f"[FOUND APK] Found saved APK: {msg.file.name}")
                return msg.media
    except Exception as e:
        print(f"[ERROR] Saved Messages se APK read karne me error: {e}")
    return None

album_cache = {}

@client.on(events.NewMessage(chats=SOURCE_CHAT))
async def handler(event):
    try:
        print(f"[NEW MESSAGE RECEIVED] Chat: {event.chat_id}")

        # Check if incoming message is an APK document
        is_apk = False
        if event.file and event.file.name and event.file.name.endswith('.apk'):
            is_apk = True
            print("[DETECTED] Source me APK aayi hai. Saved Messages wali APK se replace kar rahe hain...")

        updated_text = process_text(event.raw_text)

        # 1. Handling APK Messages (Replace with Saved Messages APK)
        if is_apk:
            my_apk_media = await get_my_saved_apk()
            if my_apk_media:
                await client.send_file(DESTINATION_CHAT, my_apk_media, caption=updated_text)
                print("[SUCCESS] Aapki Saved Messages wali APK post ho gayi!")
            else:
                await client.send_message(DESTINATION_CHAT, updated_text)
                print("[WARNING] Saved Messages me APK nahi mili. Plain text bhej diya.")
            return

        # 2. Multi-photo / Album Handling
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
                    print("[SUCCESS] Album forward ho gaya!")
            return

        # 3. Regular Photo / Video / Text Handling
        if event.media:
            await client.send_file(DESTINATION_CHAT, event.media, caption=updated_text)
            print("[SUCCESS] Media message forward ho gaya!")
        else:
            if updated_text:
                await client.send_message(DESTINATION_CHAT, updated_text)
                print("[SUCCESS] Text message forward ho gaya!")

    except FloodWaitError as fwe:
        print(f"[FLOOD WAIT] Waiting for {fwe.seconds} seconds.")
        await asyncio.sleep(fwe.seconds + 2)
    except Exception as err:
        print(f"[ERROR] Handler issue: {err}")

async def main():
    while True:
        try:
            print(f"[STATUS] Listening for messages from: {SOURCE_CHAT} to {DESTINATION_CHAT}")
            await client.start()
            await client.run_until_disconnected()
        except Exception as crash_err:
            print(f"[CRASH ERROR] {crash_err}")
            await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())
