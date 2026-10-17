# MovieBox + AnimeDubHindi Streaming Source API

A production-ready FastAPI backend that uses TMDB as the single source of truth for movie and anime metadata, while obtaining authorized streaming links and sources from `MovieBox` and `AnimeDubHindi` providers.

---

## Features
- **TMDB Metadata Integration**: Canonical title, release year, external IDs, and metadata lookup.
- **Provider Adapters**:
  - `MovieBoxAdapter`: HMAC-MD5 signing, JWT token lifecycle management, search, and play-info extraction.
  - `AnimeDubHindiAdapter`: HTML scraping of post pages, iframe inspection, and HubCloud/GDFlix source discovery.
- **FastAPI Endpoints**: Health check, providers list, and source retrieval endpoints for movies, TV series, and anime.
- **Performance & Caching**: Bounded in-memory TTLCaching for metadata and source lookups, connection timeouts, and robust error handling.
- **Deployment Ready**: Configured for Render deployment with `render.yaml` and `requirements.txt`.

---

## API Endpoints
- `GET /health` — Health check endpoint.
- `GET /providers` — List integrated providers and supported content types/languages.
- `GET /sources/movie/{tmdb_id}` — Get authorized streaming sources for a movie.
- `GET /sources/tv/{tmdb_id}/season/{season}/episode/{episode}` — Get authorized streaming sources for a TV show episode.
- `GET /sources/anime/{tmdb_id}/season/{season}/episode/{episode}` — Get authorized streaming sources for an anime episode.

---

## Environment Variables
Copy `.env.example` to `.env` and configure:
```env
TMDB_API_KEY=your_tmdb_api_key_here
PORT=8000
LOG_LEVEL=INFO
```

---

## Local Setup & Testing

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the development server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

3. Run tests:
   ```bash
   pytest
   ```
