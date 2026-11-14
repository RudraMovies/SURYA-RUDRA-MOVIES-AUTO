
import asyncio
import io
import logging
import threading

from aiohttp import (
    web,
    ClientSession,
    ClientTimeout,
    FormData
)

from PIL import Image, ImageOps, ImageFilter

from pyrogram import Client, filters

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
    get_poster_url
)

from formatter import create_caption


# =====================================
# LOGGING
# =====================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

logger.info("SURYA RUDRA MOVIES STARTING")


# =====================================
# BOT
# =====================================

app = Client(
    "surya_rudra_movies",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


# =====================================
# HEALTH SERVER
# =====================================

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
            int(PORT)
        )

        await site.start()

        logger.info("Health server running on port %s", PORT)

        while True:
            await asyncio.sleep(3600)

    def thread_target():
        asyncio.run(run_server())

    threading.Thread(
        target=thread_target,
        daemon=True
    ).start()


# =====================================
# TELEGRAM API
# =====================================

async def telegram_api(method, data):

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/{method}"
    )

    timeout = ClientTimeout(total=60)

    async with ClientSession(timeout=timeout) as session:

        async with session.post(
            url,
            json=data
        ) as response:

            result = await response.json()

            if not result.get("ok"):
                raise RuntimeError(
                    f"Telegram API Error: {result}"
                )

            return result["result"]


# =====================================
# DOWNLOAD AND CONVERT POSTER
# =====================================

async def create_16_9_poster(poster_url):

    timeout = ClientTimeout(total=45)

    async with ClientSession(timeout=timeout) as session:

        async with session.get(poster_url) as response:

            response.raise_for_status()

            image_data = await response.read()

    original = Image.open(
        io.BytesIO(image_data)
    ).convert("RGB")

    width = 1280
    height = 720

    # Landscape blurred background
    background = ImageOps.fit(
        original,
        (width, height),
        method=Image.Resampling.LANCZOS
    )

    background = background.filter(
        ImageFilter.GaussianBlur(30)
    )

    # Slightly darken background
    dark_layer = Image.new(
        "RGB",
        (width, height),
        (0, 0, 0)
    )

    background = Image.blend(
        background,
        dark_layer,
        0.35
    )

    # Keep complete original poster visible
    foreground = ImageOps.contain(
        original,
        (width, height),
        method=Image.Resampling.LANCZOS
    )

    x = (width - foreground.width) // 2
    y = (height - foreground.height) // 2

    background.paste(
        foreground,
        (x, y)
    )

    output = io.BytesIO()

    background.save(
        output,
        format="JPEG",
        quality=90,
        optimize=True
    )

    output.seek(0)

    return output.getvalue()


# =====================================
# POST MOVIE DETAILS
# =====================================

async def post_movie_to_channel(caption, poster_url):

    if not CHANNEL_ID:
        raise ValueError(
            "CHANNEL_ID is missing"
        )

    # FIRST: Text message
    await telegram_api(
        "sendMessage",
        {
            "chat_id": CHANNEL_ID,
            "text": caption,
            "disable_web_page_preview": True
        }
    )

    logger.info("Movie details posted")

    # SECOND: 16:9 photo attachment
    if not poster_url:
        logger.warning("Poster not available")
        return

    poster_bytes = await create_16_9_poster(
        poster_url
    )

    form = FormData()

    form.add_field(
        "chat_id",
        str(CHANNEL_ID)
    )

    form.add_field(
        "photo",
        poster_bytes,
        filename="rudra_poster_16_9.jpg",
        content_type="image/jpeg"
    )

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendPhoto"
    )

    timeout = ClientTimeout(total=90)

    async with ClientSession(timeout=timeout) as session:

        async with session.post(
            url,
            data=form
        ) as response:

            result = await response.json()

            if not result.get("ok"):
                raise RuntimeError(
                    f"Poster Upload Error: {result}"
                )

    logger.info("16:9 Poster attachment uploaded")


# =====================================
# START COMMAND
# =====================================

@app.on_message(
    filters.private & filters.command("start")
)
async def start_command(client, message):

    await message.reply_text(
        "👑 SURYA RUDRA MOVIES\n\n"
        "🎬 WELCOME!\n\n"
        "🔎 SEND A MOVIE NAME."
    )


# =====================================
# MOVIE SEARCH
# =====================================

@app.on_message(
    filters.private
    & filters.text
    & ~filters.command(["start"])
)
async def movie_search(client, message):

    user_id = (
        message.from_user.id
        if message.from_user
        else 0
    )

    # Owner restriction
    if OWNER_ID and int(OWNER_ID) != int(user_id):

        await message.reply_text(
            "⛔ UNAUTHORIZED USER."
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
                "❌ MOVIE NOT FOUND."
            )

            return

        movie_id = movie.get("id")

        if not movie_id:

            await status.edit_text(
                "❌ MOVIE ID NOT FOUND."
            )

            return

        # Movie details
        details = await get_movie_details(
            movie_id
        )

        if not details:

            await status.edit_text(
                "❌ MOVIE DETAILS NOT AVAILABLE."
            )

            return

        # Director only
        directors = await get_movie_director(
            movie_id
        )

        # Create caption
        caption = create_caption(
            movie,
            details,
            directors
        )

        # Poster URL
        poster_path = (
            details.get("poster")
            or movie.get("poster")
        )

        poster_url = None

        if poster_path:

            if str(poster_path).startswith("https://"):

                poster_url = poster_path

            else:

                poster_url = get_poster_url(
                    poster_path
                )

        # Post details and poster
        await post_movie_to_channel(
            caption,
            poster_url
        )

        await status.edit_text(
            "✅ MOVIE POSTED SUCCESSFULLY!"
        )

        logger.info(
            "Movie posted: %s",
            movie.get("title")
        )

    except Exception:

        logger.exception(
            "Movie posting failed"
        )

        await status.edit_text(
            "❌ MOVIE POSTING FAILED. CHECK LOGS."
        )


# =====================================
# MAIN
# =====================================

if __name__ == "__main__":

    start_health_server()

    logger.info(
        "Starting SURYA RUDRA MOVIES..."
    )

    app.run()
