from pydantic import BaseModel
from datetime import date

class StockBasicInfo(BaseModel):
    stock_code: str
    company_name: str
    industry: str
    exchange_market: str

class StockFinancialInfo(BaseModel):
    stock_code: str
    report_date: date
    net_profit: float | None
    debt_ratio: float | None
    net_profit_growth_percent: float | None

class StockResearchReport(BaseModel):
    report_id: int
    stock_code: str
    report_title: str
    institution: str
    publish_date: date
    rating: str
    summary: str
    similarity_score: float
