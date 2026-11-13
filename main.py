
import os
import logging

from pyrogram import Client, filters

from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    CHANNEL_ID
)

from tmdb import search_movie, get_movie_cast, get_poster_url
from omdb import get_imdb_details
from formatter import create_caption

logging.basicConfig(level=logging.INFO)

OWNER_ID = int(os.getenv("OWNER_ID", "0"))

app = Client(
    "surya_rudra_movies",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


@app.on_message(filters.private & filters.command("start"))
async def start_command(client, message):
    await message.reply_text(
        "👑 ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ꜱᴜʀʏᴀ ʀᴜᴅʀᴀ ᴍᴏᴠɪᴇꜱ ʙᴏᴛ!\n\n"
        "🎬 ꜱᴇɴᴅ ᴀ ᴍᴏᴠɪᴇ ɴᴀᴍᴇ ᴛᴏ ꜱᴛᴀʀᴛ."
    )


@app.on_message(filters.private & filters.text & ~filters.command("start"))
async def movie_search(client, message):

    if not message.from_user or message.from_user.id != OWNER_ID:
        await message.reply_text("⛔ ᴀᴄᴄᴇꜱꜱ ᴅᴇɴɪᴇᴅ.")
        return

    movie_name = message.text.strip()

    status = await message.reply_text(
        "🔎 ᴍᴏᴠɪᴇ ꜱᴇᴀʀᴄʜɪɴɢ..."
    )

    try:
        movie = await search_movie(movie_name)

        if not movie:
            await status.edit_text("❌ ᴍᴏᴠɪᴇ ɴᴏᴛ ꜰᴏᴜɴᴅ.")
            return

        year = (movie.get("release_date") or "")[:4]

        imdb = await get_imdb_details(
            movie.get("title"),
            year=year or None
        )

        imdb = imdb or {}

        cast = await get_movie_cast(movie["id"])

        caption = create_caption(movie, imdb, cast)

        poster = get_poster_url(movie.get("poster"))

        if not CHANNEL_ID:
            await status.edit_text("❌ ᴄʜᴀɴɴᴇʟ ɪᴅ ɴᴏᴛ ꜱᴇᴛ.")
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

        await status.edit_text(
            "✅ ᴍᴏᴠɪᴇ ᴘᴏꜱᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!"
        )

    except Exception:
        logging.exception("Movie posting failed")
        await status.edit_text(
            "❌ ᴇʀʀᴏʀ ᴡʜɪʟᴇ ᴘᴏꜱᴛɪɴɢ. ᴄʜᴇᴄᴋ ʟᴏɢꜱ."
        )


if __name__ == "__main__":
    print("SURYA RUDRA MOVIES BOT STARTED")
    app.run()
