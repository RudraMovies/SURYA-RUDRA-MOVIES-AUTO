
import asyncio
import json
import logging
import os
import threading
from pathlib import Path

from aiohttp import web
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    PeerIdInvalid,
    ChatWriteForbidden,
    ChatAdminRequired,
    MessageNotModified,
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

from omdb import search_omdb, convert_omdb


# ==========================================
# BOT SETTINGS
# ==========================================

BOT_NAME = "SURYA RUDRA MOVIES"
POWERED_BY = "SURYA"

WELCOME_IMAGE = os.getenv("WELCOME_IMAGE", "").strip()
DATA_FILE = Path("bot_data.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = Client(
    "surya_rudra_movies",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


# ==========================================
# SMALL CAPS
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


def sc(text):
    return str(text).translate(SMALL_CAPS_MAP)


def is_owner(user_id):
    try:
        return bool(OWNER_ID) and int(user_id) == int(OWNER_ID)
    except (TypeError, ValueError):
        return False


# ==========================================
# DATA STORAGE
# ==========================================

def load_state():

    default = {
        "auto_post": True,
        "posted_ids": [],
        "searches": 0,
        "posts": 0,
        "users": []
    }

    try:
        if DATA_FILE.exists():
            saved = json.loads(
                DATA_FILE.read_text(encoding="utf-8")
            )

            if isinstance(saved, dict):
                default.update(saved)

    except Exception:
        logger.exception("DATA LOAD ERROR")

    return default


state = load_state()


def save_state():

    try:
        DATA_FILE.write_text(
            json.dumps(state, indent=2),
            encoding="utf-8"
        )

    except Exception:
        logger.exception("DATA SAVE ERROR")


def remember_user(user_id):

    users = set(state.get("users", []))
    users.add(int(user_id))

    state["users"] = list(users)

    save_state()


# ==========================================
# KEYBOARDS
# ==========================================

def main_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎬 ᴍᴏᴠɪᴇ ꜱᴇᴀʀᴄʜ",
                callback_data="help_movie"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 ꜱᴛᴀᴛꜱ",
                callback_data="public_stats"
            ),
            InlineKeyboardButton(
                "ℹ️ ʜᴇʟᴘ",
                callback_data="help"
            )
        ]
    ])


def admin_keyboard():

    status = (
        "ᴏɴ"
        if state.get("auto_post", True)
        else "ᴏꜰꜰ"
    )

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"📡 ᴀᴜᴛᴏ ᴘᴏꜱᴛ: {status}",
                callback_data="admin_toggle"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 ʙᴏᴛ ꜱᴛᴀᴛꜱ",
                callback_data="admin_stats"
            )
        ],
        [
            InlineKeyboardButton(
                "🔄 ʀᴇꜰʀᴇꜱʜ",
                callback_data="admin_refresh"
            )
        ]
    ])


# ==========================================
# MOVIE CAPTION
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

    rating = (
        details.get("rating")
        or movie.get("rating")
    )

    try:
        rating_text = f"{float(rating):.1f}/10"
    except (TypeError, ValueError):
        rating_text = "N/A"

    imdb_rating = details.get("imdb_rating")

    try:
        imdb_text = (
            f"{float(imdb_rating):.1f}/10"
            if imdb_rating and imdb_rating != "N/A"
            else "N/A"
        )
    except (TypeError, ValueError):
        imdb_text = "N/A"

    genres = details.get("genres") or []

    genre_names = [
        genre.get("name", "")
        for genre in genres
        if isinstance(genre, dict) and genre.get("name")
    ]

    genre_text = (
        ", ".join(genre_names)
        if genre_names
        else "N/A"
    )

    language = (
        details.get("language")
        or movie.get("language")
        or "N/A"
    )

    language = language.upper()

    director_text = (
        ", ".join(directors)
        if directors
        else "N/A"
    )

    runtime = details.get("runtime")

    runtime_text = (
        f"{runtime} MIN"
        if runtime
        else "N/A"
    )

    caption = (
        "🎬 RM MOVIES • EXCLUSIVE MOVIE DROP 🍿\n\n"
        f"🎥 TITLE : {title} ({year})\n"
        f"⭐ TMDB RATING : {rating_text}\n"
        f"🌟 IMDb RATING : {imdb_text}\n"
        f"🎭 GENRES : {genre_text}\n"
        f"🌐 LANGUAGE : {language}\n"
        f"📅 RELEASE : {year}\n"
        f"🎬 DIRECTOR : {director_text}\n"
        f"⏳ RUNTIME : {runtime_text}\n\n"
        f"👑 POWERED BY {POWERED_BY}"
    )

    return sc(caption)


