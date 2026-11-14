
import logging
import aiohttp

from config import TMDB_API_KEY, TMDB_ACCESS_TOKEN


# =====================================
# LOGGING
# =====================================

logger = logging.getLogger(__name__)

TMDB_BASE_URL = "https://api.themoviedb.org/3"

TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p"


# =====================================
# HEADERS
# =====================================

def get_headers():

    headers = {
        "accept": "application/json"
    }

    if TMDB_ACCESS_TOKEN:
        headers["Authorization"] = (
            f"Bearer {TMDB_ACCESS_TOKEN}"
        )

    return headers


# =====================================
# API REQUEST
# =====================================

async def api_request(endpoint, extra_params=None):

    params = extra_params or {}

    if not TMDB_ACCESS_TOKEN:

        if not TMDB_API_KEY:
            raise ValueError(
                "TMDB API KEY OR ACCESS TOKEN IS MISSING"
            )

        params["api_key"] = TMDB_API_KEY

    url = f"{TMDB_BASE_URL}/{endpoint.lstrip('/')}"

    timeout = aiohttp.ClientTimeout(total=30)

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

                    error_text = await response.text()

                    logger.error(
                        "TMDB API ERROR %s: %s",
                        response.status,
                        error_text
                    )

                    return None

                return await response.json()

    except aiohttp.ClientError:

        logger.exception("TMDB NETWORK ERROR")

        return None

    except Exception:

        logger.exception("TMDB REQUEST FAILED")

        return None


# =====================================
# SEARCH MOVIE
# =====================================

async def search_movie(movie_name):

    if not movie_name:
        return None

    data = await api_request(
        "search/movie",
        {
            "query": movie_name,
            "include_adult": "false",
            "language": "en-US",
            "page": 1
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

        "original_title": movie.get(
            "original_title"
        ),

        "overview": movie.get("overview"),

        "release_date": movie.get(
            "release_date"
        ),

        "poster": movie.get(
            "poster_path"
        ),

        "backdrop": movie.get(
            "backdrop_path"
        ),

        "rating": movie.get(
            "vote_average"
        ),

        "vote_count": movie.get(
            "vote_count"
        ),

        "language": movie.get(
            "original_language"
        ),

        "popularity": movie.get(
            "popularity"
        )
    }


# =====================================
# MOVIE DETAILS
# =====================================

async def get_movie_details(movie_id):

    if not movie_id:
        return None

    data = await api_request(
        f"movie/{movie_id}",
        {
            "language": "en-US",
            "append_to_response": "external_ids"
        }
    )

    if not data:
        return None

    external_ids = data.get(
        "external_ids",
        {}
    )

    return {
        "id": data.get("id"),

        "title": data.get("title"),

        "original_title": data.get(
            "original_title"
        ),

        "overview": data.get("overview"),

        "release_date": data.get(
            "release_date"
        ),

        "runtime": data.get(
            "runtime"
        ),

        "genres": data.get(
            "genres",
            []
        ),

        "language": data.get(
            "original_language"
        ),

        "country": data.get(
            "origin_country",
            []
        ),

        "poster": data.get(
            "poster_path"
        ),

        "backdrop": data.get(
            "backdrop_path"
        ),

        "rating": data.get(
            "vote_average"
        ),

        "vote_count": data.get(
            "vote_count"
        ),

        "imdb_id": external_ids.get(
            "imdb_id"
        ),

        "popularity": data.get(
            "popularity"
        )
    }


# =====================================
# MOVIE DIRECTOR
# =====================================

async def get_movie_director(movie_id):

    if not movie_id:
        return []

    data = await api_request(
        f"movie/{movie_id}/credits"
    )

    if not data:
        return []

    crew = data.get("crew", [])

    directors = [
        person.get("name")
        for person in crew
        if person.get("job") == "Director"
        and person.get("name")
    ]

    return directors


# =====================================
# MOVIE CAST
# =====================================

async def get_movie_cast(movie_id):

    if not movie_id:
        return []

    data = await api_request(
        f"movie/{movie_id}/credits"
    )

    if not data:
        return []

    cast = data.get("cast", [])

    return [
        person.get("name")
        for person in cast
        if person.get("name")
    ]


# =====================================
# POSTER URL
# =====================================

def get_poster_url(poster_path):

    if not poster_path:
        return None

    if poster_path.startswith("http"):
        return poster_path

    return (
        f"{TMDB_IMAGE_BASE}/w780"
        f"{poster_path}"
    )


# =====================================
# LANDSCAPE BACKDROP URL
# =====================================

def get_backdrop_url(backdrop_path):

    if not backdrop_path:
        return None

    if backdrop_path.startswith("http"):
        return backdrop_path

    return (
        f"{TMDB_IMAGE_BASE}/w1280"
        f"{backdrop_path}"
    )


# =====================================
# IMAGE URL
# =====================================

def get_movie_image_url(movie):

    if not movie:
        return None

    backdrop = movie.get("backdrop")

    if backdrop:
        return get_backdrop_url(backdrop)

    poster = movie.get("poster")

    if poster:
        return get_poster_url(poster)

    return None
