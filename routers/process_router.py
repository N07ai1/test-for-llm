from fastapi import APIRouter, HTTPException
from app.services.text_processing import clean_text, extract_keywords
from app.models.base import BaseResponse
from app.core.database import get_db_connection

router = APIRouter(prefix="/process", tags=["文本处理"])

@router.post("/text", response_model=BaseResponse)
def process_text(request: dict):
    # 保持原有逻辑，调用text_processing服务
    pass