# ==========================================
# CHANNEL RESOLUTION
# ==========================================

async def get_target_chat(client):

    if not CHANNEL_ID:
        return None

    channel = str(CHANNEL_ID).strip()

    if channel.lstrip("-").isdigit():

        wanted = int(channel)

        async for dialog in client.get_dialogs():

            if dialog.chat.id == wanted:
                return dialog.chat.id

        chat = await client.get_chat(wanted)

    else:
        chat = await client.get_chat(channel)

    return chat.id


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

    logger.info("HEALTH SERVER RUNNING")

    while True:
        await asyncio.sleep(3600)


def start_health():

    thread = threading.Thread(
        target=lambda: asyncio.run(start_health_server()),
        daemon=True
    )

    thread.start()


# ==========================================
# WELCOME
# ==========================================

async def send_welcome(message):

    welcome_text = (
        "👑 " + sc("WELCOME TO SURYA RUDRA MOVIES") + "\n\n"
        "🎬 " + sc("YOUR MOVIE SEARCH EXPERIENCE STARTS HERE") + "\n"
        "🔎 " + sc("SEND A MOVIE NAME TO SEARCH") + "\n\n"
        "✨ " + sc("FAST • SIMPLE • PREMIUM") + "\n"
        "👑 " + sc("POWERED BY SURYA")
    )

    if WELCOME_IMAGE:

        await message.reply_photo(
            photo=WELCOME_IMAGE,
            caption=welcome_text,
            reply_markup=main_keyboard(),
            parse_mode=ParseMode.DISABLED
        )

    else:

        await message.reply_text(
            welcome_text,
            reply_markup=main_keyboard(),
            parse_mode=ParseMode.DISABLED
        )


@app.on_message(
    filters.command("start") & filters.private
)
async def start_command(client, message):

    remember_user(message.from_user.id)

    await send_welcome(message)


# ==========================================
# MOVIE SEARCH ENGINE
# ==========================================

