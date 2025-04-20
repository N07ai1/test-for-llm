import numpy as np
import requests
from psycopg2 import sql
from app.core.database import get_db_connection, DatabaseConnectionError
from app.core.config import settings
from app.services.text_processing import extract_keywords
from app.models.search import HybridSearchResult, StockResearchReport

def get_embedding(text: str) -> np.ndarray:
    """获取文本嵌入向量（修正版）"""
    payload = {
        "model": settings.MODEL_NAME,
        "input": text  # 向量模型使用 input 字段
    }
    try:
        response = requests.post(settings.LLM_API_URL, json=payload, timeout=10)
        response.raise_for_status()
        # 假设接口返回 {"embeddings": [0.1, 0.2, ...]}
        embedding = response.json()["embeddings"]
        return np.array(embedding, dtype=np.float32)
    except Exception as e:
        raise RuntimeError(f"嵌入向量获取失败: {str(e)}") from e

def hybrid_search(input_text: str) -> list[HybridSearchResult]:
    """混合检索核心逻辑"""
    keywords = extract_keywords(input_text)
    query_embedding = get_embedding(input_text)
    results = []
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. 向量化检索（含三表连接）
        vector_query = sql.SQL("""
            WITH latest_finance AS (
                SELECT stock_code, MAX(report_date) AS latest_date
                FROM stock_financial_statements
                GROUP BY stock_code
            )
            SELECT 
                r.id, r.stock_code, r.report_title, r.institution, r.publish_date, r.rating, r.summary,
                b.company_name, b.industry, b.exchange_market,
                f.net_profit, f.debt_ratio, f.net_profit_growth_percent,
                vector_similarity(r.report_vector, %s) AS sim_score
            FROM stock_research_reports r
            JOIN stock_basic_info b ON r.stock_code = b.stock_code
            LEFT JOIN latest_finance lf ON r.stock_code = lf.stock_code
            LEFT JOIN stock_financial_statements f ON r.stock_code = f.stock_code AND lf.latest_date = f.report_date
            WHERE r.report_vector IS NOT NULL
            ORDER BY r.report_vector <=> %s
            LIMIT 100
        """)
        cur.execute(vector_query, (query_embedding.tolist(), query_embedding.tolist()))
        vector_results = cur.fetchall()
        
        # 2. 文本检索（基于多表字段）
        if keywords:
            tsquery = " & ".join([f"'{kw}':*" for kw in keywords])  # 模糊匹配
            text_query = sql.SQL("""
                WITH latest_finance AS (
                    SELECT stock_code, MAX(report_date) AS latest_date
                    FROM stock_financial_statements
                    GROUP BY stock_code
                )
                SELECT 
                    r.id, r.stock_code, r.report_title, r.institution, r.publish_date, r.rating, r.summary,
                    b.company_name, b.industry, b.exchange_market,
                    f.net_profit, f.debt_ratio, f.net_profit_growth_percent,
                    ts_rank_cd(to_tsvector('chinese', COALESCE(r.summary, '') || ' ' || COALESCE(b.company_name, '') || ' ' || COALESCE(b.industry, '')), to_tsquery(%s)) AS text_score
                FROM stock_research_reports r
                JOIN stock_basic_info b ON r.stock_code = b.stock_code
                LEFT JOIN latest_finance lf ON r.stock_code = lf.stock_code
                LEFT JOIN stock_financial_statements f ON r.stock_code = f.stock_code AND lf.latest_date = f.report_date
                WHERE to_tsvector('chinese', COALESCE(r.summary, '') || ' ' || COALESCE(b.company_name, '') || ' ' || COALESCE(b.industry, '')) @@ to_tsquery(%s)
            """)
            cur.execute(text_query, (tsquery, tsquery))
            text_results = cur.fetchall()
        else:
            text_results = []
        
        # 3. 合并结果并计算综合得分
        all_results = []
        for result in vector_results + text_results:
            report_data = StockResearchReport(
                report_id=result[0],
                stock_code=result[1],
                report_title=result[2],
                institution=result[3],
                publish_date=result[4].date() if isinstance(result[4], datetime) else result[4],
                rating=result[5],
                summary=result[6],
                similarity_score=result[-1] if "sim_score" in locals() else result[-1]
            )
            company_info = StockBasicInfo(
                stock_code=result[1],
                company_name=result[7],
                industry=result[8],
                exchange_market=result[9]
            )
            financial_info = StockFinancialInfo(
                stock_code=result[1],
                report_date=result[10].date() if isinstance(result[10], datetime) else None,
                net_profit=result[11],
                debt_ratio=result[12],
                net_profit_growth_percent=result[13]
            ) if result[10] is not None else None
            
            # 计算综合得分（向量得分*60% + 文本得分*40%）
            vector_score = result[-1] if len(result) > 14 and result[-1] is not None else 0.0
            text_score = result[-1] if len(result) <= 14 and result[-1] is not None else 0.0
            combined_score = (settings.VECTOR_WEIGHT * vector_score) + (settings.TEXT_WEIGHT * text_score)
            
            if combined_score >= settings.SIMILARITY_THRESHOLD:
                all_results.append({
                    "combined_score": combined_score,
                    "report": report_data,
                    "company_info": company_info,
                    "financial_info": financial_info
                })
        
        # 4. 按综合得分排序并去重
        sorted_results = sorted(all_results, key=lambda x: (-x["combined_score"], x["report"].publish_date), reverse=False)
        unique_results = {}
        for item in sorted_results:
            if item["report"].report_id not in unique_results:
                unique_results[item["report"].report_id] = item
        
        return [HybridSearchResult(**item) for item in unique_results.values()]
    
    except DatabaseConnectionError as e:
        raise e
    except Exception as e:
        raise RuntimeError(f"检索处理失败: {str(e)}") from e
    finally:
        if conn:
            conn.close()
