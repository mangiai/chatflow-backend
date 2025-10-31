from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.db import Base, engine
from auth.router import router as auth_router
from knowledge.router import router as knowledge_router
from business.router import router as business_router
from widget.router import router as widget_router
from integerations.calendly.router import router as calendly_router
from dotenv import load_dotenv
load_dotenv()


Base.metadata.create_all(bind=engine)

app = FastAPI(title="ChatFlow Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(knowledge_router)
app.include_router(business_router)
app.include_router(widget_router)
app.include_router(calendly_router)

@app.get("/health")
def health():
    return {"status": "ok"}
