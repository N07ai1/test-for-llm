import re
import hashlib
from typing import Dict, Optional
import os
import chardet  # 用于检测文件编码

class FileProcessor:
    @staticmethod
    def parse_filename(filename: str) -> Dict[str, str]:
        """
        解析文件名，提取日期、行业、标题和作者信息
        文件名格式示例：2025-04-02-通信设备-中国会计通讯2025年3月-安永(中国)企业咨询
        """
        # 去除文件扩展名
        filename = os.path.splitext(filename)[0]
        pattern = r"^(\d{4}-\d{2}-\d{2})-(.*?)-(.*?)-(.*)$"
        match = re.match(pattern, filename)
        
        if not match:
            raise ValueError("文件名格式不正确，无法解析")
            
        return {
            "modif_time": match.group(1),
            "industry": match.group(2),
            "title": match.group(3),
            "company": match.group(4)
        }
    
    @staticmethod
    def read_file_content(file_path: str) -> str:
        """
        读取文件内容
        :param file_path: 文件路径
        :return: 文件内容字符串
        """
        try:
            if file_path.lower().endswith('.pdf'):
                import PyPDF2
                content = ""
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        content += page.extract_text()
                return content
            elif file_path.lower().endswith('.docx'):
                import docx
                doc = docx.Document(file_path)
                return "\n".join([para.text for para in doc.paragraphs])
            elif file_path.lower().endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                # 检测文件编码
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                    result = chardet.detect(raw_data)
                    encoding = result['encoding']
                    if encoding is None:
                        encoding = 'utf-8'  # 默认使用 UTF-8
                    content = raw_data.decode(encoding)
                return content
        except Exception as e:
            raise Exception(f"读取文件失败: {str(e)}")
            
    @staticmethod
    def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
        """
        计算文件内容的哈希值
        :param file_path: 文件路径
        :param algorithm: 哈希算法，支持'md5'或'sha256'
        :return: 哈希值字符串
        """
        if algorithm not in ["md5", "sha256"]:
            raise ValueError("不支持的哈希算法，仅支持'md5'和'sha256'")
            
        hash_func = hashlib.md5() if algorithm == "md5" else hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            raise Exception(f"计算文件哈希失败: {str(e)}")