import base64
import hashlib
import hmac
import json
import random
import time
from urllib.parse import urlparse, parse_qsl, urlencode

SECRET_KEY_DEFAULT = base64.b64decode(b"NzZpUmwwN3MweFNOOWpxbUVXQXQ3OUVCSlp1bElRSXNWNjRGWnIyTw==")
SECRET_KEY_ALT = base64.b64decode(b"WHFuMm5uTzQxL0w5Mm8xaXVYaFNMSFRiWHZZNFo1Wlo2Mm04bVNMQQ==")

def md5_hex(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()

def reverse_string(input_str: str) -> str:
    return input_str[::-1]

def generate_x_client_token(hardcoded_timestamp: int = None) -> str:
    timestamp = str(hardcoded_timestamp or int(time.time() * 1000))
    reversed_ts = reverse_string(timestamp)
    h = md5_hex(reversed_ts.encode('utf-8'))
    return f"{timestamp},{h}"

def generate_device_id() -> str:
    return "".join(random.choices("0123456789abcdef", k=32))

BRAND_MODELS = {
    "Samsung": ["SM-S918B", "SM-A528B", "SM-M336B"],
    "Xiaomi": ["2201117TI", "M2012K11AI", "Redmi Note 11"],
    "OnePlus": ["LE2111", "CPH2449", "IN2023"],
    "Google": ["Pixel 6", "Pixel 7", "Pixel 8"],
    "Realme": ["RMX3085", "RMX3360", "RMX3551"]
}

def random_brand_model() -> tuple:
    brand = random.choice(list(BRAND_MODELS.keys()))
    model = random.choice(BRAND_MODELS[brand])
    return brand, model

def build_canonical_string(method: str, accept: str, content_type: str, url: str, body: str = None, timestamp: int = None) -> str:
    parsed = urlparse(url)
    path = parsed.path or ""

    # Sort query parameters
    query_params = parse_qsl(parsed.query, keep_blank_values=True)
    query_params.sort(key=lambda x: x[0])
    query_string = urlencode(query_params, doseq=True) if query_params else ""

    canonical_url = f"{path}?{query_string}" if query_string else path

    body_bytes = body.encode('utf-8') if body else b""
    body_hash = md5_hex(body_bytes[:102400]) if body_bytes else ""
    body_length = str(len(body_bytes)) if body_bytes else ""

    ts = timestamp or int(time.time() * 1000)

    return f"{method.upper()}\n{accept or ''}\n{content_type or ''}\n{body_length}\n{ts}\n{body_hash}\n{canonical_url}"

def generate_x_tr_signature(method: str, accept: str, content_type: str, url: str, body: str = None, use_alt_key: bool = False, hardcoded_timestamp: int = None) -> str:
    timestamp = hardcoded_timestamp or int(time.time() * 1000)
    canonical = build_canonical_string(method, accept, content_type, url, body, timestamp)
    secret = SECRET_KEY_ALT if use_alt_key else SECRET_KEY_DEFAULT

    signature = hmac.new(secret, canonical.encode('utf-8'), hashlib.md5).digest()
    signature_b64 = base64.b64encode(signature).decode('utf-8')

    return f"{timestamp}|2|{signature_b64}"

def decode_jwt_expiry(token: str) -> int:
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return 0
        payload = parts[1]
        padded = payload.replace("-", "+").replace("_", "/") + "=" * ((4 - len(payload) % 4) % 4)
        decoded = base64.b64decode(padded).decode('utf-8')
        return json.loads(decoded).get("exp", 0)
    except Exception:
        return 0

def is_token_valid(token: str) -> bool:
    if not token:
        return False
    exp = decode_jwt_expiry(token)
    return exp > int(time.time()) + 3600
