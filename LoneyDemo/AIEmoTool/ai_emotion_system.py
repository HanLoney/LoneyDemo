"""
AI自主情感系统 - 主程序
整合所有功能模块，实现AI的自主情感管理
"""

import os
import sys
from datetime import datetime
from typing import Dict, Optional

# 导入自定义模块
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from emotion_state import EmotionStateManager, EmotionState
from emotion_analyzer import AIEmotionAnalyzer
from emotion_smoother import EmotionSmoother
from emotion_expression import EmotionExpression

# 导入LLM客户端
from openai import OpenAI

class AIEmotionSystem:
    """AI自主情感系统"""
    
    def __init__(self, state_file: str = "ai_emotion_state.json"):
        print("🤖 初始化AI自主情感系统...")
        
        # 初始化各个组件
        self.state_manager = EmotionStateManager(state_file)
        self.emotion_analyzer = AIEmotionAnalyzer()
        self.emotion_smoother = EmotionSmoother()
        self.emotion_expression = EmotionExpression()
        
        # 初始化LLM客户端 (用于生成回复)
        self.llm_client = OpenAI(
            api_key="sk-6ae0aeb3b5624855aa8ea15ef0350f65",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        # 系统配置
        self.config = {
            "enable_emotion_analysis": True,
            "enable_emotion_smoothing": True,
            "enable_emotion_expression": True,
            "auto_save_state": True,
            "debug_mode": False
        }
        
        print("✅ AI自主情感系统初始化完成！")
        self._display_current_emotion()
    
    def process_user_input(self, user_input: str) -> str:
        """
        处理用户输入，更新AI情感状态，并生成带有情感的回复
        
        Args:
            user_input: 用户输入的文本
            
        Returns:
            AI的情感化回复
        """
        
        print(f"\n📝 用户输入: {user_input}")
        
        # 1. 获取当前情感状态
        current_state = self.state_manager.get_current_state()
        current_emotion_summary = current_state.get_emotion_summary()
        
        if self.config["debug_mode"]:
            print(f"🎭 当前情感状态: {current_emotion_summary}")
        
        # 2. 分析用户输入对AI情感的影响
        emotion_impact = None
        if self.config["enable_emotion_analysis"]:
            emotion_impact = self.emotion_analyzer.analyze_emotion_impact(
                user_input, current_emotion_summary
            )
            
            if emotion_impact and self.config["debug_mode"]:
                print(f"📊 情感影响分析: {emotion_impact['interaction_type']}")
                print(f"💭 分析原因: {emotion_impact['reasoning']}")
        
        # 3. 应用情感平滑算法
        if emotion_impact and self.config["enable_emotion_smoothing"]:
            smoothed_changes, smoothed_intensity = self.emotion_smoother.smooth_emotion_changes(
                current_state.emotions,
                emotion_impact["emotion_changes"],
                current_state.intensity,
                emotion_impact["intensity_change"],
                {"interaction_type": emotion_impact.get("interaction_type", "neutral")}
            )
            
            # 更新情感状态
            self.state_manager.update_emotion(smoothed_changes, smoothed_intensity)
            
            if self.config["debug_mode"]:
                print(f"🎛️ 平滑后的情感变化已应用")
        
        # 4. 生成基础回复
        base_response = self._generate_base_response(user_input)
        
        # 5. 应用情感表达
        final_response = base_response
        if self.config["enable_emotion_expression"]:
            updated_state = self.state_manager.get_current_state()
            final_response = self.emotion_expression.generate_emotional_response(
                base_response, updated_state, "general"
            )
        
        # 6. 显示更新后的情感状态
        self._display_current_emotion()
        
        return final_response
    
    def _generate_base_response(self, user_input: str) -> str:
        """生成基础回复内容"""
        try:
            # 获取当前情感状态用于指导回复生成
            current_state = self.state_manager.get_current_state()
            dominant_emotion, _ = current_state.get_dominant_emotion()
            
            # 构建系统提示词
            system_prompt = f"""你是一个有情感的AI助手。当前你的主要情感状态是{dominant_emotion}，情感强度为{current_state.intensity:.2f}。

请根据你的当前情感状态来回复用户，但要保持专业和有帮助。你的回复应该：
1. 体现出你当前的情感状态
2. 回复要简洁明了，不要过长

请直接回复用户，不要解释你的情感状态。"""
            
            response = self.llm_client.chat.completions.create(
                model="qwen-flash",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"⚠️ 生成回复失败: {e}")
            return "抱歉，我现在有点困惑，请稍后再试。"
    
    def _display_current_emotion(self):
        """显示当前情感状态"""
        current_state = self.state_manager.get_current_state()
        dominant_emotion, emotion_value = current_state.get_dominant_emotion()
        
        emotion_names = {
            "happiness": "😊 快乐",
            "sadness": "😔 悲伤",
            "anger": "😠 愤怒",
            "fear": "😰 恐惧",
            "surprise": "😲 惊讶",
            "trust": "😌 信任",
            "anticipation": "✨ 期待",
            "disgust": "😤 厌恶"
        }
        
        emotion_display = emotion_names.get(dominant_emotion, dominant_emotion)
        intensity_desc = "平静" if current_state.intensity < 0.3 else "适中" if current_state.intensity < 0.7 else "强烈"
        
        print(f"🎭 AI当前情感: {emotion_display} ({emotion_value:.2f}) | 强度: {intensity_desc} ({current_state.intensity:.2f})")
    
    def get_emotion_greeting(self) -> str:
        """获取情感化的问候语"""
        current_state = self.state_manager.get_current_state()
        return self.emotion_expression.get_emotion_greeting(current_state)
    
    def reset_emotion(self):
        """重置情感状态到基线"""
        self.state_manager.reset_to_baseline()
        print("🔄 AI情感状态已重置")
    
    def adjust_emotion_manually(self, emotion_changes: Dict[str, float]):
        """手动调整情感状态"""
        self.state_manager.update_emotion(emotion_changes)
        print("🎛️ AI情感状态已手动调整")
    
    def get_emotion_status(self) -> Dict:
        """获取详细的情感状态信息"""
        current_state = self.state_manager.get_current_state()
        return {
            "current_emotions": current_state.emotions,
            "intensity": current_state.intensity,
            "stability": current_state.stability,
            "dominant_emotion": current_state.get_dominant_emotion(),
            "last_update": current_state.last_update.isoformat(),
            "emotion_history": current_state.emotion_history[-5:],  # 最近5条记录
            "smoother_status": self.emotion_smoother.get_smoothing_status()
        }
    
    def configure_system(self, **kwargs):
        """配置系统参数"""
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
                print(f"⚙️ 配置更新: {key} = {value}")
    
    def save_emotion_state(self):
        """手动保存情感状态"""
        self.state_manager.save_state()
        print("💾 情感状态已保存")


def main():
    """主程序入口"""
    print("🤖 欢迎使用AI自主情感系统！")
    print("=" * 50)
    
    # 初始化系统
    ai_emotion_system = AIEmotionSystem()
    
    # 显示问候语
    greeting = ai_emotion_system.get_emotion_greeting()
    print(f"\n🤖 AI: {greeting}")
    
    print("\n💡 输入 'quit' 退出，'reset' 重置情感，'status' 查看状态")
    print("=" * 50)
    
    # 主循环
    while True:
        try:
            # 获取用户输入
            user_input = input("\n👤 用户: ").strip()
            
            if not user_input:
                continue
            
            # 处理特殊命令
            if user_input.lower() == 'quit':
                print("\n👋 再见！")
                break
            elif user_input.lower() == 'reset':
                ai_emotion_system.reset_emotion()
                continue
            elif user_input.lower() == 'status':
                status = ai_emotion_system.get_emotion_status()
                print(f"\n📊 详细情感状态:")
                print(f"主导情感: {status['dominant_emotion']}")
                print(f"情感强度: {status['intensity']:.2f}")
                print(f"情感稳定性: {status['stability']:.2f}")
                continue
            elif user_input.lower() == 'debug':
                current_debug = ai_emotion_system.config["debug_mode"]
                ai_emotion_system.configure_system(debug_mode=not current_debug)
                continue
            
            # 处理正常输入
            response = ai_emotion_system.process_user_input(user_input)
            print(f"\n🤖 AI: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 程序被用户中断，再见！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            continue


if __name__ == "__main__":
    main()