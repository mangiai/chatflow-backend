from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from uuid import UUID
from core.db import get_db
from . import service
from .schemas import OAuthStartResponse, CalendlyStatus, EventTypesResponse, ScheduleLinkRequest, ScheduleLinkResponse

router = APIRouter(prefix="/integrations/calendly", tags=["Calendly"])

@router.get("/status", response_model=CalendlyStatus)
def calendly_status(business_id: UUID = Query(...), db: Session = Depends(get_db)):
    return service.get_status(db, business_id)

@router.get("/oauth/start", response_model=OAuthStartResponse)
def oauth_start(business_id: UUID = Query(...)):
    try:
        authorize_url, state = service.build_authorize_url(business_id)
        return {"authorize_url": authorize_url, "state": state}
    except AssertionError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/oauth/callback")
def oauth_callback(code: str, state: str, db: Session = Depends(get_db)):
    try:
        # Extract business_id from state
        business_id = UUID(state.split(":")[0])

        # Save Calendly tokens
        service.upsert_token_from_code(db, business_id, code)

        # Redirect to frontend after success
        frontend_url = f"http://localhost:8080/dashboard/integrations?connected=calendly&business_id={business_id}"
        return RedirectResponse(url=frontend_url)

    except Exception as e:
        # Optional error fallback redirect
        error_url = f"http://localhost:8080/dashboard/integrations?error={str(e)}"
        return RedirectResponse(url=error_url)

@router.get("/event-types", response_model=EventTypesResponse)
def list_event_types(business_id: UUID = Query(...), db: Session = Depends(get_db)):
    try:
        items = service.fetch_event_types(db, business_id)
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/schedule-link", response_model=ScheduleLinkResponse)
def get_schedule_link(payload: ScheduleLinkRequest, business_id: UUID = Query(...), db: Session = Depends(get_db)):
    try:
        url = service.get_scheduling_url_for_event_type(db, business_id, payload.event_type_uri)
        return {"scheduling_url": url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
