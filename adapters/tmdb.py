import os
import httpx
import logging
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

TMDB_API_BASE = "https://api.themoviedb.org/3"

async def get_tmdb_api_key() -> str:
    # Fallback to key found in code if environment variable is not set
    return os.getenv("TMDB_API_KEY", "1865f43a0549ca50d341dd9ab8b29f49")

async def get_tmdb_details(tmdb_id: int, content_type: str) -> Optional[Dict[str, Any]]:
    api_key = await get_tmdb_api_key()
    media_type = "tv" if content_type in ["tv", "anime"] else "movie"
    url = f"{TMDB_API_BASE}/{media_type}/{tmdb_id}?api_key={api_key}&append_to_response=external_ids"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                imdb_id = data.get("external_ids", {}).get("imdb_id")
                title = data.get("title") or data.get("name")
                original_title = data.get("original_title") or data.get("original_name")
                release_date = data.get("release_date") or data.get("first_air_date")
                year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None

                return {
                    "tmdb_id": tmdb_id,
                    "content_type": media_type,
                    "title": title,
                    "original_title": original_title,
                    "release_year": year,
                    "imdb_id": imdb_id,
                    "overview": data.get("overview"),
                    "poster_path": data.get("poster_path"),
                    "backdrop_path": data.get("backdrop_path"),
                    "vote_average": data.get("vote_average"),
                    "raw": data
                }
        except Exception as e:
            logger.error(f"Error fetching TMDB details for {tmdb_id}: {e}")
    return None

async def search_tmdb(query: str, year: Optional[int] = None, content_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
    api_key = await get_tmdb_api_key()
    media_type = content_type if content_type in ["movie", "tv"] else "multi"
    url = f"{TMDB_API_BASE}/search/{media_type}"

    params = {
        "api_key": api_key,
        "query": query,
        "include_adult": "false",
        "page": 1
    }
    if year:
        if media_type == "tv":
            params["first_air_date_year"] = year
        elif media_type == "movie":
            params["year"] = year

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results:
                    best = results[0]
                    t_id = best.get("id")
                    m_type = best.get("media_type") or media_type
                    if m_type == "multi":
                        m_type = best.get("media_type", "movie")
                    return await get_tmdb_details(t_id, m_type)
        except Exception as e:
            logger.error(f"Error searching TMDB for query {query}: {e}")
    return None
