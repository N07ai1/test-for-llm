from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from typing import List, Dict, Literal
import os
import jieba

class JiebaTokenizer:
    """
    Jieba分词器类，支持多种分词模式
    
    模式说明:
    - 精确模式（默认）: cut_all=False, use_paddle=False
    - 全模式: cut_all=True, 扫描所有可能的分词
    - 搜索引擎模式: 在精确模式基础上对长词再次切分
    - Paddle模式: use_paddle=True, 利用PaddlePaddle深度学习框架分词
    """
    def __init__(self, cut_all: bool = False, use_paddle: bool = False):
        self.cut_all = cut_all
        self.use_paddle = use_paddle
    
    def tokenize(self, text: str) -> List[str]:
        if self.use_paddle:
            jieba.enable_paddle()
            words = jieba.cut(text, use_paddle=True)
        else:
            words = jieba.cut(text, cut_all=self.cut_all)
        return list(words)

class TextSplitter:
    def __init__(self, 
                 tokenizer_type: Literal['langchain', 'jieba'] = 'langchain',
                 chunk_size: int = 512, 
                 chunk_overlap: int = 128, 
                 separators: List[str] = None,
                 jieba_cut_all: bool = False,
                 jieba_use_paddle: bool = False):
        
        self.tokenizer_type = tokenizer_type
        
        if tokenizer_type == 'langchain':
            if separators is None:
                separators = ["\n\n", "。", "？", "！" , "?", "!"]
                self.keep_separator = True
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=separators
            )
        else:
            self.jieba_tokenizer = JiebaTokenizer(cut_all=jieba_cut_all, use_paddle=jieba_use_paddle)
    
    def split_text(self, text: str) -> List[str]:
        content = text.replace('\n', ' ')
        
        if self.tokenizer_type == 'langchain':
            print(f"使用的分隔符: {self.text_splitter._separators}")
            chunks = self.text_splitter.split_text(content)
            print(f"分块数量: {len(chunks)}")
        else:
            chunks = self.jieba_tokenizer.tokenize(content)
            print(f"使用jieba分词，分词数量: {len(chunks)}")
        
        return chunks

class EmbeddingProcessor:
    def __init__(self, ollama_ip: str = "172.20.70.233", ollama_port: int = 11434, 
                 ollama_model: str = "quentinz/bge-large-zh-v1.5:f16"):
        self.embeddings = OllamaEmbeddings(
            model=ollama_model,
            base_url=f"http://{ollama_ip}:{ollama_port}"
        )
    
    async def embed_text(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)

class TextProcessor:
    def __init__(self, text_splitter: TextSplitter, embedding_processor: EmbeddingProcessor):
        self.text_splitter = text_splitter
        self.embedding_processor = embedding_processor
    
    async def process_text(self, text: str) -> List[Dict]:
        try:
            chunks = self.text_splitter.split_text(text)
            from datetime import datetime
            
            results = []
            for i, chunk in enumerate(chunks):
                content_vector = await self.embedding_processor.embed_text(chunk)
                
                results.append({
                    "id": i+1,
                    "create_time": datetime.now().strftime("%Y-%m-%d"),
                    "content": chunk,
                    "content_embedding": content_vector,
                    "status": "enabled"
                })
            
            return results
        except Exception as e:
            raise Exception(f"文本处理失败: {str(e)}")