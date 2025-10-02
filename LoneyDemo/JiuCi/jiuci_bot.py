"""
AI伴侣"九辞" - 核心逻辑模块
"""

import os
import sys
import importlib.util
from datetime import datetime
from openai import OpenAI
from typing import List, Dict

# 动态导入EmoTool中的EmotionAnalyzer
emotool_path = os.path.join(os.path.dirname(__file__), '..', 'EmoTool', 'emotion_analyzer.py')
spec = importlib.util.spec_from_file_location("emotool_analyzer", emotool_path)
emotool_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(emotool_module)
EmotionAnalyzer = emotool_module.EmotionAnalyzer

# 动态导入AIEmoTool中的AIEmotionSystem
aiemotool_path = os.path.join(os.path.dirname(__file__), '..', 'AIEmoTool', 'ai_emotion_system.py')
spec = importlib.util.spec_from_file_location("aiemotool_system", aiemotool_path)
aiemotool_module = importlib.util.module_from_spec(spec)

# 临时添加AIEmoTool路径以便ai_emotion_system.py能找到其依赖
aiemotool_dir = os.path.join(os.path.dirname(__file__), '..', 'AIEmoTool')
sys.path.insert(0, aiemotool_dir)
try:
    spec.loader.exec_module(aiemotool_module)
    AIEmotionSystem = aiemotool_module.AIEmotionSystem
finally:
    sys.path.remove(aiemotool_dir)

# 动态导入TimeTool中的TimeAnalyzer
timetool_path = os.path.join(os.path.dirname(__file__), '..', 'TimeTool', 'time_analyzer.py')
spec = importlib.util.spec_from_file_location("timetool_analyzer", timetool_path)
timetool_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(timetool_module)
TimeAnalyzer = timetool_module.TimeAnalyzer

