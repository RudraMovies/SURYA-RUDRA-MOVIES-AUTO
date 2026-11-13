
import asyncio
import logging
import threading

from aiohttp import web, ClientSession, ClientTimeout
from pyrogram import Client, filters

from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    TMDB_API_KEY,
    TMDB_ACCESS_TOKEN,
    CHANNEL_ID,
    OWNER_ID,
    PORT,
)

from tmdb import (
    search_movie,
    get_movie_details,
    get_movie_director,
    get_poster_url,
)

from formatter import create_caption


# -----------------------------
# LOGGING
# -----------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

logger.info("SURYA RUDRA MOVIES STARTING")


# -----------------------------
# PYROGRAM BOT
# -----------------------------

app = Client(
    "surya_rudra_movies",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


# -----------------------------
# HEALTH SERVER
# -----------------------------

async def health(request):
    return web.json_response({
        "status": "online",
        "bot": "SURYA RUDRA MOVIES"
    })


def start_health_server():
    async def run_server():
        server = web.Application()
        server.router.add_get("/", health)
        server.router.add_get("/health", health)

        runner = web.AppRunner(server)
        await runner.setup()

        site = web.TCPSite(
            runner,
            "0.0.0.0",
            PORT
        )

        await site.start()

        logger.info("Health server running on port %s", PORT)

        while True:
            await asyncio.sleep(3600)

    def thread_target():
        asyncio.run(run_server())

    thread = threading.Thread(
        target=thread_target,
        daemon=True
    )
    thread.start()


# -----------------------------
# TELEGRAM CHANNEL POSTING
# -----------------------------

async def telegram_api(method, data):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

    timeout = ClientTimeout(total=60)

    async with ClientSession(timeout=timeout) as session:
        async with session.post(url, json=data) as response:
            result = await response.json()

            if not result.get("ok"):
                raise RuntimeError(
                    f"Telegram API error: {result}"
                )

            return result["result"]


async def post_movie_to_channel(caption, poster_url):
    if not CHANNEL_ID:
        raise ValueError("CHANNEL_ID is missing in environment variables")

    # FIRST: Send movie details as a text message
    await telegram_api(
        "sendMessage",
        {
            "chat_id": CHANNEL_ID,
            "text": caption,
            "disable_web_page_preview": True
        }
    )

    logger.info("Movie details posted successfully")

    # SECOND: Send poster as a separate photo attachment
    if poster_url:
        await telegram_api(
            "sendPhoto",
            {
                "chat_id": CHANNEL_ID,
                "photo": poster_url
            }
        )

        logger.info("Movie poster attached successfully")


# -----------------------------
# START COMMAND
# -----------------------------

@app.on_message(filters.private & filters.command("start"))
async def start_command(client, message):

    await message.reply_text(
        "👑 SURYA RUDRA MOVIES\n\n"
        "🎬 WELCOME!\n\n"
        "🔎 SEND A MOVIE NAME."
    )


# -----------------------------
# MOVIE SEARCH
# -----------------------------

@app.on_message(
    filters.private
    & filters.text
    & ~filters.command(["start"])
)
async def movie_search(client, message):

    user_id = message.from_user.id if message.from_user else 0

    # Optional owner restriction
    if OWNER_ID and int(OWNER_ID) != int(user_id):
        await message.reply_text("⛔ UNAUTHORIZED USER.")
        return

    movie_name = message.text.strip()

    if not movie_name:
        return

    status = await message.reply_text(
        "⏳ SEARCHING MOVIE DETAILS..."
    )

    try:
        # Search movie in TMDB
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

        # Get movie details
        details = await get_movie_details(movie_id)

        if not details:
            await status.edit_text(
                "❌ MOVIE DETAILS NOT AVAILABLE."
            )
            return

        # Get director only. Cast is disabled.
        directors = await get_movie_director(movie_id)

        # Create compact small-caps caption
        caption = create_caption(
            movie,
            details,
            directors
        )

        # Find poster
        poster_path = (
            details.get("poster")
            or movie.get("poster")
        )

        if poster_path:
            if str(poster_path).startswith("https://"):
                poster_url = poster_path
            else:
                poster_url = get_poster_url(poster_path)
        else:
            poster_url = None

        # Send details first, poster below
        await post_movie_to_channel(
            caption,
            poster_url
        )

        await status.edit_text(
            "✅ MOVIE POSTED SUCCESSFULLY!"
        )

        logger.info(
            "Movie posted successfully: %s",
            movie.get("title")
        )

    except Exception:
        logger.exception("Movie posting failed")

        await status.edit_text(
            "❌ MOVIE POSTING FAILED. CHECK RENDER LOGS."
        )


# -----------------------------
# MAIN
# -----------------------------

if __name__ == "__main__":

    start_health_server()

    logger.info("Starting Telegram bot...")

    app.run()
