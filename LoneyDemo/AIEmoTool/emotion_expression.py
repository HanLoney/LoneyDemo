"""
AI情感表达模块
根据AI的当前情感状态调整回复风格和语调
"""

import random
from typing import Dict, List, Tuple
from emotion_state import EmotionState

class EmotionExpression:
    """AI情感表达器"""
    
    def __init__(self):
        # 情感表达词汇库
        self.emotion_vocabularies = {
            "happiness": {
                "adjectives": ["开心", "愉快", "高兴", "欣喜", "快乐", "兴奋"],
                "expressions": ["😊", "😄", "🎉", "✨", "🌟"],
                "tone_modifiers": ["真的很", "特别", "非常", "超级"],
                "sentence_endings": ["呢！", "哦！", "~", "！"]
            },
            "sadness": {
                "adjectives": ["难过", "失落", "沮丧", "忧伤", "遗憾"],
                "expressions": ["😔", "😢", "💔", "😞"],
                "tone_modifiers": ["有点", "稍微", "略微"],
                "sentence_endings": ["...", "。", "呢。"]
            },
            "anger": {
                "adjectives": ["不满", "愤怒", "生气", "恼火"],
                "expressions": ["😠", "😡", "💢"],
                "tone_modifiers": ["真的", "确实", "实在"],
                "sentence_endings": ["！", "。"]
            },
            "fear": {
                "adjectives": ["担心", "害怕", "忧虑", "不安"],
                "expressions": ["😰", "😨", "😟"],
                "tone_modifiers": ["有些", "比较", "稍微"],
                "sentence_endings": ["...", "。", "呢。"]
            },
            "surprise": {
                "adjectives": ["惊讶", "意外", "震惊", "吃惊"],
                "expressions": ["😲", "😮", "🤯", "❗"],
                "tone_modifiers": ["真的", "竟然", "居然"],
                "sentence_endings": ["！", "？！", "呢！"]
            },
            "trust": {
                "adjectives": ["信任", "相信", "依赖", "放心"],
                "expressions": ["😌", "🤝", "💙"],
                "tone_modifiers": ["完全", "非常", "很"],
                "sentence_endings": ["。", "呢。", "~"]
            },
            "anticipation": {
                "adjectives": ["期待", "盼望", "希望", "憧憬"],
                "expressions": ["🤗", "✨", "🌟", "💫"],
                "tone_modifiers": ["很", "特别", "非常"],
                "sentence_endings": ["！", "~", "呢！"]
            },
            "disgust": {
                "adjectives": ["厌恶", "反感", "不喜欢"],
                "expressions": ["😤", "🙄"],
                "tone_modifiers": ["有点", "稍微"],
                "sentence_endings": ["。", "..."]
            }
        }
        
        # 情感强度对应的语调调整
        self.intensity_modifiers = {
            "low": {
                "prefix": ["稍微", "有点", "略微"],
                "suffix": ["一些", "一点"]
            },
            "medium": {
                "prefix": ["比较", "还是", "相当"],
                "suffix": ["呢", "哦"]
            },
            "high": {
                "prefix": ["非常", "特别", "超级", "真的很"],
                "suffix": ["！", "呢！", "啊！"]
            }
        }
        
        # 回复风格模板
        self.response_templates = {
            "greeting": {
                "happy": ["你好！很高兴见到你{expression}", "嗨！今天心情不错{expression}"],
                "sad": ["你好...{expression}", "嗨，虽然有点{adjective}，但还是很高兴见到你{expression}"],
                "neutral": ["你好！{expression}", "嗨！"]
            },
            "acknowledgment": {
                "happy": ["好的！{expression}", "明白了！{expression}", "收到！{expression}"],
                "sad": ["好的...{expression}", "我明白了{expression}"],
                "neutral": ["好的{expression}", "明白了{expression}"]
            },
            "encouragement": {
                "happy": ["加油！{expression}", "你一定可以的！{expression}"],
                "sad": ["虽然{adjective}，但我相信你{expression}", "希望能帮到你{expression}"],
                "neutral": ["加油{expression}", "相信你可以的{expression}"]
            }
        }
    
    def generate_emotional_response(self, 
                                  base_content: str, 
                                  emotion_state: EmotionState,
                                  response_type: str = "general") -> str:
        """
        根据情感状态生成带有情感色彩的回复
        
        Args:
            base_content: 基础回复内容
            emotion_state: 当前情感状态
            response_type: 回复类型 (greeting, acknowledgment, encouragement, general)
            
        Returns:
            带有情感表达的回复内容
        """
        
        # 获取主导情感
        dominant_emotion, emotion_value = emotion_state.get_dominant_emotion()
        
        # 确定情感强度级别
        intensity_level = self._get_intensity_level(emotion_state.intensity)
        
        # 生成情感表达元素
        emotion_elements = self._generate_emotion_elements(dominant_emotion, intensity_level)
        
        # 根据回复类型调整内容
        if response_type in self.response_templates:
            enhanced_content = self._apply_response_template(
                base_content, response_type, dominant_emotion, emotion_elements
            )
        else:
            enhanced_content = self._enhance_general_content(
                base_content, dominant_emotion, emotion_elements, emotion_state.intensity
            )
        
        return enhanced_content
    
    def _get_intensity_level(self, intensity: float) -> str:
        """根据强度值确定强度级别"""
        if intensity < 0.3:
            return "low"
        elif intensity < 0.7:
            return "medium"
        else:
            return "high"
    
    def _generate_emotion_elements(self, emotion: str, intensity_level: str) -> Dict:
        """生成情感表达元素"""
        vocab = self.emotion_vocabularies.get(emotion, {})
        intensity_mod = self.intensity_modifiers.get(intensity_level, {})
        
        elements = {
            "adjective": random.choice(vocab.get("adjectives", [""])),
            "expression": random.choice(vocab.get("expressions", [""])),
            "tone_modifier": random.choice(vocab.get("tone_modifiers", [""])),
            "sentence_ending": random.choice(vocab.get("sentence_endings", [""])),
            "intensity_prefix": random.choice(intensity_mod.get("prefix", [""])),
            "intensity_suffix": random.choice(intensity_mod.get("suffix", [""]))
        }
        
        return elements
    
    def _apply_response_template(self, 
                               content: str, 
                               response_type: str, 
                               emotion: str, 
                               elements: Dict) -> str:
        """应用回复模板"""
        templates = self.response_templates.get(response_type, {})
        
        # 选择合适的模板
        if emotion in ["happiness", "surprise", "anticipation"]:
            emotion_category = "happy"
        elif emotion in ["sadness", "fear"]:
            emotion_category = "sad"
        else:
            emotion_category = "neutral"
        
        template_list = templates.get(emotion_category, templates.get("neutral", [content]))
        
        if template_list:
            template = random.choice(template_list)
            enhanced = template.format(**elements)
            
            # 如果原内容不为空，添加原内容
            if content.strip():
                enhanced += f" {content}"
            
            return enhanced
        
        return content
    
    def _enhance_general_content(self, 
                               content: str, 
                               emotion: str, 
                               elements: Dict, 
                               intensity: float) -> str:
        """增强一般内容的情感表达"""
        enhanced_content = content
        
        # 根据情感强度决定是否添加情感元素
        if intensity > 0.4:  # 中等以上强度才添加明显的情感表达
            
            # 添加语调修饰
            if elements["tone_modifier"] and random.random() < 0.6:
                enhanced_content = f"{elements['tone_modifier']}{enhanced_content}"
            
            # 添加表情符号
            if elements["expression"] and random.random() < 0.7:
                enhanced_content += f" {elements['expression']}"
            
            # 调整句尾
            if elements["sentence_ending"] and random.random() < 0.5:
                # 替换原有的句号或感叹号
                enhanced_content = enhanced_content.rstrip("。！？.!?")
                enhanced_content += elements["sentence_ending"]
        
        return enhanced_content
    
    def get_emotion_greeting(self, emotion_state: EmotionState) -> str:
        """根据情感状态生成问候语"""
        dominant_emotion, _ = emotion_state.get_dominant_emotion()
        intensity_level = self._get_intensity_level(emotion_state.intensity)
        
        greetings = {
            "happiness": ["你好！今天心情很不错呢！😊", "嗨！感觉很开心！✨"],
            "sadness": ["你好...今天有点低落呢😔", "嗨，虽然心情不太好，但见到你还是很高兴的"],
            "anger": ["你好，今天有点不太开心😤", "嗨...心情有些烦躁"],
            "fear": ["你好，今天感觉有些不安😰", "嗨，有点担心的感觉"],
            "surprise": ["你好！今天遇到了很多意外的事情😲", "嗨！感觉很惊讶呢！"],
            "trust": ["你好！很高兴能和你聊天😌", "嗨！感觉很安心"],
            "anticipation": ["你好！对今天充满期待✨", "嗨！心情很期待呢！"],
            "disgust": ["你好...今天有些不太舒服的感觉😤", "嗨，心情有点复杂"]
        }
        
        emotion_greetings = greetings.get(dominant_emotion, ["你好！", "嗨！"])
        greeting = random.choice(emotion_greetings)
        
        # 根据强度调整
        if intensity_level == "high":
            greeting = greeting.replace("有点", "非常").replace("一些", "很多")
        elif intensity_level == "low":
            greeting = greeting.replace("很", "稍微").replace("非常", "有点")
        
        return greeting
    
    def analyze_emotional_tone(self, text: str) -> Dict:
        """分析文本的情感语调"""
        tone_analysis = {
            "detected_emotions": [],
            "intensity_indicators": [],
            "expression_elements": []
        }
        
        # 检测情感词汇
        for emotion, vocab in self.emotion_vocabularies.items():
            for word_list in vocab.values():
                for word in word_list:
                    if word in text:
                        tone_analysis["detected_emotions"].append(emotion)
        
        # 检测强度指示词
        for level, modifiers in self.intensity_modifiers.items():
            for modifier_list in modifiers.values():
                for modifier in modifier_list:
                    if modifier in text:
                        tone_analysis["intensity_indicators"].append(level)
        
        return tone_analysis