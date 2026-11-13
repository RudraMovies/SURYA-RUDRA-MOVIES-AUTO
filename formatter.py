
SMALL_CAPS_MAP = str.maketrans({
    "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ",
    "e": "ᴇ", "f": "ғ", "g": "ɢ", "h": "ʜ",
    "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ",
    "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ",
    "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ",
    "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x",
    "y": "ʏ", "z": "ᴢ"
})


def small_caps(text):
    if not text:
        return ""
    return str(text).lower().translate(SMALL_CAPS_MAP)


def clean_text(value, default="N/A"):
    if value is None or value == "":
        return default

    if isinstance(value, list):
        value = ", ".join(str(x) for x in value if x)

    return str(value).strip() or default


def create_caption(movie, details, directors):

    title = clean_text(
        details.get("title") or movie.get("title")
    )

    release_date = clean_text(
        details.get("release_date")
        or movie.get("release_date"),
        "N/A"
    )

    year = release_date[:4] if len(release_date) >= 4 else "N/A"

    language = clean_text(
        details.get("language") or movie.get("language")
    )

    genres = clean_text(
        details.get("genres") or movie.get("genres")
    )

    rating = details.get("rating") or movie.get("rating")

    try:
        rating = f"{float(rating):.1f}"
    except (TypeError, ValueError):
        rating = "N/A"

    if isinstance(directors, list):
        director = ", ".join(str(x) for x in directors if x)
    else:
        director = clean_text(directors)

    runtime = details.get("runtime")
    runtime = f"{runtime} min" if runtime else "N/A"

    lines = [
        f"🎬 {small_caps(title)} ({year}) 🍿",
        "",
        f"⭐ {small_caps('Rating')} : {rating}/10",
        f"🎭 {small_caps('Genres')} : {small_caps(genres)}",
        f"🌐 {small_caps('Language')} : {small_caps(language)}",
        f"📅 {small_caps('Release')} : {year}",
        f"🎬 {small_caps('Director')} : {small_caps(director)}",
        f"⏳ {small_caps('Runtime')} : {small_caps(runtime)}",
        "",
        f"👑 {small_caps('Powered By')} @RudraMoviez"
    ]

    return "\n".join(lines)


def create_cast_message(cast):
    return ""
