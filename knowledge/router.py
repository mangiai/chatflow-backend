from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
import tempfile
from knowledge import service, schemas
from core.db import get_db

router = APIRouter(prefix="/knowledge", tags=["Knowledge Studio"])

@router.post("/upload", response_model=schemas.UploadResponse)
def upload_knowledge(business_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    text = service.extract_text(tmp_path)
    record = service.upload_file(db, business_id, file.filename, text)
    return {"id": str(record.id), "file_name": record.file_name, "message": "File uploaded & processed successfully"}

@router.post("/train")
def train_bot(business_id: str, db: Session = Depends(get_db)):
    return service.train_business_knowledge(db, business_id)

@router.post("/test")
def test_agent(payload: schemas.QuestionInput):
    response = service.answer_query(payload.business_id, payload.query)
    return {"response": response}
