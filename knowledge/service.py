# knowledge/service.py
# ----------------------------------------------------
# Cleaned & Organized Version — 2025 Edition
# ----------------------------------------------------

import uuid
import fitz
import docx2txt
from datetime import datetime
from sqlalchemy.orm import Session
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from langchain_community.vectorstores import Qdrant

from core.config import settings
from core.db import get_db
from knowledge.models import Knowledge, ManualQA


from typing import Optional, List
from langchain_qdrant import Qdrant as QdrantVS
from langchain_core.prompts import PromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

from core.config import settings
openaikey=settings.OPENAI_API_KEY
# Helper: infer which payload key holds the chunk text
POSSIBLE_TEXT_KEYS = ("page_content", "text", "content", "chunk", "body", "document", "raw_text")

# ----------------------------------------------------
# Qdrant Setup
# ----------------------------------------------------
qdrant = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)

def ensure_collection():
    """Ensure Qdrant collection and index exist."""
    try:
        collections = [c.name for c in qdrant.get_collections().collections]
        if "chatflow_vectors" not in collections:
            qdrant.create_collection(
                collection_name="chatflow_vectors",
                vectors_config=qmodels.VectorParams(size=1536, distance=qmodels.Distance.COSINE),
            )
            print("✅ Created Qdrant collection 'chatflow_vectors'")

        # Ensure payload index for filtering
        qdrant.create_payload_index(
            collection_name="chatflow_vectors",
            field_name="business_id",
            field_schema="keyword",
        )
    except Exception as e:
        if "already exists" not in str(e):
            print(f"⚠️ ensure_collection warning: {e}")

ensure_collection()


# ----------------------------------------------------
# 1. Text Extraction
# ----------------------------------------------------
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


# ----------------------------------------------------
# 2. Save Uploaded File to DB
# ----------------------------------------------------
def upload_file(db: Session, business_id: str, file_name: str, text: str):
    record = Knowledge(business_id=business_id, file_name=file_name, content=text)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ----------------------------------------------------
