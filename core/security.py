import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from hashlib import sha256
from core.config import settings  # ✅ import your Settings class

# Initialize password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==========================
# PASSWORD UTILITIES
# ==========================

def hash_password(password: str):
    """Hash a password using bcrypt, safely handling long passwords."""
    if len(password.encode()) > 72:
        password = sha256(password.encode()).hexdigest()
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    """Verify a plain password against the stored hash."""
    if len(plain_password.encode()) > 72:
        plain_password = sha256(plain_password.encode()).hexdigest()
    return pwd_context.verify(plain_password, hashed_password)

# ==========================
# JWT TOKEN UTILITIES
# ==========================

def create_access_token(data: dict):
    """Generate a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token

def verify_access_token(token: str):
    """Verify JWT validity and decode payload."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
