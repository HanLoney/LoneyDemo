"""
基础事件类
"""
from abc import ABC
from datetime import datetime
from typing import Any, Dict
import uuid


class BaseEvent(ABC):
    """基础事件类"""
    
    def __init__(self, data: Dict[str, Any] = None):
        """
        初始化事件
        
        Args:
            data: 事件数据
        """
        self.id = str(uuid.uuid4())
        self.timestamp = datetime.now()
        self.data = data or {}
        self.event_type = self.__class__.__name__
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type,
            'data': self.data
        }
    
    def __str__(self) -> str:
        return f"{self.event_type}(id={self.id}, timestamp={self.timestamp})"
    
    def __repr__(self) -> str:
        return self.__str__()