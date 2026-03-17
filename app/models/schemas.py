from pydantic import BaseModel
from typing import List, Optional

class TokenRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    collection: Optional[str] = None

class SearchResult(BaseModel):
    id: str
    score: float
    payload: dict

class SearchResponse(BaseModel):
    results: List[SearchResult]
    cached: bool = False
    query_ms: float