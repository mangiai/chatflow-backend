from pydantic import BaseModel
from typing import Optional

class UploadResponse(BaseModel):
    id: str
    file_name: str
    message: str

class QuestionInput(BaseModel):
    business_id: str
    query: str
