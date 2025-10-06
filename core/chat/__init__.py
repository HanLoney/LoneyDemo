"""
对话模块
提供完整的对话服务功能
"""

from .chat_manager import ChatManager
from .llm_client import LLMClient, LLMClientManager, llm_manager
from .chat_service import ChatService

__version__ = "1.0.0"
__author__ = "LoneyDemo Team"
__description__ = "对话服务模块，提供智能对话、情感分析和会话管理功能"

__all__ = [
    "ChatManager",
    "LLMClient", 
    "LLMClientManager",
    "llm_manager",
    "ChatService"
]