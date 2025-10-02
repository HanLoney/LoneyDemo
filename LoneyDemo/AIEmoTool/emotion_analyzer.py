"""
AI情感影响分析器
使用LLM分析用户输入对AI情感状态的影响
"""

import json
import re
from openai import OpenAI
from typing import Dict, Optional

class AIEmotionAnalyzer:
    """AI情感影响分析器"""
    
    def __init__(self):
        # 初始化LLM客户端
        self.client = OpenAI(
            api_key="sk-6ae0aeb3b5624855aa8ea15ef0350f65",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        # 系统提示词
        self.system_prompt = """你是一个专业的AI情感影响分析师。你的任务是分析用户的输入对AI助手情感状态的影响。

请分析用户输入对AI的以下8个情感维度的影响：
1. happiness (快乐): 用户的话语是否让AI感到愉悦、开心
2. sadness (悲伤): 用户的话语是否让AI感到难过、失落
3. anger (愤怒): 用户的话语是否让AI感到愤怒、不满
4. fear (恐惧): 用户的话语是否让AI感到担心、恐惧
5. surprise (惊讶): 用户的话语是否让AI感到意外、惊讶
6. trust (信任): 用户的话语是否增强或减少AI对用户的信任
7. anticipation (期待): 用户的话语是否让AI对未来产生期待
8. disgust (厌恶): 用户的话语是否让AI感到厌恶、反感

分析原则：
- AI应该有自主的情感反应，不完全被用户情绪主导
- 考虑AI的独立性：即使用户很愤怒，AI也不应该完全被影响
- 考虑情感的合理性：AI会对赞美感到高兴，对批评有轻微的负面反应
- 变化幅度应该适中：单次交互的影响应该在-0.3到+0.3之间
- 强度变化：分析这次交互是否会让AI整体情感更加激烈或平静

请以JSON格式返回分析结果：
{
    "emotion_changes": {
        "happiness": 0.1,     // -1到1之间的变化量
        "sadness": 0.0,
        "anger": 0.0,
        "fear": 0.0,
        "surprise": 0.2,
        "trust": 0.1,
        "anticipation": 0.0,
        "disgust": 0.0
    },
    "intensity_change": 0.1,  // -1到1之间，正值表示情感更激烈
    "reasoning": "用户表达了赞美，这让AI感到高兴和惊讶，同时增加了对用户的信任。",
    "interaction_type": "positive"  // positive/negative/neutral/complex
}

注意：
- 只返回JSON格式，不要其他文字
- 变化量要合理，避免极端值
- 考虑AI的情感独立性和稳定性
- 分析要符合AI助手的角色特点"""

    def analyze_emotion_impact(self, user_input: str, current_ai_emotion: str = "") -> Optional[Dict]:
        """
        分析用户输入对AI情感的影响
        
        Args:
            user_input: 用户输入的文本
            current_ai_emotion: 当前AI的情感状态描述
            
        Returns:
            包含情感变化分析的字典
        """
        try:
            # 构建分析提示
            analysis_prompt = f"""
当前AI情感状态: {current_ai_emotion}

用户输入: "{user_input}"

请分析这个用户输入对AI情感状态的影响。
"""
            
            # 调用LLM进行分析
            response = self.client.chat.completions.create(
                model="qwen-flash",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # 提取响应内容
            content = response.choices[0].message.content.strip()
            
            # 尝试解析JSON
            try:
                # 查找JSON内容
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    result = json.loads(json_str)
                    
                    # 验证结果格式
                    if self._validate_analysis_result(result):
                        return result
                    else:
                        print("⚠️ LLM返回的分析结果格式不正确")
                        return self._create_neutral_result("格式验证失败")
                else:
                    print("⚠️ 未找到有效的JSON格式")
                    return self._create_neutral_result("未找到JSON")
                    
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON解析失败: {e}")
                return self._create_neutral_result("JSON解析失败")
                
        except Exception as e:
            print(f"❌ 情感影响分析失败: {e}")
            return self._create_neutral_result(f"分析异常: {str(e)}")
    
    def _validate_analysis_result(self, result: Dict) -> bool:
        """验证分析结果的格式"""
        required_keys = ["emotion_changes", "intensity_change", "reasoning", "interaction_type"]
        
        # 检查必需的键
        if not all(key in result for key in required_keys):
            return False
        
        # 检查emotion_changes格式
        emotion_changes = result["emotion_changes"]
        required_emotions = ["happiness", "sadness", "anger", "fear", "surprise", "trust", "anticipation", "disgust"]
        
        if not all(emotion in emotion_changes for emotion in required_emotions):
            return False
        
        # 检查数值范围
        for emotion, value in emotion_changes.items():
            if not isinstance(value, (int, float)) or not -1 <= value <= 1:
                return False
        
        # 检查intensity_change
        intensity_change = result["intensity_change"]
        if not isinstance(intensity_change, (int, float)) or not -1 <= intensity_change <= 1:
            return False
        
        return True
    
    def _create_neutral_result(self, reason: str) -> Dict:
        """创建中性的分析结果"""
        return {
            "emotion_changes": {
                "happiness": 0.0,
                "sadness": 0.0,
                "anger": 0.0,
                "fear": 0.0,
                "surprise": 0.0,
                "trust": 0.0,
                "anticipation": 0.0,
                "disgust": 0.0
            },
            "intensity_change": 0.0,
            "reasoning": f"分析失败，保持中性状态。原因: {reason}",
            "interaction_type": "neutral"
        }
    
    def analyze_batch_interactions(self, interactions: list) -> Dict:
        """批量分析多个交互的情感影响"""
        total_changes = {
            "happiness": 0.0,
            "sadness": 0.0,
            "anger": 0.0,
            "fear": 0.0,
            "surprise": 0.0,
            "trust": 0.0,
            "anticipation": 0.0,
            "disgust": 0.0
        }
        total_intensity_change = 0.0
        
        analysis_results = []
        
        for interaction in interactions:
            result = self.analyze_emotion_impact(interaction)
            if result:
                analysis_results.append(result)
                
                # 累积变化
                for emotion, change in result["emotion_changes"].items():
                    total_changes[emotion] += change
                
                total_intensity_change += result["intensity_change"]
        
        # 计算平均影响
        count = len(analysis_results)
        if count > 0:
            for emotion in total_changes:
                total_changes[emotion] /= count
            total_intensity_change /= count
        
        return {
            "total_emotion_changes": total_changes,
            "total_intensity_change": total_intensity_change,
            "individual_results": analysis_results,
            "interaction_count": count
        }