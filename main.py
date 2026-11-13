
import os
import asyncio
import logging
import threading

from aiohttp import web
from pyrogram import Client, filters
from dotenv import load_dotenv

# =====================================
# SURYA RUDRA MOVIES AUTO BOT
# =====================================

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

CHANNEL_ID = os.getenv("CHANNEL_ID")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

PMDB_API_KEY = os.getenv("PMDB_API_KEY")

PORT = int(os.getenv("PORT", "10000"))


# =====================================
# CREDENTIAL VALIDATION
# =====================================

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise RuntimeError(
        "Missing API_ID, API_HASH or BOT_TOKEN"
    )


# =====================================
# PYROGRAM CLIENT
# =====================================

app = Client(
    "surya_rudra_movies",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


# =====================================
# SMALL CAPS FORMATTER
# =====================================

def small_caps(text):

    normal = "abcdefghijklmnopqrstuvwxyz"
    small = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"

    return str(text).translate(
        str.maketrans(normal, small)
    )


# =====================================
# HTTP HEALTH SERVER
# =====================================

async def health(request):

    return web.json_response({
        "status": "online",
        "bot": "SURYA RUDRA MOVIES",
        "health": "OK"
    })


async def start_health_server():

    web_app = web.Application()

    web_app.router.add_get("/", health)
    web_app.router.add_get("/health", health)

    runner = web.AppRunner(web_app)

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        PORT
    )

    await site.start()

    logger.info(
        f"HTTP HEALTH SERVER RUNNING ON PORT {PORT}"
    )

    return runner


async def health_server_loop():

    runner = await start_health_server()

    try:
        await asyncio.Event().wait()

    finally:
        await runner.cleanup()


def run_health_server():

    asyncio.run(health_server_loop())


def start_health_thread():

    thread = threading.Thread(
        target=run_health_server,
        daemon=True
    )

    thread.start()


# =====================================
# START COMMAND
# =====================================

@app.on_message(
    filters.private & filters.command("start")
)
async def start_command(client, message):

    text = """
👑 ꜱᴜʀʏᴀ ʀᴜᴅʀᴀ ᴍᴏᴠɪᴇꜱ

🎬 ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴏᴜʀ ᴀᴜᴛᴏ ᴍᴏᴠɪᴇ ʙᴏᴛ!

🔎 ꜱᴇɴᴅ ᴀ ᴍᴏᴠɪᴇ ɴᴀᴍᴇ ᴛᴏ ꜱᴛᴀʀᴛ.

👑 ᴘᴏᴡᴇʀᴇᴅ ʙʏ ꜱᴜʀʏᴀ
"""

    await message.reply_text(text)


# =====================================
# MOVIE SEARCH HANDLER
# =====================================

@app.on_message(
    filters.private &
    filters.text &
    ~filters.command("start")
)
async def movie_search(client, message):

    if not message.from_user:
        return

    if OWNER_ID and message.from_user.id != OWNER_ID:

        await message.reply_text(
            "⛔ ᴀᴄᴄᴇꜱꜱ ᴅᴇɴɪᴇᴅ."
        )

        return

    movie_name = message.text.strip()

    if not movie_name:
        return

    await message.reply_text(
        f"🔎 ᴍᴏᴠɪᴇ ꜱᴇᴀʀᴄʜ: {small_caps(movie_name)}\n\n"
        "⏳ ᴍᴏᴠɪᴇ ᴅᴀᴛᴀ ɪɴᴛᴇɢʀᴀᴛɪᴏɴ ɪꜱ ᴘᴇɴᴅɪɴɢ."
    )

    logger.info(
        f"Movie search requested: {movie_name}"
    )


# =====================================
# BOT STARTUP
# =====================================

if __name__ == "__main__":

    logger.info(
        "SURYA RUDRA MOVIES BOT STARTING..."
    )

    start_health_thread()

    app.run()
