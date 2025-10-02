"""
JiuCiVoice - 九辞语音伴侣
集成九辞AI伴侣和语音合成功能
"""

import asyncio
import os
import sys
import logging
import importlib.util
from datetime import datetime
from typing import Optional, Dict, Any
from tts_synthesizer import AsyncTTSManager

# 动态导入九辞AI伴侣
jiuci_path = os.path.join(os.path.dirname(__file__), '..', 'JiuCi', 'jiuci_bot.py')
spec = importlib.util.spec_from_file_location("jiuci_bot", jiuci_path)
jiuci_module = importlib.util.module_from_spec(spec)

# 临时添加JiuCi路径以便jiuci_bot.py能找到其依赖
jiuci_dir = os.path.join(os.path.dirname(__file__), '..', 'JiuCi')
sys.path.insert(0, jiuci_dir)
try:
    spec.loader.exec_module(jiuci_module)
    JiuCiBot = jiuci_module.JiuCiBot
finally:
    sys.path.remove(jiuci_dir)

logger = logging.getLogger(__name__)


class JiuCiVoiceBot:
    """九辞语音伴侣 - 集成文字对话和语音合成"""
    
    def __init__(self, config_path: str = None):
        """
        初始化九辞语音伴侣
        
        Args:
            config_path: TTS配置文件路径
        """
        self.jiuci_bot = JiuCiBot()  # 初始化九辞AI伴侣
        self.tts_manager = AsyncTTSManager(config_path)  # 初始化TTS管理器
        self.config = None
        self.output_dir = None
        
    async def initialize(self):
        """初始化语音合成器和配置"""
        await self.tts_manager.initialize()
        self.config = self.tts_manager.load_config()
        
        # 创建输出目录
        jiuci_config = self.config.get("jiuci_voice", {})
        self.output_dir = jiuci_config.get("default_output_dir", "./output")
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info("九辞语音伴侣初始化完成")
    
    def get_voice_profile(self, profile_name: str = "sweet") -> str:
        """
        获取语音配置文件
        
        Args:
            profile_name: 语音配置名称（sweet, gentle, lively, mature）
            
        Returns:
            对应的音色标识符
        """
        jiuci_config = self.config.get("jiuci_voice", {})
        voice_profiles = jiuci_config.get("voice_profiles", {})
        return voice_profiles.get(profile_name, "S_female_01")
    
    def generate_output_filename(self, user_input: str = "") -> str:
        """
        生成输出文件名
        
        Args:
            user_input: 用户输入（用于生成有意义的文件名）
            
        Returns:
            完整的输出文件路径
        """
        jiuci_config = self.config.get("jiuci_voice", {})
        template = jiuci_config.get("filename_template", "jiuci_reply_{timestamp}.wav")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = template.format(timestamp=timestamp)
        
        return os.path.join(self.output_dir, filename)
    
    async def chat_with_voice(self, user_input: str, voice_profile: str = "sweet", 
                            save_audio: bool = None) -> Dict[str, Any]:
        """
        与九辞进行语音对话
        
        Args:
            user_input: 用户输入的文本
            voice_profile: 语音配置（sweet, gentle, lively, mature）
            save_audio: 是否保存音频文件（None时使用配置中的auto_save设置）
            
        Returns:
            包含文字回复、音频数据和文件路径的字典
        """
        if not self.tts_manager.synthesizer:
            await self.initialize()
        
        # 1. 获取九辞的文字回复
        print("🤖 九辞正在思考...")
        text_reply = self.jiuci_bot.chat(user_input)
        print(f"\n💬 九辞说: {text_reply}")
        
        # 2. 将文字回复转换为语音
        print("\n🎵 正在生成语音...")
        speaker = self.get_voice_profile(voice_profile)
        
        # 决定是否保存音频文件
        jiuci_config = self.config.get("jiuci_voice", {})
        should_save = save_audio if save_audio is not None else jiuci_config.get("auto_save", True)
        
        output_file = None
        if should_save:
            output_file = self.generate_output_filename(user_input)
        
        # 生成语音
        audio_data = await self.tts_manager.text_to_speech(
            text=text_reply,
            speaker=speaker,
            output_file=output_file
        )
        
        result = {
            "user_input": user_input,
            "text_reply": text_reply,
            "audio_data": audio_data,
            "audio_file": output_file,
            "voice_profile": voice_profile,
            "speaker": speaker,
            "audio_size": len(audio_data)
        }
        
        if output_file:
            print(f"🎵 语音已保存到: {output_file}")
        print(f"✅ 语音生成完成 ({len(audio_data)} 字节)")
        
        return result
    
    async def get_initial_greeting_with_voice(self, voice_profile: str = "sweet") -> Dict[str, Any]:
        """
        获取九辞的初始问候语音
        
        Args:
            voice_profile: 语音配置
            
        Returns:
            包含问候语和语音的字典
        """
        if not self.tts_manager.synthesizer:
            await self.initialize()
        
        # 获取九辞的初始问候语
        greeting = self.jiuci_bot.get_initial_greeting()
        print(f"💬 九辞说: {greeting}")
        
        # 转换为语音
        print("🎵 正在生成问候语音...")
        speaker = self.get_voice_profile(voice_profile)
        
        jiuci_config = self.config.get("jiuci_voice", {})
        should_save = jiuci_config.get("auto_save", True)
        
        output_file = None
        if should_save:
            output_file = os.path.join(self.output_dir, f"jiuci_greeting_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")
        
        audio_data = await self.tts_manager.text_to_speech(
            text=greeting,
            speaker=speaker,
            output_file=output_file
        )
        
        result = {
            "greeting": greeting,
            "audio_data": audio_data,
            "audio_file": output_file,
            "voice_profile": voice_profile,
            "speaker": speaker,
            "audio_size": len(audio_data)
        }
        
        if output_file:
            print(f"🎵 问候语音已保存到: {output_file}")
        print(f"✅ 问候语音生成完成 ({len(audio_data)} 字节)")
        
        return result
    
    async def batch_synthesize_replies(self, conversations: list, voice_profile: str = "sweet") -> list:
        """
        批量合成多个对话的语音
        
        Args:
            conversations: 对话列表，每个元素为用户输入字符串
            voice_profile: 语音配置
            
        Returns:
            结果列表，每个元素包含对话和语音信息
        """
        if not self.tts_manager.synthesizer:
            await self.initialize()
        
        results = []
        for i, user_input in enumerate(conversations):
            print(f"\n--- 对话 {i+1}/{len(conversations)} ---")
            result = await self.chat_with_voice(user_input, voice_profile, save_audio=True)
            results.append(result)
        
        return results


