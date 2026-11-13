
import re
from html import escape


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
    """Convert normal text to Unicode small caps."""
    if not text:
        return ""
    return str(text).translate(SMALL_CAPS_MAP)


def clean_text(value, default="N/A"):
    """Clean empty or missing values."""
    if value is None:
        return default

    if isinstance(value, list):
        value = ", ".join(str(x) for x in value if x)

    value = str(value).strip()
    return value if value else default


def get_director_name(directors):
    """Convert director list into readable text."""
    if isinstance(directors, list):
        names = [
            str(item).strip()
            for item in directors
            if item
        ]
        return ", ".join(names) if names else "N/A"

    return clean_text(directors)


def create_caption(movie, details, directors):
    """Create a compact premium movie caption."""

    title = clean_text(
        details.get("title") or movie.get("title")
    )

    release_date = clean_text(
        details.get("release_date")
        or movie.get("release_date"),
        "N/A"
    )

    year = (
        release_date[:4]
        if len(release_date) >= 4
        else "N/A"
    )

    language = clean_text(
        details.get("language")
        or movie.get("language"),
        "N/A"
    ).upper()

    genres = clean_text(
        details.get("genres")
        or movie.get("genres"),
        "N/A"
    )

    rating = clean_text(
        details.get("rating")
        or movie.get("rating"),
        "N/A"
    )

    director = get_director_name(directors)

    runtime = details.get("runtime")

    if runtime:
        runtime_text = f"{runtime} MIN"
    else:
        runtime_text = "N/A"

    # Main caption
    lines = [
        f"🎬 {small_caps(title)} ({year}) 🍿",
        "",
        f"⭐ {small_caps('Rating')}: {rating}/10",
        f"🎭 {small_caps('Genres')}: {small_caps(genres)}",
        f"🌐 {small_caps('Language')}: {small_caps(language)}",
        f"📅 {small_caps('Release')}: {year}",
        f"🎬 {small_caps('Director')}: {small_caps(director)}",
        f"⏳ {small_caps('Runtime')}: {runtime_text}",
        "",
        f"👑 {small_caps('Powered By')} @RudraMoviez",
        "",
        f"📌 {small_caps('Data & Images')}: TMDB"
    ]

    caption = "\n".join(lines)

    # Telegram photo caption limit safety
    if len(caption) > 1000:
        caption = caption[:997] + "..."

    return caption


def create_cast_message(cast):
    """
    Cast posting disabled.
    Kept for compatibility with older main.py imports.
    """
    return ""
