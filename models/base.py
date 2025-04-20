from pydantic import BaseModel
from datetime import date, datetime

class BaseResponse(BaseModel):
    code: int = 200
    message: str = "成功"