async def perform_movie_search(client, message, movie_name):

    status = await message.reply_text(
        sc("⏳ SEARCHING TMDB...")
    )

    try:

        movie = None
        details = None
        directors = []
        image_url = None

        # FIRST: TMDB

        try:

            movie = await search_movie(movie_name)

            if movie:

                movie_id = movie.get("id")

                if movie_id:

                    details = await get_movie_details(movie_id)

                    if details:

                        directors = await get_movie_director(movie_id)

                        image_url = (
                            get_movie_image_url(details)
                            or get_movie_image_url(movie)
                        )

        except Exception:

            logger.exception("TMDB SEARCH ERROR")

        # BACKUP: OMDB

        omdb_result = None

        if not details or not image_url:

            await status.edit_text(
                sc("⏳ TRYING OMDB BACKUP SEARCH...")
            )

            try:

                omdb_result = await search_omdb(movie_name)

            except Exception:

                logger.exception("OMDB SEARCH ERROR")

            if omdb_result:

                omdb_details = convert_omdb(omdb_result)

                if omdb_details:

                    if not details:

                        details = omdb_details

                        movie = {
                            "title": omdb_details.get("title"),
                            "rating": omdb_details.get("rating"),
                            "release_date": omdb_details.get("release_date"),
                            "language": omdb_details.get("language")
                        }

                        directors = (
                            [omdb_details["director"]]
                            if omdb_details.get("director")
                            and omdb_details["director"] != "N/A"
                            else []
                        )

                    # Use OMDb poster if TMDB image unavailable

                    if not image_url:

                        image_url = omdb_details.get("poster")

                    # Keep IMDb rating separate from TMDB rating

                    if details:

                        details["imdb_rating"] = omdb_details.get("rating")

                        if not details.get("imdb_id"):
                            details["imdb_id"] = omdb_details.get("imdb_id")

        if not details:

            await status.edit_text(
                sc("❌ MOVIE NOT FOUND IN TMDB OR OMDB.")
            )
            return

        if not image_url or image_url == "N/A":

            await status.edit_text(
                sc("❌ MOVIE IMAGE NOT AVAILABLE.")
            )
            return

        remember_user(message.from_user.id)

        state["searches"] = int(state.get("searches", 0)) + 1

        movie_key = str(
            details.get("imdb_id")
            or (movie or {}).get("id")
            or details.get("title", "").lower()
        )

        caption = build_caption(
            movie or {},
            details,
            directors
        )

        if len(caption) > 1000:
            caption = caption[:990] + "..."

        # AUTO POST ON

        if state.get("auto_post", True):

            if movie_key in set(state.get("posted_ids", [])):

                await status.edit_text(
                    sc("ℹ️ THIS MOVIE WAS ALREADY POSTED.")
                )
                return

            target_chat = await get_target_chat(client)

            if target_chat is None:
                target_chat = message.chat.id

            await client.send_photo(
                chat_id=target_chat,
                photo=image_url,
                caption=caption,
                parse_mode=ParseMode.DISABLED
            )

            posted = set(state.get("posted_ids", []))
            posted.add(movie_key)

            state["posted_ids"] = list(posted)

            state["posts"] = int(state.get("posts", 0)) + 1

            save_state()

            await status.edit_text(
                sc("✅ MOVIE POSTED SUCCESSFULLY.")
            )

            logger.info(
                "MOVIE POSTED: %s",
                details.get("title")
            )

        # AUTO POST OFF

        else:

            await client.send_photo(
                chat_id=message.chat.id,
                photo=image_url,
                caption=caption,
                parse_mode=ParseMode.DISABLED
            )

            await status.edit_text(
                sc("✅ MOVIE DETAILS SENT. AUTO POST IS OFF.")
            )

    except PeerIdInvalid:

        logger.exception("INVALID CHANNEL PEER")

        await status.edit_text(
            sc("❌ CHANNEL ACCESS ERROR. CHECK CHANNEL ID.")
        )

    except ChatWriteForbidden:

        logger.exception("CHANNEL WRITE FORBIDDEN")

        await status.edit_text(
            sc("❌ BOT CANNOT POST. GIVE POST MESSAGES PERMISSION.")
        )

    except ChatAdminRequired:

        logger.exception("BOT ADMIN REQUIRED")

        await status.edit_text(
            sc("❌ BOT ADMIN PERMISSION REQUIRED.")
        )

    except Exception:

        logger.exception("MOVIE SEARCH FAILED")

        await status.edit_text(
            sc("❌ MOVIE SEARCH FAILED. CHECK RENDER LOGS.")
        )


# ==========================================
# MOVIE COMMAND
# ==========================================

@app.on_message(
    filters.command("movie") & filters.private
)
async def movie_command(client, message):

    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:

        await message.reply_text(
            sc("USAGE: /movie MOVIE NAME")
        )
        return

    await perform_movie_search(
        client,
        message,
        parts[1].strip()
    )


# ==========================================
# NORMAL TEXT SEARCH
# ==========================================

@app.on_message(
    filters.private
    & filters.text
    & ~filters.command([
        "start",
        "movie",
        "help",
        "stats",
        "admin",
        "about"
    ])
)
async def text_movie_search(client, message):

    movie_name = (message.text or "").strip()

    if movie_name:

        await perform_movie_search(
            client,
            message,
            movie_name
        )


# ==========================================
# HELP
# ==========================================

@app.on_message(
    filters.command("help") & filters.private
)
async def help_command(client, message):

    help_text = (
        "📚 " + sc("HELP MENU") + "\n\n"
        "🔎 /movie NAME - " + sc("SEARCH A MOVIE") + "\n"
        "📊 /stats - " + sc("BOT STATISTICS") + "\n"
        "👑 /admin - " + sc("OWNER ADMIN PANEL") + "\n"
        "ℹ️ /about - " + sc("ABOUT THIS BOT") + "\n"
        "📖 /help - " + sc("SHOW HELP MENU") + "\n\n"
        + sc("OR SIMPLY SEND A MOVIE NAME.")
    )

    await message.reply_text(
        help_text,
        reply_markup=main_keyboard(),
        parse_mode=ParseMode.DISABLED
    )


