"""
时间分析器 (Time Analyzer)
- 识别文本中的时间表达 (包括模糊时间)
- 以系统时间为基准，将时间转换为绝对时间
- 调用LLM进行内容总结，并嵌入转换后的时间
"""

import os
from datetime import datetime
from openai import OpenAI

class TimeAnalyzer:
    """时间分析与总结工具"""

    def __init__(self):
        """初始化LLM客户端"""
        self.client = OpenAI(
            api_key="sk-6ae0aeb3b5624855aa8ea15ef0350f65",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

    def analyze_and_summarize(self, text: str) -> str:
        """
        分析文本中的时间信息，总结内容，并返回带有绝对时间的总结。

        Args:
            text: 用户输入的文本。

        Returns:
            带有绝对时间的总结内容。
        """
        # 1. 获取当前系统时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 2. 构建发送给LLM的Prompt
        prompt = self._build_prompt(text, current_time)

        try:
            # 3. 调用LLM进行分析和总结
            response = self.client.chat.completions.create(
                model="qwen-flash",
                messages=[
                    {"role": "system", "content": "你是一个强大的时间分析和内容总结助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )

            # 4. 提取并返回LLM的回复
            summary = response.choices[0].message.content
            return summary

        except Exception as e:
            return f"时间分析失败: {str(e)}"

    def analyze_conversation_round(self, user_input: str, ai_response: str) -> str:
        """
        分析完整对话轮次中的时间信息，总结用户输入和AI回复的内容。

        Args:
            user_input: 用户的输入内容。
            ai_response: AI的回复内容。

        Returns:
            带有绝对时间的对话轮次总结。
        """
        # 1. 获取当前系统时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 2. 构建对话轮次的分析Prompt
        prompt = self._build_conversation_prompt(user_input, ai_response, current_time)

        try:
            # 3. 调用LLM进行分析和总结
            response = self.client.chat.completions.create(
                model="qwen-flash",
                messages=[
                    {"role": "system", "content": "你是一个强大的对话分析和时间处理助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )

            # 4. 提取并返回LLM的回复
            summary = response.choices[0].message.content
            return summary

        except Exception as e:
            return f"对话时间分析失败: {str(e)}"

    def _build_prompt(self, text: str, current_time: str) -> str:
        """
        构建用于LLM分析的Prompt。

        Args:
            text: 用户输入的文本。
            current_time: 当前系统时间。

        Returns:
            构建好的Prompt字符串。
        """
        return f"""
        请分析以下内容，并遵循以下规则：

        1.  **总结核心内容**: 简要总结文本的主要信息。
        2.  **识别时间表达**: 找出文本中所有与时间相关的描述，包括明确时间（如"明天下午3点"）和模糊时间（如"下周五"、"两个小时后"）。
        3.  **转换时间**: 以当前系统时间 **{current_time}** 作为基准，将所有识别到的时间转换为精确的绝对时间格式（YYYY-MM-DD HH:MM:SS）。
        4.  **嵌入时间**: 将转换后的绝对时间无缝地嵌入到总结内容中，确保总结的流畅性和准确性。

        ---
        **待分析内容**:
        "{text}"
        ---

        **输出格式**:
        直接输出带有绝对时间的总结内容。
        """

    def _build_conversation_prompt(self, user_input: str, ai_response: str, current_time: str) -> str:
        """
        构建用于对话轮次分析的Prompt。

        Args:
            user_input: 用户的输入内容。
            ai_response: AI的回复内容。
            current_time: 当前系统时间。

        Returns:
            构建好的对话分析Prompt字符串。
        """
        return f"""
        请分析以下完整对话轮次，并遵循以下规则：

        1.  **总结对话内容**: 简要总结用户输入和AI回复的核心信息。
        2.  **识别时间表达**: 找出用户输入和AI回复中所有与时间相关的描述，包括明确时间和模糊时间。
        3.  **转换时间**: 以当前系统时间 **{current_time}** 作为基准，将所有识别到的时间转换为精确的绝对时间格式（YYYY-MM-DD HH:MM:SS）。
        4.  **嵌入时间**: 将转换后的绝对时间无缝地嵌入到对话总结中，确保总结的流畅性和准确性。

        ---
        **用户输入**:
        "{user_input}"
        
        **AI回复**:
        "{ai_response}"
        ---

        **输出格式**:
        直接输出带有绝对时间的对话轮次总结。
        """

if __name__ == '__main__':
    # 示例用法
    analyzer = TimeAnalyzer()
    
    # 示例1: 包含模糊时间
    text1 = "我们下周五开会，讨论一下项目计划，会议大概在下午两点开始。"
    summary1 = analyzer.analyze_and_summarize(text1)
    print(f"原文: {text1}")
    print(f"总结: {summary1}\n")

    # 示例2: 包含多个时间点
    text2 = "我明天上午要去一趟银行，然后下午3点和朋友有个约会，晚上我们一起看电影。"
    summary2 = analyzer.analyze_and_summarize(text2)
    print(f"原文: {text2}")
    print(f"总结: {summary2}\n")

    # 示例3: 没有时间信息
    text3 = "这个新发布的手机性能非常强大，我很喜欢它的设计。"
    summary3 = analyzer.analyze_and_summarize(text3)
    print(f"原文: {text3}")
    print(f"总结: {summary3}\n")

    # 示例4: 对话轮次分析
    user_input = "我明天下午要去开会，大概3点开始，你能帮我准备一下会议资料吗？"
    ai_response = "当然可以！我建议您在会议前一小时，也就是明天下午2点左右开始准备。您需要准备哪些具体的资料呢？"
    conversation_summary = analyzer.analyze_conversation_round(user_input, ai_response)
    print(f"对话轮次分析:")
    print(f"用户: {user_input}")
    print(f"AI: {ai_response}")
    print(f"总结: {conversation_summary}")