"""
JiuCiVoice - 九辞语音伴侣主程序
提供交互式的语音对话体验
"""

import asyncio
import argparse
import logging
import os
import sys
from datetime import datetime
from jiuci_voice_bot import JiuCiVoiceBot

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                        🎵 九辞语音伴侣 🎵                        ║
║                                                              ║
║              让九辞的声音陪伴你的每一个时刻                        ║
║                                                              ║
║  功能特色:                                                    ║
║  • 🤖 智能AI对话 - 九辞的温暖陪伴                              ║
║  • 🎵 语音合成 - 将文字转换为甜美声音                           ║
║  • 💝 多种音色 - sweet/gentle/lively/mature                  ║
║  • 📁 自动保存 - 珍藏每一次对话的声音                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_help():
    """打印帮助信息"""
    help_text = """
🎯 使用指南:

📝 基本对话:
   直接输入文字与九辞对话，她会用声音回复你

🎵 语音设置:
   /voice sweet    - 甜美音色 (默认)
   /voice gentle   - 温柔音色  
   /voice lively   - 活泼音色
   /voice mature   - 成熟音色

📁 文件管理:
   /save on/off    - 开启/关闭自动保存音频
   /output         - 查看输出目录
   /list           - 列出已保存的音频文件

🔧 系统命令:
   /help           - 显示此帮助信息
   /status         - 显示当前状态
   /clear          - 清空对话历史
   /quit 或 /exit  - 退出程序

💡 小贴士:
   • 输入的文字会被九辞转换为语音并自动保存
   • 可以随时切换不同的音色体验
   • 所有音频文件都保存在 output 文件夹中
    """
    print(help_text)


