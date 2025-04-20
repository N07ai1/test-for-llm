
from pydantic import BaseModel
from typing import List

class TextRequest(BaseModel):
    input_text: str

class CleaningResult(BaseModel):
    bool: str
    stock_codes: str
    company_names: str
    text: str
