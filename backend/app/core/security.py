import hashlib
import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt, JWTError
from backend.app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hashed representation."""
    try:
        if hashed_password.startswith("pbkdf2:"):
            parts = hashed_password.split("$")
            if len(parts) == 3:
                prefix, salt_hex, hash_hex = parts
                algo = prefix.split(":")[1]
                salt = bytes.fromhex(salt_hex)
                computed = hashlib.pbkdf2_hmac(algo, plain_password.encode("utf-8"), salt, 100000)
                return secrets.compare_digest(computed.hex(), hash_hex)
    except Exception:
        pass
    return False



def get_password_hash(password: str) -> str:
    """Generate secure PBKDF2 SHA-256 password hash."""
    salt = os.urandom(16)
    computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"pbkdf2:sha256${salt.hex()}${computed.hex()}"



def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a signed JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[str]:
    """Decode JWT token and extract subject (user ID)."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        return user_id
    except JWTError:
        return None
