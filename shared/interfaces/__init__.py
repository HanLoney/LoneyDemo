"""
服务接口定义模块
"""
from .chat_service import ChatServiceInterface
from .emotion_service import EmotionServiceInterface
from .voice_service import VoiceServiceInterface
from .analysis_service import AnalysisServiceInterface

__all__ = [
    'ChatServiceInterface',
    'EmotionServiceInterface', 
    'VoiceServiceInterface',
    'AnalysisServiceInterface'
]