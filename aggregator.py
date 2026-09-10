import os
import logging
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, filters, idle
from pyrogram.types import Message

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Завантаження змінних із .env
load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL", "metaaggregator").strip()
DONOR_CHANNELS = [x.strip() for x in os.getenv("DONOR_CHANNELS", "cryptosadua,tropimoney,teamcryptoua,soyercrypto,newgramua,fwfewffw").split(",") if x.strip()]

app = Client(
    "meta_aggregator_session",
    api_id=API_ID,
    api_hash=API_HASH
)

@app.on_message(filters.channel)
async def handle_new_post(client: Client, message: Message):
    # Перевіряємо, чи належить пост до відстежуваних донорів
    if not hasattr(client, "donor_ids") or message.chat.id not in client.donor_ids:
        return

    try:
        # Нативна пересилка (репост із збереженням плашки джерела)
        await client.forward_messages(
            chat_id=client.target_chat_id,
            from_chat_id=message.chat.id,
            message_ids=message.id
        )
        logging.info(f"🔄 Пост успішно репостнуто з [{message.chat.title}] -> [{TARGET_CHANNEL}]")
    except Exception as e:
        logging.error(f"❌ Помилка при пересиланні з {message.chat.title} ({message.chat.id}): {e}")

async def main():
    await app.start()
    logging.info("🚀 Aggregator v7.0 Pro успішно ініціалізовано!")

    # Резолвимо та кешуємо канали-донори (усуває Peer id invalid)
    resolved_donors = []
    for username in DONOR_CHANNELS:
        try:
            chat = await app.get_chat(username)
            resolved_donors.append(chat.id)
            logging.info(f"✅ Донор підключений: {chat.title} (ID: {chat.id})")
        except Exception as e:
            logging.error(f"❌ Не вдалося підключити донора {username}: {e}")

    app.donor_ids = resolved_donors

    # Кешуємо цільовий канал
    try:
        target_chat = await app.get_chat(TARGET_CHANNEL)
        app.target_chat_id = target_chat.id
        logging.info(f"🎯 Цільовий канал підключений: {target_chat.title} (ID: {target_chat.id})")
    except Exception as e:
        logging.error(f"❌ Не вдалося підключити цільовий канал {TARGET_CHANNEL}: {e}")

    logging.info("🛰️ Бот активний та відстежує нові пости...")
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())