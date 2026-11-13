
import os
import aiohttp

OMDB_API_KEY = os.getenv("OMDB_API_KEY")

BASE_URL = "https://www.omdbapi.com/"


async def get_imdb_details(movie_name, year=None):

    if not OMDB_API_KEY:
        return None

    params = {
        "apikey": OMDB_API_KEY,
        "t": movie_name,
        "plot": "full"
    }

    if year:
        params["y"] = year

    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL, params=params) as response:

            if response.status != 200:
                return None

            data = await response.json()

            if data.get("Response") != "True":
                return None

            return {
                "imdb_id": data.get("imdbID"),
                "imdb_rating": data.get("imdbRating"),
                "imdb_votes": data.get("imdbVotes"),
                "runtime": data.get("Runtime"),
                "director": data.get("Director"),
                "genre": data.get("Genre"),
                "language": data.get("Language"),
                "country": data.get("Country"),
                "plot": data.get("Plot")
            }
