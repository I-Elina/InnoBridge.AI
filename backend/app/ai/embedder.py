from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.core.config import settings
import uuid

model = SentenceTransformer("all-MiniLM-L6-v2")

client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY,
)

COLLECTION_NAME = "papers"

def ensure_collection():
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

def embed_and_store(paper_id: str, title: str, abstract: str) -> str:
    ensure_collection()
    text = f"{title}. {abstract}"
    vector = model.encode(text).tolist()
    point_id = str(uuid.uuid4())
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[PointStruct(id=point_id, vector=vector, payload={"paper_id": paper_id})]
    )
    return point_id