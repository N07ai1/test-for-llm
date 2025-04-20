from fastapi import APIRouter, HTTPException
from app.services.text_processing import process_text
from app.models.processing import TextRequest, CleaningResult  # 新增模型导入

router = APIRouter(prefix="/process", tags=["文本处理"])

@router.post("/text", response_model=CleaningResult)
async def process_text_endpoint(request: TextRequest):
    try:
        result = process_text(request.input_text)
        return CleaningResult(**result)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
