import os
from io import BytesIO
from fastapi import UploadFile
from file_upload_handler import FileUploadHandler
from text_processor import TextProcessor
from file_processor import FileProcessor
from database_handler import DatabaseHandler
import logging
import urllib.parse

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_file_processing():
    """
    测试文件上传、文本处理和文件信息提取的完整流程
    """
    try:
        # 模拟UploadFile对象
        file_path = "./2025-04-02-通信设备-中国会计通讯2025年3月-安永(中国)企业咨询.pdf"
        logging.info(f"尝试读取文件: {file_path}")
        with open(file_path, 'rb') as f:
            file_content = f.read()
        file = UploadFile(filename=os.path.basename(file_path), file=BytesIO(file_content))
        logging.info(f"文件 {file.filename} 读取成功")

        # 2. 文本向量拆分
        text_processor = TextProcessor()
        logging.info("开始进行文本向量拆分")
        vectors = await text_processor.process_text(file_path)
        logging.info(f"文本向量拆分完成，生成 {len(vectors)} 个向量")

        # 3. 文件信息提取
        filename = os.path.basename(file_path)
        # 去除文件扩展名
        filename_without_ext = os.path.splitext(filename)[0]
        logging.info(f"尝试解析文件名: {filename_without_ext}")
        file_info = FileProcessor.parse_filename(filename_without_ext)
        logging.info(f"文件名解析成功，提取信息: {file_info}")

        # 4. 计算文件哈希
        logging.info(f"开始计算文件 {file_path} 的哈希值")
        file_hash = FileProcessor.calculate_file_hash(file_path)
        logging.info(f"文件哈希值计算成功: {file_hash}")

        # 5. 写入数据库
        host = "172.20.70.233"
        port = 6432
        username = "postgres"
        password = "Eccom@123"
        # 对密码进行 URL 编码
        encoded_password = urllib.parse.quote_plus(password)
        database = "test"
        db_url = f"postgresql://{username}:{encoded_password}@{host}:{port}/{database}"
        logging.info(f"尝试连接数据库，数据库连接字符串: {db_url}")
        try:
            logging.debug(f"数据库连接字符串字节表示: {db_url.encode()}")
            db_handler = DatabaseHandler(
                host=host,
                port=port,
                username=username,
                password=encoded_password,
                database=database
            )
            logging.info("数据库连接成功")
        except Exception as db_ex:
            logging.error(f"数据库连接失败: {str(db_ex)}")
            raise

        logging.info("开始插入数据到数据库")
        try:
            success = db_handler.insert_documents(vectors)
            assert success, "数据插入失败"
            logging.info("数据插入成功")
        except Exception as insert_ex:
            logging.error(f"数据插入失败: {str(insert_ex)}")
            raise

        # 验证数据是否成功插入
        logging.info(f"尝试查询公司为 {file_info['company']} 的文档")
        try:
            inserted_docs = db_handler.get_documents_by_company(file_info['company'])
            assert len(inserted_docs) > 0, "未查询到插入的数据"
            assert inserted_docs[0]['company'] == file_info['company'], "公司名称不匹配"
            assert inserted_docs[0]['title'] == vectors[0]['title'], "标题不匹配"
            logging.info("数据验证通过")
        except Exception as verify_ex:
            logging.error(f"数据验证失败: {str(verify_ex)}")
            raise

        logging.info("数据成功写入并验证通过")

        return True
    except Exception as e:
        logging.error(f"测试失败: {str(e)}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_file_processing())