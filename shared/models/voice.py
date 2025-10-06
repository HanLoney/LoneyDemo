"""
语音相关数据模型
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from enum import Enum


class AudioFormat(Enum):
    """音频格式"""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    FLAC = "flac"


class VoiceProvider(Enum):
    """语音提供商"""
    EDGE = "edge"
    AZURE = "azure"
    OPENAI = "openai"
    GOOGLE = "google"
    AMAZON = "amazon"


@dataclass
class VoiceConfig:
    """语音配置"""
    provider: VoiceProvider
    voice_name: str
    language: str = "zh-CN"
    rate: str = "+0%"
    volume: str = "+0%"
    pitch: str = "+0%"
    audio_format: AudioFormat = AudioFormat.WAV
    sample_rate: int = 16000
    bit_rate: int = 128
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'provider': self.provider.value,
            'voice_name': self.voice_name,
            'language': self.language,
            'rate': self.rate,
            'volume': self.volume,
            'pitch': self.pitch,
            'audio_format': self.audio_format.value,
            'sample_rate': self.sample_rate,
            'bit_rate': self.bit_rate,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VoiceConfig':
        """从字典创建"""
        return cls(
            provider=VoiceProvider(data['provider']),
            voice_name=data['voice_name'],
            language=data.get('language', 'zh-CN'),
            rate=data.get('rate', '+0%'),
            volume=data.get('volume', '+0%'),
            pitch=data.get('pitch', '+0%'),
            audio_format=AudioFormat(data.get('audio_format', 'wav')),
            sample_rate=data.get('sample_rate', 16000),
            bit_rate=data.get('bit_rate', 128),
            metadata=data.get('metadata', {})
        )


@dataclass
class AudioFile:
    """音频文件"""
    file_path: Path
    file_name: str
    file_size: int
    duration: float
    audio_format: AudioFormat
    sample_rate: int
    bit_rate: int
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def file_size_mb(self) -> float:
        """文件大小（MB）"""
        return self.file_size / (1024 * 1024)
    
    @property
    def exists(self) -> bool:
        """文件是否存在"""
        return self.file_path.exists()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'file_path': str(self.file_path),
            'file_name': self.file_name,
            'file_size': self.file_size,
            'duration': self.duration,
            'audio_format': self.audio_format.value,
            'sample_rate': self.sample_rate,
            'bit_rate': self.bit_rate,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AudioFile':
        """从字典创建"""
        return cls(
            file_path=Path(data['file_path']),
            file_name=data['file_name'],
            file_size=data['file_size'],
            duration=data['duration'],
            audio_format=AudioFormat(data['audio_format']),
            sample_rate=data['sample_rate'],
            bit_rate=data['bit_rate'],
            created_at=datetime.fromisoformat(data['created_at']),
            metadata=data.get('metadata', {})
        )


@dataclass
class TTSRequest:
    """TTS请求"""
    text: str
    voice_config: VoiceConfig
    output_path: Optional[Path] = None
    request_id: str = field(default_factory=lambda: str(datetime.now().timestamp()))
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'text': self.text,
            'voice_config': self.voice_config.to_dict(),
            'output_path': str(self.output_path) if self.output_path else None,
            'request_id': self.request_id,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class TTSResponse:
    """TTS响应"""
    success: bool
    text: str
    voice: str
    processing_time: float = 0.0
    audio_data: Optional[bytes] = None
    audio_size: int = 0
    output_file: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(datetime.now().timestamp()))
    completed_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'success': self.success,
            'text': self.text,
            'voice': self.voice,
            'processing_time': self.processing_time,
            'audio_size': self.audio_size,
            'output_file': self.output_file,
            'error': self.error,
            'metadata': self.metadata,
            'request_id': self.request_id,
            'completed_at': self.completed_at.isoformat()
        }


@dataclass
class VoiceRequest:
    """语音请求基类"""
    request_id: str = field(default_factory=lambda: str(datetime.now().timestamp()))
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'request_id': self.request_id,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class VoiceResponse:
    """语音响应基类"""
    success: bool
    request_id: str
    processing_time: float = 0.0
    error: Optional[str] = None
    completed_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'success': self.success,
            'request_id': self.request_id,
            'processing_time': self.processing_time,
            'error': self.error,
            'completed_at': self.completed_at.isoformat()
        }