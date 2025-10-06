"""
情感状态管理器
管理AI的情感状态，包括状态更新、持久化和历史记录
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from shared.models.emotion import EmotionState, EmotionType, EmotionTransition, EmotionProfile
from shared.utils import get_all_config, get_logger, FileUtils, TimeUtils


class EmotionManager:
    """情感状态管理器"""
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.config = get_all_config()
        self.logger = get_logger(__name__)
        
        # 情感配置
        self.emotion_config = self.config.get('services.emotion', {})
        self.stability = self.emotion_config.get('stability', 0.7)
        self.decay_rate = self.emotion_config.get('decay_rate', 0.1)
        self.max_intensity = self.emotion_config.get('max_intensity', 1.0)
        
        # 状态文件路径
        self.state_file = Path(self.config.get('app.data_dir', 'data')) / f"emotion_state_{user_id}.json"
        
        # 当前情感状态
        self.current_state = self._load_emotion_state()
        
        # 情感历史
        self.emotion_history: List[EmotionTransition] = []
        
        # 用户情感档案
        self.emotion_profile = self._load_emotion_profile()
    
    def get_current_state(self) -> EmotionState:
        """获取当前情感状态"""
        # 应用自然衰减
        self._apply_natural_decay()
        return self.current_state
    
    def update_emotion(self, emotion_changes: Dict[str, float], intensity_change: float = 0.0, 
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
        try:
            # 记录变化前的状态
            old_state = EmotionState(
                primary_emotion=self.current_state.primary_emotion,
                intensity=self.current_state.intensity,
                emotions=self.current_state.emotions.copy()
            )
            
            # 应用自然衰减
            self._apply_natural_decay()
            
            # 计算稳定性影响因子 (调整为更敏感的变化)
            stability_factor = 1.0 - self.stability * 0.2  # 从0.5减少到0.2，让稳定性影响更小
            
            # 更新各个情感维度
            for emotion_name, change in emotion_changes.items():
                try:
                    emotion_type = EmotionType(emotion_name)
                    
                    # 如果情感类型不存在，初始化为0.1
                    if emotion_type not in self.current_state.emotions:
                        self.current_state.emotions[emotion_type] = 0.1
                        self.logger.debug(f"初始化情感类型: {emotion_type.value}")
                    
                    # 应用稳定性影响
                    actual_change = change * stability_factor
                    
                    # 更新情感值，确保在0-1范围内
                    current_value = self.current_state.emotions[emotion_type]
                    new_value = current_value + actual_change
                    self.current_state.emotions[emotion_type] = max(0.0, min(1.0, new_value))
                    
                    self.logger.debug(f"更新情感 {emotion_type.value}: {current_value:.3f} -> {new_value:.3f} (变化: {actual_change:.3f})")
                    
                except ValueError:
                    self.logger.warning(f"未知的情感类型: {emotion_name}")
                    continue
            
            # 更新强度
            if intensity_change != 0:
                actual_intensity_change = intensity_change * stability_factor
                new_intensity = self.current_state.intensity + actual_intensity_change
                self.current_state.intensity = max(0.0, min(self.max_intensity, new_intensity))
            
            # 更新主要情感
            self._update_primary_emotion()
            
            # 更新时间戳
            self.current_state.last_update = TimeUtils.now()
            
            # 记录情感变化
            transition = EmotionTransition(
                from_emotion=old_state,
                to_emotion=self.current_state,
                trigger=metadata.get('trigger', 'unknown') if metadata else 'unknown',
                transition_time=0.0  # 可以后续计算实际转换时间
            )
            
            self.emotion_history.append(transition)
            
            # 限制历史记录长度
            max_history = self.emotion_config.get('max_history', 100)
            if len(self.emotion_history) > max_history:
                self.emotion_history = self.emotion_history[-max_history:]
            
            # 更新用户情感档案
            self.emotion_profile.add_emotion_state(self.current_state)
            
            # 保存状态
            self._save_emotion_state()
            
            self.logger.debug(f"情感状态已更新: {self.current_state.primary_emotion.value} ({self.current_state.intensity:.2f})")
            
            return self.current_state
            
        except Exception as e:
            self.logger.error(f"更新情感状态失败: {e}")
            return self.current_state
    
    def reset_emotion(self, emotion_type: Optional[EmotionType] = None, intensity: float = 0.5) -> EmotionState:
        """
        重置情感状态
        
        Args:
            emotion_type: 要重置到的情感类型，None表示重置为中性
            intensity: 重置后的强度
            
        Returns:
            重置后的情感状态
        """
        if emotion_type is None:
            emotion_type = EmotionType.NEUTRAL
        
        # 重置所有情感值
        for emotion in EmotionType:
            if emotion == emotion_type:
                self.current_state.emotions[emotion] = 0.8
            else:
                self.current_state.emotions[emotion] = 0.1
        
        self.current_state.primary_emotion = emotion_type
        self.current_state.intensity = intensity
        self.current_state.last_update = TimeUtils.now()
        
        # 保存状态
        self._save_emotion_state()
        
        self.logger.info(f"情感状态已重置为: {emotion_type.value} ({intensity:.2f})")
        return self.current_state
    
    def get_emotion_history(self, limit: int = 10) -> List[EmotionTransition]:
        """获取情感变化历史"""
        return self.emotion_history[-limit:] if limit > 0 else self.emotion_history
    
    def get_emotion_statistics(self) -> Dict[str, Any]:
        """获取情感统计信息"""
        if not self.emotion_history:
            return {
                "total_transitions": 0,
                "most_common_emotion": EmotionType.NEUTRAL.value,
                "average_intensity": 0.5,
                "emotion_distribution": {}
            }
        
        # 统计情感分布
        emotion_counts = {}
        total_intensity = 0
        
        for transition in self.emotion_history:
            emotion = transition.to_emotion.primary_emotion.value
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            total_intensity += transition.to_intensity
        
        most_common_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
        average_intensity = total_intensity / len(self.emotion_history)
        
        # 计算情感分布百分比
        total_count = len(self.emotion_history)
        emotion_distribution = {
            emotion: count / total_count * 100
            for emotion, count in emotion_counts.items()
        }
        
        return {
            "total_transitions": len(self.emotion_history),
            "most_common_emotion": most_common_emotion,
            "average_intensity": average_intensity,
            "emotion_distribution": emotion_distribution,
            "current_state": {
                "emotion": self.current_state.primary_emotion.value,
                "intensity": self.current_state.intensity,
                "last_update": self.current_state.last_update.isoformat()
            }
        }
    
    def clear_emotion_history(self) -> None:
        """清空情感历史"""
        self.emotion_history.clear()
        self.emotion_profile = EmotionProfile(user_id=self.user_id)
        self._save_emotion_state()
        self.logger.info("情感历史已清空")
    
    def _load_emotion_state(self) -> EmotionState:
        """加载情感状态"""
        try:
            if self.state_file.exists():
                data = FileUtils.read_json(self.state_file)
                if data:
                    # 从字典创建EmotionState
                    return EmotionState(
                        primary_emotion=EmotionType(data.get('primary_emotion', 'neutral')),
                        intensity=data.get('intensity', 0.5),
                        emotions={EmotionType(k): v for k, v in data.get('emotions', {}).items()},
                        timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
                        context=data.get('context', {})
                    )
        except Exception as e:
            self.logger.error(f"加载情感状态失败: {e}")
        
        # 返回默认状态 - 初始化所有情感类型，让neutral不会过于占主导
        default_emotions = {}
        for emotion_type in EmotionType:
            if emotion_type == EmotionType.NEUTRAL:
                default_emotions[emotion_type] = 0.3  # 降低neutral的初始值
            else:
                default_emotions[emotion_type] = 0.1  # 给其他情感一个基础值
        
        self.logger.info(f"初始化默认情感状态，包含情感类型: {list(default_emotions.keys())}")
        
        return EmotionState(
            primary_emotion=EmotionType.NEUTRAL,
            intensity=0.5,
            emotions=default_emotions
        )
    
    def _save_emotion_state(self) -> None:
        """保存情感状态"""
        try:
            data = {
                "current_state": self.current_state.to_dict(),
                "emotion_history": [transition.to_dict() for transition in self.emotion_history[-50:]],  # 只保存最近50条
                "emotion_profile": self.emotion_profile.to_dict(),
                "last_save": TimeUtils.now().isoformat()
            }
            
            FileUtils.write_json(self.state_file, data)
        except Exception as e:
            self.logger.error(f"保存情感状态失败: {e}")
    
    def _load_emotion_profile(self) -> EmotionProfile:
        """加载用户情感档案"""
        try:
            if self.state_file.exists():
                data = FileUtils.read_json(self.state_file)
                if data and 'emotion_profile' in data:
                    profile = EmotionProfile(user_id=self.user_id)
                    profile.from_dict(data['emotion_profile'])
                    return profile
        except Exception as e:
            self.logger.error(f"加载情感档案失败: {e}")
        
        return EmotionProfile(user_id=self.user_id)
    
    def _apply_natural_decay(self) -> None:
        """应用自然衰减"""
        try:
            now = TimeUtils.now()
            time_diff = TimeUtils.time_diff_seconds(now, self.current_state.last_update)
            
            # 如果时间差小于1分钟，不应用衰减
            if time_diff < 60:
                return
            
            # 计算衰减因子（基于时间）
            decay_factor = min(time_diff / 3600 * self.decay_rate, 0.1)  # 每小时最多衰减10%
            
            # 向中性状态衰减
            neutral_target = 0.5
            for emotion_type in EmotionType:
                # 安全地获取当前情感值，如果不存在则使用默认值
                current_value = self.current_state.emotions.get(emotion_type, 0.0)
                
                if emotion_type == EmotionType.NEUTRAL:
                    # 中性情感向上衰减
                    if current_value < neutral_target:
                        self.current_state.emotions[emotion_type] = min(
                            neutral_target, current_value + decay_factor
                        )
                else:
                    # 其他情感向下衰减
                    if current_value > 0.1:
                        self.current_state.emotions[emotion_type] = max(
                            0.1, current_value - decay_factor
                        )
                    elif current_value > 0.0:
                        # 如果值很小但大于0，设置为0
                        self.current_state.emotions[emotion_type] = 0.0
            
            # 强度向中等水平衰减
            if self.current_state.intensity > 0.5:
                self.current_state.intensity = max(0.5, self.current_state.intensity - decay_factor)
            elif self.current_state.intensity < 0.5:
                self.current_state.intensity = min(0.5, self.current_state.intensity + decay_factor)
            
            # 更新时间戳
            self.current_state.last_update = now
            
            # 更新主要情感
            self._update_primary_emotion()
            
        except Exception as e:
            self.logger.error(f"应用自然衰减失败: {e}")
    
    def _update_primary_emotion(self) -> None:
        """更新主要情感"""
        try:
            # 找到值最大的情感
            max_emotion = max(self.current_state.emotions.items(), key=lambda x: x[1])
            self.current_state.primary_emotion = max_emotion[0]
        except Exception as e:
            self.logger.error(f"更新主要情感失败: {e}")
            self.current_state.primary_emotion = EmotionType.NEUTRAL