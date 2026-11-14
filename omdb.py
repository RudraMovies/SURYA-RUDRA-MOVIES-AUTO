import os
import aiohttp

OMDB_API_KEY = os.getenv("OMDB_API_KEY", "")

async def search_omdb(movie_name):

    if not OMDB_API_KEY:
        return None

    url = "https://www.omdbapi.com/"

    params = {
        "apikey": OMDB_API_KEY,
        "t": movie_name,
        "plot": "short"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                params=params,
                timeout=15
            ) as response:

                data = await response.json()

                if data.get("Response") != "True":
                    return None

                return data

    except Exception:
        return None


def convert_omdb(data):

    if not data:
        return None

    return {
        "title": data.get("Title", "UNKNOWN"),
        "release_date": data.get("Released", ""),
        "rating": data.get("imdbRating"),
        "genres": [
            {"name": genre.strip()}
            for genre in data.get("Genre", "").split(",")
            if genre.strip()
        ],
        "language": data.get("Language", "N/A"),
        "runtime": int(
            data.get("Runtime", "0").split()[0]
        ) if data.get("Runtime", "").split()
        and data.get("Runtime", "").split()[0].isdigit()
        else None,
        "poster": data.get("Poster"),
        "director": data.get("Director", "N/A"),
        "imdb_id": data.get("imdbID")
    }
