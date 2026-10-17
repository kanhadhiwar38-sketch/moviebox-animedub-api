import httpx
import logging
import traceback
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class AnimeDubHindiAdapter:
    def __init__(self):
        self.main_url = "https://www.animedubhindi.cc"

    async def search(self, query: str) -> List[Dict[str, Any]]:
        queries = [query]
        if ":" in query:
            queries.append(query.split(":")[0].strip())
        words = query.split()
        if len(words) > 2:
            queries.append(" ".join(words[:2]))
        if len(words) > 1 and " ".join(words[:2]) != words[0]:
            queries.append(words[0])

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            for q in queries:
                search_url = f"{self.main_url}/?s={q}"
                try:
                    resp = await client.get(search_url, headers={"User-Agent": "Mozilla/5.0"})
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        results = []
                        for article in soup.select("article"):
                            a_tag = article.select_one("h2 a")
                            if not a_tag:
                                continue
                            title = a_tag.get_text(strip=True)
                            href = a_tag.get("href")
                            if not href:
                                continue
                            img = article.select_one("img")
                            poster = img.get("src") if img else None
                            results.append({
                                "title": title,
                                "url": href,
                                "poster": poster,
                                "type": "anime"
                            })
                        if results:
                            return results
                except Exception as e:
                    logger.error(f"AnimeDubHindi search error for '{q}': {e}")
        return []

    async def get_links(self, post_url: str, season: int = 1, episode: int = 1) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            try:
                resp = await client.get(post_url, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code != 200:
                    return []

                soup = BeautifulSoup(resp.text, "html.parser")
                iframe_a = soup.select_one("div.wp-block-button a")
                if not iframe_a:
                    iframe_a = soup.select_one("iframe") or soup.select_one(".entry-content a")
                if not iframe_a:
                    return []

                iframe_url = iframe_a.get("href") or iframe_a.get("src")
                if not iframe_url:
                    return []

                sources = []
                if iframe_url.startswith("http"):
                    try:
                        i_resp = await client.get(iframe_url, headers={"User-Agent": "Mozilla/5.0"})
                        if i_resp.status_code == 200:
                            i_soup = BeautifulSoup(i_resp.text, "html.parser")
                            for a in i_soup.select("a"):
                                href = a.get("href", "")
                                if "hubcloud" in href or "gdflix" in href or "pixeldrain" in href:
                                    sources.append({
                                        "provider": "AnimeDubHindi",
                                        "url": href,
                                        "quality": "1080p",
                                        "language": "Hindi",
                                        "source_type": "official_watch_url"
                                    })
                    except Exception:
                        pass

                for a in soup.select("a"):
                    href = a.get("href", "")
                    if "hubcloud" in href or "gdflix" in href or "pixeldrain" in href:
                        if not any(s["url"] == href for s in sources):
                            sources.append({
                                "provider": "AnimeDubHindi",
                                "url": href,
                                "quality": "1080p",
                                "language": "Hindi",
                                "source_type": "official_watch_url"
                            })

                return sources
            except Exception as e:
                traceback.print_exc()
                logger.error(f"AnimeDubHindi get_links error: {e}")
        return []
