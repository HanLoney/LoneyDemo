"""
情感服务实现
整合情感分析、状态管理和表达功能的完整服务
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from shared.interfaces.emotion_service import EmotionServiceInterface
from shared.models.emotion import (
    EmotionState, EmotionType, EmotionAnalysisResult, 
    EmotionTransition, EmotionProfile
)
from shared.utils import get_all_config, get_logger

from .emotion_analyzer import EmotionAnalyzer
from .emotion_manager import EmotionManager
from .emotion_expression import EmotionExpression, ExpressionStyle


class EmotionService(EmotionServiceInterface):
    """情感服务实现"""
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.config = get_all_config()
        self.logger = get_logger(__name__)
        
        # 初始化组件
        self.analyzer = EmotionAnalyzer()
        self.manager = EmotionManager(user_id)
        self.expression = EmotionExpression()
        
        # 服务配置
        self.emotion_config = self.config.get('services.emotion', {})
        self.auto_update = self.emotion_config.get('auto_update', True)
        self.expression_enabled = self.emotion_config.get('expression_enabled', True)
        
        self.logger.info(f"情感服务已初始化 - 用户: {user_id}")
    
    async def analyze_text_emotion(self, text: str, context: Optional[Dict[str, Any]] = None) -> EmotionAnalysisResult:
        """
        分析文本情感
        
        Args:
            text: 要分析的文本
            context: 上下文信息
            
        Returns:
            情感分析结果
        """
        try:
            self.logger.debug(f"开始分析文本情感: {text[:50]}...")
            
            # 使用分析器分析文本情感
            result = self.analyzer.analyze_text_emotion(text)
            
            # 如果启用自动更新，则更新AI的情感状态
            if self.auto_update and context and context.get('update_ai_emotion', True):
                # 分析用户输入对AI情感的影响
                emotion_impact = self.analyzer.analyze_ai_emotion_impact(
                    text, self.manager.get_current_state()
                )
                
                if emotion_impact:
                    # 更新AI情感状态
                    metadata = {
                        'trigger': 'user_input',
                        'user_text': text,
                        'analysis_result': result.to_dict(),
                        'context': context or {}
                    }
                    
                    self.manager.update_emotion(
                        emotion_impact['emotion_changes'],
                        emotion_impact['intensity_change'],
                        metadata
                    )
            
            self.logger.debug(f"文本情感分析完成: {result.primary_emotion.value}")
            return result
            
        except Exception as e:
            self.logger.error(f"分析文本情感失败: {e}")
            # 返回默认结果
            return EmotionAnalysisResult(
                text=text,
                detected_emotions={EmotionType.NEUTRAL: 0.8},
                primary_emotion=EmotionType.NEUTRAL,
                confidence=0.0,
                sentiment_score=0.0
            )
    
    def get_current_emotion_state_sync(self) -> EmotionState:
        """获取当前情感状态（同步版本）"""
        return self.manager.get_current_state()
    
    def get_current_state(self) -> EmotionState:
        """获取当前情感状态（同步方法）"""
        return self.manager.get_current_state()
    
    def get_emotion_state(self) -> EmotionState:
        """获取情感状态（兼容性方法）"""
        return self.get_current_emotion_state_sync()
    
    def analyze_text_emotion_sync(self, text: str, context: Optional[Dict[str, Any]] = None) -> EmotionAnalysisResult:
        """分析文本情感（同步版本）"""
        try:
            self.logger.debug(f"开始分析文本情感(同步): {text[:50]}...")
            
            # 使用分析器分析文本情感
            result = self.analyzer.analyze_text_emotion(text)
            
            self.logger.debug(f"文本情感分析完成(同步): {result.primary_emotion.value}")
            return result
            
        except Exception as e:
            self.logger.error(f"分析文本情感失败(同步): {e}")
            # 返回默认结果
            return EmotionAnalysisResult(
                text=text,
                detected_emotions={EmotionType.NEUTRAL: 0.8},
                primary_emotion=EmotionType.NEUTRAL,
                confidence=0.0,
                sentiment_score=0.0
            )
    
    def update_emotion_state(self, emotion_changes: Dict[str, float], 
                           intensity_change: float = 0.0,
                           metadata: Optional[Dict[str, Any]] = None) -> EmotionState:
        """
        更新情感状态
        
        Args:
            emotion_changes: 情感变化量字典
            intensity_change: 强度变化量
            metadata: 附加元数据
            
        Returns:
            更新后的情感状态
        """
        return self.manager.update_emotion(emotion_changes, intensity_change, metadata)
    
    def reset_emotion_state(self, emotion_type: Optional[EmotionType] = None, 
                          intensity: float = 0.5) -> EmotionState:
        """
        重置情感状态
        
        Args:
            emotion_type: 要重置到的情感类型
            intensity: 重置后的强度
            
        Returns:
            重置后的情感状态
        """
        return self.manager.reset_emotion(emotion_type, intensity)
    
    def get_emotion_history(self, limit: int = 10) -> List[EmotionTransition]:
        """获取情感变化历史"""
        return self.manager.get_emotion_history(limit)
    
    def update_emotion_from_input(self, user_input: str, user_emotion: Optional[EmotionAnalysisResult] = None) -> Optional[EmotionTransition]:
        """
        根据用户输入更新AI情感状态
        
        Args:
            user_input: 用户输入文本
            user_emotion: 用户情感分析结果
            
        Returns:
            AI情感变化信息
        """
        try:
            self.logger.info(f"开始更新AI情感状态 - 用户输入: {user_input[:50]}...")
            self.logger.info(f"auto_update状态: {self.auto_update}")
            
            if not self.auto_update:
                self.logger.warning("auto_update为False，跳过AI情感状态更新")
                return None
                
            # 分析用户输入对AI情感的影响
            current_state = self.get_current_emotion_state_sync()
            self.logger.info(f"当前AI情感状态: {current_state.primary_emotion.value}, 强度: {current_state.intensity}")
            
            try:
                ai_emotion_impact = self.analyzer.analyze_ai_emotion_impact(
                    user_input, current_state
                )
                
                self.logger.info(f"AI情感影响分析结果: {ai_emotion_impact}")
                
                if ai_emotion_impact and ai_emotion_impact.get('emotion_changes'):
                    self.logger.info("检测到情感变化，开始更新AI情感状态")
                    
                    # 更新AI情感状态
                    emotion_changes = {}
                    for emotion_type, intensity in ai_emotion_impact['emotion_changes'].items():
                        emotion_changes[emotion_type] = intensity * 0.8  # 调节影响强度 (从0.3增加到0.8)
                    
                    self.logger.info(f"处理后的情感变化: {emotion_changes}")
                    
                    # 更新情感状态
                    new_state = self.manager.update_emotion(
                        emotion_changes=emotion_changes,
                        intensity_change=ai_emotion_impact.get('intensity_change', 0.0) * 0.6,  # 从0.2增加到0.6
                        metadata={
                            "trigger": "user_input",
                            "user_input": user_input,
                            "user_emotion": user_emotion.primary_emotion.value if user_emotion else None,
                            "reasoning": ai_emotion_impact.get('reasoning', '')
                        }
                    )
                    
                    self.logger.info(f"更新后的AI情感状态: {new_state.primary_emotion.value}, 强度: {new_state.intensity}")
                    
                    # 获取最新的情感变化
                    history = self.manager.get_emotion_history(limit=1)
                    transition = history[0] if history else None
                    self.logger.info(f"返回的情感变化: {transition}")
                    return transition
                else:
                    self.logger.warning("未检测到有效的情感变化，AI情感状态保持不变")
                    
            except Exception as api_error:
                self.logger.error(f"AI情感影响分析失败: {api_error}")
                # 如果API调用失败，确保系统能够继续运行
                # 但不更新AI情感状态
                self.logger.warning("由于分析失败，AI情感状态保持不变")
                
        except Exception as e:
            self.logger.error(f"更新AI情感状态失败: {e}")
            
        return None
    
    def get_emotion_expressions(self, emotion_state: Optional[EmotionState] = None) -> Dict[str, Any]:
        """
        获取情感表达信息
        
        Args:
            emotion_state: 情感状态，None表示使用当前状态
            
        Returns:
            情感表达信息
        """
        if emotion_state is None:
            emotion_state = self.manager.get_current_state()
        
        return {
            "emoji": self.expression.get_emotion_emoji(
                emotion_state.primary_emotion, 
                emotion_state.intensity
            ),
            "description": self.expression.get_emotion_description(emotion_state),
            "primary_emotion": emotion_state.primary_emotion.value,
            "intensity": emotion_state.intensity,
            "emotions": {
                emotion.value: value 
                for emotion, value in emotion_state.emotions.items()
            },
            "last_update": emotion_state.last_update.isoformat()
        }
    
    def apply_emotion_to_response(self, response: str, 
                                style_preference: Optional[str] = None) -> str:
        """
        将情感应用到回复中
        
        Args:
            response: 原始回复内容
            style_preference: 风格偏好
            
        Returns:
            应用情感后的回复
        """
        if not self.expression_enabled:
            return response
        
        try:
            current_state = self.manager.get_current_state()
            
            # 转换风格偏好
            style = None
            if style_preference:
                try:
                    style = ExpressionStyle(style_preference)
                except ValueError:
                    self.logger.warning(f"未知的风格偏好: {style_preference}")
            
            return self.expression.apply_emotion_to_response(
                response, current_state, style
            )
            
        except Exception as e:
            self.logger.error(f"应用情感到回复失败: {e}")
            return response
    
    def configure_emotion_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        配置情感参数
        
        Args:
            parameters: 参数字典
            
        Returns:
            配置是否成功
        """
        try:
            # 更新管理器参数
            if 'stability' in parameters:
                self.manager.stability = max(0.0, min(1.0, parameters['stability']))
            
            if 'decay_rate' in parameters:
                self.manager.decay_rate = max(0.0, min(1.0, parameters['decay_rate']))
            
            if 'max_intensity' in parameters:
                self.manager.max_intensity = max(0.1, min(2.0, parameters['max_intensity']))
            
            # 更新服务参数
            if 'auto_update' in parameters:
                self.auto_update = bool(parameters['auto_update'])
            
            if 'expression_enabled' in parameters:
                self.expression_enabled = bool(parameters['expression_enabled'])
            
            self.logger.info(f"情感参数已更新: {parameters}")
            return True
            
        except Exception as e:
            self.logger.error(f"配置情感参数失败: {e}")
            return False
    
    def get_emotion_statistics(self) -> Dict[str, Any]:
        """获取情感统计信息"""
        try:
            # 获取基础统计
            stats = self.manager.get_emotion_statistics()
            
            # 添加服务级别的统计
            stats.update({
                "service_config": {
                    "auto_update": self.auto_update,
                    "expression_enabled": self.expression_enabled,
                    "stability": self.manager.stability,
                    "decay_rate": self.manager.decay_rate,
                    "max_intensity": self.manager.max_intensity
                },
                "user_id": self.user_id,
                "service_status": "active"
            })
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取情感统计失败: {e}")
            return {
                "error": str(e),
                "service_status": "error"
            }
    
    def clear_emotion_history(self) -> bool:
        """清空情感历史"""
        try:
            self.manager.clear_emotion_history()
            self.logger.info("情感历史已清空")
            return True
        except Exception as e:
            self.logger.error(f"清空情感历史失败: {e}")
            return False
    
    def export_emotion_data(self) -> Dict[str, Any]:
        """导出情感数据"""
        try:
            current_state = self.manager.get_current_state()
            history = self.manager.get_emotion_history(limit=0)  # 获取全部历史
            stats = self.get_emotion_statistics()
            
            return {
                "export_time": datetime.now().isoformat(),
                "user_id": self.user_id,
                "current_state": current_state.to_dict(),
                "emotion_history": [transition.to_dict() for transition in history],
                "statistics": stats,
                "emotion_profile": self.manager.emotion_profile.to_dict()
            }
            
        except Exception as e:
            self.logger.error(f"导出情感数据失败: {e}")
            return {"error": str(e)}
    
    def import_emotion_data(self, data: Dict[str, Any]) -> bool:
        """导入情感数据"""
        try:
            if 'current_state' in data:
                state = EmotionState()
                state.from_dict(data['current_state'])
                self.manager.current_state = state
            
            if 'emotion_history' in data:
                history = []
                for transition_data in data['emotion_history']:
                    transition = EmotionTransition()
                    transition.from_dict(transition_data)
                    history.append(transition)
                self.manager.emotion_history = history
            
            if 'emotion_profile' in data:
                profile = EmotionProfile(user_id=self.user_id)
                profile.from_dict(data['emotion_profile'])
                self.manager.emotion_profile = profile
            
            # 保存导入的数据
            self.manager._save_emotion_state()
            
            self.logger.info("情感数据导入成功")
            return True
            
        except Exception as e:
            self.logger.error(f"导入情感数据失败: {e}")
            return False
    
    async def batch_analyze_emotions(self, texts: List[str], 
                                   context: Optional[Dict[str, Any]] = None) -> List[EmotionAnalysisResult]:
        """
        批量分析文本情感
        
        Args:
            texts: 文本列表
            context: 上下文信息
            
        Returns:
            情感分析结果列表
        """
        results = []
        
        for text in texts:
            try:
                result = await self.analyze_text_emotion(text, context)
                results.append(result)
            except Exception as e:
                self.logger.error(f"批量分析中单个文本失败: {e}")
                # 添加默认结果
                results.append(EmotionAnalysisResult(
                    text=text,
                    detected_emotions={EmotionType.NEUTRAL: 0.8},
                    primary_emotion=EmotionType.NEUTRAL,
                    confidence=0.0,
                    sentiment_score=0.0
                ))
        
        return results
    
    def get_emotion_trends(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取情感趋势分析
        
        Args:
            hours: 分析的时间范围（小时）
            
        Returns:
            情感趋势数据
        """
        try:
            from datetime import timedelta
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_history = [
                transition for transition in self.manager.emotion_history
                if transition.timestamp >= cutoff_time
            ]
            
            if not recent_history:
                return {
                    "period_hours": hours,
                    "total_transitions": 0,
                    "trends": {},
                    "message": "没有足够的数据进行趋势分析"
                }
            
            # 计算趋势
            emotion_counts = {}
            intensity_sum = {}
            
            for transition in recent_history:
                emotion = transition.to_emotion.value
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
                intensity_sum[emotion] = intensity_sum.get(emotion, 0) + transition.to_intensity
            
            # 计算平均强度
            emotion_trends = {}
            for emotion, count in emotion_counts.items():
                emotion_trends[emotion] = {
                    "count": count,
                    "average_intensity": intensity_sum[emotion] / count,
                    "percentage": count / len(recent_history) * 100
                }
            
            return {
                "period_hours": hours,
                "total_transitions": len(recent_history),
                "trends": emotion_trends,
                "most_frequent": max(emotion_counts.items(), key=lambda x: x[1])[0],
                "analysis_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"获取情感趋势失败: {e}")
            return {"error": str(e)}
    
    # 实现抽象方法
    async def analyze_emotion(self, text: str, context: Optional[Dict[str, Any]] = None) -> EmotionAnalysisResult:
        """分析文本情感 - 抽象方法实现"""
        return await self.analyze_text_emotion(text, context)
    
    async def get_current_emotion_state(self) -> EmotionState:
        """获取当前情感状态 - 抽象方法实现"""
        return self.get_current_emotion_state_sync()
    
    async def update_emotion_state(self, emotion_data: Dict[str, Any]) -> EmotionState:
        """更新情感状态 - 抽象方法实现"""
        emotion_changes = emotion_data.get('emotion_changes', {})
        intensity_change = emotion_data.get('intensity_change', 0.0)
        metadata = emotion_data.get('metadata')
        return self.manager.update_emotion(emotion_changes, intensity_change, metadata)
    
    async def get_emotion_history(self, limit: int = 100) -> List[EmotionState]:
        """获取情感历史 - 抽象方法实现"""
        transitions = self.manager.get_emotion_history(limit)
        # 转换为EmotionState列表
        return [transition.to_state for transition in transitions]
    
    async def reset_emotion_state(self) -> EmotionState:
        """重置情感状态 - 抽象方法实现"""
        return self.manager.reset_emotion()
    
    async def get_emotion_expression(self, emotion_state: EmotionState) -> str:
        """获取情感表达 - 抽象方法实现"""
        expressions = self.get_emotion_expressions(emotion_state)
        return expressions.get('description', '')
    
    async def configure_emotion_parameters(self, parameters: Dict[str, Any]) -> bool:
        """配置情感参数 - 抽象方法实现"""
        try:
            # 更新配置
            if 'auto_update' in parameters:
                self.auto_update = parameters['auto_update']
            if 'expression_enabled' in parameters:
                self.expression_enabled = parameters['expression_enabled']
            
            self.logger.info(f"情感参数配置已更新: {parameters}")
            return True
        except Exception as e:
            self.logger.error(f"配置情感参数失败: {e}")
            return False