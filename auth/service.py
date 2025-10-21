from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt


from core.db import get_db
from core.security import hash_password, verify_password, create_access_token
from core.config import settings
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


# ===============================
# GET CURRENT USER 
# ===============================



# Token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

SECRET_KEY = settings.JWT_SECRET
ALGORITHM = settings.JWT_ALGORITHM


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Verifies JWT token, decodes it, and returns the current user object.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user
