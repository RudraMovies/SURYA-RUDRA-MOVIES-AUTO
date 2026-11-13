
import aiohttp
import logging

from config import TMDB_API_KEY, TMDB_ACCESS_TOKEN

BASE_URL = "https://api.themoviedb.org/3"

IMAGE_URL = "https://image.tmdb.org/t/p/w500"

logger = logging.getLogger(__name__)


def get_headers():
    headers = {
        "accept": "application/json"
    }

    if TMDB_ACCESS_TOKEN:
        headers["Authorization"] = (
            f"Bearer {TMDB_ACCESS_TOKEN}"
        )

    return headers


def get_params():
    if TMDB_ACCESS_TOKEN:
        return {}

    return {
        "api_key": TMDB_API_KEY
    }


async def api_request(endpoint, extra_params=None):

    url = f"{BASE_URL}/{endpoint}"

    params = get_params()

    if extra_params:
        params.update(extra_params)

    timeout = aiohttp.ClientTimeout(total=20)

    try:
        async with aiohttp.ClientSession(
            timeout=timeout
        ) as session:

            async with session.get(
                url,
                headers=get_headers(),
                params=params
            ) as response:

                if response.status != 200:
                    logger.error(
                        "TMDB API error: %s",
                        response.status
                    )
                    return None

                return await response.json()

    except Exception:
        logger.exception("TMDB request failed")
        return None


# =====================================
# SEARCH MOVIE
# =====================================

async def search_movie(movie_name):

    data = await api_request(
        "search/movie",
        {
            "query": movie_name,
            "include_adult": "false"
        }
    )

    if not data:
        return None

    results = data.get("results", [])

    if not results:
        return None

    movie = results[0]

    return {
        "id": movie.get("id"),
        "title": movie.get("title"),
        "original_title": movie.get("original_title"),
        "overview": movie.get("overview"),
        "release_date": movie.get("release_date"),
        "poster": movie.get("poster_path"),
        "backdrop": movie.get("backdrop_path"),
        "rating": movie.get("vote_average"),
        "vote_count": movie.get("vote_count"),
        "language": movie.get("original_language"),
        "popularity": movie.get("popularity")
    }


# =====================================
# COMPLETE MOVIE DETAILS
# =====================================

async def get_movie_details(movie_id):

    data = await api_request(
        f"movie/{movie_id}",
        {
            "append_to_response": "external_ids"
        }
    )

    if not data:
        return None

    genres = [
        item.get("name")
        for item in data.get("genres", [])
    ]

    external_ids = data.get("external_ids", {})

    return {
        "title": data.get("title"),
        "overview": data.get("overview"),
        "release_date": data.get("release_date"),
        "runtime": data.get("runtime"),
        "genres": genres,
        "language": data.get("original_language"),
        "country": [
            item.get("name")
            for item in data.get("production_countries", [])
        ],
        "poster": data.get("poster_path"),
        "rating": data.get("vote_average"),
        "imdb_id": external_ids.get("imdb_id")
    }


# =====================================
# FULL CAST AND CREW
# =====================================

async def get_movie_cast(movie_id):

    data = await api_request(
        f"movie/{movie_id}/credits"
    )

    if not data:
        return []

    return [
        person.get("name")
        for person in data.get("cast", [])
        if person.get("name")
    ]


async def get_movie_director(movie_id):

    data = await api_request(
        f"movie/{movie_id}/credits"
    )

    if not data:
        return []

    return [
        person.get("name")
        for person in data.get("crew", [])
        if person.get("job") == "Director"
    ]


# =====================================
# POSTER URL
# =====================================

def get_poster_url(poster_path):

    if not poster_path:
        return None

    return f"{IMAGE_URL}{poster_path}"
