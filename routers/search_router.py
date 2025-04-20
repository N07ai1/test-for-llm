from fastapi import APIRouter, HTTPException
from app.models.search import SearchRankResponse, SearchRankRequest
from app.services.search_service import hybrid_search

router = APIRouter(prefix="/search", tags=["混合检索"])

@router.post("/rank", response_model=SearchRankResponse)
def search_rank(request: SearchRankRequest):
    try:
        results = hybrid_search(request.input_text)
        return SearchRankResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
