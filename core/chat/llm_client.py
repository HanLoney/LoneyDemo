"""
LLM客户端
负责与OpenAI API交互
"""
import json
import time
from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from shared.utils import get_logger
from shared.utils.config import config


class LLMClient:
    """LLM客户端"""
    
    def __init__(self):
        self.config = config
        self.logger = get_logger(__name__)
        
        # OpenAI配置 - 从external_apis获取
        self.api_key = self.config.get('external_apis.openai.api_key')
        self.base_url = self.config.get('external_apis.openai.base_url')
        self.model = self.config.get('external_apis.openai.model', 'gpt-3.5-turbo')
        self.max_tokens = self.config.get('external_apis.openai.max_tokens', 2000)
        self.temperature = self.config.get('external_apis.openai.temperature', 0.7)
        self.timeout = self.config.get('external_apis.openai.timeout', 30)
        
        # 初始化客户端
        self.client = self._init_client()
        self.async_client = self._init_async_client()
        
        # 请求统计
        self.request_count = 0
        self.total_tokens = 0
        self.error_count = 0
        
        self.logger.info(f"LLM客户端已初始化 - 模型: {self.model}")
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       **kwargs) -> Optional[ChatCompletion]:
        """
        同步聊天完成
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            聊天完成响应
        """
        try:
            if not self.client:
                self.logger.warning("LLM客户端未初始化，无法进行聊天完成")
                return None
                
            start_time = time.time()
            
            # 合并参数
            params = self._build_completion_params(messages, **kwargs)
            
            # 调用API
            response = self.client.chat.completions.create(**params)
            
            # 更新统计
            self._update_stats(response, time.time() - start_time)
            
            self.logger.debug(f"聊天完成成功 - 耗时: {time.time() - start_time:.2f}s")
            return response
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"聊天完成失败: {e}")
            return None
    
    async def async_chat_completion(self, 
                                   messages: List[Dict[str, str]], 
                                   **kwargs) -> Optional[ChatCompletion]:
        """
        异步聊天完成
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            聊天完成响应
        """
        try:
            if not self.async_client:
                self.logger.warning("异步LLM客户端未初始化，无法进行异步聊天完成")
                return None
                
            start_time = time.time()
            
            # 合并参数
            params = self._build_completion_params(messages, **kwargs)
            
            # 调用API
            response = await self.async_client.chat.completions.create(**params)
            
            # 更新统计
            self._update_stats(response, time.time() - start_time)
            
            self.logger.debug(f"异步聊天完成成功 - 耗时: {time.time() - start_time:.2f}s")
            return response
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"异步聊天完成失败: {e}")
            return None
    
    def stream_chat_completion(self, 
                              messages: List[Dict[str, str]], 
                              **kwargs) -> Optional[AsyncGenerator[ChatCompletionChunk, None]]:
        """
        流式聊天完成
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            流式响应生成器
        """
        try:
            # 合并参数
            params = self._build_completion_params(messages, stream=True, **kwargs)
            
            # 调用API
            stream = self.client.chat.completions.create(**params)
            
            self.logger.debug("流式聊天完成开始")
            return stream
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"流式聊天完成失败: {e}")
            return None
    
    async def async_stream_chat_completion(self, 
                                          messages: List[Dict[str, str]], 
                                          **kwargs) -> Optional[AsyncGenerator[ChatCompletionChunk, None]]:
        """
        异步流式聊天完成
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            异步流式响应生成器
        """
        try:
            # 合并参数
            params = self._build_completion_params(messages, stream=True, **kwargs)
            
            # 调用API
            stream = await self.async_client.chat.completions.create(**params)
            
            self.logger.debug("异步流式聊天完成开始")
            return stream
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"异步流式聊天完成失败: {e}")
            return None
    
    def extract_response_content(self, response: ChatCompletion) -> str:
        """
        提取响应内容
        
        Args:
            response: 聊天完成响应
            
        Returns:
            响应内容
        """
        try:
            if response and response.choices:
                return response.choices[0].message.content or ""
            return ""
        except Exception as e:
            self.logger.error(f"提取响应内容失败: {e}")
            return ""
    
    def extract_stream_content(self, chunk: ChatCompletionChunk) -> str:
        """
        提取流式响应内容
        
        Args:
            chunk: 流式响应块
            
        Returns:
            内容片段
        """
        try:
            if chunk.choices and chunk.choices[0].delta.content:
                return chunk.choices[0].delta.content
            return ""
        except Exception as e:
            self.logger.error(f"提取流式内容失败: {e}")
            return ""
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        return {
            "request_count": self.request_count,
            "total_tokens": self.total_tokens,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1),
            "model": self.model,
            "base_url": self.base_url
        }
    
    def reset_stats(self) -> None:
        """重置统计"""
        self.request_count = 0
        self.total_tokens = 0
        self.error_count = 0
        self.logger.info("LLM使用统计已重置")
    
    def test_connection(self) -> bool:
        """测试连接"""
        try:
            test_messages = [
                {"role": "user", "content": "Hello"}
            ]
            
            response = self.chat_completion(
                messages=test_messages,
                max_tokens=10,
                temperature=0
            )
            
            if response:
                self.logger.info("LLM连接测试成功")
                return True
            else:
                self.logger.error("LLM连接测试失败")
                return False
                
        except Exception as e:
            self.logger.error(f"LLM连接测试异常: {e}")
            return False
    
    def _init_client(self) -> Optional[OpenAI]:
        """初始化同步客户端"""
        try:
            if not self.api_key:
                self.logger.warning("OpenAI API密钥未配置，LLM客户端将无法使用")
                return None
                
            client_kwargs = {
                "api_key": self.api_key,
                "timeout": self.timeout
            }
            
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            
            return OpenAI(**client_kwargs)
            
        except Exception as e:
            self.logger.error(f"初始化同步客户端失败: {e}")
            raise
    
    def _init_async_client(self) -> Optional[AsyncOpenAI]:
        """初始化异步客户端"""
        try:
            if not self.api_key:
                self.logger.warning("OpenAI API密钥未配置，异步LLM客户端将无法使用")
                return None
                
            client_kwargs = {
                "api_key": self.api_key,
                "timeout": self.timeout
            }
            
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            
            return AsyncOpenAI(**client_kwargs)
            
        except Exception as e:
            self.logger.error(f"初始化异步客户端失败: {e}")
            raise
    
    def _build_completion_params(self, 
                                messages: List[Dict[str, str]], 
                                **kwargs) -> Dict[str, Any]:
        """构建完成参数"""
        params = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
            "stream": kwargs.get("stream", False)
        }
        
        # 添加其他可选参数
        optional_params = [
            "top_p", "frequency_penalty", "presence_penalty", 
            "stop", "user", "functions", "function_call"
        ]
        
        for param in optional_params:
            if param in kwargs:
                params[param] = kwargs[param]
        
        return params
    
    def _update_stats(self, response: ChatCompletion, duration: float) -> None:
        """更新统计信息"""
        try:
            self.request_count += 1
            
            if response and response.usage:
                self.total_tokens += response.usage.total_tokens
            
            self.logger.debug(f"请求统计更新 - 请求数: {self.request_count}, "
                            f"总Token: {self.total_tokens}, 耗时: {duration:.2f}s")
            
        except Exception as e:
            self.logger.error(f"更新统计失败: {e}")


