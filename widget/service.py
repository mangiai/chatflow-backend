from sqlalchemy.orm import Session
from fastapi import HTTPException
from widget.models import WidgetSettings
from widget.schemas import WidgetSettingsCreate, WidgetQueryResponse
from knowledge.service import answer_query  # ✅ Using your existing logic

# -----------------------------------------------------
# Save / Update Widget Settings
# -----------------------------------------------------
def save_widget_settings(db: Session, payload: WidgetSettingsCreate):
    existing = db.query(WidgetSettings).filter_by(business_id=payload.business_id).first()

    if existing:
        for field, value in payload.dict().items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return {"message": "Widget settings updated successfully."}

    new_setting = WidgetSettings(**payload.dict())
    db.add(new_setting)
    db.commit()
    db.refresh(new_setting)
    return {"message": "Widget settings created successfully."}

# -----------------------------------------------------
# Fetch Widget Settings
# -----------------------------------------------------
def get_widget_settings(db: Session, business_id):
    settings = db.query(WidgetSettings).filter_by(business_id=business_id).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Widget settings not found.")
    return settings

# -----------------------------------------------------
# Handle Widget Query (calls Knowledge logic)
# -----------------------------------------------------
def handle_widget_query(db: Session, business_id, query: str) -> WidgetQueryResponse:
    try:
        # ✅ call existing answer_query() function from knowledge/service.py
        result = answer_query(str(business_id), query)

        # normalize the output regardless of nested dicts
        if isinstance(result, dict):
            answer = (
                result.get("result", {}).get("response", {}).get("result")
                or result.get("response", {}).get("result")
                or str(result)
            )
        else:
            answer = str(result)

        return WidgetQueryResponse(answer=answer)

    except Exception as e:
        return WidgetQueryResponse(answer=f"Error: {str(e)}")
