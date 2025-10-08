from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from core.security import hash_password, verify_password, create_access_token
from auth.models import User
from auth.schemas import UserCreate, UserLogin

# ===============================
# SIGNUP & LOGIN
# ===============================

def create_user(db: Session, payload: UserCreate):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        business_name=payload.business_name,
        email=payload.email,
        password_hash=hash_password(payload.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, payload: UserLogin):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

# ===============================
# LOGOUT FLOW
# ===============================

TOKEN_BLACKLIST = set()

def logout_user(token: str):
    """Invalidate JWT by adding it to a blacklist."""
    TOKEN_BLACKLIST.add(token)
    return {"message": "Successfully logged out"}

def is_token_blacklisted(token: str) -> bool:
    """Check if JWT is blacklisted."""
    return token in TOKEN_BLACKLIST
