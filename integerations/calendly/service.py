import os, secrets
from datetime import datetime, timedelta, timezone
import httpx
from sqlalchemy.orm import Session
from uuid import UUID
from .models import CalendlyCredential
from dotenv import load_dotenv
load_dotenv()

AUTH_URL = os.getenv("CALENDLY_AUTH_URL", "https://auth.calendly.com/oauth/authorize")
TOKEN_URL = os.getenv("CALENDLY_TOKEN_URL", "https://auth.calendly.com/oauth/token")
API_BASE = os.getenv("CALENDLY_API_BASE", "https://api.calendly.com")

CLIENT_ID = os.getenv("CALENDLY_CLIENT_ID")
CLIENT_SECRET = os.getenv("CALENDLY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("CALENDLY_REDIRECT_URI")

def _now(): return datetime.now(timezone.utc)
def _exp_from(expires_in:int): return _now() + timedelta(seconds=max(0, expires_in - 60))

def build_authorize_url(business_id: UUID) -> tuple[str, str]:
    if not (CLIENT_ID and REDIRECT_URI): raise AssertionError("Calendly env vars missing")
    state = f"{business_id}:{secrets.token_urlsafe(16)}"
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "state": state,
    }
    qp = "&".join([f"{k}={httpx.QueryParams({k:v})[k]}" for k,v in params.items()])
    return f"{AUTH_URL}?{qp}", state

def _post_form(url:str, data:dict) -> dict:
    with httpx.Client(timeout=20) as c:
        r = c.post(url, data=data)
        r.raise_for_status()
        return r.json()

def _exchange_code_for_token(code:str) -> dict:
    return _post_form(TOKEN_URL, {
        "grant_type":"authorization_code",
        "client_id":CLIENT_ID,
        "client_secret":CLIENT_SECRET,
        "redirect_uri":REDIRECT_URI,
        "code":code
    })

def _refresh_access_token(refresh_token:str) -> dict:
    return _post_form(TOKEN_URL, {
        "grant_type":"refresh_token",
        "client_id":CLIENT_ID,
        "client_secret":CLIENT_SECRET,
        "refresh_token":refresh_token
    })

def _save_token(db:Session, business_id:UUID, p:dict) -> CalendlyCredential:
    cred = db.query(CalendlyCredential).filter_by(business_id=business_id).first()
    if not cred:
        cred = CalendlyCredential(business_id=business_id, access_token=p["access_token"])
        db.add(cred)
    cred.access_token = p["access_token"]
    if "refresh_token" in p and p["refresh_token"]:
        cred.refresh_token = p["refresh_token"]
    if "expires_in" in p and p["expires_in"]:
        cred.expires_at = _exp_from(int(p["expires_in"]))
    cred.owner = p.get("owner")
    cred.organization = p.get("organization")
    cred.scope = p.get("scope")
    db.commit(); db.refresh(cred)
    return cred

def upsert_token_from_code(db:Session, business_id:UUID, code:str) -> CalendlyCredential:
    payload = _exchange_code_for_token(code)
    return _save_token(db, business_id, payload)

def get_valid_token(db:Session, business_id:UUID) -> str:
    cred = db.query(CalendlyCredential).filter_by(business_id=business_id).first()
    if not cred: raise ValueError("Calendly not connected")
    if cred.expires_at and cred.expires_at <= _now():
        if not cred.refresh_token: raise ValueError("Token expired and no refresh token")
        payload = _refresh_access_token(cred.refresh_token)
        cred = _save_token(db, business_id, payload)
    return cred.access_token

def get_status(db:Session, business_id:UUID) -> dict:
    cred = db.query(CalendlyCredential).filter_by(business_id=business_id).first()
    if not cred: return {"connected":False, "owner":None, "expires_at":None}
    return {"connected":True, "owner":cred.owner, "expires_at":cred.expires_at}

def fetch_event_types(db: Session, business_id: UUID) -> list[dict]:
    token = get_valid_token(db, business_id)
    headers = {"Authorization": f"Bearer {token}"}

    # 🔍 Get Calendly credential record for this business
    cred = db.query(CalendlyCredential).filter_by(business_id=business_id).first()

    # Prefer user if available, else organization
    if cred and cred.owner:
        url = f"{API_BASE}/event_types?user={cred.owner}"
    elif cred and cred.organization:
        url = f"{API_BASE}/event_types?organization={cred.organization}"
    else:
        url = f"{API_BASE}/event_types"

    print("📡 Fetching Calendly event types from:", url)  # Debugging

    with httpx.Client(timeout=20) as c:
        r = c.get(url, headers=headers)
        if r.status_code != 200:
            # Log full Calendly error for easier debugging
            print("❌ Calendly API error:", r.text)
            r.raise_for_status()
        data = r.json()

    items = data.get("collection") or data.get("data") or []
    return [
        {
            "uri": it.get("uri", ""),
            "name": it.get("name"),
            "slug": it.get("slug"),
            "kind": it.get("kind"),
            "scheduling_url": it.get("scheduling_url"),
            "active": it.get("active", True),
        }
        for it in items
    ]



def get_scheduling_url_for_event_type(db:Session, business_id:UUID, event_type_uri:str) -> str:
    token = get_valid_token(db, business_id)
    headers = {"Authorization": f"Bearer {token}"}
    # accept full URI or id suffix
    url = event_type_uri if event_type_uri.startswith("http") else f"{API_BASE}/event_types/{event_type_uri.split('/')[-1]}"
    with httpx.Client(timeout=20) as c:
        r = c.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
    resource = data.get("resource") or data.get("data") or data
    sched = resource.get("scheduling_url")
    if not sched: raise ValueError("No scheduling_url found")
    return sched
