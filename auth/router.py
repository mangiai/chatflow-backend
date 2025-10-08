from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from core.db import get_db
from core.security import verify_access_token
from auth import service, schemas

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup", response_model=schemas.Token)
def signup(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    user = service.create_user(db, payload)
    token = service.create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    return service.authenticate_user(db, payload)

@router.post("/logout")
def logout(request: Request):
    """Logout current user by invalidating their JWT."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = auth_header.split(" ")[1]
    payload = verify_access_token(token)

    if not payload or service.is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return service.logout_user(token)
