
import asyncio
import json
import logging
import os
from pathlib import Path

import aiohttp
from aiohttp import web

from pyrogram import Client, filters, idle

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
# SURYA RUDRA MOVIES SETTINGS
# ==========================================

BOT_NAME = "SURYA RUDRA MOVIES"
POWERED_BY = "POWERED BY SURYA"

WELCOME_IMAGE = os.getenv("WELCOME_IMAGE", "").strip()

DATA_FILE = Path("bot_data.json")


# ==========================================
# LOGGING
# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ==========================================
# PYROGRAM CLIENT
# ==========================================

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


# ==========================================
# DATA STORAGE
# ==========================================

def load_data():

    default = {
        "total_searches": 0,
        "total_posts": 0,
        "auto_post": True,
        "posted_movies": []
    }

    if DATA_FILE.exists():

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                saved = json.load(file)

            default.update(saved)

        except Exception as error:
            logger.error("DATA LOAD ERROR: %s", error)

    return default


data = load_data()


def save_data():

    try:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    except Exception as error:
        logger.error("DATA SAVE ERROR: %s", error)


def is_owner(user_id):

    try:
        return int(user_id) == int(OWNER_ID)

    except Exception:
        return False


# ==========================================
# VALUE HELPER
# ==========================================

def get_value(item, *keys, default="N/A"):

    if not isinstance(item, dict):
        return default

    for key in keys:

        value = item.get(key)

        if value not in (None, "", "N/A"):
            return value

    return default


# ==========================================
# TELEGRAM CHANNEL POSTING
# ==========================================

async def send_channel_post(caption, photo=None):

    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"

    if photo:

        url = f"{base_url}/sendPhoto"

        payload = {
            "chat_id": str(CHANNEL_ID),
            "photo": photo,
            "caption": caption
        }

    else:

        url = f"{base_url}/sendMessage"

        payload = {
            "chat_id": str(CHANNEL_ID),
            "text": caption
        }

    timeout = aiohttp.ClientTimeout(total=45)

    async with aiohttp.ClientSession(timeout=timeout) as session:

        async with session.post(url, json=payload) as response:

            result = await response.json()

            if not result.get("ok"):

                logger.error(
                    "CHANNEL POST FAILED: %s",
                    result
                )

                raise RuntimeError(
                    result.get("description", "Telegram API error")
                )

            return result


# ==========================================
# TMDB + OMDB MOVIE INFORMATION
# ==========================================

async def get_movie_information(movie_name):

    movie = None
    details = None

    imdb_rating = "N/A"
    imdb_id = "N/A"

    # TMDB SEARCH
    try:

        results = await search_movie(movie_name)

        if results:

            movie = results[0] if isinstance(results, list) else results

            movie_id = get_value(
                movie,
                "id",
                "movie_id",
                default=None
            )

            if movie_id:

                details = await get_movie_details(movie_id)

            if not details:
                details = movie

    except Exception as error:

        logger.exception("TMDB SEARCH ERROR: %s", error)

    # OMDB SEARCH
    try:

        omdb_result = await search_omdb(movie_name)

        if omdb_result:

            omdb_details = convert_omdb(omdb_result)

            if omdb_details:

                imdb_rating = get_value(
                    omdb_details,
                    "rating",
                    "imdb_rating"
                )

                imdb_id = get_value(
                    omdb_details,
                    "imdb_id"
                )

                if not details:

                    details = omdb_details
                    movie = omdb_details

    except Exception as error:

        logger.exception("OMDB SEARCH ERROR: %s", error)

    if not details:
        return None

    # POSTER
    poster = None

    try:

        poster = get_movie_image_url(details)

    except Exception as error:

        logger.warning("POSTER ERROR: %s", error)

    if not poster:

        poster = get_value(
            details,
            "poster",
            "poster_url",
            default=None
        )

    # DIRECTOR
    director = "N/A"

    try:

        movie_id = get_value(
            movie,
            "id",
            "movie_id",
            default=None
        )

        if movie_id:

            director = await get_movie_director(movie_id)

    except Exception as error:

        logger.warning("DIRECTOR ERROR: %s", error)

    if isinstance(director, dict):

        director = get_value(
            director,
            "name"
        )

    return {
        "title": get_value(
            details,
            "title",
            "name"
        ),

        "release": get_value(
            details,
            "release_date",
            "year"
        ),

        "rating": get_value(
            details,
            "vote_average",
            "rating"
        ),

        "imdb_rating": imdb_rating,

        "imdb_id": imdb_id,

        "genres": get_value(
            details,
            "genres"
        ),

        "language": get_value(
            details,
            "original_language",
            "language"
        ),

        "runtime": get_value(
            details,
            "runtime",
            "duration"
        ),

        "director": director,

        "poster": poster
    }