# ==========================================
# ABOUT / ATTRIBUTION
# ==========================================

@app.on_message(
    filters.command("about") & filters.private
)
async def about_command(client, message):

    about_text = (
        "👑 " + sc("SURYA RUDRA MOVIES") + "\n\n"
        + sc("MOVIE INFORMATION POWERED BY TMDB AND OMDB.") + "\n\n"
        + sc("THIS PRODUCT USES THE TMDB API BUT IS NOT ENDORSED OR CERTIFIED BY TMDB.") + "\n\n"
        + sc("POWERED BY SURYA")
    )

    await message.reply_text(
        about_text,
        parse_mode=ParseMode.DISABLED
    )


# ==========================================
# STATISTICS
# ==========================================

def build_stats():

    return (
        "📊 " + sc("BOT STATISTICS") + "\n\n"
        f"👥 {sc('USERS')}: {len(state.get('users', []))}\n"
        f"🔎 {sc('SEARCHES')}: {state.get('searches', 0)}\n"
        f"🎬 {sc('CHANNEL POSTS')}: {state.get('posts', 0)}"
    )


@app.on_message(
    filters.command("stats") & filters.private
)
async def stats_command(client, message):

    await message.reply_text(
        build_stats(),
        parse_mode=ParseMode.DISABLED
    )


# ==========================================
# ADMIN PANEL
# ==========================================

@app.on_message(
    filters.command("admin") & filters.private
)
async def admin_command(client, message):

    if not is_owner(message.from_user.id):

        await message.reply_text(
            sc("⛔ OWNER ONLY COMMAND.")
        )
        return

    await message.reply_text(
        "👑 " + sc("SURYA ADMIN PANEL"),
        reply_markup=admin_keyboard(),
        parse_mode=ParseMode.DISABLED
    )


# ==========================================
# CALLBACK HANDLER
# ==========================================

@app.on_callback_query()
async def callback_handler(client, query):

    data = query.data or ""
    user_id = query.from_user.id

    if data == "help_movie":

        await query.answer(
            "SEND A MOVIE NAME OR USE /movie NAME",
            show_alert=True
        )
        return

    if data == "help":

        await query.answer()

        await query.message.reply_text(
            sc("SEND A MOVIE NAME OR USE /movie NAME.")
        )
        return

    if data == "public_stats":

        await query.answer()

        await query.message.reply_text(
            build_stats(),
            parse_mode=ParseMode.DISABLED
        )
        return

    # ADMIN SECURITY

    if data.startswith("admin_") and not is_owner(user_id):

        await query.answer(
            "OWNER ONLY",
            show_alert=True
        )
        return

    # AUTO POST TOGGLE

    if data == "admin_toggle":

        state["auto_post"] = not bool(
            state.get("auto_post", True)
        )

        save_state()

        await query.answer("AUTO POST UPDATED")

        try:

            await query.message.edit_reply_markup(
                reply_markup=admin_keyboard()
            )

        except MessageNotModified:
            pass

        return

    # ADMIN STATS

    if data == "admin_stats":

        await query.answer()

        admin_stats = (
            "📊 " + sc("ADMIN STATISTICS") + "\n\n"
            f"👥 {sc('USERS')}: {len(state.get('users', []))}\n"
            f"🔎 {sc('SEARCHES')}: {state.get('searches', 0)}\n"
            f"🎬 {sc('POSTS')}: {state.get('posts', 0)}\n"
            f"📡 {sc('AUTO POST')}: "
            f"{sc('ON' if state.get('auto_post', True) else 'OFF')}\n"
            f"🧾 {sc('UNIQUE MOVIES')}: "
            f"{len(state.get('posted_ids', []))}"
        )

        await query.message.reply_text(
            admin_stats,
            parse_mode=ParseMode.DISABLED
        )

        return

    # REFRESH

    if data == "admin_refresh":

        await query.answer("PANEL REFRESHED")

        try:

            await query.message.edit_reply_markup(
                reply_markup=admin_keyboard()
            )

        except MessageNotModified:
            pass

        return


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    logger.info("%s STARTING", BOT_NAME)

    start_health()

    app.run()
