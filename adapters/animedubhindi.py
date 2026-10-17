import httpx
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class AnimeDubHindiAdapter:
    def __init__(self):
        self.main_url = "https://www.animedubhindi.cc"

    async def search(self, query: str) -> List[Dict[str, Any]]:
        search_url = f"{self.main_url}/?s={query}"
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            try:
                resp = await client.get(search_url, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    results = []
                    for article in soup.select("article"):
                        a_tag = article.select_first("h2 a")
                        if not a_tag:
                            continue
                        title = a_tag.text.strip()
                        href = a_tag.get("href")
                        img = article.select_first("img")
                        poster = img.get("src") if img else None
                        results.append({
                            "title": title,
                            "url": href,
                            "poster": poster,
                            "type": "anime"
                        })
                    return results
            except Exception as e:
                logger.error(f"AnimeDubHindi search error: {e}")
        return []

    async def get_links(self, post_url: str, season: int = 1, episode: int = 1) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            try:
                resp = await client.get(post_url, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code != 200:
                    return []

                soup = BeautifulSoup(resp.text, "html.parser")
                iframe_a = soup.select_first("div.wp-block-button a")
                if not iframe_a:
                    return []
                iframe_url = iframe_a.get("href")

                # Fetch iframe/embed page
                i_resp = await client.get(iframe_url, headers={"User-Agent": "Mozilla/5.0"})
                if i_resp.status_code != 200:
                    return []

                i_soup = BeautifulSoup(i_resp.text, "html.parser")
                sources = []

                # Check for episodes or movie quality blocks
                # If TV series, look for specific episode block
                ep_blocks = i_soup.select("div.wp-block-group, div.pro-ep-card")
                if ep_blocks:
                    for block in ep_blocks:
                        ep_title = block.text
                        if f"Episode {episode}" in ep_title or not ep_blocks:
                            for a in block.select("a"):
                                href = a.get("href", "")
                                text = a.text.strip()
                                if "hubcloud" in href or "gdflix" in href:
                                    sources.append({
                                        "provider": "AnimeDubHindi",
                                        "url": href,
                                        "quality": "1080p",
                                        "language": "Hindi",
                                        "source_type": "official_watch_url"
                                    })
                else:
                    # Movie links
                    for a in i_soup.select("a"):
                        href = a.get("href", "")
                        text = a.text.strip()
                        if "hubcloud" in href or "gdflix" in href:
                            sources.append({
                                "provider": "AnimeDubHindi",
                                "url": href,
                                "quality": "1080p",
                                "language": "Hindi",
                                "source_type": "official_watch_url"
                            })

                return sources
            except Exception as e:
                logger.error(f"AnimeDubHindi get_links error: {e}")
        return []
