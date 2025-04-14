from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from typing import Dict, Any, Optional, List, Union
import requests
import json

# 提示词模板
PROMPT_TEMPLATE = """
你是一个专业的回答助手，只会回答已经知道的问题。
如果不知道答案，请回答："抱歉，我不知道这个问题的答案。"

已知问题：{question}
回答格式要求：
1. 提供清晰简洁的答案
2. 包含相关代码示例（如果适用）
3. 解释关键步骤

问题：{user_question}
"""

class CustomDeepSeekLLM(LLM):
    """自定义DeepSeek LLM封装类"""
    
    model_name: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 256
    do_sample: bool = True
    top_k: int = 50
    top_p: float = 1.0
    repetition_penalty: float = 1.0
    no_repeat_ngram_size: int = 0
    max_new_tokens: Optional[int] = None
    min_new_tokens: Optional[int] = None
    early_stopping: bool = False
    num_return_sequences: int = 1
    api_base: str = "https://api.deepseek.com/v1"
    api_key: Optional[str] = None
    
    @property
    def _llm_type(self) -> str:
        return "custom_deepseek"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """调用DeepSeek API"""
        if not self.api_key:
            raise ValueError("DeepSeek API key未设置")
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "repetition_penalty": self.repetition_penalty,
            "no_repeat_ngram_size": self.no_repeat_ngram_size,
            **kwargs
        }
        
        response = requests.post(
            f"{self.api_base}/chat/completions",
            headers=headers,
            data=json.dumps(payload)
        )
        
        if response.status_code != 200:
            raise ValueError(f"DeepSeek API请求失败: {response.text}")
            
        return response.json()["choices"][0]["message"]["content"]


class LLMIntegration:
    def __init__(
        self,
        model_name: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 256,
        do_sample: bool = True,
        top_k: int = 50,
        top_p: float = 1.0,
        repetition_penalty: float = 1.0,
        no_repeat_ngram_size: int = 0,
        max_new_tokens: Optional[int] = None,
        min_new_tokens: Optional[int] = None,
        early_stopping: bool = False,
        num_return_sequences: int = 1,
        api_base: Optional[str] = "https://api.deepseek.com/v1",
        api_key: Optional[str] = "sk-9686704788fa4bcdae0ed0b09142dd2d"
    ):
        """
        初始化LLM配置

        :param model_name:            模型名称，默认使用"deepseek-chat"
        :param temperature:          温度参数(0-2)，控制生成文本的随机性，值越高越随机，默认0.7
        :param max_tokens:           最大token数(1-4096)，控制生成文本长度，默认256
        :param do_sample:            是否采样，True时使用采样策略生成文本，默认True
        :param top_k:                保留概率最高的k个token(1-1000)，用于限制采样范围，默认50
        :param top_p:                保留概率累积和达到p的最小token集合(0-1)，用于动态采样，默认1.0
        :param repetition_penalty:   重复惩罚系数(1-2)，值越高越避免重复，默认1.0
        :param no_repeat_ngram_size: 禁止重复的ngram大小(0-10)，0表示不限制，默认0
        :param max_new_tokens:       最大新生成token数，None表示无限制，默认None
        :param min_new_tokens:       最小新生成token数，None表示无限制，默认None
        :param early_stopping:       是否提前停止生成，False时生成完整文本，默认False
        :param num_return_sequences: 返回的序列数量(1-10)，默认1
        """
        # 使用自定义的 CustomDeepSeekLLM 类
        self.llm = CustomDeepSeekLLM(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            do_sample=do_sample,
            top_k=top_k,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            no_repeat_ngram_size=no_repeat_ngram_size,
            max_new_tokens=max_new_tokens,
            min_new_tokens=min_new_tokens,
            early_stopping=early_stopping,
            num_return_sequences=num_return_sequences,
            api_base=api_base,
            api_key=api_key
        )
        

    def set_prompt_template(self, template: str, input_variables: list) -> None:
        """
        设置提示词模板
        :param template: 提示词模板字符串
        :param input_variables: 模板中的变量列表
        """
        self.prompt = PromptTemplate(
            template=template,
            input_variables=input_variables
        )
    

    def run_chain(self, inputs: Dict[str, Any] = None) -> str:
        """
        运行LLM链
        :param inputs: 输入参数字典，可选。如果未提供，将通过input()获取用户问题
        :return: LLM生成的文本
        """
        if not hasattr(self, 'prompt'):
            raise ValueError("请先设置提示词模板")
            
        if inputs is None:
            user_question = input("请输入您的问题：")
            inputs = {"user_question": user_question, "question": user_question}
            
        chain = LLMChain(llm=self.llm, prompt=self.prompt)
        return chain.run(inputs)


    def get_config(self) -> Dict[str, Any]:
        """
        获取当前LLM配置
        :return: 配置参数字典
        """
        return {
            "model_name": self.llm.model_name,
            "temperature": self.llm.temperature,
            "max_tokens": self.llm.max_tokens,
            "do_sample": self.llm.do_sample,
            "top_k": self.llm.top_k,
            "top_p": self.llm.top_p,
            "repetition_penalty": self.llm.repetition_penalty,
            "no_repeat_ngram_size": self.llm.no_repeat_ngram_size,
            "max_new_tokens": self.llm.max_new_tokens,
            "min_new_tokens": self.llm.min_new_tokens,
            "early_stopping": self.llm.early_stopping,
            "num_return_sequences": self.llm.num_return_sequences,
            "api_base": self.llm.api_base,
            "api_key": "*****" if self.llm.api_key else None,
            "prompt_template": self.prompt.template if hasattr(self, 'prompt') else None
        }