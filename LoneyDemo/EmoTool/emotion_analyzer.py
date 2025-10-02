from openai import OpenAI
import json
import re

class EmotionAnalyzer:
    def __init__(self):
        """
        初始化情感分析器
        """
        self.client = OpenAI(
            api_key="sk-6ae0aeb3b5624855aa8ea15ef0350f65",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        
        # 情感分析的系统提示词
        self.system_prompt = """你是一个专业的情感分析专家。请分析用户输入文本的具体情绪，注意识别复杂和混合的情绪状态。

请按照以下格式返回分析结果：
{
    "emotion": "主要情绪",
    "secondary_emotion": "次要情绪(如果存在)",
    "confidence": 置信度(0-1之间的数字),
    "intensity": "情感强度",
    "keywords": ["关键词1", "关键词2"],
    "explanation": "详细解释情绪判断的依据"
}

具体情绪类别包括：
- joy: 纯粹的开心、快乐、兴奋、愉悦、满足
- anger: 愤怒、生气、恼火、暴躁、不满
- sadness: 悲伤、难过、失落、沮丧、忧郁
- happiness: 高兴、欢乐、喜悦、轻松、舒畅
- surprise: 惊讶、震惊、意外、诧异
- fear: 恐惧、害怕、担心、焦虑、紧张
- contemplation: 思考、沉思、困惑、疑惑
- love: 喜爱、热爱、钟情、迷恋、感激
- hate: 厌恶、憎恨、讨厌、反感
- shame: 羞耻、尴尬、害羞、不好意思
- mockery: 嘲笑、调侃、戏谑、讽刺、幽默
- helplessness: 无奈、无助、认命、苦笑
- excitement: 激动、兴奋、热情、期待
- disappointment: 失望、沮丧、不满意
- relief: 解脱、轻松、如释重负
- neutral: 平静、客观、无明显情感倾向

注意事项：
1. 如果文本包含复杂情绪（如苦笑、调侃等），请选择最准确的主要情绪
2. 如果存在明显的次要情绪，请在secondary_emotion中标注
3. 对于网络用语和梗，要理解其真实的情感表达
4. emotion字段必须从上述列表中选择，不要使用其他词汇

请确保返回的是有效的JSON格式。"""

    def analyze_emotion(self, text):
        """
        分析文本的情感
        
        Args:
            text (str): 要分析的文本
            
        Returns:
            dict: 情感分析结果
        """
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"请分析以下文本的情感：\n\n{text}"}
            ]
            
            completion = self.client.chat.completions.create(
                model="qwen-flash",
                messages=messages,
                temperature=0.3,  # 降低随机性，提高一致性
                max_tokens=500
            )
            
            response_text = completion.choices[0].message.content
            
            # 尝试解析JSON响应
            try:
                # 提取JSON部分
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    result = json.loads(json_str)
                    return result
                else:
                    # 如果没有找到JSON，返回错误信息
                    return {
                        "emotion": "unknown",
                        "secondary_emotion": "",
                        "confidence": 0.0,
                        "intensity": "unknown",
                        "keywords": [],
                        "explanation": "LLM未返回有效的JSON格式结果"
                    }
                    
            except json.JSONDecodeError:
                # JSON解析失败，返回错误信息
                return {
                    "emotion": "unknown",
                    "secondary_emotion": "",
                    "confidence": 0.0,
                    "intensity": "unknown",
                    "keywords": [],
                    "explanation": "LLM返回的JSON格式无效"
                }
                
        except Exception as e:
            return {
                "emotion": "unknown",
                "secondary_emotion": "",
                "confidence": 0.0,
                "intensity": "unknown",
                "keywords": [],
                "explanation": f"分析过程中出现错误: {str(e)}"
            }
    

    
    def format_result(self, result):
        """
        格式化输出结果
        """
        emotion_map = {
            "joy": "😄 喜悦",
            "anger": "😠 愤怒",
            "sadness": "😢 悲伤", 
            "happiness": "😊 快乐",
            "surprise": "😲 惊讶",
            "fear": "😨 恐惧",
            "contemplation": "🤔 沉思",
            "love": "😍 喜爱",
            "hate": "😤 厌恶",
            "shame": "😳 羞耻",
            "mockery": "😏 调侃",
            "helplessness": "😔 无奈",
            "excitement": "🤩 激动",
            "disappointment": "😞 失望",
            "relief": "😌 解脱",
            "neutral": "😐 中性",
            "unknown": "❓ 未知"
        }
        
        intensity_map = {
            "strong": "🔥 强烈",
            "moderate": "🌟 中等",
            "mild": "💫 轻微",
            "unknown": "❓ 未知"
        }
        
        emotion_display = emotion_map.get(result["emotion"], result["emotion"])
        intensity_display = intensity_map.get(result["intensity"], result["intensity"])
        confidence_percent = int(result["confidence"] * 100)
        
        output = f"""
╭─────────────────────────────────────╮
│           情感分析结果              │
╰─────────────────────────────────────╯

🎯 主要情绪: {emotion_display}
📊 置信度: {confidence_percent}%
⚡ 情感强度: {intensity_display}
"""
        
        # 如果存在次要情绪，显示它
        if result.get("secondary_emotion") and result["secondary_emotion"]:
            secondary_display = emotion_map.get(result["secondary_emotion"], result["secondary_emotion"])
            output += f"🔄 次要情绪: {secondary_display}\n"
        
        if result["keywords"]:
            keywords_str = "、".join(result["keywords"])
            output += f"🔑 关键词: {keywords_str}\n"
        
        output += f"💭 分析说明: {result['explanation']}\n"
        
        return output

def main():
    """
    主程序入口
    """
    print("=" * 50)
    print("🎭 情感分析系统")
    print("=" * 50)
    print("输入文本，我将分析其中的情感倾向")
    print("输入 'quit' 或 'exit' 退出程序")
    print("-" * 50)
    
    analyzer = EmotionAnalyzer()
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\n请输入要分析的文本: ").strip()
            
            # 检查退出条件
            if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                print("\n👋 感谢使用情感分析系统，再见！")
                break
                
            if not user_input:
                print("❌ 请输入有效的文本。")
                continue
            
            print("\n🔍 正在分析中...")
            
            # 进行情感分析
            result = analyzer.analyze_emotion(user_input)
            
            # 显示格式化结果
            formatted_output = analyzer.format_result(result)
            print(formatted_output)
            
        except KeyboardInterrupt:
            print("\n\n👋 程序被用户中断，再见！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")

if __name__ == "__main__":
    main()