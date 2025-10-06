"""
情感表达器
根据AI的情感状态调整回复的语言风格和表达方式
"""
import random
from typing import Dict, List, Optional, Any
from enum import Enum

from shared.models.emotion import EmotionType, EmotionState
from shared.utils import get_all_config, get_logger


class ExpressionStyle(Enum):
    """表达风格"""
    FORMAL = "formal"           # 正式
    CASUAL = "casual"           # 随意
    ENTHUSIASTIC = "enthusiastic"  # 热情
    GENTLE = "gentle"           # 温和
    SERIOUS = "serious"         # 严肃
    PLAYFUL = "playful"         # 俏皮
    SUPPORTIVE = "supportive"   # 支持性
    CAUTIOUS = "cautious"       # 谨慎


class EmotionExpression:
    """情感表达器"""
    
    def __init__(self):
        self.config = get_all_config()
        self.logger = get_logger(__name__)
        
        # 情感词汇库
        self.emotion_vocabularies = self._init_emotion_vocabularies()
        
        # 强度修饰符
        self.intensity_modifiers = self._init_intensity_modifiers()
        
        # 情感表达模板
        self.expression_templates = self._init_expression_templates()
        
        # 情感对应的表达风格
        self.emotion_styles = self._init_emotion_styles()
    
    def apply_emotion_to_response(self, response: str, emotion_state: EmotionState, 
                                 style_preference: Optional[ExpressionStyle] = None) -> str:
        """
        根据情感状态调整回复内容
        
        Args:
            response: 原始回复内容
            emotion_state: 当前情感状态
            style_preference: 风格偏好
            
        Returns:
            调整后的回复内容
        """
        try:
            # 确定表达风格
            expression_style = self._determine_expression_style(emotion_state, style_preference)
            
            # 添加情感前缀
            emotion_prefix = self._get_emotion_prefix(emotion_state, expression_style)
            
            # 调整语言风格
            adjusted_response = self._adjust_language_style(response, emotion_state, expression_style)
            
            # 添加情感后缀
            emotion_suffix = self._get_emotion_suffix(emotion_state, expression_style)
            
            # 组合最终回复
            final_response = self._combine_response_parts(
                emotion_prefix, adjusted_response, emotion_suffix
            )
            
            self.logger.debug(f"应用情感表达: {emotion_state.primary_emotion.value} -> {expression_style.value}")
            
            return final_response
            
        except Exception as e:
            self.logger.error(f"应用情感表达失败: {e}")
            return response
    
    def get_emotion_emoji(self, emotion_type: EmotionType, intensity: float = 0.5) -> str:
        """获取情感对应的表情符号"""
        emoji_map = {
            EmotionType.HAPPY: ["😊", "😄", "😁", "🥰", "😍"],
            EmotionType.SAD: ["😢", "😭", "😔", "😞", "💔"],
            EmotionType.ANGRY: ["😠", "😡", "🤬", "😤", "💢"],
            EmotionType.FEAR: ["😨", "😰", "😱", "😟", "😧"],
            EmotionType.SURPRISE: ["😲", "😮", "🤯", "😯", "😦"],
            EmotionType.DISGUST: ["🤢", "🤮", "😷", "😖", "😣"],
            EmotionType.NEUTRAL: ["😐", "😑", "🙂", "😌", "😊"],
            EmotionType.EXCITED: ["🤩", "😆", "🎉", "✨", "🔥"],
            EmotionType.CALM: ["😌", "😇", "🧘", "☮️", "🕊️"],
            EmotionType.CONFUSED: ["😕", "🤔", "😵", "🤷", "❓"]
        }
        
        emojis = emoji_map.get(emotion_type, ["😊"])
        
        # 根据强度选择表情
        if intensity < 0.3:
            return emojis[0] if len(emojis) > 0 else "😊"
        elif intensity < 0.7:
            return emojis[min(1, len(emojis) - 1)] if len(emojis) > 1 else emojis[0]
        else:
            return emojis[-1]
    
    def get_emotion_description(self, emotion_state: EmotionState) -> str:
        """获取情感状态的文字描述"""
        emotion = emotion_state.primary_emotion
        intensity = emotion_state.intensity
        
        descriptions = {
            EmotionType.HAPPY: {
                "low": "心情不错",
                "medium": "感到开心",
                "high": "非常愉快"
            },
            EmotionType.SAD: {
                "low": "有些失落",
                "medium": "感到难过",
                "high": "非常伤心"
            },
            EmotionType.ANGRY: {
                "low": "有点不满",
                "medium": "感到愤怒",
                "high": "非常生气"
            },
            EmotionType.FEAR: {
                "low": "有些担心",
                "medium": "感到害怕",
                "high": "非常恐惧"
            },
            EmotionType.SURPRISE: {
                "low": "有点意外",
                "medium": "感到惊讶",
                "high": "非常震惊"
            },
            EmotionType.DISGUST: {
                "low": "有些反感",
                "medium": "感到厌恶",
                "high": "非常恶心"
            },
            EmotionType.NEUTRAL: {
                "low": "心情平静",
                "medium": "状态正常",
                "high": "非常平和"
            },
            EmotionType.EXCITED: {
                "low": "有些兴奋",
                "medium": "感到激动",
                "high": "非常兴奋"
            },
            EmotionType.CALM: {
                "low": "比较平静",
                "medium": "感到安静",
                "high": "非常宁静"
            },
            EmotionType.CONFUSED: {
                "low": "有些疑惑",
                "medium": "感到困惑",
                "high": "非常迷茫"
            }
        }
        
        emotion_desc = descriptions.get(emotion, descriptions[EmotionType.NEUTRAL])
        
        if intensity < 0.3:
            level = "low"
        elif intensity < 0.7:
            level = "medium"
        else:
            level = "high"
        
        return emotion_desc[level]
    
    def _determine_expression_style(self, emotion_state: EmotionState, 
                                   style_preference: Optional[ExpressionStyle]) -> ExpressionStyle:
        """确定表达风格"""
        if style_preference:
            return style_preference
        
        # 根据情感类型确定风格
        emotion_styles = self.emotion_styles.get(emotion_state.primary_emotion, [ExpressionStyle.CASUAL])
        
        # 根据强度调整风格选择
        if emotion_state.intensity > 0.7:
            # 高强度时选择更强烈的风格
            intense_styles = [ExpressionStyle.ENTHUSIASTIC, ExpressionStyle.SERIOUS]
            available_styles = [style for style in emotion_styles if style in intense_styles]
            if available_styles:
                return random.choice(available_styles)
        
        return random.choice(emotion_styles)
    
    def _get_emotion_prefix(self, emotion_state: EmotionState, style: ExpressionStyle) -> str:
        """获取情感前缀"""
        prefixes = self.expression_templates.get("prefixes", {})
        emotion_prefixes = prefixes.get(emotion_state.primary_emotion.value, {})
        style_prefixes = emotion_prefixes.get(style.value, [])
        
        if not style_prefixes:
            return ""
        
        # 根据强度选择前缀
        if emotion_state.intensity > 0.7 and len(style_prefixes) > 1:
            return random.choice(style_prefixes[-2:])  # 选择更强烈的前缀
        else:
            return random.choice(style_prefixes[:2] if len(style_prefixes) > 2 else style_prefixes)
    
    def _get_emotion_suffix(self, emotion_state: EmotionState, style: ExpressionStyle) -> str:
        """获取情感后缀"""
        suffixes = self.expression_templates.get("suffixes", {})
        emotion_suffixes = suffixes.get(emotion_state.primary_emotion.value, {})
        style_suffixes = emotion_suffixes.get(style.value, [])
        
        if not style_suffixes:
            return ""
        
        return random.choice(style_suffixes)
    
    def _adjust_language_style(self, response: str, emotion_state: EmotionState, 
                              style: ExpressionStyle) -> str:
        """调整语言风格"""
        # 根据情感和风格调整语言
        adjustments = {
            ExpressionStyle.ENTHUSIASTIC: self._make_enthusiastic,
            ExpressionStyle.GENTLE: self._make_gentle,
            ExpressionStyle.SERIOUS: self._make_serious,
            ExpressionStyle.PLAYFUL: self._make_playful,
            ExpressionStyle.SUPPORTIVE: self._make_supportive,
            ExpressionStyle.CAUTIOUS: self._make_cautious
        }
        
        adjustment_func = adjustments.get(style)
        if adjustment_func:
            return adjustment_func(response, emotion_state)
        
        return response
    
    def _make_enthusiastic(self, response: str, emotion_state: EmotionState) -> str:
        """使回复更热情"""
        # 添加感叹号
        if not response.endswith(('!', '！')):
            response += "！"
        
        # 添加强调词
        enthusiasm_words = ["真的", "非常", "特别", "超级", "极其"]
        if emotion_state.intensity > 0.7:
            word = random.choice(enthusiasm_words)
            response = response.replace("很", word).replace("比较", word)
        
        return response
    
    def _make_gentle(self, response: str, emotion_state: EmotionState) -> str:
        """使回复更温和"""
        # 添加温和的词汇
        gentle_words = ["轻轻地", "慢慢地", "温柔地", "小心地"]
        if "。" in response:
            parts = response.split("。")
            if len(parts) > 1 and random.random() < 0.3:
                word = random.choice(gentle_words)
                parts[0] = word + parts[0]
                response = "。".join(parts)
        
        return response
    
    def _make_serious(self, response: str, emotion_state: EmotionState) -> str:
        """使回复更严肃"""
        # 移除过于随意的表达
        response = response.replace("哈哈", "").replace("呵呵", "")
        response = response.replace("～", "").replace("~", "")
        
        return response
    
    def _make_playful(self, response: str, emotion_state: EmotionState) -> str:
        """使回复更俏皮"""
        # 添加俏皮的表达
        if random.random() < 0.3:
            playful_endings = ["呢～", "哦～", "呀～", "嘛～"]
            if response.endswith("。"):
                response = response[:-1] + random.choice(playful_endings)
        
        return response
    
    def _make_supportive(self, response: str, emotion_state: EmotionState) -> str:
        """使回复更支持性"""
        # 添加支持性的词汇
        supportive_words = ["我理解", "我明白", "我支持", "我相信"]
        if random.random() < 0.4:
            word = random.choice(supportive_words)
            response = word + "，" + response
        
        return response
    
    def _make_cautious(self, response: str, emotion_state: EmotionState) -> str:
        """使回复更谨慎"""
        # 添加谨慎的表达
        cautious_words = ["可能", "也许", "或许", "大概", "似乎"]
        if random.random() < 0.3:
            word = random.choice(cautious_words)
            response = response.replace("是", word + "是").replace("会", word + "会")
        
        return response
    
    def _combine_response_parts(self, prefix: str, response: str, suffix: str) -> str:
        """组合回复各部分"""
        parts = []
        
        if prefix:
            parts.append(prefix)
        
        parts.append(response)
        
        if suffix:
            parts.append(suffix)
        
        return " ".join(parts)
    
    def _init_emotion_vocabularies(self) -> Dict[str, List[str]]:
        """初始化情感词汇库"""
        return {
            "happy": ["开心", "愉快", "高兴", "欣喜", "快乐", "兴奋", "满足"],
            "sad": ["难过", "伤心", "失落", "沮丧", "悲伤", "忧郁", "低落"],
            "angry": ["生气", "愤怒", "恼火", "不满", "烦躁", "暴躁", "愤慨"],
            "fear": ["害怕", "恐惧", "担心", "忧虑", "紧张", "不安", "焦虑"],
            "surprise": ["惊讶", "意外", "震惊", "吃惊", "诧异", "惊奇", "惊愕"],
            "disgust": ["厌恶", "反感", "恶心", "讨厌", "排斥", "嫌弃", "憎恶"],
            "neutral": ["平静", "正常", "一般", "普通", "平和", "稳定", "中性"],
            "excited": ["兴奋", "激动", "热情", "亢奋", "振奋", "狂热", "激昂"],
            "calm": ["平静", "安静", "宁静", "淡定", "从容", "冷静", "安详"],
            "confused": ["困惑", "迷茫", "疑惑", "不解", "茫然", "混乱", "糊涂"]
        }
    
    def _init_intensity_modifiers(self) -> Dict[str, List[str]]:
        """初始化强度修饰符"""
        return {
            "low": ["有点", "稍微", "略微", "一点", "些许"],
            "medium": ["比较", "相当", "挺", "还算", "蛮"],
            "high": ["非常", "极其", "特别", "超级", "十分", "相当"]
        }
    
    def _init_expression_templates(self) -> Dict[str, Any]:
        """初始化表达模板"""
        return {
            "prefixes": {
                "happy": {
                    "enthusiastic": ["太好了！", "真棒！", "哇！"],
                    "gentle": ["真高兴", "很开心", "感到愉快"],
                    "casual": ["不错呢", "挺好的", "还可以"]
                },
                "sad": {
                    "gentle": ["有些难过", "感到失落", "心情不太好"],
                    "supportive": ["我理解", "我明白", "这确实让人难过"],
                    "serious": ["这很遗憾", "确实令人沮丧"]
                },
                "angry": {
                    "serious": ["这很令人愤怒", "确实让人生气"],
                    "cautious": ["这可能有些问题", "似乎不太合适"]
                }
            },
            "suffixes": {
                "happy": {
                    "enthusiastic": ["真是太棒了！", "太开心了！"],
                    "playful": ["呢～", "哦～"],
                    "casual": ["挺不错的", "还可以"]
                },
                "sad": {
                    "supportive": ["希望你能好起来", "我会陪着你"],
                    "gentle": ["慢慢会好的", "别太难过"]
                }
            }
        }
    
    def _init_emotion_styles(self) -> Dict[EmotionType, List[ExpressionStyle]]:
        """初始化情感对应的表达风格"""
        return {
            EmotionType.HAPPY: [ExpressionStyle.ENTHUSIASTIC, ExpressionStyle.PLAYFUL, ExpressionStyle.CASUAL],
            EmotionType.SAD: [ExpressionStyle.GENTLE, ExpressionStyle.SUPPORTIVE, ExpressionStyle.SERIOUS],
            EmotionType.ANGRY: [ExpressionStyle.SERIOUS, ExpressionStyle.CAUTIOUS, ExpressionStyle.FORMAL],
            EmotionType.FEAR: [ExpressionStyle.GENTLE, ExpressionStyle.SUPPORTIVE, ExpressionStyle.CAUTIOUS],
            EmotionType.SURPRISE: [ExpressionStyle.ENTHUSIASTIC, ExpressionStyle.CASUAL, ExpressionStyle.PLAYFUL],
            EmotionType.DISGUST: [ExpressionStyle.SERIOUS, ExpressionStyle.CAUTIOUS, ExpressionStyle.FORMAL],
            EmotionType.NEUTRAL: [ExpressionStyle.CASUAL, ExpressionStyle.FORMAL, ExpressionStyle.GENTLE],
            EmotionType.EXCITED: [ExpressionStyle.ENTHUSIASTIC, ExpressionStyle.PLAYFUL, ExpressionStyle.CASUAL],
            EmotionType.CALM: [ExpressionStyle.GENTLE, ExpressionStyle.FORMAL, ExpressionStyle.SUPPORTIVE],
            EmotionType.CONFUSED: [ExpressionStyle.CAUTIOUS, ExpressionStyle.GENTLE, ExpressionStyle.SUPPORTIVE]
        }