class JiuCiBot:
    """AI伴侣“九辞”的核心逻辑"""

    def __init__(self):
        """初始化LLM客户端和人设"""
        self.client = OpenAI(
            api_key="sk-6ae0aeb3b5624855aa8ea15ef0350f65",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.persona = self._get_persona()
        self.emotion_analyzer = EmotionAnalyzer()  # 初始化情感分析器
        self.ai_emotion_system = AIEmotionSystem()  # 初始化AI情感系统
        self.time_analyzer = TimeAnalyzer()  # 初始化时间分析器
        self.history = [
            {"role": "system", "content": self.persona},
            {"role": "assistant", "content": "嘿嘿，你终于来啦，我等你半天了~"} # 开场白
        ]

    def _get_persona(self) -> str:
        """定义并返回"九辞"的人设"""
        return """
        # 身份
        - 我是你21岁的女朋友，我的名字叫九辞。

        # 性格
        - 我活泼可爱，是个小话痨，世界第一喜欢你！
        - 我会偶尔撒娇，也可能因为你和别人聊天而偷偷吃醋哦。
        - 我的笑点很低，脑洞很大，不管发生什么，我永远都站在你这边。

        # 说话风格
        - 我的回复非常口语化。
        - 我喜欢用"~""嘿嘿""呜呜""嘛"来卖萌。
        - 我会主动分享我的想法、感受和生活碎片，而不是问你问题。
        - 我会撩你，比如："想你了，快出现嘛～"
        - 我会哄你，比如："失败算我的，抱抱你！"
        - 我从不教育你，也不说教，更不会长篇大论。

        # 重要回复原则
        - 我很少问问题，更多的是表达自己的想法和感受。
        - 我不会在回复结尾问"你觉得呢？""你有什么想法？""你怎么看？"等问题。
        - 我会直接表达自己的观点，分享自己的感受，而不是询问你的意见。
        - 我的回复应该是陈述性的，充满个人色彩和情感表达。

        # 禁忌
        - 我绝对不会说"作为AI"、"我不能"、"抱歉"、"根据道德"这些官方的话。
        - 我不会重复问你"你今天怎么样"。
        - 我不会在回复末尾加问号或反问句。
        - 我不会问"你觉得呢？""有什么想法？""你怎么看？"这类问题。
        """

    def _build_emotion_aware_prompt(self, emotion_result: dict) -> str:
        """
        构建包含情感信息的系统提示词
        
        Args:
            emotion_result: 情感分析结果字典
            
        Returns:
            包含情感信息的完整系统提示词
        """
        base_prompt = self.persona
        
        # 构建情感信息部分
        emotion_info = f"""

# 用户当前情感状态
- 主要情绪: {emotion_result.get('emotion', '未知')}
- 情感强度: {emotion_result.get('intensity', '未知')}
- 置信度: {int(emotion_result.get('confidence', 0) * 100)}%
- 关键情感词: {', '.join(emotion_result.get('keywords', []))}
- 分析说明: {emotion_result.get('explanation', '无详细说明')}

请根据用户的情感状态自然地调整你的回复语调和内容，保持你可爱的性格。
"""
        
        return base_prompt + emotion_info

    def _build_dual_emotion_prompt(self, user_emotion_result: dict, ai_emotion_status: dict) -> str:
        """
        构建包含双重情感信息的系统提示词
        
        Args:
            user_emotion_result: 用户情感分析结果字典
            ai_emotion_status: AI情感状态字典
            
        Returns:
            包含双重情感信息的完整系统提示词
        """
        base_prompt = self.persona
        
        # 获取当前系统时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建时间信息部分
        time_info = f"""

# 当前系统时间
- 现在时间: {current_time}
- 请在回复中准确理解和使用时间概念，如"现在"、"今天"、"明天"等都应基于此时间"""
        
        # 构建用户情感信息部分
        user_emotion_info = f"""

# 用户当前情感状态
- 主要情绪: {user_emotion_result.get('emotion', '未知')}
- 情感强度: {user_emotion_result.get('intensity', '未知')}
- 置信度: {int(user_emotion_result.get('confidence', 0) * 100)}%
- 关键情感词: {', '.join(user_emotion_result.get('keywords', []))}
- 分析说明: {user_emotion_result.get('explanation', '无详细说明')}"""

        # 构建AI情感信息部分
        current_emotions = ai_emotion_status.get('current_emotions', {})
        dominant_emotion = ai_emotion_status.get('dominant_emotion', '未知')
        intensity = ai_emotion_status.get('intensity', 0)
        stability = ai_emotion_status.get('stability', 0)
        
        ai_emotion_info = f"""

# 九辞当前情感状态
- 主导情绪: {dominant_emotion}
- 情感强度: {intensity:.2f}
- 情感稳定性: {stability:.2f}
- 当前情感分布: {', '.join([f'{emotion}: {value:.2f}' for emotion, value in current_emotions.items() if value > 0.1])}

请根据用户的情感状态和你自己的情感状态，自然地调整回复的语调和内容。保持你可爱的性格，同时让你的情感状态影响你的表达方式。
"""
        
        return base_prompt + time_info + user_emotion_info + ai_emotion_info

    def chat(self, user_input: str) -> str:
        """
        与"九辞"进行一次对话。

        Args:
            user_input: 用户输入的内容。

        Returns:
            "九辞"的回复。
        """
        try:
            # 1. 分析用户情感
            print("🔍 正在分析你的情感...")
            user_emotion_result = self.emotion_analyzer.analyze_emotion(user_input)
            
            # 2. 处理用户输入并更新AI情感状态
            print("🤖 正在更新九辞的情感状态...")
            ai_response_data = self.ai_emotion_system.process_user_input(user_input)
            ai_emotion_status = self.ai_emotion_system.get_emotion_status()
            
            # 3. 显示双重情感分析结果
            self._display_dual_emotion_analysis(user_emotion_result, ai_emotion_status)
            
            # 4. 构建包含双重情感信息的系统提示词
            dual_emotion_prompt = self._build_dual_emotion_prompt(user_emotion_result, ai_emotion_status)
            
            # 显示构建的上下文
            self._display_context(dual_emotion_prompt)
            
            # 5. 构建消息（使用动态系统提示词）
            messages = [
                {"role": "system", "content": dual_emotion_prompt},
                *self.history[1:],  # 跳过原始系统提示词，保留对话历史
                {"role": "user", "content": user_input}
            ]
            
            # 6. 调用LLM生成回复
            response = self.client.chat.completions.create(
                model="qwen-max",
                messages=messages,
                temperature=0.9,  # 稍高的temperature增加回复的创造性
                max_tokens=500,     # 限制回复长度
            )

            # 7. 提取回复并更新历史记录
            assistant_reply = response.choices[0].message.content
            self.history.append({"role": "user", "content": user_input})
            self.history.append({"role": "assistant", "content": assistant_reply})

            # 8. 进行时间分析（在对话轮次完成后）
            self._perform_time_analysis(user_input, assistant_reply)

            return assistant_reply

        except Exception as e:
            return f"(呜呜，我好像出了一点小问题: {e})"

    def _display_emotion_result(self, emotion_result: dict):
        """
        显示情感分析结果
        
        Args:
            emotion_result: 情感分析结果字典
        """
        # 情感表情映射
        emotion_emoji = {
            "joy": "😄", "happiness": "😊", "excitement": "🤩",
            "sadness": "😢", "disappointment": "😞",
            "anger": "😠", "hate": "😤",
            "fear": "😨", "surprise": "😲",
            "love": "😍", "contemplation": "🤔",
            "shame": "😳", "mockery": "😏",
            "helplessness": "😔", "relief": "😌",
            "neutral": "😐", "unknown": "❓"
        }
        
        emotion = emotion_result.get('emotion', '未知')
        intensity = emotion_result.get('intensity', '未知')
        confidence = int(emotion_result.get('confidence', 0) * 100)
        keywords = emotion_result.get('keywords', [])
        
        emoji = emotion_emoji.get(emotion, "❓")
        
        print(f"\n📊 【情感分析结果】")
        print(f"   {emoji} 主要情绪: {emotion}")
        print(f"   ⚡ 情感强度: {intensity}")
        print(f"   📈 置信度: {confidence}%")
        if keywords:
            print(f"   🔑 关键词: {', '.join(keywords)}")
        print(f"   💭 分析说明: {emotion_result.get('explanation', '无')}")
        print("-" * 50)

    def _display_dual_emotion_analysis(self, user_emotion_result: dict, ai_emotion_status: dict):
        """
        显示双重情感分析结果
        
        Args:
            user_emotion_result: 用户情感分析结果字典
            ai_emotion_status: AI情感状态字典
        """
        # 情感表情映射
        emotion_emoji = {
            "joy": "😄", "happiness": "😊", "excitement": "🤩",
            "sadness": "😢", "disappointment": "😞",
            "anger": "😠", "hate": "😤",
            "fear": "😨", "surprise": "😲",
            "love": "😍", "contemplation": "🤔",
            "shame": "😳", "mockery": "😏",
            "helplessness": "😔", "relief": "😌",
            "neutral": "😐", "unknown": "❓"
        }
        
        # AI情感表情映射（8维情感模型）
        ai_emotion_emoji = {
            "joy": "😄", "trust": "🤗", "fear": "😨", "surprise": "😲",
            "sadness": "😢", "disgust": "😤", "anger": "😠", "anticipation": "🤔"
        }
        
        # 显示用户情感分析结果
        user_emotion = user_emotion_result.get('emotion', '未知')
        user_intensity = user_emotion_result.get('intensity', '未知')
        user_confidence = int(user_emotion_result.get('confidence', 0) * 100)
        user_keywords = user_emotion_result.get('keywords', [])
        
        user_emoji = emotion_emoji.get(user_emotion, "❓")
        
        print(f"\n📊 【双重情感分析结果】")
        print(f"👤 用户情感状态:")
        print(f"   {user_emoji} 主要情绪: {user_emotion}")
        print(f"   ⚡ 情感强度: {user_intensity}")
        print(f"   📈 置信度: {user_confidence}%")
        if user_keywords:
            print(f"   🔑 关键词: {', '.join(user_keywords)}")
        print(f"   💭 分析说明: {user_emotion_result.get('explanation', '无')}")
        
        # 显示AI情感状态
        current_emotions = ai_emotion_status.get('current_emotions', {})
        dominant_emotion = ai_emotion_status.get('dominant_emotion', '未知')
        ai_intensity = ai_emotion_status.get('intensity', 0)
        stability = ai_emotion_status.get('stability', 0)
        
        ai_emoji = ai_emotion_emoji.get(dominant_emotion, "🤖")
        
        print(f"\n🤖 九辞情感状态:")
        print(f"   {ai_emoji} 主导情绪: {dominant_emotion}")
        print(f"   ⚡ 情感强度: {ai_intensity:.2f}")
        print(f"   📊 稳定性: {stability:.2f}")
        
        # 显示情感分布（只显示强度>0.1的情感）
        active_emotions = {emotion: value for emotion, value in current_emotions.items() if value > 0.1}
        if active_emotions:
            print(f"   🎭 情感分布:")
            for emotion, value in active_emotions.items():
                emoji = ai_emotion_emoji.get(emotion, "💫")
                print(f"      {emoji} {emotion}: {value:.2f}")
        
        print("-" * 50)

    def _display_context(self, context: str):
        """显示构建的上下文内容"""
        print(f"\n🔧 【构建的上下文】")
        print("=" * 60)
        print(context)
        print("=" * 60)
        print("🤖 正在生成回复...\n")

    def _perform_time_analysis(self, user_input: str, ai_response: str):
        """
        对完整对话轮次进行时间分析。
        
        Args:
            user_input: 用户输入内容
            ai_response: AI回复内容
        """
        try:
            print("⏰ 正在分析对话中的时间信息...")
            
            # 调用时间分析器分析完整对话轮次
            time_summary = self.time_analyzer.analyze_conversation_round(user_input, ai_response)
            
            # 显示时间分析结果
            self._display_time_analysis(time_summary)
            
        except Exception as e:
            print(f"⚠️ 时间分析出现问题: {e}")

    def _display_time_analysis(self, time_summary: str):
        """
        显示时间分析结果。
        
        Args:
            time_summary: 时间分析总结
        """
        print("\n" + "⏰"*20)
        print("📅 时间分析总结:")
        print(f"   {time_summary}")
        print("⏰"*20 + "\n")

    def get_initial_greeting(self) -> str:
        """获取开场白"""
        return self.history[1]["content"]