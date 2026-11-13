
import os
import asyncio
import logging
import threading

from aiohttp import web
from pyrogram import Client, filters
from dotenv import load_dotenv

from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    CHANNEL_ID,
    OWNER_ID
)

from tmdb import (
    search_movie,
    get_movie_details,
    get_movie_cast,
    get_movie_director,
    get_poster_url
)

from formatter import (
    create_caption,
    create_cast_message
)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", "10000"))

app = Client(
    "surya_rudra_movies",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
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

    logger.info("Health server running on port %s", PORT)

    return runner


async def health_loop():
    runner = await start_health_server()

    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


def run_health_server():
    asyncio.run(health_loop())


def start_health_thread():
    threading.Thread(
        target=run_health_server,
        daemon=True
    ).start()


# =====================================
# START COMMAND
# =====================================

@app.on_message(
    filters.private & filters.command("start")
)
async def start_command(client, message):

    await message.reply_text(
        "👑 ꜱᴜʀʏᴀ ʀᴜᴅʀᴀ ᴍᴏᴠɪᴇꜱ\n\n"
        "🎬 ᴡᴇʟᴄᴏᴍᴇ!\n\n"
        "🔎 ꜱᴇɴᴅ ᴀ ᴍᴏᴠɪᴇ ɴᴀᴍᴇ."
    )


# =====================================
# MOVIE SEARCH
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

    status = await message.reply_text(
        "🔎 ᴍᴏᴠɪᴇ ꜱᴇᴀʀᴄʜɪɴɢ..."
    )

    try:
        movie = await search_movie(movie_name)

        if not movie:
            await status.edit_text(
                "❌ ᴍᴏᴠɪᴇ ɴᴏᴛ ꜰᴏᴜɴᴅ."
            )
            return

        movie_id = movie.get("id")

        details = await get_movie_details(movie_id)

        if not details:
            await status.edit_text(
                "❌ ᴍᴏᴠɪᴇ ᴅᴇᴛᴀɪʟꜱ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ."
            )
            return

        cast = await get_movie_cast(movie_id)

        directors = await get_movie_director(movie_id)

        caption = create_caption(
            movie,
            details,
            directors
        )

        cast_text = create_cast_message(cast)

        poster = get_poster_url(
            details.get("poster")
        )

        if not CHANNEL_ID:
            await status.edit_text(
                "❌ ᴄʜᴀɴɴᴇʟ ɪᴅ ɴᴏᴛ ꜱᴇᴛ."
            )
            return

        if poster:
            await client.send_photo(
                chat_id=CHANNEL_ID,
                photo=poster,
                caption=caption
            )
        else:
            await client.send_message(
                chat_id=CHANNEL_ID,
                text=caption
            )

        # Send full cast separately
        await client.send_message(
            chat_id=CHANNEL_ID,
            text=cast_text
        )

        await status.edit_text(
            "✅ ᴍᴏᴠɪᴇ ᴘᴏꜱᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!"
        )

    except Exception:
        logger.exception("Movie posting failed")

        await status.edit_text(
            "❌ ᴍᴏᴠɪᴇ ᴘᴏꜱᴛɪɴɢ ꜰᴀɪʟᴇᴅ. ᴄʜᴇᴄᴋ ʟᴏɢꜱ."
        )


# =====================================
# START BOT
# =====================================

if __name__ == "__main__":

    logger.info("SURYA RUDRA MOVIES STARTING")

    start_health_thread()

    app.run()
