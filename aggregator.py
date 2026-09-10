import asyncio
import os
import logging
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import Message
import aiosqlite

# Виправлення для сумісності asyncio з новими версіями Python
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

load_dotenv()

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL", "metaaggregator")
DONOR_CHANNELS_RAW = os.getenv("DONOR_CHANNELS", "")

DONOR_CHANNELS = [ch.strip() for ch in DONOR_CHANNELS_RAW.split(",") if ch.strip()]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Client("meta_aggregator_session", api_id=API_ID, api_hash=API_HASH)

DB_FILE = "aggregator_db.sqlite"

async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS resolved_chats (
                username TEXT PRIMARY KEY,
                chat_id INTEGER
            )
        """)
        await db.commit()

async def get_cached_chat_id(client, username):
    clean_username = username.lstrip("@")
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT chat_id FROM resolved_chats WHERE username = ?", (clean_username,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
    
    try:
        chat = await client.get_chat(clean_username)
        chat_id = chat.id
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("INSERT OR REPLACE INTO resolved_chats (username, chat_id) VALUES (?, ?)", (clean_username, chat_id))
            await db.commit()
        logging.info(f"Отримано та збережено ID для @{clean_username}: {chat_id}")
        return chat_id
    except Exception as e:
        logging.error(f"Помилка при отриманні ID для @{clean_username}: {e}")
        return None

donor_chat_ids = []

@app.on_message(filters.chat(donor_chat_ids) & (filters.text | filters.photo | filters.video | filters.document))
async def forward_handler(client: Client, message: Message):
    try:
        target_id = await get_cached_chat_id(client, TARGET_CHANNEL)
        if not target_id:
            logging.error(f"Не вдалося знайти ID цільового каналу: {TARGET_CHANNEL}")
            return
        
        await message.forward(target_id)
        logging.info(f"Успішно переслано пост з каналу {message.chat.title or message.chat.id}")
    except Exception as e:
        logging.error(f"Помилка пересилання повідомлення: {e}")

async def main():
    global donor_chat_ids
    await init_db()
    async with app:
        logging.info("🚀 Запуск агрегатора...")
        
        target_id = await get_cached_chat_id(app, TARGET_CHANNEL)
        if target_id:
            logging.info(f"🎯 Цільовий канал підключено: {TARGET_CHANNEL} (ID: {target_id})")
        else:
            logging.warning(f"⚠️ Увага: Не вдалося знайти цільовий канал {TARGET_CHANNEL}")

        for donor in DONOR_CHANNELS:
            cid = await get_cached_chat_id(app, donor)
            if cid:
                donor_chat_ids.append(cid)
                logging.info(f"✅ Донор підключено: @{donor} (ID: {cid})")
            else:
                logging.warning(f"⚠️ Не вдалося підключити донора: @{donor}")

        if not donor_chat_ids:
            logging.error("❌ Жодного донора не підключено! Перевірте налаштування DONOR_CHANNELS.")
            return

        logging.info(f"🛰️ Бот успішно запущений і слухає {len(donor_chat_ids)} донорів 24/7...")
        
        # Тримаємо клієнта активним
        await asyncio.Future()

if __name__ == "__main__":
    app.run(main())
