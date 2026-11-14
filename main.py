
import asyncio
import io
import logging
import threading

from aiohttp import web, ClientSession, ClientTimeout, FormData
from PIL import Image, ImageOps, ImageFilter

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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

from formatter import small_caps


# =====================================
# LOGGING
# =====================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

logger.info("SURYA RUDRA MOVIES STARTING")


# =====================================
# PYROGRAM BOT
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

        logger.info(
            "Health server running on port %s",
            PORT
        )

        while True:
            await asyncio.sleep(3600)

    def thread_target():
        asyncio.run(run_server())

    threading.Thread(
        target=thread_target,
        daemon=True
    ).start()


# =====================================
# 16:9 LANDSCAPE IMAGE CONVERSION
# =====================================

async def create_16_9_image(image_url):

    timeout = ClientTimeout(total=60)

    async with ClientSession(timeout=timeout) as session:

        async with session.get(image_url) as response:

            response.raise_for_status()
            image_data = await response.read()

    original = Image.open(
        io.BytesIO(image_data)
    ).convert("RGB")

    width = 1280
    height = 720

    # Landscape images fill the 16:9 frame.
    # Portrait fallback images remain fully visible.
    if original.width / original.height >= 1.65:

        final_image = ImageOps.fit(
            original,
            (width, height),
            method=Image.Resampling.LANCZOS
        )

    else:

        background = ImageOps.fit(
            original,
            (width, height),
            method=Image.Resampling.LANCZOS
        )

        background = background.filter(
            ImageFilter.GaussianBlur(30)
        )

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

        final_image = background

    output = io.BytesIO()

    final_image.save(
        output,
        format="JPEG",
        quality=90,
        optimize=True
    )

    output.seek(0)

    return output.getvalue()


# =====================================
# MOVIE CAPTION
# =====================================

def build_movie_caption(movie, details, directors):

    title = (
        details.get("title")
        or movie.get("title")
        or "Unknown"
    )

    release_date = (
        details.get("release_date")
        or movie.get("release_date")
        or ""
    )

    release_year = (
        release_date[:4]
        if release_date
        else "N/A"
    )

    rating = details.get("rating", "N/A")

    if isinstance(rating, (int, float)):
        rating = f"{rating:.1f}/10"

    genres = details.get("genres") or []

    if isinstance(genres, list):

        genre_text = ", ".join(
            str(item.get("name", ""))
            if isinstance(item, dict)
            else str(item)
            for item in genres
        )

    else:
        genre_text = str(genres)

    language = (
        details.get("language")
        or movie.get("language")
        or "N/A"
    )

    runtime = details.get("runtime")

    runtime_text = (
        f"{runtime} MIN"
        if runtime
        else "N/A"
    )

    if isinstance(directors, list):

        director_text = ", ".join(
            str(name) for name in directors
        )

    else:
        director_text = str(directors or "N/A")

    caption = (
        f"🎬 RM MOVIES • EXCLUSIVE MOVIE DROP 🍿\n\n"
        f"🎥 TITLE : {title} ({release_year})\n"
        f"⭐ RATING : {rating}\n"
        f"🎭 GENRES : {genre_text or 'N/A'}\n"
        f"🌐 LANGUAGE : {language}\n"
        f"📅 RELEASE : {release_year}\n"
        f"🎬 DIRECTOR : {director_text}\n"
        f"⏳ RUNTIME : {runtime_text}\n\n"
        f"👑 POWERED BY @RudraMoviez"
    )

    # Telegram photo caption limit
    if len(caption) > 1000:
        caption = caption[:997] + "..."

    return small_caps(caption)


# =====================================
# TELEGRAM CHANNEL POST
# =====================================

async def post_movie_to_channel(caption, image_url):

    if not CHANNEL_ID:
        raise ValueError("CHANNEL_ID is missing")

    if not image_url:
        raise ValueError("Movie image not available")

    image_bytes = await create_16_9_image(
        image_url
    )

    form = FormData()

    form.add_field(
        "chat_id",
        str(CHANNEL_ID)
    )

    form.add_field(
        "photo",
        image_bytes,
        filename="rudra_landscape_16_9.jpg",
        content_type="image/jpeg"
    )

    form.add_field(
        "caption",
        caption
    )

    form.add_field(
        "show_caption_above_media",
        "true"
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
                    f"Telegram API Error: {result}"
                )

    logger.info(
        "ONE POST: Movie details + landscape image uploaded"
    )


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
        "🔎 SEND A MOVIE NAME.\n\n"
        "📌 USE /credits FOR TMDB ATTRIBUTION."
    )


# =====================================
# CREDITS COMMAND
# =====================================

@app.on_message(
    filters.private & filters.command("credits")
)
async def credits_command(client, message):

    await message.reply_text(
        "TMDB ATTRIBUTION\n\n"
        "This product uses the TMDB API "
        "but is not endorsed or certified by TMDB.\n\n"
        "Official logo and attribution guidelines:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "TMDB LOGO & ATTRIBUTION",
                    url="https://www.themoviedb.org/about/logos-attribution"
                )
            ]
        ])
    )


# =====================================
# MOVIE SEARCH
# =====================================

@app.on_message(
    filters.private
    & filters.text
    & ~filters.command(["start", "credits"])
)
async def movie_search(client, message):

    user_id = (
        message.from_user.id
        if message.from_user
        else 0
    )

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
                "❌ MOVIE NOT FOUND. TRY ANOTHER NAME."
            )

            return

        movie_id = movie.get("id")

        if not movie_id:

            await status.edit_text(
                "❌ MOVIE ID NOT FOUND."
            )

            return

        # Get details
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

        caption = build_movie_caption(
            movie,
            details,
            directors
        )

        # Prefer landscape backdrop
        image_path = (
            details.get("backdrop")
            or movie.get("backdrop")
        )

        # Fallback to portrait poster
        if not image_path:

            image_path = (
                details.get("poster")
                or movie.get("poster")
            )

        if not image_path:

            await status.edit_text(
                "❌ MOVIE IMAGE NOT AVAILABLE."
            )

            return

        if str(image_path).startswith("https://"):

            image_url = image_path

        else:

            image_url = get_poster_url(
                image_path
            )

        if not image_url:

            await status.edit_text(
                "❌ IMAGE URL NOT AVAILABLE."
            )

            return

        # One Telegram post
        await post_movie_to_channel(
            caption,
            image_url
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
            "❌ MOVIE POSTING FAILED. CHECK RENDER LOGS."
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
