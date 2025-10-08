import os
import fitz
import docx2txt
from sqlalchemy.orm import Session
from knowledge.models import Knowledge
from knowledge.schemas import UploadResponse
from core.config import settings

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Qdrant
from langchain.chains import RetrievalQA

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels


# ✅ Load environment variables safely
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ✅ Initialize Qdrant client
try:
    qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    print(f"✅ Connected to Qdrant at {QDRANT_URL}")
except Exception as e:
    print(f"❌ Failed to connect to Qdrant: {e}")

# ✅ Create collection (if not exists)
def ensure_collection():
    try:
        collections = [c.name for c in qdrant.get_collections().collections]
        if "chatflow_vectors" not in collections:
            qdrant.create_collection(
                collection_name="chatflow_vectors",
                vectors_config=qmodels.VectorParams(size=1536, distance=qmodels.Distance.COSINE)
            )
            print("✅ Qdrant collection 'chatflow_vectors' created.")
        else:
            print("✅ Qdrant collection 'chatflow_vectors' already exists.")
    except Exception as e:
        print(f"⚠️ Qdrant collection check failed: {e}")

ensure_collection()

# ✅ Initialize embedding model
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)


# 🧩 1. Extract text from PDF/DOCX
def extract_text(file_path: str):
    if file_path.endswith(".pdf"):
        text = ""
        with fitz.open(file_path) as pdf:
            for page in pdf:
                text += page.get_text()
        return text

    elif file_path.endswith(".docx"):
        return docx2txt.process(file_path)

    else:
        raise ValueError("Unsupported file format")


# 🧩 2. Save extracted content in DB
def upload_file(db: Session, business_id: str, file_name: str, text: str):
    record = Knowledge(
        business_id=business_id,
        file_name=file_name,
        content=text
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# 🧩 3. Train business knowledge into vector DB
def train_business_knowledge(db: Session, business_id: str):
    docs = db.query(Knowledge).filter(Knowledge.business_id == business_id).all()
    if not docs:
        return {"message": "No documents found for this business"}

    all_text = " ".join([d.content for d in docs])

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_text(all_text)

    Qdrant.from_texts(
        texts=chunks,
        embedding=embeddings,
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        collection_name="chatflow_vectors",
        metadata=[{"business_id": business_id} for _ in chunks]
    )

    return {"message": f"✅ Training completed for {len(chunks)} chunks."}


# 🧩 4. Ask questions to business-specific knowledge base
def answer_query(business_id: str, query: str):
    try:
        vectorstore = Qdrant(
            client=qdrant,
            collection_name="chatflow_vectors",
            embeddings=embeddings,
            content_payload_key="text",
            metadata_payload_key="metadata"
        )

        retriever = vectorstore.as_retriever(
            search_kwargs={
                "filter": qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="business_id",
                            match=qmodels.MatchValue(value=business_id)
                        )
                    ]
                )
            }
        )

        llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name="gpt-3.5-turbo")

        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever
        )

        response = qa_chain.run(query)
        return response

    except Exception as e:
        print(f"❌ Error in answer_query: {e}")
        return {"error": str(e)}
