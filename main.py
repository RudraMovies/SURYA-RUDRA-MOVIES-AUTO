
import os
import asyncio
from pyrogram import Client, filters
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client(
    "surya_rudra_movies",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text(
        "👑 ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ꜱᴜʀʏᴀ ʀᴜᴅʀᴀ ᴍᴏᴠɪᴇꜱ ʙᴏᴛ!\n\n"
        "🎬 ꜱᴇɴᴅ ᴀ ᴍᴏᴠɪᴇ ɴᴀᴍᴇ ᴛᴏ ꜱᴛᴀʀᴛ."
    )

@app.on_message(filters.text & ~filters.command("start"))
async def movie_search(client, message):
    movie_name = message.text.strip()

    await message.reply_text(
        f"🔎 ᴍᴏᴠɪᴇ ꜱᴇᴀʀᴄʜ: {movie_name}\n\n"
        "ᴍᴏᴠɪᴇ ᴅᴀᴛᴀʙᴀꜱᴇ ɪɴᴛᴇɢʀᴀᴛɪᴏɴ ᴄᴏᴍɪɴɢ..."
    )

if __name__ == "__main__":
    print("SURYA RUDRA MOVIES BOT STARTING...")
    app.run()