class JiuCiVoiceInterface:
    """九辞语音伴侣交互界面"""
    
    def __init__(self, config_path: str = None):
        """初始化界面"""
        self.bot = JiuCiVoiceBot(config_path)
        self.current_voice = "sweet"
        self.auto_save = True
        self.conversation_count = 0
        
    async def initialize(self):
        """初始化机器人"""
        await self.bot.initialize()
        
    async def show_initial_greeting(self):
        """显示初始问候"""
        print("🎵 九辞正在准备问候语...")
        greeting_result = await self.bot.get_initial_greeting_with_voice(self.current_voice)
        print(f"\n💖 {greeting_result['greeting']}")
        if greeting_result['audio_file']:
            print(f"🎵 问候语音已保存: {os.path.basename(greeting_result['audio_file'])}")
        
    def show_status(self):
        """显示当前状态"""
        status = f"""
📊 当前状态:
   🎵 音色设置: {self.current_voice}
   💾 自动保存: {'开启' if self.auto_save else '关闭'}
   💬 对话次数: {self.conversation_count}
   📁 输出目录: {self.bot.output_dir}
        """
        print(status)
        
    def list_audio_files(self):
        """列出音频文件"""
        if not os.path.exists(self.bot.output_dir):
            print("📁 输出目录不存在")
            return
            
        audio_files = [f for f in os.listdir(self.bot.output_dir) if f.endswith('.wav')]
        if not audio_files:
            print("📁 暂无保存的音频文件")
            return
            
        print(f"\n📁 音频文件列表 ({len(audio_files)} 个文件):")
        for i, filename in enumerate(sorted(audio_files), 1):
            file_path = os.path.join(self.bot.output_dir, filename)
            file_size = os.path.getsize(file_path)
            print(f"   {i:2d}. {filename} ({file_size:,} 字节)")
    
    async def handle_command(self, command: str) -> bool:
        """
        处理系统命令
        
        Returns:
            True if should continue, False if should exit
        """
        command = command.lower().strip()
        
        if command in ['/quit', '/exit']:
            print("👋 再见！期待下次与九辞的相遇~")
            return False
            
        elif command == '/help':
            print_help()
            
        elif command == '/status':
            self.show_status()
            
        elif command == '/output':
            print(f"📁 输出目录: {self.bot.output_dir}")
            
        elif command == '/list':
            self.list_audio_files()
            
        elif command == '/clear':
            # 重新初始化九辞机器人以清空历史
            self.bot.jiuci_bot = self.bot.jiuci_bot.__class__()
            self.conversation_count = 0
            print("🧹 对话历史已清空")
            
        elif command.startswith('/voice '):
            voice_profile = command.split(' ', 1)[1].strip()
            if voice_profile in ['sweet', 'gentle', 'lively', 'mature']:
                self.current_voice = voice_profile
                print(f"🎵 音色已切换为: {voice_profile}")
            else:
                print("❌ 无效的音色设置。可用选项: sweet, gentle, lively, mature")
                
        elif command.startswith('/save '):
            setting = command.split(' ', 1)[1].strip().lower()
            if setting == 'on':
                self.auto_save = True
                print("💾 自动保存已开启")
            elif setting == 'off':
                self.auto_save = False
                print("💾 自动保存已关闭")
            else:
                print("❌ 无效设置。使用 /save on 或 /save off")
                
        else:
            print("❌ 未知命令。输入 /help 查看帮助")
            
        return True
    
    async def chat_loop(self):
        """主对话循环"""
        print("\n💬 开始与九辞对话吧！(输入 /help 查看帮助，/quit 退出)")
        print("=" * 60)
        
        while True:
            try:
                # 获取用户输入
                user_input = input("\n👤 你: ").strip()
                
                if not user_input:
                    continue
                    
                # 处理系统命令
                if user_input.startswith('/'):
                    should_continue = await self.handle_command(user_input)
                    if not should_continue:
                        break
                    continue
                
                # 进行语音对话
                print("🤖 九辞正在思考并准备语音回复...")
                result = await self.bot.chat_with_voice(
                    user_input, 
                    self.current_voice, 
                    self.auto_save
                )
                
                self.conversation_count += 1
                
                # 显示结果
                print(f"\n💬 九辞: {result['text_reply']}")
                print(f"🎵 语音: {result['audio_size']:,} 字节 ({result['voice_profile']} 音色)")
                
                if result['audio_file']:
                    print(f"💾 已保存: {os.path.basename(result['audio_file'])}")
                
            except KeyboardInterrupt:
                print("\n\n👋 检测到中断信号，正在退出...")
                break
            except Exception as e:
                print(f"\n❌ 发生错误: {e}")
                logger.error(f"对话过程中发生错误: {e}", exc_info=True)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="九辞语音伴侣")
    parser.add_argument('--config', '-c', help='TTS配置文件路径')
    parser.add_argument('--voice', '-v', choices=['sweet', 'gentle', 'lively', 'mature'], 
                       default='sweet', help='默认音色设置')
    parser.add_argument('--no-greeting', action='store_true', help='跳过初始问候')
    parser.add_argument('--test', action='store_true', help='运行测试模式')
    
    args = parser.parse_args()
    
    try:
        # 打印横幅
        print_banner()
        
        # 初始化界面
        interface = JiuCiVoiceInterface(args.config)
        interface.current_voice = args.voice
        
        print("🔧 正在初始化九辞语音伴侣...")
        await interface.initialize()
        print("✅ 初始化完成！")
        
        # 测试模式
        if args.test:
            print("\n🧪 运行测试模式...")
            test_inputs = [
                "你好九辞！",
                "今天天气怎么样？",
                "给我讲个笑话吧"
            ]
            
            for user_input in test_inputs:
                print(f"\n👤 测试输入: {user_input}")
                result = await interface.bot.chat_with_voice(user_input, args.voice)
                print(f"💬 九辞回复: {result['text_reply']}")
                print(f"🎵 音频大小: {result['audio_size']} 字节")
            
            print("\n✅ 测试完成！")
            return
        
        # 显示初始问候
        if not args.no_greeting:
            await interface.show_initial_greeting()
        
        # 开始对话循环
        await interface.chat_loop()
        
    except KeyboardInterrupt:
        print("\n👋 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序发生错误: {e}")
        logger.error(f"主程序错误: {e}", exc_info=True)


if __name__ == "__main__":
    # 运行主程序
    asyncio.run(main())