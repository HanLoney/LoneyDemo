"""
情感相关数据模型
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum


class EmotionType(Enum):
    """情感类型"""
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    NEUTRAL = "neutral"
    EXCITED = "excited"
    CALM = "calm"
    CONFUSED = "confused"


@dataclass
class EmotionState:
    """情感状态"""
    primary_emotion: EmotionType
    intensity: float  # 0.0 - 1.0
    emotions: Dict[EmotionType, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    last_update: datetime = field(default_factory=datetime.now)
    stability: float = 0.7  # 情感稳定性
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保强度在有效范围内
        self.intensity = max(0.0, min(1.0, self.intensity))
        
        # 如果emotions为空，设置主要情感
        if not self.emotions:
            self.emotions = {self.primary_emotion: self.intensity}
    
    def get_dominant_emotion(self) -> EmotionType:
        """获取主导情感"""
        if not self.emotions:
            return self.primary_emotion
        return max(self.emotions.items(), key=lambda x: x[1])[0]
    
    def get_emotion_intensity(self, emotion: EmotionType) -> float:
        """获取特定情感的强度"""
        return self.emotions.get(emotion, 0.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'primary_emotion': self.primary_emotion.value,
            'intensity': self.intensity,
            'emotions': {e.value: v for e, v in self.emotions.items()},
            'timestamp': self.timestamp.isoformat(),
            'context': self.context,
            'last_update': self.last_update.isoformat(),
            'stability': self.stability
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmotionState':
        """从字典创建"""
        emotions = {EmotionType(k): v for k, v in data.get('emotions', {}).items()}
        return cls(
            primary_emotion=EmotionType(data['primary_emotion']),
            intensity=data['intensity'],
            emotions=emotions,
            timestamp=datetime.fromisoformat(data['timestamp']),
            context=data.get('context', {}),
            last_update=datetime.fromisoformat(data.get('last_update', data['timestamp'])),
            stability=data.get('stability', 0.7)
        )


@dataclass
class EmotionAnalysisResult:
    """情感分析结果"""
    text: str
    detected_emotions: Dict[EmotionType, float]
    primary_emotion: EmotionType
    confidence: float
    sentiment_score: float  # -1.0 (negative) to 1.0 (positive)
    analysis_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'text': self.text,
            'detected_emotions': {e.value: v for e, v in self.detected_emotions.items()},
            'primary_emotion': self.primary_emotion.value,
            'confidence': self.confidence,
            'sentiment_score': self.sentiment_score,
            'analysis_time': self.analysis_time,
            'metadata': self.metadata
        }


@dataclass
class EmotionTransition:
    """情感转换"""
    from_emotion: EmotionState
    to_emotion: EmotionState
    trigger: str
    transition_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def to_intensity(self) -> float:
        """获取目标情感强度"""
        return self.to_emotion.intensity
    
    @property
    def from_intensity(self) -> float:
        """获取源情感强度"""
        return self.from_emotion.intensity
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'from_emotion': self.from_emotion.to_dict(),
            'to_emotion': self.to_emotion.to_dict(),
            'trigger': self.trigger,
            'transition_time': self.transition_time,
            'timestamp': self.timestamp.isoformat(),
            'to_intensity': self.to_intensity,
            'from_intensity': self.from_intensity
        }


@dataclass
class EmotionProfile:
    """情感档案"""
    user_id: str
    baseline_emotions: Dict[EmotionType, float] = field(default_factory=dict)
    emotion_history: List[EmotionState] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_emotion_state(self, emotion_state: EmotionState):
        """添加情感状态"""
        self.emotion_history.append(emotion_state)
        self.updated_at = datetime.now()
        
        # 保持历史记录在合理范围内
        if len(self.emotion_history) > 1000:
            self.emotion_history = self.emotion_history[-500:]
    
    def get_recent_emotions(self, limit: int = 10) -> List[EmotionState]:
        """获取最近的情感状态"""
        return self.emotion_history[-limit:] if limit > 0 else self.emotion_history
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'baseline_emotions': {e.value: v for e, v in self.baseline_emotions.items()},
            'emotion_history': [e.to_dict() for e in self.emotion_history],
            'preferences': self.preferences,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmotionProfile':
        """从字典创建"""
        baseline_emotions = {EmotionType(k): v for k, v in data.get('baseline_emotions', {}).items()}
        emotion_history = [EmotionState.from_dict(e) for e in data.get('emotion_history', [])]
        
        return cls(
            user_id=data['user_id'],
            baseline_emotions=baseline_emotions,
            emotion_history=emotion_history,
            preferences=data.get('preferences', {}),
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat()))
        )