from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
import tempfile, os

from knowledge import service, schemas
from core.db import get_db

router = APIRouter(prefix="/knowledge", tags=["Knowledge Studio"])


@router.post("/upload", response_model=schemas.UploadResponse)
def upload_knowledge(
    business_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF or DOCX files are supported.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    try:
        text = service.extract_text(tmp_path)
        record = service.upload_file(db, business_id, file.filename, text)
    finally:
        os.remove(tmp_path)

    return {"id": str(record.id), "file_name": record.file_name, "message": "File uploaded & processed successfully."}


@router.post("/qa")
def add_manual_qa(payload: schemas.ManualQAInput, db: Session = Depends(get_db)):
    return service.add_manual_qa(db, payload)


@router.post("/train", response_model=schemas.TrainResponse)
def train_bot(payload: schemas.TrainRequest, db: Session = Depends(get_db)):
    return service.train_business_knowledge(db, payload.business_id)



@router.post("/test")
def test_agent(payload: schemas.QuestionInput):
    result = service.answer_query(payload.business_id, payload.query)

    # Safely extract text from nested dicts
    if isinstance(result, dict):
        try:
            # Extract final answer string no matter how deeply nested
            answer = (
                result.get("response", {}).get("result")
                or result.get("result", {}).get("response", {}).get("result")
                or result.get("result", {}).get("result", {}).get("response", {}).get("result")
                or "I'm sorry, I couldn't find an answer."
            )
        except Exception:
            answer = str(result)
    else:
        answer = str(result)

    return {"result": answer}



@router.get("/qa/{business_id}", response_model=schemas.ManualQAListResponse)
def get_manual_qa(business_id: str, db: Session = Depends(get_db)):
    return service.get_manual_qa(db, business_id)


@router.delete("/upload/{knowledge_id}")
def delete_knowledge(knowledge_id: str, db: Session = Depends(get_db)):
    return service.delete_knowledge(db, knowledge_id)


@router.delete("/qa/{qa_id}")
def delete_manual_qa(qa_id: str, db: Session = Depends(get_db)):
    return service.delete_manual_qa(db, qa_id)