# 便捷函数
async def quick_jiuci_chat(user_input: str, voice_profile: str = "sweet", 
                          config_path: str = None) -> Dict[str, Any]:
    """
    快速与九辞进行语音对话
    
    Args:
        user_input: 用户输入
        voice_profile: 语音配置
        config_path: TTS配置文件路径
        
    Returns:
        对话结果字典
    """
    bot = JiuCiVoiceBot(config_path)
    return await bot.chat_with_voice(user_input, voice_profile)


if __name__ == "__main__":
    # 测试代码
    async def test_jiuci_voice():
        """测试九辞语音伴侣功能"""
        try:
            bot = JiuCiVoiceBot()
            
            # 测试初始问候
            print("=== 测试初始问候 ===")
            greeting_result = await bot.get_initial_greeting_with_voice("sweet")
            
            # 测试对话
            print("\n=== 测试语音对话 ===")
            test_inputs = [
                "你好九辞，今天天气真不错呢",
                "你最喜欢做什么事情？",
                "给我讲个笑话吧"
            ]
            
            for user_input in test_inputs:
                print(f"\n👤 用户: {user_input}")
                result = await bot.chat_with_voice(user_input, "sweet")
                print(f"📊 音频大小: {result['audio_size']} 字节")
                if result['audio_file']:
                    print(f"📁 文件: {result['audio_file']}")
                
        except Exception as e:
            print(f"测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 运行测试
    asyncio.run(test_jiuci_voice())