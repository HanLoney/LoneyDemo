"""
语音服务模块
提供TTS（文本转语音）和STT（语音转文本）功能
"""

from .tts_client import TTSClient, TTSClientManager, tts_manager
from .voice_service import VoiceService, voice_service

# 导出主要类和实例
__all__ = [
    'TTSClient',
    'TTSClientManager', 
    'tts_manager',
    'VoiceService',
    'voice_service'
]

# 模块信息
__version__ = "1.0.0"
__author__ = "LoneyDemo Team"
__description__ = "语音服务模块，提供TTS和STT功能"