import pytest
from backend.auth import (
    hash_password, verify_password,
    create_access_token, decode_token,
    encrypt_garmin_credentials, decrypt_garmin_credentials,
)


def test_password_hash_and_verify():
    hashed = hash_password("mysecret")
    assert verify_password("mysecret", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_access_token_round_trip():
    token = create_access_token(42)
    payload = decode_token(token)
    assert payload["sub"] == "42"


def test_garmin_credentials_encryption():
    encrypted = encrypt_garmin_credentials("user@example.com", "garminpass")
    username, password = decrypt_garmin_credentials(encrypted)
    assert username == "user@example.com"
    assert password == "garminpass"
