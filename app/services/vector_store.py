from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.core.config import settings
import hashlib

def stub_embed(text: str) -> list[float]:
    """Stub embedding: deterministic from text hash. Replace with real model."""
    h = hashlib.sha256(text.encode()).digest()
    vec = [((b / 255.0) - 0.5) * 2 for b in h]  # 32-dim stub vector
    return vec

def get_qdrant() -> QdrantClient:
    return QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

async def vector_search(query: str, top_k: int = 5) -> list[dict]:
    client = get_qdrant()
    query_vec = stub_embed(query)
    try:
        results = client.search(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=query_vec,
            limit=top_k,
        )
        return [
            {"id": str(r.id), "score": r.score, "payload": r.payload or {}}
            for r in results
        ]
    except Exception:
        # Collection may not exist yet — return empty
        return []