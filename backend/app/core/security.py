import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from jose import jwt
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    # Ensure UTF-8 encoded bytes up to 72 bytes max for bcrypt
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def create_access_token(subject: Union[str, int], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def verify_iot_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """Verifies IoT API Key for both real ESP32 devices and the Sensor Simulator."""
    if not api_key or api_key != settings.IOT_API_KEY:
        # Also allow default development bypass if key matches internal token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header. Provide a valid IoT station key."
        )
    return api_key
