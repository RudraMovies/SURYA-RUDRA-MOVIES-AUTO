
import asyncio
import logging
import threading
import os
import html

from aiohttp import web
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.errors import (
    PeerIdInvalid,
    ChatWriteForbidden,
    ChatAdminRequired
)

from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    CHANNEL_ID,
    OWNER_ID,
    PORT
)

from tmdb import (
    search_movie,
    get_movie_details,
    get_movie_director,
    get_movie_image_url
)


# ==========================================
# LOGGING
# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ==========================================
# BOT SETTINGS
# ==========================================

BOT_NAME = "SURYA RUDRA MOVIES"
POWERED_BY = "@RudraMoviez"

app = Client(
    "surya_rudra_movies",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


# ==========================================
# SMALL CAPS CONVERTER
# ==========================================

SMALL_CAPS_MAP = str.maketrans({
    "a": "ᴀ", "b": "ʙ", "c": "ᴄ",
    "d": "ᴅ", "e": "ᴇ", "f": "ꜰ",
    "g": "ɢ", "h": "ʜ", "i": "ɪ",
    "j": "ᴊ", "k": "ᴋ", "l": "ʟ",
    "m": "ᴍ", "n": "ɴ", "o": "ᴏ",
    "p": "ᴘ", "q": "ǫ", "r": "ʀ",
    "s": "ꜱ", "t": "ᴛ", "u": "ᴜ",
    "v": "ᴠ", "w": "ᴡ", "x": "x",
    "y": "ʏ", "z": "ᴢ"
})


def small_caps(text):
    return str(text).translate(SMALL_CAPS_MAP)


# ==========================================
# CAPTION FORMATTER
# ==========================================

def build_caption(movie, details, directors):

    title = (
        details.get("title")
        or movie.get("title")
        or "UNKNOWN"
    )

    release_date = (
        details.get("release_date")
        or movie.get("release_date")
        or ""
    )

    year = (
        release_date[:4]
        if len(release_date) >= 4
        else "N/A"
    )

    rating = details.get("rating")

    if rating is None:
        rating = movie.get("rating")

    try:
        rating_text = f"{float(rating):.1f}/10"
    except (TypeError, ValueError):
        rating_text = "N/A"

    genres = details.get("genres") or []

    genre_names = [
        genre.get("name", "")
        for genre in genres
        if genre.get("name")
    ]

    genre_text = (
        ", ".join(genre_names)
        if genre_names else "N/A"
    )

    language = (
        details.get("language")
        or movie.get("language")
        or "N/A"
    )

    language = language.upper()

    director_text = (
        ", ".join(directors)
        if directors else "N/A"
    )

    runtime = details.get("runtime")

    if runtime:
        runtime_text = f"{runtime} MIN"
    else:
        runtime_text = "N/A"

    caption = (
        "🎬 RM MOVIES • EXCLUSIVE MOVIE DROP 🍿\n\n"

        f"🎥 TITLE : {title} ({year})\n"

        f"⭐ RATING : {rating_text}\n"

        f"🎭 GENRES : {genre_text}\n"

        f"🌐 LANGUAGE : {language}\n"

        f"📅 RELEASE : {year}\n"

        f"🎬 DIRECTOR : {director_text}\n"

        f"⏳ RUNTIME : {runtime_text}\n\n"

        "👑 POWERED BY "
    )

    # Convert caption text to small caps.
    # Keep username in normal ASCII.
    caption = small_caps(caption)

    caption += POWERED_BY

    return caption


# ==========================================
# RESOLVE CHANNEL
# ==========================================

async def get_target_chat(client):

    if not CHANNEL_ID:
        return None

    channel = str(CHANNEL_ID).strip()

    try:
        if channel.lstrip("-").isdigit():
            chat = await client.get_chat(int(channel))
        else:
            chat = await client.get_chat(channel)

        return chat.id

    except Exception:
        logger.exception("CHANNEL RESOLUTION FAILED")
        raise


# ==========================================
# HEALTH SERVER
# ==========================================

async def health(request):

    return web.json_response({
        "status": "online",
        "bot": BOT_NAME
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
        int(PORT or 10000)
    )

    await site.start()

    logger.info(
        "HEALTH SERVER RUNNING ON PORT %s",
        PORT or 10000
    )

    while True:
        await asyncio.sleep(3600)


def health_thread():

    asyncio.run(start_health_server())


def start_health():

    thread = threading.Thread(
        target=health_thread,
        daemon=True
    )

    thread.start()


# ==========================================
# START COMMAND
# ==========================================

@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):

    await message.reply_text(
        "👑 SURYA RUDRA MOVIES\n\n"
        "🎬 WELCOME!\n\n"
        "🔎 SEND A MOVIE NAME."
    )


# ==========================================
# MOVIE SEARCH HANDLER
# ==========================================

@app.on_message(
    filters.private
    & filters.text
    & ~filters.command(["start"])
)
async def movie_search(client, message):

    user_id = message.from_user.id

    # Optional owner restriction
    if OWNER_ID and user_id != int(OWNER_ID):
        await message.reply_text(
            "⛔ YOU ARE NOT AUTHORIZED."
        )
        return

    movie_name = message.text.strip()

    if not movie_name:
        return

    status = await message.reply_text(
        "⏳ SEARCHING MOVIE DETAILS..."
    )

    try:

        # Search TMDB
        movie = await search_movie(movie_name)

        if not movie:
            await status.edit_text(
                "❌ MOVIE NOT FOUND. TRY ANOTHER NAME."
            )
            return

        movie_id = movie.get("id")

        if not movie_id:
            await status.edit_text(
                "❌ MOVIE ID NOT FOUND."
            )
            return

        # Fetch details
        details = await get_movie_details(movie_id)

        if not details:
            await status.edit_text(
                "❌ MOVIE DETAILS NOT AVAILABLE."
            )
            return

        # Director only. No cast.
        directors = await get_movie_director(movie_id)

        # Get landscape backdrop first.
        image_url = get_movie_image_url(details)

        # Fallback to search result image.
        if not image_url:
            image_url = get_movie_image_url(movie)

        if not image_url:
            await status.edit_text(
                "❌ MOVIE IMAGE NOT AVAILABLE."
            )
            return

        # Build caption
        caption = build_caption(
            movie,
            details,
            directors
        )

        # Telegram photo caption limit is 1024 characters.
        if len(caption) > 1000:
            caption = caption[:990] + "..."

        # Resolve destination
        target_chat = await get_target_chat(client)

        if target_chat is None:
            target_chat = message.chat.id

        # ONE PHOTO + ONE CAPTION.
        # Photo appears ABOVE the caption.
        await client.send_photo(
            chat_id=target_chat,
            photo=image_url,
            caption=caption,
            parse_mode=ParseMode.DISABLED
        )

        await status.edit_text(
            "✅ MOVIE POSTED SUCCESSFULLY."
        )

        logger.info(
            "MOVIE POSTED: %s",
            details.get("title")
        )

    except PeerIdInvalid:

        logger.exception("INVALID CHANNEL PEER")

        await status.edit_text(
            "❌ CHANNEL ACCESS ERROR.\n\n"
            "ADD THE BOT AS CHANNEL ADMIN "
            "AND CHECK CHANNEL ID."
        )

    except ChatWriteForbidden:

        logger.exception("CHANNEL WRITE FORBIDDEN")

        await status.edit_text(
            "❌ BOT CANNOT POST IN THIS CHANNEL.\n"
            "GIVE THE BOT POST MESSAGES PERMISSION."
        )

    except ChatAdminRequired:

        logger.exception("BOT ADMIN REQUIRED")

        await status.edit_text(
            "❌ MAKE THE BOT AN ADMIN "
            "WITH POST MESSAGES PERMISSION."
        )

    except Exception:

        logger.exception("MOVIE POSTING FAILED")

        await status.edit_text(
            "❌ MOVIE POSTING FAILED. CHECK RENDER LOGS."
        )


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    logger.info("%s STARTING", BOT_NAME)

    start_health()

    app.run()
