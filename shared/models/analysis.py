"""
分析相关数据模型
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum


class AnalysisType(Enum):
    """分析类型"""
    GENERAL = "general"
    SENTIMENT = "sentiment"
    KEYWORD = "keyword"
    SUMMARY = "summary"
    EMOTION = "emotion"
    TOPIC = "topic"
    LANGUAGE = "language"


@dataclass
class AnalysisResult:
    """分析结果"""
    analysis_id: str
    analysis_type: AnalysisType
    content: str
    results: Dict[str, Any]
    confidence: float
    processing_time: float
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'analysis_id': self.analysis_id,
            'analysis_type': self.analysis_type.value,
            'content': self.content,
            'results': self.results,
            'confidence': self.confidence,
            'processing_time': self.processing_time,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """从字典创建"""
        return cls(
            analysis_id=data['analysis_id'],
            analysis_type=AnalysisType(data['analysis_type']),
            content=data['content'],
            results=data['results'],
            confidence=data['confidence'],
            processing_time=data['processing_time'],
            created_at=datetime.fromisoformat(data['created_at']),
            metadata=data.get('metadata', {})
        )


@dataclass
class ContentSummary:
    """内容摘要"""
    original_content: str
    summary: str
    key_points: List[str]
    word_count: int
    summary_ratio: float  # 摘要比例
    language: str = "zh"
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'original_content': self.original_content,
            'summary': self.summary,
            'key_points': self.key_points,
            'word_count': self.word_count,
            'summary_ratio': self.summary_ratio,
            'language': self.language,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentSummary':
        """从字典创建"""
        return cls(
            original_content=data['original_content'],
            summary=data['summary'],
            key_points=data['key_points'],
            word_count=data['word_count'],
            summary_ratio=data['summary_ratio'],
            language=data.get('language', 'zh'),
            created_at=datetime.fromisoformat(data['created_at'])
        )


@dataclass
class KeywordExtraction:
    """关键词提取"""
    content: str
    keywords: List[Dict[str, Any]]  # [{"keyword": str, "score": float, "frequency": int}]
    extraction_method: str
    total_keywords: int
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_top_keywords(self, limit: int = 10) -> List[str]:
        """获取排名前N的关键词"""
        sorted_keywords = sorted(self.keywords, key=lambda x: x['score'], reverse=True)
        return [kw['keyword'] for kw in sorted_keywords[:limit]]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'content': self.content,
            'keywords': self.keywords,
            'extraction_method': self.extraction_method,
            'total_keywords': self.total_keywords,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class SentimentAnalysis:
    """情感分析"""
    content: str
    sentiment_score: float  # -1.0 (negative) to 1.0 (positive)
    sentiment_label: str  # positive, negative, neutral
    confidence: float
    emotions: Dict[str, float]  # 具体情感分布
    analysis_method: str
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def is_positive(self) -> bool:
        """是否为正面情感"""
        return self.sentiment_score > 0.1
    
    @property
    def is_negative(self) -> bool:
        """是否为负面情感"""
        return self.sentiment_score < -0.1
    
    @property
    def is_neutral(self) -> bool:
        """是否为中性情感"""
        return -0.1 <= self.sentiment_score <= 0.1
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'content': self.content,
            'sentiment_score': self.sentiment_score,
            'sentiment_label': self.sentiment_label,
            'confidence': self.confidence,
            'emotions': self.emotions,
            'analysis_method': self.analysis_method,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class TopicAnalysis:
    """主题分析"""
    content: str
    topics: List[Dict[str, Any]]  # [{"topic": str, "probability": float, "keywords": List[str]}]
    dominant_topic: str
    topic_distribution: Dict[str, float]
    analysis_method: str
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'content': self.content,
            'topics': self.topics,
            'dominant_topic': self.dominant_topic,
            'topic_distribution': self.topic_distribution,
            'analysis_method': self.analysis_method,
            'created_at': self.created_at.isoformat()
        }