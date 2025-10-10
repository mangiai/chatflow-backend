from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
import os
from dotenv import load_dotenv
load_dotenv()

client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))

# delete old collection
try:
    client.delete_collection("chatflow_vectors")
    print("🧹 Old collection deleted.")
except:
    pass

# recreate properly with keyword index ready
client.create_collection(
    collection_name="chatflow_vectors",
    vectors_config=qmodels.VectorParams(size=1536, distance=qmodels.Distance.COSINE),
)
client.create_payload_index(
    collection_name="chatflow_vectors",
    field_name="business_id",
    field_schema="keyword"
)
print("✅ Fresh chatflow_vectors collection created and indexed.")
