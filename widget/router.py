from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.db import get_db
from widget import service
from widget.schemas import WidgetSettingsCreate, WidgetSettingsResponse, WidgetQuery, WidgetQueryResponse
from uuid import UUID

router = APIRouter(prefix="/widget", tags=["Widget"])

# -----------------------------------------------------
# Save / Update Widget Settings
# -----------------------------------------------------
@router.post("/settings")
def create_or_update_widget_settings(payload: WidgetSettingsCreate, db: Session = Depends(get_db)):
    return service.save_widget_settings(db, payload)

# -----------------------------------------------------
# Fetch Widget Settings by Business ID
# -----------------------------------------------------
@router.get("/settings/{business_id}", response_model=WidgetSettingsResponse)
def get_settings(business_id: UUID, db: Session = Depends(get_db)):
    return service.get_widget_settings(db, business_id)

# -----------------------------------------------------
# Widget Query Endpoint (Chat Message)
# -----------------------------------------------------
@router.post("/query", response_model=WidgetQueryResponse)
def chat_with_widget(payload: WidgetQuery, db: Session = Depends(get_db)):
    """
    Endpoint used by the embedded website widget.
    Sends user message -> returns AI answer based on knowledge & manual QA.
    """
    return service.handle_widget_query(db, payload.business_id, payload.query)
