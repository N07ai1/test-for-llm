from text_processor import TextProcessor, EmbeddingProcessor
import string
import jieba
from typing import List, Dict

class QuestionProcessor:
    def __init__(self, text_processor: TextProcessor):
        self.text_processor = text_processor
        
    def remove_punctuation(self, text: str) -> str:
        """去除标点符号"""
        return text.translate(str.maketrans('', '', string.punctuation))
    
    def remove_stopwords(self, text: str) -> str:
        """去除停用词"""
        # 使用jieba进行中文分词
        words = [word for word in jieba.cut(text) if word.strip()]
        
        # 返回结果
        return ' '.join(words)
    
    def preprocess_question(self, question: str) -> str:
        """预处理问题"""
        # 去除标点
        text = self.remove_punctuation(question)
        # 去除停用词
        text = self.remove_stopwords(text)
        return text
    
    async def process_question(self, question: str) -> List[Dict]:
        """处理问题并向量化"""
        processed_text = self.preprocess_question(question)
        return await self.text_processor.process_text(processed_text)