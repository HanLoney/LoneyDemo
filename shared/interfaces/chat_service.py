"""
对话服务接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..models.chat import ChatMessage, ChatResponse


class ChatServiceInterface(ABC):
    """对话服务接口"""
    
    @abstractmethod
    async def send_message(self, message: str, user_id: str = "default", 
                          context: Optional[Dict[str, Any]] = None) -> ChatResponse:
        """
        发送消息并获取回复
        
        Args:
            message: 用户消息
            user_id: 用户ID
            context: 上下文信息
            
        Returns:
            对话回复
        """
        pass
    
    @abstractmethod
    async def get_chat_history(self, user_id: str = "default", 
                              limit: int = 50) -> List[ChatMessage]:
        """
        获取对话历史
        
        Args:
            user_id: 用户ID
            limit: 限制数量
            
        Returns:
            对话历史列表
        """
        pass
    
    @abstractmethod
    async def clear_chat_history(self, user_id: str = "default") -> bool:
        """
        清空对话历史
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    async def set_system_prompt(self, prompt: str) -> bool:
        """
        设置系统提示词
        
        Args:
            prompt: 系统提示词
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    async def get_chat_statistics(self, user_id: str = "default") -> Dict[str, Any]:
        """
        获取对话统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计信息
        """
        pass