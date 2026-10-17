import httpx
import logging
from typing import List, Dict, Any, Optional
from utils.crypto import (
    generate_x_client_token,
    generate_x_tr_signature,
    generate_device_id,
    random_brand_model,
    is_token_valid
)

logger = logging.getLogger(__name__)

HOST_POOL = [
    "https://api6.aoneroom.com",
    "https://api5.aoneroom.com",
    "https://api4.aoneroom.com",
    "https://api4sg.aoneroom.com",
    "https://api3.aoneroom.com",
]

class MovieBoxAdapter:
    def __init__(self):
        self.device_id = generate_device_id()
        self.bearer_token: Optional[str] = None

    async def _get_working_host(self, client: httpx.AsyncClient) -> str:
        brand, model = random_brand_model()
        for host in HOST_POOL:
            url = f"{host}/wefeed-mobile-bff/tab/ranking-list?tabId=0&categoryType=4516404531735022304&page=1&perPage=1"
            x_client_token = generate_x_client_token()
            x_tr_signature = generate_x_tr_signature("GET", "application/json", "application/json", url)
            headers = {
                "user-agent": f"com.community.oneroom/50020088 (Linux; U; Android 13; en_US; {brand}; Build/TQ3A.230901.001; Cronet/145.0.7582.0)",
                "accept": "application/json",
                "content-type": "application/json",
                "x-client-token": x_client_token,
                "x-tr-signature": x_tr_signature,
                "x-client-info": f'{{"package_name":"com.community.oneroom","version_name":"3.0.13.0325.03","version_code":50020088,"os":"android","os_version":"13","device_id":"{self.device_id}","install_store":"ps","system_language":"en","net":"NETWORK_WIFI","region":"US","timezone":"Asia/Calcutta","sp_code":""}}',
                "x-client-status": "0"
            }
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code in [200, 401, 441]:
                    x_user = resp.headers.get("x-user")
                    if x_user:
                        import json
                        token = json.loads(x_user).get("token")
                        if token and is_token_valid(token):
                            self.bearer_token = token
                    return host
            except Exception:
                continue
        return HOST_POOL[0]

    async def _get_cached_token(self, client: httpx.AsyncClient, host: str) -> str:
        if is_token_valid(self.bearer_token or ""):
            return self.bearer_token

        url = f"{host}/wefeed-mobile-bff/tab/ranking-list?tabId=0&categoryType=4516404531735022304&page=1&perPage=1"
        brand, model = random_brand_model()
        x_client_token = generate_x_client_token()
        x_tr_signature = generate_x_tr_signature("GET", "application/json", "application/json", url)

        headers = {
            "user-agent": f"com.community.oneroom/50020088 (Linux; U; Android 13; en_US; {brand}; Build/TQ3A.230901.001; Cronet/145.0.7582.0)",
            "accept": "application/json",
            "content-type": "application/json",
            "x-client-token": x_client_token,
            "x-tr-signature": x_tr_signature,
            "x-client-info": f'{{"package_name":"com.community.oneroom","version_name":"3.0.13.0325.03","version_code":50020088,"os":"android","os_version":"13","device_id":"{self.device_id}","install_store":"ps","system_language":"en","net":"NETWORK_WIFI","region":"US","timezone":"Asia/Calcutta","sp_code":""}}',
            "x-client-status": "0"
        }

        try:
            resp = await client.get(url, headers=headers)
            x_user = resp.headers.get("x-user")
            if x_user:
                import json
                token = json.loads(x_user).get("token")
                if token and is_token_valid(token):
                    self.bearer_token = token
                    return token
        except Exception as e:
            logger.error(f"MovieBox token fetch error: {e}")
        return ""

    def _persist_token_from_header(self, x_user_header: Optional[str]):
        if not x_user_header:
            return
        try:
            import json
            token = json.loads(x_user_header).get("token")
            if token and is_token_valid(token):
                self.bearer_token = token
        except Exception:
            pass

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
            host = await self._get_working_host(client)
            token = await self._get_cached_token(client, host)

            for q in queries:
                url = f"{host}/wefeed-mobile-bff/subject-api/search/v2"
                json_body = {"page": 1, "perPage": 20, "keyword": q}
                import json
                body_str = json.dumps(json_body)

                x_client_token = generate_x_client_token()
                x_tr_signature = generate_x_tr_signature("POST", "application/json", "application/json; charset=utf-8", url, body_str)
                brand, model = random_brand_model()

                headers = {
                    "user-agent": "com.community.mbox.in/50020042 (Linux; U; Android 16; en_IN; sdk_gphone64_x86_64; Build/BP22.250325.006; Cronet/133.0.6876.3)",
                    "accept": "application/json",
                    "content-type": "application/json",
                    "x-client-token": x_client_token,
                    "x-tr-signature": x_tr_signature,
                    "x-client-info": f'{{"package_name":"com.community.mbox.in","version_name":"3.0.03.0529.03","version_code":50020042,"os":"android","os_version":"16","device_id":"{self.device_id}","install_store":"ps","gaid":"d7578036d13336cc","brand":"{brand}","model":"{model}","system_language":"en","net":"NETWORK_WIFI","region":"IN","timezone":"Asia/Calcutta","sp_code":""}}',
                    "x-client-status": "0"
                }
                if token:
                    headers["Authorization"] = f"Bearer {token}"

                try:
                    resp = await client.post(url, headers=headers, content=body_str)
                    self._persist_token_from_header(resp.headers.get("x-user"))
                    if resp.status_code == 200:
                        data = resp.json()
                        results = data.get("data", {}).get("results", [])
                        matched = []
                        for res in results:
                            for subject in res.get("subjects", []):
                                matched.append({
                                    "id": subject.get("subjectId"),
                                    "title": subject.get("title"),
                                    "poster": subject.get("cover", {}).get("url"),
                                    "type": "movie" if subject.get("subjectType", 1) == 1 else "tv",
                                    "rating": subject.get("imdbRatingValue")
                                })
                        if matched:
                            return matched
                except Exception as e:
                    logger.error(f"MovieBox search error for query '{q}': {e}")
        return []

    async def get_links(self, subject_id: str, season: int = 0, episode: int = 0) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            host = await self._get_working_host(client)
            token = await self._get_cached_token(client, host)
            brand, model = random_brand_model()

            subject_url = f"{host}/wefeed-mobile-bff/subject-api/get?subjectId={subject_id}"
            x_ct = generate_x_client_token()
            x_sig = generate_x_tr_signature("GET", "application/json", "application/json", subject_url)
            headers = {
                "user-agent": f"com.community.oneroom/50020088 (Linux; U; Android 13; en_US; {brand}; Build/TQ3A.230901.001; Cronet/145.0.7582.0)",
                "accept": "application/json",
                "content-type": "application/json",
                "x-client-token": x_ct,
                "x-tr-signature": x_sig,
                "x-client-status": "0"
            }
            if token:
                headers["Authorization"] = f"Bearer {token}"

            subject_ids_to_check = [(subject_id, "Original")]
            try:
                resp = await client.get(subject_url, headers=headers)
                self._persist_token_from_header(resp.headers.get("x-user"))
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    for dub in data.get("dubs", []):
                        sid = dub.get("subjectId")
                        lan = dub.get("lanName", "Audio")
                        if sid and sid != subject_id:
                            subject_ids_to_check.append((sid, lan))
            except Exception as e:
                logger.error(f"MovieBox subject get error: {e}")

            extracted_sources = []
            for sid, language in subject_ids_to_check:
                play_url = f"{host}/wefeed-mobile-bff/subject-api/play-info?subjectId={sid}&se={season}&ep={episode}"
                pct = generate_x_client_token()
                psig = generate_x_tr_signature("GET", "application/json", "application/json", play_url)
                p_headers = {
                    "user-agent": headers["user-agent"],
                    "accept": "application/json",
                    "content-type": "application/json",
                    "x-client-token": pct,
                    "x-tr-signature": psig,
                    "x-client-status": "0"
                }
                if token:
                    p_headers["Authorization"] = f"Bearer {token}"

                try:
                    presp = await client.get(play_url, headers=p_headers)
                    if presp.status_code == 200:
                        pdata = presp.json().get("data", {})
                        for stream in pdata.get("streams", []):
                            s_url = stream.get("url")
                            if not s_url:
                                continue
                            quality = stream.get("resolutions", "1080p")
                            extracted_sources.append({
                                "provider": "MovieBox",
                                "url": s_url,
                                "quality": quality,
                                "language": language,
                                "source_type": "official_watch_url"
                            })
                except Exception as e:
                    logger.error(f"MovieBox play-info error for sid {sid}: {e}")

            return extracted_sources
