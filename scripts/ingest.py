# scripts/ingest.py — Run this to populate your local Qdrant
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
)
import hashlib, uuid

# --- Stubbed embedding (replace with real model for production) ---
def stub_embed(text: str, dim: int = 384) -> list[float]:
    """Deterministic 384-dim stub. Replace with SentenceTransformers or OpenAI."""
    import struct, zlib
    seed = zlib.adler32(text.encode()) & 0xFFFFFFFF
    vec = []
    for i in range(dim):
        seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
        val = (seed / 0xFFFFFFFF) * 2 - 1
        vec.append(round(val, 6))
    norm = sum(x**2 for x in vec) ** 0.5
    return [x / norm for x in vec]  # unit-normalize


# --- Chunking ---
def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """Simple word-based chunker with overlap."""
    words = text.split()
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


# --- Setup ---
client = QdrantClient(host="localhost", port=6333)
COLLECTION = "documents"
VECTOR_DIM = 384

# Create collection if not exists
if COLLECTION not in [c.name for c in client.get_collections().collections]:
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
    )
    print(f"Created collection '{COLLECTION}'")

# --- Sample documents ---
documents = [
    {"id": "doc1", "title": "FastAPI Guide", "text": "FastAPI is a modern web framework for building APIs with Python 3.6+ based on standard Python type hints. It provides automatic interactive API documentation and is very fast."},
    {"id": "doc2", "title": "Kubernetes Overview", "text": "Kubernetes is an open-source container orchestration system. It automates deployment, scaling, and management of containerized applications across clusters of hosts."},
    {"id": "doc3", "title": "RAG Architecture", "text": "Retrieval-Augmented Generation combines a retrieval system with a language model. Documents are embedded, stored in a vector database, and retrieved at query time to ground LLM responses."},
]

# --- Ingest ---
points = []
for doc in documents:
    chunks = chunk_text(doc["text"])
    for idx, chunk in enumerate(chunks):
        vec = stub_embed(chunk)
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc['id']}-{idx}"))
        points.append(PointStruct(
            id=point_id,
            vector=vec,
            payload={
                "doc_id": doc["id"],
                "title": doc["title"],
                "chunk_index": idx,
                "text": chunk,
            }
        ))

client.upsert(collection_name=COLLECTION, points=points)
print(f"Ingested {len(points)} chunks from {len(documents)} documents")


# --- Search ---
def search(query: str, top_k: int = 5) -> list[dict]:
    query_vec = stub_embed(query)
    results = client.search(
        collection_name=COLLECTION,
        query_vector=query_vec,
        limit=top_k,
        with_payload=True,
    )
    return results

# --- Reranking ---
def rerank(results, query: str, alpha: float = 0.7) -> list:
    """
    Simple reranker: blend vector score + keyword overlap score.
    alpha: weight for vector score (1-alpha for keyword).
    """
    query_words = set(query.lower().split())
    reranked = []
    for r in results:
        text = r.payload.get("text", "").lower()
        text_words = set(text.split())
        keyword_score = len(query_words & text_words) / max(len(query_words), 1)
        blended = alpha * r.score + (1 - alpha) * keyword_score
        reranked.append({
            "id": r.id,
            "vector_score": round(r.score, 4),
            "keyword_score": round(keyword_score, 4),
            "blended_score": round(blended, 4),
            "text": r.payload.get("text", "")[:100],
            "title": r.payload.get("title", ""),
        })
    reranked.sort(key=lambda x: x["blended_score"], reverse=True)
    return reranked


# --- Run demo ---
query = "API framework Python"
raw_results = search(query, top_k=5)
reranked = rerank(raw_results, query)

print(f"\nTop results for: '{query}'")
for i, r in enumerate(reranked, 1):
    print(f"{i}. [{r['blended_score']:.3f}] {r['title']}: {r['text'][:80]}...")

# --- Filtered search example ---
filtered = client.search(
    collection_name=COLLECTION,
    query_vector=stub_embed("container orchestration"),
    query_filter=Filter(
        must=[FieldCondition(key="doc_id", match=MatchValue(value="doc2"))]
    ),
    limit=3,
)
print(f"\nFiltered search (doc2 only): {len(filtered)} results")