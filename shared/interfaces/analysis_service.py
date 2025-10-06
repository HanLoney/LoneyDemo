"""
分析服务接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from ..models.analysis import AnalysisResult, ContentSummary


class AnalysisServiceInterface(ABC):
    """分析服务接口"""
    
    @abstractmethod
    async def analyze_content(self, content: str, analysis_type: str = "general") -> AnalysisResult:
        """
        分析内容
        
        Args:
            content: 待分析内容
            analysis_type: 分析类型
            
        Returns:
            分析结果
        """
        pass
    
    @abstractmethod
    async def summarize_content(self, content: str, max_length: int = 200) -> ContentSummary:
        """
        内容摘要
        
        Args:
            content: 待摘要内容
            max_length: 最大长度
            
        Returns:
            内容摘要
        """
        pass
    
    @abstractmethod
    async def extract_keywords(self, content: str, max_keywords: int = 10) -> List[str]:
        """
        提取关键词
        
        Args:
            content: 待分析内容
            max_keywords: 最大关键词数量
            
        Returns:
            关键词列表
        """
        pass
    
    @abstractmethod
    async def analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """
        情感分析
        
        Args:
            content: 待分析内容
            
        Returns:
            情感分析结果
        """
        pass
    
    @abstractmethod
    async def get_analysis_history(self, limit: int = 50) -> List[AnalysisResult]:
        """
        获取分析历史
        
        Args:
            limit: 限制数量
            
        Returns:
            分析历史列表
        """
        pass
    
    @abstractmethod
    async def clear_analysis_history(self) -> bool:
        """
        清空分析历史
        
        Returns:
            是否成功
        """
        pass