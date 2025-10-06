"""
情感模块
提供AI情感分析、状态管理和表达功能
"""

from .emotion_analyzer import EmotionAnalyzer
from .emotion_manager import EmotionManager
from .emotion_expression import EmotionExpression, ExpressionStyle
from .emotion_service import EmotionService

__all__ = [
    'EmotionAnalyzer',
    'EmotionManager', 
    'EmotionExpression',
    'ExpressionStyle',
    'EmotionService'
]

# 版本信息
__version__ = '1.0.0'
__author__ = 'LoneyDemo Team'
__description__ = 'AI情感分析与表达模块'