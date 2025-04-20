import re
import jieba
from app.core.config import settings

# 加载停用词和分词词典
with open(settings.STOPWORDS_FILE, "r", encoding="utf-8") as f:
    stopwords = set([line.strip() for line in f])
jieba.load_userdict(settings.STOCK_DICT_FILE)

def clean_text(text: str) -> str:
    """文本清洗"""
    return re.sub(r"[^\u4e00-\u9fa50-9A-Za-z\s]", "", text)

def extract_keywords(text: str) -> list[str]:
    """提取关键词"""
    words = jieba.lcut(clean_text(text))
    return [word for word in words if word not in stopwords and len(word) >= 2]