# ==========================================
# MOVIE CAPTION
# ==========================================

def build_caption(movie):

    return (
        f"🎬 {sc(movie['title'])}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"

        f"📅 {sc('Release')}: {movie['release']}\n"

        f"⭐ {sc('TMDB Rating')}: {movie['rating']}\n"

        f"⭐ {sc('IMDb Rating')}: {movie['imdb_rating']}\n"

        f"🎭 {sc('Genres')}: {movie['genres']}\n"

        f"🌐 {sc('Language')}: {movie['language']}\n"

        f"⏱ {sc('Runtime')}: {movie['runtime']}\n"

        f"🎥 {sc('Director')}: {movie['director']}\n\n"

        f"━━━━━━━━━━━━━━━━━━\n"

        f"👑 {sc(POWERED_BY)}"
    )


# ==========================================
# START COMMAND
# ==========================================

@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message):

    welcome_text = (
        f"👑 {sc('Welcome To')} {sc(BOT_NAME)}\n\n"

        f"🎬 {sc('Your Movie Information Assistant')}\n\n"

        f"🔎 {sc('Search Movies')}\n"

        f"⭐ {sc('Get Movie Ratings')}\n"

        f"🎭 {sc('Get Movie Details')}\n\n"

        f"📌 {sc('Use /movie Movie Name')}\n\n"

        f"✨ {sc(POWERED_BY)}"
    )

    try:

        if WELCOME_IMAGE.startswith("https://"):

            await message.reply_photo(
                photo=WELCOME_IMAGE,
                caption=welcome_text
            )

        else:

            await message.reply_text(welcome_text)

    except Exception as error:

        logger.exception("WELCOME ERROR")

        await message.reply_text(welcome_text)


# ==========================================
# HELP COMMAND
# ==========================================

@app.on_message(filters.command("help") & filters.private)
async def help_command(client, message):

    text = (
        f"📚 {sc('BOT COMMANDS')}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"

        f"🎬 /movie Movie Name\n"

        f"🏠 /start\n"

        f"📚 /help\n"

        f"ℹ️ /about\n\n"

        f"👑 {sc('ADMIN COMMANDS')}\n"

        f"/stats\n"

        f"/autopost on\n"

        f"/autopost off\n\n"

        f"✨ {sc(POWERED_BY)}"
    )

    await message.reply_text(text)


# ==========================================
# ABOUT COMMAND
# ==========================================

@app.on_message(filters.command("about") & filters.private)
async def about_command(client, message):

    text = (
        f"👑 {sc(BOT_NAME)}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"

        f"🎬 {sc('Movie Information Bot')}\n"

        f"⭐ {sc('TMDB and IMDb Information')}\n"

        f"⚡ {sc('Fast Movie Search')}\n\n"

        f"✨ {sc(POWERED_BY)}\n\n"

        f"Movie metadata provided by TMDB. "
        f"This product uses the TMDB API but is not endorsed or certified by TMDB."
    )

    await message.reply_text(text)


# ==========================================
# AUTO POST CONTROL
# ==========================================