class LLMClientManager:
    """LLM客户端管理器"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._clients: Dict[str, LLMClient] = {}
        self._default_client: Optional[LLMClient] = None
    
    def get_client(self, client_id: str = "default") -> LLMClient:
        """
        获取LLM客户端
        
        Args:
            client_id: 客户端ID
            
        Returns:
            LLM客户端
        """
        if client_id not in self._clients:
            self._clients[client_id] = LLMClient()
            
            if client_id == "default":
                self._default_client = self._clients[client_id]
        
        return self._clients[client_id]
    
    def get_default_client(self) -> LLMClient:
        """获取默认客户端"""
        if not self._default_client:
            self._default_client = self.get_client("default")
        return self._default_client
    
    def remove_client(self, client_id: str) -> bool:
        """移除客户端"""
        if client_id in self._clients:
            del self._clients[client_id]
            self.logger.info(f"移除LLM客户端: {client_id}")
            return True
        return False
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有客户端统计"""
        return {
            client_id: client.get_usage_stats()
            for client_id, client in self._clients.items()
        }
    
    def reset_all_stats(self) -> None:
        """重置所有客户端统计"""
        for client in self._clients.values():
            client.reset_stats()
        self.logger.info("所有LLM客户端统计已重置")


# 全局客户端管理器
llm_manager = LLMClientManager()