import pytest
from utils.crypto import (
    generate_x_client_token,
    generate_x_tr_signature,
    generate_device_id,
    random_brand_model,
    is_token_valid
)

def test_crypto_token():
    token = generate_x_client_token()
    assert "," in token
    parts = token.split(",")
    assert len(parts[0]) > 0
    assert len(parts[1]) == 32

def test_device_id():
    did = generate_device_id()
    assert len(did) == 32

def test_brand_model():
    brand, model = random_brand_model()
    assert brand in ["Samsung", "Xiaomi", "OnePlus", "Google", "Realme"]
    assert len(model) > 0

def test_signature():
    sig = generate_x_tr_signature("GET", "application/json", "application/json", "https://api.example.com/test")
    assert "|" in sig
    parts = sig.split("|")
    assert len(parts) == 3
    assert parts[1] == "2"

def test_token_validity():
    assert is_token_valid("") is False
    assert is_token_valid("invalid.jwt.token") is False
