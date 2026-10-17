import os
import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from cachetools import TTLCache
from pydantic import BaseModel

from adapters.tmdb import get_tmdb_details, search_tmdb
from adapters.moviebox import MovieBoxAdapter
from adapters.animedubhindi import AnimeDubHindiAdapter

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MovieBox + AnimeDubHindi Streaming Source API",
    version="1.0.0",
    description="Authorized streaming source API using TMDB as metadata source of truth."
)

# Caching: metadata cache (TTL 24 hours), sources cache (TTL 30 minutes)
metadata_cache = TTLCache(maxsize=1000, ttl=86400)
source_cache = TTLCache(maxsize=500, ttl=1800)

moviebox_adapter = MovieBoxAdapter()
animedub_adapter = AnimeDubHindiAdapter()

class SourceItem(BaseModel):
    provider: str
    url: str
    quality: Optional[str] = "1080p"
    language: Optional[str] = "Hindi"
    source_type: Optional[str] = "official_watch_url"

class SourceResponse(BaseModel):
    tmdb_id: int
    content_type: str
    sources: List[SourceItem]
    errors: List[str] = []

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "streaming-source-api"}

@app.get("/providers")
async def list_providers():
    return {
        "providers": [
            {
                "name": "MovieBoxProvider",
                "active": True,
                "languages": ["Hindi", "English", "Original"],
                "supported_types": ["movie", "tv"]
            },
            {
                "name": "Animedubhindi",
                "active": True,
                "languages": ["Hindi"],
                "supported_types": ["anime", "tv", "movie"]
            }
        ]
    }

async def resolve_tmdb_to_providers(tmdb_id: int, content_type: str, season: int = 0, episode: int = 0) -> SourceResponse:
    cache_key = f"{content_type}:{tmdb_id}:{season}:{episode}"
    if cache_key in source_cache:
        return source_cache[cache_key]

    errors = []
    sources = []

    # 1. Get TMDB details
    details = await get_tmdb_details(tmdb_id, content_type)
    if not details:
        raise HTTPException(status_code=404, detail=f"TMDB ID {tmdb_id} not found.")

    canonical_title = details["title"]
    release_year = details["release_year"]

    # 2. Query MovieBox Adapter
    try:
        mb_results = await moviebox_adapter.search(canonical_title)
        # Match by title/year if possible
        matched_mb = None
        for item in mb_results:
            if canonical_title.lower() in item["title"].lower() or (item.get("rating") and float(item["rating"]) > 0):
                matched_mb = item
                break
        if not matched_mb and mb_results:
            matched_mb = mb_results[0]  # fallback to first result

        if matched_mb:
            mb_links = await moviebox_adapter.get_links(matched_mb["id"], season=season, episode=episode)
            for l in mb_links:
                sources.append(SourceItem(**l))
    except Exception as e:
        err_msg = f"MovieBox error: {str(e)}"
        logger.error(err_msg)
        errors.append(err_msg)

    # 3. Query AnimeDubHindi Adapter (primarily for anime/tv)
    try:
        adh_results = await animedub_adapter.search(canonical_title)
        matched_adh = None
        for item in adh_results:
            if canonical_title.lower() in item["title"].lower():
                matched_adh = item
                break
        if not matched_adh and adh_results:
            matched_adh = adh_results[0]

        if matched_adh:
            adh_links = await animedub_adapter.get_links(matched_adh["url"], season=season, episode=episode)
            for l in adh_links:
                sources.append(SourceItem(**l))
    except Exception as e:
        err_msg = f"AnimeDubHindi error: {str(e)}"
        logger.error(err_msg)
        errors.append(err_msg)

    response = SourceResponse(
        tmdb_id=tmdb_id,
        content_type=content_type,
        sources=sources,
        errors=errors
    )
    source_cache[cache_key] = response
    return response

@app.get("/sources/movie/{tmdb_id}", response_model=SourceResponse)
async def get_movie_sources(tmdb_id: int, language: Optional[str] = None, quality: Optional[str] = None):
    return await resolve_tmdb_to_providers(tmdb_id, "movie", season=0, episode=0)

@app.get("/sources/tv/{tmdb_id}/season/{season}/episode/{episode}", response_model=SourceResponse)
async def get_tv_sources(tmdb_id: int, season: int, episode: int, language: Optional[str] = None, quality: Optional[str] = None):
    return await resolve_tmdb_to_providers(tmdb_id, "tv", season=season, episode=episode)

@app.get("/sources/anime/{tmdb_id}/season/{season}/episode/{episode}", response_model=SourceResponse)
async def get_anime_sources(tmdb_id: int, season: int, episode: int, language: Optional[str] = None, quality: Optional[str] = None):
    return await resolve_tmdb_to_providers(tmdb_id, "anime", season=season, episode=episode)
