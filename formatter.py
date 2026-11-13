
def small_caps(text):
    normal = "abcdefghijklmnopqrstuvwxyz"
    small = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"

    return str(text).translate(
        str.maketrans(normal, small)
    )


def create_caption(movie, details, directors):

    title = details.get("title") or movie.get("title") or "N/A"

    release = details.get("release_date") or ""
    year = release[:4] if release else "N/A"

    genres = details.get("genres") or []
    genre_text = ", ".join(genres) if genres else "N/A"

    language = details.get("language") or "N/A"

    rating = details.get("rating")
    rating_text = f"{rating:.1f}/10" if rating is not None else "N/A"

    runtime = details.get("runtime")
    runtime_text = f"{runtime} min" if runtime else "N/A"

    director_text = ", ".join(directors) if directors else "N/A"

    story = (
        details.get("overview")
        or movie.get("overview")
        or "N/A"
    )

    imdb_id = details.get("imdb_id")

    imdb_link = (
        f"https://www.imdb.com/title/{imdb_id}/"
        if imdb_id else "N/A"
    )

    caption = f"""
🎬 ʀᴍ ᴍᴏᴠɪᴇꜱ • ᴇxᴄʟᴜꜱɪᴠᴇ ᴅʀᴏᴘ 🍿

🎥 ᴛɪᴛʟᴇ : {title} ({year})

🌐 ʟᴀɴɢᴜᴀɢᴇ : {language}

🎭 ɢᴇɴʀᴇ : {genre_text}

⭐ ᴛᴍᴅʙ ʀᴀᴛɪɴɢ : {rating_text}

🎬 ᴅɪʀᴇᴄᴛᴏʀ : {director_text}

⏳ ʀᴜɴᴛɪᴍᴇ : {runtime_text}

📝 ꜱᴛᴏʀʏ :
{story}

🔗 ɪᴍᴅʙ : {imdb_link}

👑 ᴘᴏᴡᴇʀᴇᴅ ʙʏ @ʀᴜᴅʀᴀᴍᴏᴠɪᴇᴢ

📌 ᴅᴀᴛᴀ & ɪᴍᴀɢᴇꜱ: ᴛᴍᴅʙ
"""

    return small_caps(caption)


def create_cast_message(cast):

    if not cast:
        return "👥 ᴄᴀꜱᴛ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ."

    names = "\n".join(
        f"• {name}" for name in cast
    )

    return small_caps(
        f"👥 ꜰᴜʟʟ ᴄᴀꜱᴛ ʟɪꜱᴛ\n\n{names}"
    )
