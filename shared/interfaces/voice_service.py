"""
语音服务接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
from ..models.voice import VoiceConfig, AudioFile


class VoiceServiceInterface(ABC):
    """语音服务接口"""
    
    @abstractmethod
    async def text_to_speech(self, text: str, voice_config: Optional[VoiceConfig] = None) -> AudioFile:
        """
        文本转语音
        
        Args:
            text: 待转换文本
            voice_config: 语音配置
            
        Returns:
            音频文件信息
        """
        pass
    
    @abstractmethod
    async def speech_to_text(self, audio_file: Path) -> str:
        """
        语音转文本
        
        Args:
            audio_file: 音频文件路径
            
        Returns:
            转换后的文本
        """
        pass
    
    @abstractmethod
    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        获取可用语音列表
        
        Returns:
            语音列表
        """
        pass
    
    @abstractmethod
    async def set_default_voice(self, voice_name: str) -> bool:
        """
        设置默认语音
        
        Args:
            voice_name: 语音名称
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    async def get_voice_config(self) -> VoiceConfig:
        """
        获取语音配置
        
        Returns:
            语音配置
        """
        pass
    
    @abstractmethod
    async def update_voice_config(self, config: VoiceConfig) -> bool:
        """
        更新语音配置
        
        Args:
            config: 语音配置
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    async def delete_audio_file(self, file_path: Path) -> bool:
        """
        删除音频文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    async def get_audio_files(self, limit: int = 50) -> List[AudioFile]:
        """
        获取音频文件列表
        
        Args:
            limit: 限制数量
            
        Returns:
            音频文件列表
        """
        pass