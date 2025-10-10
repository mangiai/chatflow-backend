from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.db import get_db
from auth.service import get_current_user     # <-- depends on your existing auth
from business import service, schemas

router = APIRouter(prefix="/business", tags=["Business"])


@router.post("/setup", response_model=schemas.BusinessResponse)
def setup_business(payload: schemas.BusinessCreate,
                   db: Session = Depends(get_db),
                   current_user=Depends(get_current_user)):
    existing = service.get_business_by_owner(db, current_user.id)
    if existing:
        raise HTTPException(status_code=400, detail="Business already exists for this user.")
    return service.create_business(db, current_user.id, payload)


@router.get("/current", response_model=schemas.BusinessResponse)
def get_current_business(db: Session = Depends(get_db),
                         current_user=Depends(get_current_user)):
    business = service.get_business_by_owner(db, current_user.id)
    if not business:
        raise HTTPException(status_code=404, detail="No business setup found.")
    return business
