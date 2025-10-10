import os
import fitz
import docx2txt
from sqlalchemy.orm import Session
from knowledge.models import Knowledge, ManualQA
from core.config import settings

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Qdrant
from langchain.chains import RetrievalQA
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

# --- ENV VARS ---
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Qdrant Setup ---
try:
    qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    print(f"✅ Connected to Qdrant at {QDRANT_URL}")
except Exception as e:
    print(f"❌ Qdrant connection failed: {e}")
    qdrant = None

def ensure_collection():
    if not qdrant:
        return
    try:
        collections = [c.name for c in qdrant.get_collections().collections]
        if "chatflow_vectors" not in collections:
            qdrant.create_collection(
                collection_name="chatflow_vectors",
                vectors_config=qmodels.VectorParams(size=1536, distance=qmodels.Distance.COSINE)
            )
            print("✅ Created Qdrant collection 'chatflow_vectors'")
    except Exception as e:
        print(f"⚠️ Qdrant collection check failed: {e}")

ensure_collection()

embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)


# --- 1. Extract Text ---
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
        raise ValueError("Unsupported file format. Use PDF or DOCX.")


# --- 2. Save File in DB ---
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


# --- 3. Save Manual Q/A ---
def add_manual_qa(db: Session, payload):
    record = ManualQA(
        business_id=payload.business_id,
        question=payload.question,
        answer=payload.answer
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": str(record.id), "message": "Manual Q/A saved successfully."}


# --- 4. Train Knowledge ---
def train_business_knowledge(db: Session, business_id: str):
    docs = db.query(Knowledge).filter(Knowledge.business_id == business_id).all()
    qas = db.query(ManualQA).filter(ManualQA.business_id == business_id).all()

    if not docs and not qas:
        return {"message": "No documents or Q/A found for this business."}

    # Combine texts
    doc_texts = [d.content for d in docs]
    qa_texts = [f"Q: {q.question}\nA: {q.answer}" for q in qas]
    combined_text = " ".join(doc_texts + qa_texts)

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_text(combined_text)

    Qdrant.from_texts(
        texts=chunks,
        embedding=embeddings,
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        collection_name="chatflow_vectors",
        metadata=[{"business_id": business_id} for _ in chunks]
    )

    return {"message": f"✅ Training completed for {len(chunks)} chunks."}


# --- 5. Query Chatbot ---
def answer_query(business_id: str, query: str):
    try:
        vectorstore = Qdrant(
            client=qdrant,
            collection_name="chatflow_vectors",
            embeddings=embeddings,
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

        llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name="gpt-3.5-turbo", temperature=0)
        qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

        return qa_chain.run(query)

    except Exception as e:
        print(f"❌ answer_query error: {e}")
        return {"error": str(e)}


# --- 6. Delete Uploaded Knowledge File ---
def delete_knowledge(db: Session, knowledge_id: str):
    record = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
    if not record:
        return {"message": "❌ Knowledge file not found."}

    # Remove from DB
    db.delete(record)
    db.commit()

    # Optional: remove from Qdrant vectors
    try:
        qdrant.delete(
            collection_name="chatflow_vectors",
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="business_id",
                            match=qmodels.MatchValue(value=str(record.business_id))
                        )
                    ]
                )
            )
        )
    except Exception as e:
        print(f"⚠️ Failed to delete vectors from Qdrant: {e}")

    return {"message": f"🗑️ Deleted knowledge file '{record.file_name}' successfully."}


# --- 7. Delete Manual Q/A ---
def delete_manual_qa(db: Session, qa_id: str):
    record = db.query(ManualQA).filter(ManualQA.id == qa_id).first()
    if not record:
        return {"message": "❌ Q/A entry not found."}

    db.delete(record)
    db.commit()

    try:
        qdrant.delete(
            collection_name="chatflow_vectors",
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="business_id",
                            match=qmodels.MatchValue(value=str(record.business_id))
                        )
                    ]
                )
            )
        )
    except Exception as e:
        print(f"⚠️ Failed to delete Qdrant vectors: {e}")

    return {"message": f"🗑️ Deleted Q/A pair successfully."}