# 3. Add Manual Q/A
# ----------------------------------------------------
def add_manual_qa(db: Session, payload):
    record = ManualQA(
        id=uuid.uuid4(),
        business_id=payload.business_id,
        question=payload.question,
        answer=payload.answer,
        created_at=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": str(record.id), "message": "✅ Manual Q/A saved successfully."}


# ----------------------------------------------------
# 4. Train Knowledge (Docs + Manual QAs)
# ----------------------------------------------------
def train_business_knowledge(db: Session, business_id: str):
    docs = db.query(Knowledge).filter(Knowledge.business_id == business_id).all()
    qas = db.query(ManualQA).filter(ManualQA.business_id == business_id).all()

    if not docs and not qas:
        return {"message": "⚠️ No documents or Q/A found for this business."}

    # Combine texts
    doc_texts = [d.content for d in docs]
    qa_texts = [f"Q: {q.question}\nA: {q.answer}" for q in qas]
    combined_text = " ".join(doc_texts + qa_texts)

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_text(combined_text)

    vectors = [embeddings.embed_query(chunk) for chunk in chunks]

    # ✅ Include both business_id and actual text payload
    payloads = [{"business_id": str(business_id), "page_content": chunk} for chunk in chunks]

    qdrant.upsert(
        collection_name="chatflow_vectors",
        points=[
            qmodels.PointStruct(
                id=str(uuid.uuid4()),
                vector=v,
                payload=p,
            )
            for v, p in zip(vectors, payloads)
        ],
    )

    print(f"✅ Added {len(chunks)} chunks with text payloads for business {business_id}")
    return {"message": f"✅ Training completed for {len(chunks)} chunks with full context."}



def get_manual_qa(db: Session, business_id: str):
    """
    Fetch all manual Q/A entries for a specific business.
    """
    qas = (
        db.query(ManualQA)
        .filter(ManualQA.business_id == business_id)
        .order_by(ManualQA.created_at.desc())
        .all()
    )

    if not qas:
        return {"message": "⚠️ No Q/A entries found for this business.", "data": []}

    results = [
        {
            "id": str(qa.id),
            "question": qa.question,
            "answer": qa.answer,
            "created_at": qa.created_at.isoformat(),
        }
        for qa in qas
    ]

    return {"message": f"✅ Found {len(results)} Q/A entries.", "data": results}




# ----------------------------------------------------
# 5. Query Chatbot
# ----------------------------------------------------

def _infer_text_key(sample_payload: dict) -> str:
    if not isinstance(sample_payload, dict):
        return "page_content"
    for k in POSSIBLE_TEXT_KEYS:
        v = sample_payload.get(k, None)
        if isinstance(v, str) and v.strip():
            return k
    # default to page_content if nothing fits
    return "page_content"

def answer_query(business_id: str, query: str):
    try:
        print(f"🔍 Query received for business={business_id}: '{query}'")

        # --- 1️⃣ Manual Q/A first (case-insensitive contains, either direction) ---
        db: Session = next(get_db())
        manual_qas = db.query(ManualQA).filter(ManualQA.business_id == business_id).all()
        qnorm = (query or "").strip().lower()
        for qa in manual_qas:
            qqa = (qa.question or "").lower()
            if not qqa:
                continue
            if qnorm in qqa or qqa in qnorm:
                db.close()
                print(f"✅ Answered from Manual QA: {qa.question}")
                return {"result": {"response": {"query": query, "result": qa.answer, "source": "manual_qa"}}}
        db.close()

        # --- 2️⃣ Probe Qdrant for payload shape, then set up vectorstore with proper keys ---
        scroll_res = qdrant.scroll(
            collection_name="chatflow_vectors",
            limit=3,
            with_payload=True,
            scroll_filter=qmodels.Filter(
                must=[qmodels.FieldCondition(
                    key="business_id",
                    match=qmodels.MatchValue(value=str(business_id))
                )]
            ),
        )
        points = scroll_res[0] if scroll_res and len(scroll_res) > 0 else []
        print(f"🔍 Found {len(points)} stored points in Qdrant for business_id={business_id}")

        sample_payload = points[0].payload if points else {}
        text_key = _infer_text_key(sample_payload)
        print(f"🧩 Using content_payload_key='{text_key}'")

        vectorstore = QdrantVS(
            client=qdrant,
            collection_name="chatflow_vectors",
            embeddings=embeddings,             # your existing embeddings
            content_payload_key=text_key,      # 👈 critical fix
            metadata_payload_key="metadata",   # adjust if you used a different meta field
        )

        retriever = vectorstore.as_retriever(
            search_kwargs={
                "filter": qmodels.Filter(
                    must=[qmodels.FieldCondition(
                        key="business_id",
                        match=qmodels.MatchValue(value=str(business_id))
                    )]
                ),
                "k": 8,
            }
        )

        # Non-deprecated retrieval
        results: List = retriever.invoke(query)  # returns List[Document]
        print(f"🔍 Retrieved {len(results)} chunks (pre-filter)")

        # --- 3️⃣ Guard against bad docs (None/empty page_content) ---
        good_docs = []
        bad_count = 0
        for d in results:
            try:
                if hasattr(d, "page_content") and isinstance(d.page_content, str) and d.page_content.strip():
                    good_docs.append(d)
                else:
                    bad_count += 1
            except Exception:
                bad_count += 1
        if bad_count:
            print(f"⚠️ Skipped {bad_count} chunks with missing/invalid page_content")

        if not good_docs:
            return {
                "result": {
                    "response": {
                        "query": query,
                        "result": "No relevant context found in the knowledge base.",
                        "source": "none"
                    }
                }
            }

        # --- 4️⃣ Prompt + chain ---
        template = (
            "You are an AI assistant that answers questions based on the provided business documents.\n\n"
            "Context:\n{context}\n\n"
            "Question: {input}\n\n"
            "If the answer is not explicitly stated, respond with a helpful summary of the relevant information from the context."
        )

        prompt = PromptTemplate(
            input_variables=["context", "input"],
            template=template
        )
       
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0,
            openai_api_key=openaikey
        )

        document_chain = create_stuff_documents_chain(
            llm=llm,
            prompt=prompt,
            document_variable_name="context",
        )

        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        response = retrieval_chain.invoke({"input": query, "context": good_docs})
        final_result = response.get("answer") or response.get("output") or str(response)

        print(f"🧠 Final Answer: {final_result}")

        return {
            "result": {
                "response": {
                    "query": query,
                    "result": final_result,
                    "source": "documents"
                }
            }
        }

    except Exception as e:
        print(f"❌ answer_query error: {e}")
        return {
            "result": {
                "response": {
                    "query": query,
                    "result": f"Error: {str(e)}",
                    "source": "error"
                }
            }
        }
    


# ----------------------------------------------------
# 6. Delete Knowledge / QAs
# ----------------------------------------------------
def delete_knowledge(db: Session, knowledge_id: str):
    record = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
    if not record:
        return {"message": "❌ Knowledge file not found."}

    db.delete(record)
    db.commit()

    try:
        qdrant.delete(
            collection_name="chatflow_vectors",
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[qmodels.FieldCondition(key="business_id", match=qmodels.MatchValue(value=str(record.business_id)))]
                )
            ),
        )
    except Exception as e:
        print(f"⚠️ Failed to delete vectors from Qdrant: {e}")

    return {"message": f"🗑️ Deleted knowledge file '{record.file_name}' successfully."}


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
                    must=[qmodels.FieldCondition(key="business_id", match=qmodels.MatchValue(value=str(record.business_id)))]
                )
            ),
        )
    except Exception as e:
        print(f"⚠️ Failed to delete Qdrant vectors: {e}")

    return {"message": "🗑️ Deleted Q/A pair successfully."}
