import json
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet
from jose import jwt, JWTError
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire},
        settings.jwt_secret,
        algorithm=ALGORITHM,
    )


def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": str(user_id), "type": "refresh", "exp": expire},
        settings.jwt_secret,
        algorithm=ALGORITHM,
    )


def decode_token(token: str) -> dict:
    """Raises JWTError on invalid or expired token."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])


def encrypt_garmin_credentials(username: str, password: str) -> str:
    f = Fernet(settings.fernet_key.encode())
    payload = json.dumps({"username": username, "password": password}).encode()
    return f.encrypt(payload).decode()


def decrypt_garmin_credentials(encrypted: str) -> tuple[str, str]:
    f = Fernet(settings.fernet_key.encode())
    data = json.loads(f.decrypt(encrypted.encode()))
    return data["username"], data["password"]
