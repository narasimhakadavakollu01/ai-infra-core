import asyncio
import hashlib
from app.services.cache import cache_get, cache_set
# Note: Real implementation lo vector_store nundi import cheyalai
# from app.services.vector_store import vector_search 

async def warm_cache(popular_queries: list[str]) -> None:
    """Pre-populate cache with known popular queries at startup."""
    for query in popular_queries:
        key = f"search:{hashlib.md5(query.encode()).hexdigest()}"
        existing = await cache_get(key)
        if not existing:
            # results = await vector_search(query, top_k=5)
            results = [{"msg": "Dummy result for " + query}] # Placeholder
            await cache_set(key, results, ttl=3600)
            print(f"🔥 Warmed: {query}")

if __name__ == "__main__":
    queries = ["FastAPI Guide", "Python Backend", "RAG Architecture"]
    asyncio.run(warm_cache(queries))