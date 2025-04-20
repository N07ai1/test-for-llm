import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:Eccom%40123@localhost:6432/Finance")
    # 向量检索配置
    LLM_API_URL: str = "http://10.255.2.7:31096/v1/embeddings"
    MODEL_NAME: str = "BAAI/bge-m3"
    VECTOR_DIMENSION: int = 512
    SIMILARITY_THRESHOLD: float = 0.6
    # 混合检索权重
    VECTOR_WEIGHT: float = 0.6
    TEXT_WEIGHT: float = 0.4
    STOPWORDS_FILE: str = "/home/backend/check_rank/app/stopwords.txt"   # 停用词文件路径（根目录）
    STOCK_DICT_FILE: str = "/home/backend/check_rank/app/stock_dict.txt" # 股票词典路径（根目录）

    # 新增相似度阈值配置
    MIN_SIMILARITY: float = 0.6  
settings = Settings()
