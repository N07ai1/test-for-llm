from pydantic import BaseModel
from datetime import date
from typing import List, Optional
from .stock import StockBasicInfo, StockFinancialInfo, StockResearchReport

# 请求模型（输入文本）
class SearchRankRequest(BaseModel):
    input_text: str

# 股票研究报告模型（含相似度得分）
class StockResearchReportWithScore(StockResearchReport):
    similarity_score: float

# 混合检索结果（三表连接）
class HybridSearchResult(BaseModel):
    report: StockResearchReportWithScore
    company_info: StockBasicInfo
    financial_info: Optional[StockFinancialInfo] = None

# 响应模型（结果列表）
class SearchRankResponse(BaseModel):
    results: List[HybridSearchResult]
