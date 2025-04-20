import psycopg2
from psycopg2.extensions import register_adapter, AsIs
import numpy as np
from app.core.config import settings

# 注册numpy类型适配器
def addapt_numpy_float32(numpy_float32):
    return AsIs(numpy_float32.item())
register_adapter(np.float32, addapt_numpy_float32)

# 获取数据库连接
def get_db_connection():
    try:
        conn = psycopg2.connect(settings.DATABASE_URL)
        return conn
    except psycopg2.Error as e:
        raise DatabaseConnectionError(f"数据库连接失败: {str(e)}") from e

# 自定义异常类
class DatabaseConnectionError(Exception):
    pass
