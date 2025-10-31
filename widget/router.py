from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, HTMLResponse
from sqlalchemy.orm import Session
from core.db import get_db
from widget import service
from widget.models import WidgetChatSession, WidgetChatMessage
from widget.schemas import (
    WidgetSettingsCreate,
    WidgetSettingsResponse,
    WidgetQuery,
    WidgetQueryResponse,
    WidgetChatSessionResponse,
    WidgetChatMessageResponse
)
from uuid import UUID

router = APIRouter(prefix="/widget", tags=["Widget"])

# -----------------------------------------------------
# 1️⃣ Save / Update Widget Settings
# -----------------------------------------------------
@router.post("/settings")
def create_or_update_widget_settings(
    payload: WidgetSettingsCreate, db: Session = Depends(get_db)
):
    return service.save_widget_settings(db, payload)


# -----------------------------------------------------
# 2️⃣ Fetch Widget Settings by Business ID
# -----------------------------------------------------
@router.get("/settings/{business_id}", response_model=WidgetSettingsResponse)
def get_settings(business_id: UUID, db: Session = Depends(get_db)):
    return service.get_widget_settings(db, business_id)


# -----------------------------------------------------
# 3️⃣ Widget Query Endpoint (Chat Message)
# -----------------------------------------------------
@router.post("/query", response_model=WidgetQueryResponse)
def chat_with_widget(payload: WidgetQuery, db: Session = Depends(get_db)):
    """
    Endpoint used by the embedded website widget.
    Sends user message -> returns AI answer based on knowledge & manual QA.
    """
    return service.handle_widget_query(db, payload.business_id, payload.query)


# -----------------------------------------------------
# 4️⃣ Widget Embedding Generation Script
# -----------------------------------------------------
@router.get("/embed.js")
def get_embed_script():
    """
    Returns a public JavaScript snippet that websites can embed.
    Uses localhost while developing.
    """
    script = """
    (function() {
      const currentScript = document.currentScript;
      const businessId = currentScript.getAttribute('data-business');
      if (!businessId) {
        console.error('ChatFlow Widget: Missing data-business attribute.');
        return;
      }

      // Localhost setup (change domain to production when deployed)
      const iframe = document.createElement('iframe');
      iframe.src = `http://localhost:8000/widget/chatbox?business_id=${businessId}`;
      iframe.style.position = 'fixed';
      iframe.style.bottom = '24px';
      iframe.style.right = '24px';
      iframe.style.width = '400px';
      iframe.style.height = '520px';
      iframe.style.border = 'none';
      iframe.style.zIndex = '999999';
      iframe.style.borderRadius = '12px';
      iframe.style.boxShadow = '0 2px 8px rgba(0,0,0,0.25)';
      iframe.setAttribute('allow', 'clipboard-write;');

      document.body.appendChild(iframe);
    })();
    """
    return Response(content=script, media_type="application/javascript")


# -----------------------------------------------------
# 5️⃣ Chatbox UI Page (Rendered Inside Iframe)
# -----------------------------------------------------
@router.get("/chatbox", response_class=HTMLResponse)
def render_chatbox(
    business_id: str,
    mode: str = "full",           # 👈 optional query param
    db: Session = Depends(get_db)
):
    """
    Serves chatbot HTML in two modes:
    - full: fullscreen chat experience
    - mini: compact embeddable widget
    """

    # Step 1: Fetch business widget settings
    settings = service.get_widget_settings(db, business_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Widget settings not found")

    # Step 2: Read key properties from settings
    bot_name = settings.bot_name or "ChatFlow Assistant"
    welcome_msg = settings.welcome_message or "Hi there 👋 How can I help you today?"
    primary_color = settings.theme.get("primary_color", "#8B5CF6") if settings.theme else "#8B5CF6"

    # Step 3: Set layout differences based on mode
    if mode == "mini":
        # Compact popup layout
        height = "480px"
        width = "420px"
        border_radius = "12px"
        show_header = False
        box_shadow = "0 2px 10px rgba(0,0,0,0.4)"
    else:
        # Full screen layout
        height = "100vh"
        width = "100vw"
        border_radius = "0"
        show_header = True
        box_shadow = "none"

    # Step 4: Construct HTML dynamically
    html = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>{bot_name}</title>
        <style>
          body {{
            margin: 0;
            background: #0b0b0b;
            color: #fff;
            font-family: Inter, Arial, sans-serif;
          }}
          .chatbox {{
            width: {width};
            height: {height};
            border-radius: {border_radius};
            box-shadow: {box_shadow};
            display: flex;
            flex-direction: column;
          }}
          .header {{
            display: {'block' if show_header else 'none'};
            background: {primary_color};
            padding: 10px;
            text-align: center;
            font-weight: bold;
            border-top-left-radius: {border_radius};
            border-top-right-radius: {border_radius};
          }}
          /* Other CSS remains the same */
        </style>
      </head>
      <body>
        <div class="chatbox">
          <div class="header">{bot_name}</div>
          <div id="messages" class="messages">
            <div><strong>Bot:</strong> {welcome_msg}</div>
          </div>
          <!-- input field + JS -->
        </div>
      </body>
    </html>
    """

    return HTMLResponse(content=html)


@router.get("/chats/{business_id}", response_model=list[WidgetChatSessionResponse])
def get_chats(business_id: UUID, db: Session = Depends(get_db)):
    return db.query(WidgetChatSession).filter_by(business_id=business_id).all()


@router.get("/messages/{session_id}", response_model=list[WidgetChatMessageResponse])
def get_messages(session_id: UUID, db: Session = Depends(get_db)):
    return (
        db.query(WidgetChatMessage)
        .filter_by(session_id=session_id)
        .order_by(WidgetChatMessage.created_at)
        .all()
    )