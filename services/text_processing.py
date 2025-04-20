import re
import jieba
from app.core.config import settings
from typing import List, Dict
from difflib import SequenceMatcher
from psycopg2 import sql
from app.core.database import get_db_connection, DatabaseConnectionError

# 加载停用词和分词词典（已在现有代码中初始化，保持一致）
# 新增相似度阈值配置
MIN_SIMILARITY = 0.6  # 可从settings中读取，这里暂时硬编码

def process_text(input_text: str) -> Dict:
    # 1. 文本清洗（复用现有清洗逻辑，保留数字）
    cleaned_text = re.sub(r"[^\u4e00-\u9fa50-9A-Za-z\s]", "", input_text)
    
    # 2. 分词处理（复用现有分词逻辑）
    words = jieba.lcut(cleaned_text)
    keywords = [word for word in words if word not in settings.STOPWORDS and len(word) >= 2]
    
    # 3. 数据库查询（整合新的匹配逻辑）
    db_result = query_database(keywords)
    
    # 4. 构建返回数据
    return {
        "bool": "1" if (db_result["stock_codes"] or db_result["company_names"]) else "0",
        "stock_codes": ",".join(db_result["stock_codes"]),
        "company_names": ",".join(db_result["company_names"]),
        "text": " ".join(keywords)
    }

def query_database(keywords: List[str]) -> Dict[str, List[str]]:
    result = {"stock_codes": [], "company_names": []}
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # 1. 精确6位代码匹配
            exact_codes = [kw for kw in keywords if re.match(r'^\d{6}$', kw)]
            if exact_codes:
                cur.execute(
                    sql.SQL("SELECT stock_code, company_name FROM stock_basic_info WHERE stock_code IN %s"),
                    (tuple(exact_codes),)
                )
                exact_results = cur.fetchall()
                result["stock_codes"].extend([code for code, _ in exact_results])
                result["company_names"].extend([name for _, name in exact_results])

            # 2. 模糊名称匹配
            fuzzy_keywords = [kw for kw in keywords if not re.match(r'^\d{6}$', kw)]
            if fuzzy_keywords:
                cur.execute("SELECT stock_code, company_name FROM stock_basic_info")
                all_records = cur.fetchall()
                matched = []
                for kw in fuzzy_keywords:
                    for code, name in all_records:
                        sim = SequenceMatcher(None, kw, name).ratio()
                        if sim >= MIN_SIMILARITY:
                            matched.append((sim, code, name))
                
                # 排序并去重
                sorted_matched = sorted(matched, key=lambda x: x[0], reverse=True)[:10]
                result["stock_codes"].extend([code for _, code, _ in sorted_matched])
                result["company_names"].extend([name for _, _, name in sorted_matched])

            # 去重逻辑（精确匹配优先）
            seen_codes = set()
            final_codes = []
            final_names = []
            
            # 处理精确匹配结果（6位代码）
            for code in result["stock_codes"]:
                if len(code) == 6 and code not in seen_codes:
                    final_codes.append(code)
                    seen_codes.add(code)
            
            # 处理模糊匹配结果（补充非6位代码或新匹配）
            for code in result["stock_codes"]:
                if code not in seen_codes:
                    final_codes.append(code)
                    seen_codes.add(code)
            
            # 名称去重（保留顺序）
            seen_names = set()
            for name in result["company_names"]:
                if name not in seen_names:
                    seen_names.add(name)
                    final_names.append(name)
            
            result["stock_codes"] = final_codes
            result["company_names"] = final_names

        conn.close()
        return result
    except DatabaseConnectionError as e:
        raise e
    except Exception as e:
        raise RuntimeError(f"数据库查询失败: {str(e)}") from e
