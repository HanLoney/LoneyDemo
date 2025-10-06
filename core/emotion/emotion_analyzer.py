"""
情感分析器
使用LLM分析文本情感和对AI情感状态的影响
"""
import json
import re
from typing import Dict, Optional, List, Any
from openai import OpenAI

from shared.models.emotion import EmotionAnalysisResult, EmotionType, EmotionState
from shared.utils import get_logger
from shared.utils.config import config


class EmotionAnalyzer:
    """情感分析器"""
    
    def __init__(self):
        self.config = config
        self.logger = get_logger(__name__)
        
        # 初始化提示词
        self._init_prompts()
        
        # 初始化OpenAI客户端
        self.client = self._init_openai_client()
        
    def _init_prompts(self):
        """初始化分析提示词"""
        # 情感分析系统提示词
        self.emotion_analysis_prompt = """你是一个专业的情感分析专家。请分析用户输入文本的具体情绪，注意识别复杂和混合的情绪状态。

请按照以下格式返回分析结果：
{
    "primary_emotion": "主要情绪",
    "secondary_emotion": "次要情绪(如果存在)",
    "confidence": 置信度(0-1之间的数字),
    "intensity": 情感强度(0-1之间的数字),
    "sentiment_score": 情感倾向(-1到1之间，负数表示负面，正数表示正面),
    "keywords": ["关键词1", "关键词2"],
    "explanation": "详细解释情绪判断的依据"
}

具体情绪类别包括：
- happy: 快乐、开心、愉悦、满足
- sad: 悲伤、难过、失落、沮丧
- angry: 愤怒、生气、恼火、不满
- fear: 恐惧、害怕、担心、焦虑
- surprise: 惊讶、震惊、意外
- disgust: 厌恶、反感、讨厌
- neutral: 平静、客观、无明显情感倾向
- excited: 激动、兴奋、热情
- calm: 冷静、平和、安静
- confused: 困惑、疑惑、不解

注意事项：
1. 如果文本包含复杂情绪，请选择最准确的主要情绪
2. 如果存在明显的次要情绪，请在secondary_emotion中标注
3. 对于网络用语和梗，要理解其真实的情感表达
4. primary_emotion字段必须从上述列表中选择

请确保返回的是有效的JSON格式。"""

        # AI情感影响分析提示词
        self.ai_emotion_impact_prompt = """你是一个专业的AI情感影响分析师。你的任务是分析用户的输入对AI助手情感状态的影响。

请分析用户输入对AI的以下情感维度的影响：
1. happy (快乐): 用户的话语是否让AI感到愉悦、开心
2. sad (悲伤): 用户的话语是否让AI感到难过、失落
3. angry (愤怒): 用户的话语是否让AI感到愤怒、不满
4. fear (恐惧): 用户的话语是否让AI感到担心、恐惧
5. surprise (惊讶): 用户的话语是否让AI感到意外、惊讶
6. disgust (厌恶): 用户的话语是否让AI感到厌恶、反感
7. neutral (中性): 基准情感状态
8. excited (兴奋): 用户的话语是否让AI感到激动、兴奋
9. calm (平静): 用户的话语是否让AI感到平静、安宁
10. confused (困惑): 用户的话语是否让AI感到困惑、不解

分析原则：
- AI应该有自主的情感反应，不完全被用户情绪主导
- 考虑AI的独立性：即使用户很愤怒，AI也不应该完全被影响
- 考虑情感的合理性：AI会对赞美感到高兴，对批评有轻微的负面反应
- 变化幅度应该适中：单次交互的影响应该在-0.3到+0.3之间
- 强度变化：分析这次交互是否会让AI整体情感更加激烈或平静

请以JSON格式返回分析结果：
{
    "emotion_changes": {
        "happy": 0.1,     // -1到1之间的变化量
        "sad": 0.0,
        "angry": 0.0,
        "fear": 0.0,
        "surprise": 0.2,
        "disgust": 0.0,
        "neutral": 0.0,
        "excited": 0.1,
        "calm": 0.0,
        "confused": 0.0
    },
    "intensity_change": 0.1,  // -1到1之间，正值表示情感更激烈
    "reasoning": "用户表达了赞美，这让AI感到高兴和惊讶。",
    "interaction_type": "positive"  // positive/negative/neutral/complex
}

注意：
- 只返回JSON格式，不要其他文字
- 变化量要合理，避免极端值
- 考虑AI的情感独立性和稳定性
- 分析要符合AI助手的角色特点"""
        
    def _init_openai_client(self):
        """初始化OpenAI客户端，增强错误处理"""
        try:
            api_key = self.config.get('external_apis.openai.api_key')
            base_url = self.config.get('external_apis.openai.base_url')
            
            self.logger.info(f"尝试初始化OpenAI客户端 - API密钥: {'已配置' if api_key else '未配置'}")
            self.logger.info(f"Base URL: {base_url}")
            
            if not api_key or api_key.strip() == "":
                self.logger.warning("OpenAI API密钥未配置或为空，情感分析功能将使用本地分析")
                return None
                
            # 创建客户端
            client_kwargs = {
                'api_key': api_key.strip(),
                'timeout': 30.0
            }
            
            if base_url and base_url.strip():
                client_kwargs['base_url'] = base_url.strip()
                
            client = OpenAI(**client_kwargs)
            
            # 测试连接
            self.logger.info("OpenAI客户端初始化成功，测试连接...")
            return client
            
        except Exception as e:
            self.logger.error(f"OpenAI客户端初始化失败: {e}")
            self.logger.warning("将使用本地情感分析作为备用方案")
            return None

    def analyze_text_emotion(self, text: str) -> EmotionAnalysisResult:
        """
        分析文本情感
        
        Args:
            text: 要分析的文本
            
        Returns:
            情感分析结果
        """
        # 如果OpenAI客户端未初始化，返回默认结果
        if not self.client:
            self.logger.warning("OpenAI客户端未初始化，返回默认情感分析结果")
            return EmotionAnalysisResult(
                text=text,
                detected_emotions={EmotionType.NEUTRAL: 0.8},
                primary_emotion=EmotionType.NEUTRAL,
                confidence=0.5,
                sentiment_score=0.0
            )
            
        try:
            messages = [
                {"role": "system", "content": self.emotion_analysis_prompt},
                {"role": "user", "content": f"请分析以下文本的情感：\n\n{text}"}
            ]
            
            completion = self.client.chat.completions.create(
                model=self.config.get('external_apis.openai.model', 'gpt-3.5-turbo'),
                messages=messages,
                temperature=0.3,
                max_tokens=500
            )
            
            response_text = completion.choices[0].message.content
            result = self._parse_emotion_analysis_response(response_text)
            
            if result:
                return EmotionAnalysisResult(
                    text=text,
                    detected_emotions={EmotionType(result['primary_emotion']): result['confidence']},
                    primary_emotion=EmotionType(result['primary_emotion']),
                    confidence=result['confidence'],
                    sentiment_score=result.get('sentiment_score', 0.0)
                )
            else:
                # 返回默认结果
                return EmotionAnalysisResult(
                    text=text,
                    detected_emotions={EmotionType.NEUTRAL: 0.5},
                    primary_emotion=EmotionType.NEUTRAL,
                    confidence=0.0,
                    sentiment_score=0.0
                )
                
        except Exception as e:
            self.logger.error(f"情感分析失败: {e}")
            return EmotionAnalysisResult(
                text=text,
                detected_emotions={EmotionType.NEUTRAL: 0.5},
                primary_emotion=EmotionType.NEUTRAL,
                confidence=0.0,
                sentiment_score=0.0
            )
    
    def analyze_ai_emotion_impact(self, user_input: str, current_state: EmotionState) -> Dict[str, Any]:
        """
        分析用户输入对AI情感状态的影响
        
        Args:
            user_input: 用户输入
            current_state: 当前AI情感状态
            
        Returns:
            情感影响分析结果
        """
        # 如果OpenAI客户端未初始化，尝试重新初始化
        if not self.client:
            self.logger.warning("OpenAI客户端未初始化，尝试重新初始化...")
            self.client = self._init_openai_client()
            
        if not self.client:
            self.logger.error("OpenAI客户端初始化失败，无法进行AI情感影响分析")
            raise Exception("OpenAI客户端未配置，无法进行情感分析")
            
        try:
            # 构建包含当前状态的提示
            context = f"""
当前AI情感状态：
主要情感: {current_state.primary_emotion.value}
情感强度: {current_state.intensity:.2f}
情感分布: {current_state.emotions}

用户输入: {user_input}
"""
            
            messages = [
                {"role": "system", "content": self.ai_emotion_impact_prompt},
                {"role": "user", "content": context}
            ]
            
            self.logger.info(f"发送AI情感影响分析请求 - 模型: {self.config.get('external_apis.openai.model', 'gpt-3.5-turbo')}")
            
            completion = self.client.chat.completions.create(
                model=self.config.get('external_apis.openai.model', 'gpt-3.5-turbo'),
                messages=messages,
                temperature=0.3,
                max_tokens=500
            )
            
            response_text = completion.choices[0].message.content
            self.logger.info(f"收到AI情感影响分析响应: {response_text[:200]}...")
            
            result = self._parse_ai_emotion_impact_response(response_text)
            
            if result and self._validate_impact_result(result):
                self.logger.info(f"AI情感影响分析成功: {result}")
                return result
            else:
                self.logger.error(f"AI情感影响分析结果验证失败: {result}")
                raise Exception("分析结果格式错误或验证失败")
                
        except Exception as e:
            self.logger.error(f"AI情感影响分析失败: {e}")
            raise e
    
    def _parse_emotion_analysis_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """解析情感分析响应"""
        try:
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                
                # 验证必需字段
                required_fields = ['primary_emotion', 'confidence']
                if all(field in result for field in required_fields):
                    return result
            
            return None
        except (json.JSONDecodeError, Exception) as e:
            self.logger.error(f"解析情感分析响应失败: {e}")
            return None
    
    def _parse_ai_emotion_impact_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """解析AI情感影响分析响应"""
        try:
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                return result
            
            return None
        except (json.JSONDecodeError, Exception) as e:
            self.logger.error(f"解析AI情感影响分析响应失败: {e}")
            return None
    
    def _validate_impact_result(self, result: Dict[str, Any]) -> bool:
        """验证影响分析结果的格式"""
        try:
            required_keys = ["emotion_changes", "intensity_change", "reasoning", "interaction_type"]
            
            # 检查必需的键
            if not all(key in result for key in required_keys):
                return False
            
            # 检查emotion_changes格式
            emotion_changes = result["emotion_changes"]
            if not isinstance(emotion_changes, dict):
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
        except Exception:
            return False