@app.on_message(filters.command("autopost") & filters.private)
async def autopost_command(client, message):

    if not message.from_user or not is_owner(message.from_user.id):

        return await message.reply_text(
            "⛔ Owner only."
        )

    args = message.text.split(maxsplit=1)

    if len(args) < 2:

        return await message.reply_text(
            "Use /autopost on or /autopost off"
        )

    choice = args[1].lower().strip()

    if choice == "on":

        data["auto_post"] = True

    elif choice == "off":

        data["auto_post"] = False

    else:

        return await message.reply_text(
            "Use /autopost on or /autopost off"
        )

    save_data()

    await message.reply_text(
        f"✅ Auto Post: {choice.upper()}"
    )


# ==========================================
# STATS COMMAND
# ==========================================

@app.on_message(filters.command("stats") & filters.private)
async def stats_command(client, message):

    if not message.from_user or not is_owner(message.from_user.id):

        return await message.reply_text(
            "⛔ Owner only."
        )

    text = (
        f"📊 {sc('BOT STATISTICS')}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"

        f"🔎 Searches: {data['total_searches']}\n"

        f"📤 Posts: {data['total_posts']}\n"

        f"⚙️ Auto Post: {data['auto_post']}\n"

        f"🎬 Saved Movies: {len(data['posted_movies'])}\n\n"

        f"✨ {sc(POWERED_BY)}"
    )

    await message.reply_text(text)


# ==========================================
# MOVIE SEARCH COMMAND
# ==========================================

@app.on_message(filters.command("movie") & filters.private)
async def movie_command(client, message):

    if len(message.command) < 2:

        return await message.reply_text(
            "🎬 Use: /movie Movie Name"
        )

    movie_name = message.text.split(
        maxsplit=1
    )[1].strip()

    if len(movie_name) > 150:

        return await message.reply_text(
            "Movie name is too long."
        )

    status = await message.reply_text(
        f"🔎 {sc('Searching Movie...')}"
    )

    try:

        movie = await get_movie_information(movie_name)

        if not movie:

            return await status.edit_text(
                f"❌ {sc('Movie Not Found')}\n\n"
                f"Try another movie name."
            )

        data["total_searches"] += 1
        save_data()

        caption = build_caption(movie)

        poster = movie["poster"]

        # AUTO POST ENABLED
        if data.get("auto_post", True):

            movie_key = (
                str(movie["title"]).lower()
                + "_"
                + str(movie["release"])
            )

            if movie_key not in data["posted_movies"]:

                await send_channel_post(
                    caption=caption,
                    photo=poster
                )

                data["posted_movies"].append(movie_key)

                data["total_posts"] += 1

                save_data()

            await status.edit_text(
                f"✅ {sc('Movie Found')}\n\n"

                f"🎬 {movie['title']}\n\n"

                f"📢 {sc('Channel Post Successful')}\n\n"

                f"✨ {sc(POWERED_BY)}"
            )

        else:

            if poster:

                await message.reply_photo(
                    photo=poster,
                    caption=caption
                )

            else:

                await message.reply_text(caption)

            await status.delete()

    except Exception as error:

        logger.exception(
            "MOVIE SEARCH FAILED: %s",
            error
        )

        await status.edit_text(
            f"❌ {sc('Something Went Wrong')}\n\n"
            f"Please check server logs."
        )


# ==========================================
# HEALTH SERVER
# ==========================================

async def health(request):

    return web.json_response({
        "status": "online",
        "bot": BOT_NAME,
        "powered_by": POWERED_BY
    })


async def start_health_server():

    server = web.Application()

    server.router.add_get("/", health)

    server.router.add_get("/health", health)

    runner = web.AppRunner(server)

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        int(PORT)
    )

    await site.start()

    logger.info(
        "HEALTH SERVER RUNNING ON PORT %s",
        PORT
    )

    return runner


# ==========================================
# MAIN
# ==========================================

async def main():

    runner = None

    try:

        logger.info(
            "%s STARTING",
            BOT_NAME
        )

        runner = await start_health_server()

        logger.info(
            "BOT STARTED SUCCESSFULLY"
        )

        await idle()

    finally:

        if runner:

            await runner.cleanup()

        logger.info(
            "HEALTH SERVER STOPPED"
        )


# ==========================================
# RUN BOT
# ==========================================

if __name__ == "__main__":

    app.run(main())
