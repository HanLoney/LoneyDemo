"""
AI情感平滑算法
防止情感剧烈波动，保持AI的情感独立性和稳定性
"""

import math
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

class EmotionSmoother:
    """情感平滑处理器"""
    
    def __init__(self):
        # 平滑参数
        self.max_single_change = 0.25      # 单次最大变化量
        self.momentum_factor = 0.8         # 动量因子 (历史趋势影响)
        self.resistance_factor = 0.6       # 阻力因子 (抗变化能力)
        self.time_decay_factor = 0.95      # 时间衰减因子
        
        # 情感变化历史 (用于计算趋势)
        self.change_history = []
        self.max_history_length = 10
        
        # 情感边界保护
        self.emotion_bounds = {
            "happiness": (0.1, 0.9),    # 快乐不会完全消失，也不会过度
            "sadness": (0.0, 0.7),      # 悲伤可以为0，但不会过度
            "anger": (0.0, 0.6),        # 愤怒可以为0，但不会过度
            "fear": (0.0, 0.5),         # 恐惧可以为0，适度限制
            "surprise": (0.0, 0.8),     # 惊讶可以较高
            "trust": (0.2, 0.9),        # 信任保持一定基线
            "anticipation": (0.1, 0.8), # 期待保持适度
            "disgust": (0.0, 0.4)       # 厌恶限制较低
        }
    
    def smooth_emotion_changes(self, 
                             current_emotions: Dict[str, float],
                             proposed_changes: Dict[str, float],
                             current_intensity: float,
                             proposed_intensity_change: float,
                             interaction_context: Dict = None) -> Tuple[Dict[str, float], float]:
        """
        平滑情感变化
        
        Args:
            current_emotions: 当前情感状态
            proposed_changes: 建议的情感变化
            current_intensity: 当前情感强度
            proposed_intensity_change: 建议的强度变化
            interaction_context: 交互上下文信息
            
        Returns:
            (平滑后的情感变化, 平滑后的强度变化)
        """
        
        # 1. 应用变化幅度限制
        limited_changes = self._apply_change_limits(proposed_changes)
        
        # 2. 考虑历史趋势和动量
        momentum_adjusted_changes = self._apply_momentum(limited_changes)
        
        # 3. 应用阻力和独立性保护
        resistance_adjusted_changes = self._apply_resistance(momentum_adjusted_changes, interaction_context)
        
        # 4. 边界保护
        final_changes = self._apply_boundary_protection(current_emotions, resistance_adjusted_changes)
        
        # 5. 平滑强度变化
        final_intensity_change = self._smooth_intensity_change(
            current_intensity, proposed_intensity_change
        )
        
        # 6. 记录变化历史
        self._record_change_history(final_changes, final_intensity_change)
        
        return final_changes, final_intensity_change
    
    def _apply_change_limits(self, proposed_changes: Dict[str, float]) -> Dict[str, float]:
        """应用单次变化幅度限制"""
        limited_changes = {}
        
        for emotion, change in proposed_changes.items():
            # 限制单次变化幅度
            if abs(change) > self.max_single_change:
                # 保持变化方向，但限制幅度
                limited_changes[emotion] = (
                    self.max_single_change if change > 0 else -self.max_single_change
                )
            else:
                limited_changes[emotion] = change
        
        return limited_changes
    
    def _apply_momentum(self, changes: Dict[str, float]) -> Dict[str, float]:
        """应用动量效应 - 考虑历史变化趋势"""
        if not self.change_history:
            return changes
        
        momentum_adjusted = {}
        
        # 计算最近的变化趋势
        recent_trends = self._calculate_recent_trends()
        
        for emotion, change in changes.items():
            trend = recent_trends.get(emotion, 0.0)
            
            # 如果变化方向与趋势一致，稍微增强
            # 如果变化方向与趋势相反，稍微减弱
            if change * trend > 0:  # 同方向
                momentum_effect = 1.0 + (self.momentum_factor - 1.0) * 0.3
            else:  # 反方向
                momentum_effect = 1.0 - (self.momentum_factor - 1.0) * 0.2
            
            momentum_adjusted[emotion] = change * momentum_effect
        
        return momentum_adjusted
    
    def _apply_resistance(self, changes: Dict[str, float], context: Dict = None) -> Dict[str, float]:
        """应用阻力效应 - 保持情感独立性"""
        resistance_adjusted = {}
        
        for emotion, change in changes.items():
            # 基础阻力
            resistance = self.resistance_factor
            
            # 根据上下文调整阻力
            if context:
                interaction_type = context.get("interaction_type", "neutral")
                
                # 对于极端交互类型，增加阻力
                if interaction_type in ["very_positive", "very_negative"]:
                    resistance *= 1.2
                elif interaction_type == "neutral":
                    resistance *= 0.9
            
            # 应用阻力
            resistance_adjusted[emotion] = change * (1.0 - resistance * 0.3)
        
        return resistance_adjusted
    
    def _apply_boundary_protection(self, 
                                 current_emotions: Dict[str, float], 
                                 changes: Dict[str, float]) -> Dict[str, float]:
        """应用边界保护 - 确保情感值在合理范围内"""
        protected_changes = {}
        
        for emotion, change in changes.items():
            current_value = current_emotions.get(emotion, 0.5)
            new_value = current_value + change
            
            # 获取该情感的边界
            min_bound, max_bound = self.emotion_bounds.get(emotion, (0.0, 1.0))
            
            # 边界保护
            if new_value < min_bound:
                protected_changes[emotion] = min_bound - current_value
            elif new_value > max_bound:
                protected_changes[emotion] = max_bound - current_value
            else:
                protected_changes[emotion] = change
        
        return protected_changes
    
    def _smooth_intensity_change(self, current_intensity: float, proposed_change: float) -> float:
        """平滑强度变化"""
        # 限制强度变化幅度
        max_intensity_change = 0.2
        
        if abs(proposed_change) > max_intensity_change:
            smoothed_change = (
                max_intensity_change if proposed_change > 0 else -max_intensity_change
            )
        else:
            smoothed_change = proposed_change
        
        # 边界保护
        new_intensity = current_intensity + smoothed_change
        if new_intensity < 0.1:
            smoothed_change = 0.1 - current_intensity
        elif new_intensity > 0.9:
            smoothed_change = 0.9 - current_intensity
        
        return smoothed_change
    
    def _calculate_recent_trends(self) -> Dict[str, float]:
        """计算最近的情感变化趋势"""
        if len(self.change_history) < 2:
            return {}
        
        trends = {}
        recent_changes = self.change_history[-3:]  # 最近3次变化
        
        for emotion in ["happiness", "sadness", "anger", "fear", "surprise", "trust", "anticipation", "disgust"]:
            emotion_changes = [
                change_record["changes"].get(emotion, 0.0) 
                for change_record in recent_changes
            ]
            
            if emotion_changes:
                # 计算加权平均趋势 (越近的权重越大)
                weights = [0.5, 0.3, 0.2][:len(emotion_changes)]
                weighted_trend = sum(
                    change * weight 
                    for change, weight in zip(reversed(emotion_changes), weights)
                )
                trends[emotion] = weighted_trend
        
        return trends
    
    def _record_change_history(self, changes: Dict[str, float], intensity_change: float):
        """记录变化历史"""
        change_record = {
            "timestamp": datetime.now(),
            "changes": changes.copy(),
            "intensity_change": intensity_change
        }
        
        self.change_history.append(change_record)
        
        # 限制历史记录长度
        if len(self.change_history) > self.max_history_length:
            self.change_history.pop(0)
    
    def adjust_smoothing_parameters(self, 
                                  max_change: float = None,
                                  momentum: float = None,
                                  resistance: float = None):
        """调整平滑参数"""
        if max_change is not None:
            self.max_single_change = max(0.05, min(0.5, max_change))
        
        if momentum is not None:
            self.momentum_factor = max(0.0, min(1.0, momentum))
        
        if resistance is not None:
            self.resistance_factor = max(0.0, min(1.0, resistance))
        
        print(f"🎛️ 平滑参数已调整: 最大变化={self.max_single_change:.2f}, "
              f"动量={self.momentum_factor:.2f}, 阻力={self.resistance_factor:.2f}")
    
    def get_smoothing_status(self) -> Dict:
        """获取平滑器状态信息"""
        return {
            "parameters": {
                "max_single_change": self.max_single_change,
                "momentum_factor": self.momentum_factor,
                "resistance_factor": self.resistance_factor
            },
            "history_length": len(self.change_history),
            "recent_trends": self._calculate_recent_trends() if self.change_history else {}
        }