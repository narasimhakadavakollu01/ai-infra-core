import time
import hashlib
from fastapi import APIRouter, Depends
from app.routers.auth import get_current_user
from app.services.cache import cache_get, cache_set
from app.services.vector_store import vector_search
from app.models.schemas import SearchRequest, SearchResponse, SearchResult

router = APIRouter(prefix="/search", tags=["search"])

@router.post("/", response_model=SearchResponse)
async def search(
    req: SearchRequest,
    user: str = Depends(get_current_user)
):
    start = time.perf_counter()
    cache_key = f"search:{hashlib.md5(f'{req.query}:{req.top_k}'.encode()).hexdigest()}"

    # Cache-aside: check cache first
    cached = await cache_get(cache_key)
    if cached:
        return SearchResponse(
            results=[SearchResult(**r) for r in cached],
            cached=True,
            query_ms=round((time.perf_counter() - start) * 1000, 2)
        )

    # Cache miss: query vector store
    raw = await vector_search(req.query, req.top_k)
    results = [SearchResult(**r) for r in raw]

    # Store in cache for 5 minutes
    await cache_set(cache_key, [r.model_dump() for r in results], ttl=300)

    return SearchResponse(
        results=results,
        cached=False,
        query_ms=round((time.perf_counter() - start) * 1000, 2)
    )