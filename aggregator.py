import os
import asyncio
import logging
from aiohttp import web
from pyrogram import Client, filters
import aiosqlite

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Читання змінних середовища
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_NAME = os.getenv("SESSION_NAME", "aggregator_session")

# Ініціалізація Pyrogram клієнта
app = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH)

# --- МІНІ-ВЕБСЕРВЕР ДЛЯ RENDER (Щоб бот не засинав і тримав порт) ---
async def handle_ping(request):
    return web.Response(text="Bot is running 24/7!")

web_app = web.Application()
web_app.router.add_get("/", handle_ping)

async def start_web_server():
    runner = web.AppRunner(web_app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"🌐 Вебсервер запущено на порті {port}")

# --- ЛОГІКА АГРЕГАТОРА ---
@app.on_message(filters.channel)
async def handle_channel_posts(client, message):
    # Тут ваша логіка обробки та пересилання повідомлень
    pass

async def main():
    # 1. Запускаємо вебсервер для Render
    await start_web_server()
    
    # 2. Запускаємо Pyrogram клієнт
    await app.start()
    logging.info("🛰️ Бот успішно запущений і працює 24/7 у хмарі...")
    
    # Утримуємо роботу програми
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот зупинений користувачем.")
