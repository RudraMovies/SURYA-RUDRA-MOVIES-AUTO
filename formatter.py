
def small_caps(text):
    normal = "abcdefghijklmnopqrstuvwxyz"
    small = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"

    return str(text).translate(
        str.maketrans(normal, small)
    )


def create_caption(movie, imdb, cast):

    title = movie.get("title", "Unknown")
    year = movie.get("release_date", "")[:4]
    story = imdb.get("plot") or movie.get("overview") or "N/A"

    caption = f"""
🎬 ʀᴍ ᴍᴏᴠɪᴇꜱ • ᴇxᴄʟᴜꜱɪᴠᴇ ᴅʀᴏᴘ 🍿

🎥 ᴛɪᴛʟᴇ : {title} ({year})

🌐 ʟᴀɴɢᴜᴀɢᴇ : {imdb.get('language', 'N/A')}

🎭 ɢᴇɴʀᴇ : {imdb.get('genre', 'N/A')}

⭐ ɪᴍᴅʙ : {imdb.get('imdb_rating', 'N/A')}/10

🎬 ᴅɪʀᴇᴄᴛᴏʀ : {imdb.get('director', 'N/A')}

👥 ᴄᴀꜱᴛ :
{chr(10).join('• ' + name for name in cast) if cast else 'N/A'}

⏳ ʀᴜɴᴛɪᴍᴇ : {imdb.get('runtime', 'N/A')}

📝 ꜱᴛᴏʀʏ :
{story}

🌐 ᴄᴏᴜɴᴛʀʏ : {imdb.get('country', 'N/A')}

👑 ᴘᴏᴡᴇʀᴇᴅ ʙʏ @ʀᴜᴅʀᴀᴍᴏᴠɪᴇᴢ
"""

    return small_caps(caption)
