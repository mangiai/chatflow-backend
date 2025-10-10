from sqlalchemy.orm import Session
from business.models import Business
from business.schemas import BusinessCreate


def create_business(db: Session, owner_id: str, payload: BusinessCreate):
    business = Business(owner_id=owner_id, **payload.dict())
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


def get_business_by_owner(db: Session, owner_id: str):
    return db.query(Business).filter(Business.owner_id == owner_id, Business.is_active == True).first()
