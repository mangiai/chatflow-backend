import os
from qdrant_client import QdrantClient
from dotenv import load_dotenv
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

points = client.scroll(
    collection_name="chatflow_vectors",
    limit=5,
    with_payload=True,
)

print("\n--- Sample Payloads in Qdrant ---")
for p in points[0]:
    print(p.payload)
