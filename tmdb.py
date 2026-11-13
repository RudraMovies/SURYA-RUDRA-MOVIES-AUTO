
import os
import aiohttp

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

BASE_URL = "https://api.themoviedb.org/3"


async def search_movie(movie_name):

    if not TMDB_API_KEY:
        return None

    url = f"{BASE_URL}/search/movie"

    params = {
        "api_key": TMDB_API_KEY,
        "query": movie_name
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:

            if response.status != 200:
                return None

            data = await response.json()

            results = data.get("results", [])

            if not results:
                return None

            movie = results[0]

            return {
                "id": movie.get("id"),
                "title": movie.get("title"),
                "overview": movie.get("overview"),
                "release_date": movie.get("release_date"),
                "poster": movie.get("poster_path"),
                "rating": movie.get("vote_average"),
            }


async def get_movie_cast(movie_id):

    url = f"{BASE_URL}/movie/{movie_id}/credits"

    params = {
        "api_key": TMDB_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:

            if response.status != 200:
                return []

            data = await response.json()

            return [
                person.get("name")
                for person in data.get("cast", [])[:5]
            ]


def get_poster_url(poster_path):

    if not poster_path:
        return None

    return f"https://image.tmdb.org/t/p/w500{poster_path}"
