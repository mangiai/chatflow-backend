from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UploadResponse(BaseModel):
    id: str
    file_name: str
    message: str


class QuestionInput(BaseModel):
    business_id: str
    query: str


class ManualQAInput(BaseModel):
    business_id: str
    question: str
    answer: str


class TrainResponse(BaseModel):
    message: str

class TrainRequest(BaseModel):
    business_id: str


class ManualQAResponse(BaseModel):
    id: str
    question: str
    answer: str
    created_at: datetime

class ManualQAListResponse(BaseModel):
    message: str
    data: List[ManualQAResponse]