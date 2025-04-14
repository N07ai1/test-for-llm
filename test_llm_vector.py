import unittest
from llm_integration import LLMIntegration
from question_processor import QuestionProcessor
from text_processor import TextProcessor, TextSplitter, EmbeddingProcessor

class TestLLMVectorIntegration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # 初始化LLM
        self.llm = LLMIntegration(
            model_name="deepseek-chat",
            api_key="sk-9686704788fa4bcdae0ed0b09142dd2d"
        )
        self.llm.set_prompt_template(
            """你是一个专业的回答助手，只会回答已经知道的问题。
如果不知道答案，请回答："抱歉，我不知道这个问题的答案。"

已知问题：{question}
回答格式要求：
1. 提供清晰简洁的答案
2. 包含相关代码示例（如果适用）
3. 解释关键步骤

问题：{user_question}""",
            ["question", "user_question"]
        )
        
        # 初始化问题处理器
        text_splitter = TextSplitter()
        embedding_processor = EmbeddingProcessor()
        self.text_processor = TextProcessor(text_splitter, embedding_processor)
        self.question_processor = QuestionProcessor(self.text_processor)
    
    async def test_llm_response(self):
        """测试LLM提问功能"""
        question = "Python中如何读取文件？"
        print(f"问题: {question}")
        chain = self.llm.prompt | self.llm.llm
        response = await chain.ainvoke({"user_question": question, "question": question})
        print(f"DeepSeek回答: {response}")
        self.assertIsInstance(response, str)
        self.assertNotEqual(response, "抱歉，我不知道这个问题的答案。")
    
    def test_question_vectorization(self):
        """测试问题向量化功能"""
        question = "Python中如何读取文件？"
        print(f"问题: {question}")
        processed = self.question_processor.preprocess_question(question)
        print(f"分词结果: {processed}")
        self.assertIsInstance(processed, str)
        self.assertTrue(len(processed) > 0)
    
    async def test_integrated_workflow(self):
        """测试完整工作流：提问+向量化"""
        # 提问和向量化
        question = "Python中如何读取文件？"
        chain = self.llm.prompt | self.llm.llm
        response = await chain.ainvoke({"user_question": question, "question": question})
        
        # 使用相同的question进行向量化
        processed = self.question_processor.preprocess_question(question)
        vectors = await self.question_processor.process_question(question)
        
        self.assertIsInstance(response, str)
        self.assertIsInstance(vectors, list)
        self.assertTrue(len(vectors) > 0)
        
        self.assertIsInstance(response, str)
        self.assertIsInstance(vectors, list)
        self.assertTrue(len(vectors) > 0)
        
    def test_tokenizer_comparison(self):
        """测试jieba分词和langchain分词结果对比"""
        test_text = "这是一个测试文本，用于比较jieba和langchain的分词效果。"
        
        # 使用jieba分词器（精确模式）
        jieba_splitter = TextSplitter(tokenizer_type='jieba')
        jieba_result = jieba_splitter.split_text(test_text)
        print(f"jieba分词结果: {jieba_result}")
        
        # 使用langchain分词器
        langchain_splitter = TextSplitter(tokenizer_type='langchain')
        langchain_result = langchain_splitter.split_text(test_text)
        print(f"langchain分词结果: {langchain_result}")
        
        # 验证两种分词器都能正常工作
        self.assertTrue(len(jieba_result) > 0)
        self.assertTrue(len(langchain_result) > 0)

if __name__ == "__main__":
    unittest.main()