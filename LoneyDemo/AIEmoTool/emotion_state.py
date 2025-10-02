"""
AI情感状态管理系统
实现AI的自主情感状态管理，包括情感连续性和独立性
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import math

class EmotionState:
    """AI情感状态类"""
    
    def __init__(self):
        # 基础情感维度 (使用多维情感模型)
        self.emotions = {
            "happiness": 0.5,      # 快乐 (0-1)
            "sadness": 0.2,        # 悲伤 (0-1)
            "anger": 0.1,          # 愤怒 (0-1)
            "fear": 0.1,           # 恐惧 (0-1)
            "surprise": 0.3,       # 惊讶 (0-1)
            "trust": 0.6,          # 信任 (0-1)
            "anticipation": 0.4,   # 期待 (0-1)
            "disgust": 0.1         # 厌恶 (0-1)
        }
        
        # 情感强度 (整体情感的激烈程度)
        self.intensity = 0.5  # 0-1
        
        # 情感稳定性 (抗干扰能力)
        self.stability = 0.7  # 0-1, 越高越稳定
        
        # 时间戳
        self.last_update = datetime.now()
        
        # 情感历史记录 (用于分析情感变化趋势)
        self.emotion_history = []
        
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "emotions": self.emotions.copy(),
            "intensity": self.intensity,
            "stability": self.stability,
            "last_update": self.last_update.isoformat(),
            "emotion_history": self.emotion_history[-10:]  # 只保留最近10条记录
        }
    
    def from_dict(self, data: Dict):
        """从字典格式加载"""
        self.emotions = data.get("emotions", self.emotions)
        self.intensity = data.get("intensity", self.intensity)
        self.stability = data.get("stability", self.stability)
        self.last_update = datetime.fromisoformat(data.get("last_update", datetime.now().isoformat()))
        self.emotion_history = data.get("emotion_history", [])
    
    def get_dominant_emotion(self) -> Tuple[str, float]:
        """获取主导情感"""
        dominant = max(self.emotions.items(), key=lambda x: x[1])
        return dominant[0], dominant[1]
    
    def get_emotion_summary(self) -> str:
        """获取情感状态摘要"""
        dominant_emotion, value = self.get_dominant_emotion()
        
        emotion_names = {
            "happiness": "快乐",
            "sadness": "悲伤", 
            "anger": "愤怒",
            "fear": "恐惧",
            "surprise": "惊讶",
            "trust": "信任",
            "anticipation": "期待",
            "disgust": "厌恶"
        }
        
        intensity_desc = "平静" if self.intensity < 0.3 else "适中" if self.intensity < 0.7 else "强烈"
        
        return f"{emotion_names.get(dominant_emotion, dominant_emotion)}({value:.2f}) - {intensity_desc}"


class EmotionStateManager:
    """AI情感状态管理器"""
    
    def __init__(self, state_file: str = "ai_emotion_state.json"):
        self.state_file = state_file
        self.current_state = EmotionState()
        self.load_state()
        
        # 情感衰减参数
        self.decay_rate = 0.95  # 情感自然衰减率
        self.baseline_emotions = {  # 基线情感状态
            "happiness": 0.5,
            "sadness": 0.2,
            "anger": 0.1,
            "fear": 0.1,
            "surprise": 0.3,
            "trust": 0.6,
            "anticipation": 0.4,
            "disgust": 0.1
        }
    
    def load_state(self):
        """加载情感状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.current_state.from_dict(data)
                print(f"✅ 加载AI情感状态: {self.current_state.get_emotion_summary()}")
            except Exception as e:
                print(f"⚠️ 加载情感状态失败: {e}")
        else:
            print("🆕 初始化新的AI情感状态")
    
    def save_state(self):
        """保存情感状态"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_state.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存情感状态失败: {e}")
    
    def apply_natural_decay(self):
        """应用自然情感衰减 - 让情感逐渐回归基线"""
        current_time = datetime.now()
        time_diff = (current_time - self.current_state.last_update).total_seconds() / 3600  # 小时
        
        # 计算衰减因子 (时间越长，衰减越多)
        decay_factor = math.exp(-time_diff * 0.1)  # 每10小时衰减约63%
        
        # 向基线情感衰减
        for emotion in self.current_state.emotions:
            current_value = self.current_state.emotions[emotion]
            baseline_value = self.baseline_emotions[emotion]
            
            # 线性插值向基线衰减
            self.current_state.emotions[emotion] = (
                current_value * decay_factor + baseline_value * (1 - decay_factor)
            )
        
        # 强度也逐渐衰减
        self.current_state.intensity = (
            self.current_state.intensity * decay_factor + 0.5 * (1 - decay_factor)
        )
    
    def update_emotion(self, emotion_changes: Dict[str, float], intensity_change: float = 0.0):
        """
        更新情感状态
        emotion_changes: 情感变化量 (-1 到 1)
        intensity_change: 强度变化量 (-1 到 1)
        """
        # 应用自然衰减
        self.apply_natural_decay()
        
        # 记录变化前的状态
        old_state = self.current_state.emotions.copy()
        
        # 计算稳定性影响因子 (稳定性越高，变化越小)
        stability_factor = 1.0 - self.current_state.stability * 0.5
        
        # 更新各个情感维度
        for emotion, change in emotion_changes.items():
            if emotion in self.current_state.emotions:
                # 应用稳定性影响
                actual_change = change * stability_factor
                
                # 更新情感值，确保在0-1范围内
                new_value = self.current_state.emotions[emotion] + actual_change
                self.current_state.emotions[emotion] = max(0.0, min(1.0, new_value))
        
        # 更新强度
        if intensity_change != 0:
            actual_intensity_change = intensity_change * stability_factor
            new_intensity = self.current_state.intensity + actual_intensity_change
            self.current_state.intensity = max(0.0, min(1.0, new_intensity))
        
        # 记录情感变化历史
        change_record = {
            "timestamp": datetime.now().isoformat(),
            "changes": emotion_changes,
            "intensity_change": intensity_change,
            "result_summary": self.current_state.get_emotion_summary()
        }
        self.current_state.emotion_history.append(change_record)
        
        # 更新时间戳
        self.current_state.last_update = datetime.now()
        
        # 保存状态
        self.save_state()
        
        print(f"🎭 AI情感状态更新: {self.current_state.get_emotion_summary()}")
    
    def get_current_state(self) -> EmotionState:
        """获取当前情感状态"""
        # 应用自然衰减
        self.apply_natural_decay()
        return self.current_state
    
    def reset_to_baseline(self):
        """重置到基线情感状态"""
        self.current_state.emotions = self.baseline_emotions.copy()
        self.current_state.intensity = 0.5
        self.current_state.last_update = datetime.now()
        self.save_state()
        print("🔄 AI情感状态已重置到基线")
    
    def adjust_stability(self, new_stability: float):
        """调整情感稳定性"""
        self.current_state.stability = max(0.0, min(1.0, new_stability))
        self.save_state()
        print(f"⚖️ AI情感稳定性调整为: {self.current_state.stability:.2f}")