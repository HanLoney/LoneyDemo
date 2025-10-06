"""
情感服务接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from ..models.emotion import EmotionState, EmotionAnalysisResult


class EmotionServiceInterface(ABC):
    """情感服务接口"""
    
    @abstractmethod
    async def analyze_emotion(self, text: str, context: Optional[Dict[str, Any]] = None) -> EmotionAnalysisResult:
        """
        分析文本情感
        
        Args:
            text: 待分析文本
            context: 上下文信息
            
        Returns:
            情感分析结果
        """
        pass
    
    @abstractmethod
    async def get_current_emotion_state(self) -> EmotionState:
        """
        获取当前情感状态
        
        Returns:
            当前情感状态
        """
        pass
    
    @abstractmethod
    async def update_emotion_state(self, emotion_data: Dict[str, Any]) -> EmotionState:
        """
        更新情感状态
        
        Args:
            emotion_data: 情感数据
            
        Returns:
            更新后的情感状态
        """
        pass
    
    @abstractmethod
    async def get_emotion_history(self, limit: int = 100) -> List[EmotionState]:
        """
        获取情感历史
        
        Args:
            limit: 限制数量
            
        Returns:
            情感历史列表
        """
        pass
    
    @abstractmethod
    async def reset_emotion_state(self) -> EmotionState:
        """
        重置情感状态
        
        Returns:
            重置后的情感状态
        """
        pass
    
    @abstractmethod
    async def get_emotion_expression(self, emotion_state: EmotionState) -> str:
        """
        获取情感表达
        
        Args:
            emotion_state: 情感状态
            
        Returns:
            情感表达文本
        """
        pass
    
    @abstractmethod
    async def configure_emotion_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        配置情感参数
        
        Args:
            parameters: 情感参数
            
        Returns:
            是否成功
        """
        pass