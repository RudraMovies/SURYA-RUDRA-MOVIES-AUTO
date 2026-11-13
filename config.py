
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# =====================================
# TELEGRAM CONFIGURATION
# =====================================

API_ID = int(os.getenv("API_ID", "0"))

API_HASH = os.getenv("API_HASH", "")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")


# =====================================
# TMDB CONFIGURATION
# =====================================

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")

TMDB_ACCESS_TOKEN = os.getenv(
    "TMDB_ACCESS_TOKEN", ""
)


# =====================================
# CHANNEL CONFIGURATION
# =====================================

CHANNEL_ID = os.getenv("CHANNEL_ID", "")

OWNER_ID = int(os.getenv("OWNER_ID", "0"))


# =====================================
# RENDER CONFIGURATION
# =====================================

PORT = int(os.getenv("PORT", "10000"))


# =====================================
# BOT BRANDING
# =====================================

BOT_NAME = "SURYA RUDRA MOVIES"

BOT_USERNAME = os.getenv(
    "BOT_USERNAME", ""
)

CHANNEL_USERNAME = os.getenv(
    "CHANNEL_USERNAME", ""
)


# =====================================
# VALIDATION
# =====================================

def validate_config():

    missing = []

    if not API_ID:
        missing.append("API_ID")

    if not API_HASH:
        missing.append("API_HASH")

    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")

    if not TMDB_API_KEY and not TMDB_ACCESS_TOKEN:
        missing.append("TMDB_API_KEY or TMDB_ACCESS_TOKEN")

    if missing:
        raise ValueError(
            "Missing environment variables: "
            + ", ".join(missing)
        )


if __name__ == "__main__":

    validate_config()

    print("SURYA RUDRA MOVIES CONFIGURATION")
    print("CONFIGURATION VALIDATION SUCCESSFUL")

