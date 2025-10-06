#!/usr/bin/env python3
"""
JiuCi AI伴侣 - 统一启动脚本
支持启动Web服务、聊天服务等不同模式
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def get_project_root():
    """获取项目根目录"""
    return Path(__file__).parent.absolute()

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    print(f"✅ Python版本: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """检查依赖包"""
    required_packages = [
        'flask',
        'flask-cors',
        'asyncio',
        'pathlib'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True

def install_dependencies():
    """安装依赖包"""
    project_root = get_project_root()
    requirements_files = [
        project_root / "requirements.txt",
        project_root / "Web" / "requirements.txt"
    ]
    
    for req_file in requirements_files:
        if req_file.exists():
            print(f"📦 安装依赖: {req_file}")
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(req_file)
                ], check=True)
                print(f"✅ 依赖安装完成: {req_file}")
            except subprocess.CalledProcessError as e:
                print(f"❌ 依赖安装失败: {e}")
                return False
    
    return True

def start_web_service():
    """启动Web服务"""
    project_root = get_project_root()
    web_dir = project_root / "Web"
    app_file = web_dir / "app.py"
    
    if not app_file.exists():
        print(f"❌ Web应用文件不存在: {app_file}")
        return False
    
    print("🚀 启动Web服务...")
    os.chdir(web_dir)
    
    try:
        subprocess.run([sys.executable, str(app_file)], check=True)
    except KeyboardInterrupt:
        print("\n👋 Web服务已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ Web服务启动失败: {e}")
        return False
    
    return True

def start_chat_service():
    """启动聊天服务（命令行模式）"""
    project_root = get_project_root()
    
    # 添加项目路径
    sys.path.insert(0, str(project_root))
    
    try:
        from core.chat import ChatService
        from core.emotion import EmotionService
        import asyncio
        
        print("🤖 启动聊天服务...")
        
        async def chat_loop():
            chat_service = ChatService()
            emotion_service = EmotionService()
            
            print("✅ 聊天服务已启动")
            print("💬 输入消息开始聊天，输入 'quit' 退出")
            print("-" * 50)
            
            while True:
                try:
                    user_input = input("\n你: ").strip()
                    if user_input.lower() in ['quit', 'exit', '退出']:
                        break
                    
                    if not user_input:
                        continue
                    
                    # 发送消息
                    response = await chat_service.async_chat(user_input)
                    if response.success:
                        print(f"九辞: {response.content}")
                    else:
                        print(f"❌ 错误: {response.error}")
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"❌ 聊天错误: {e}")
            
            print("\n👋 聊天服务已停止")
        
        asyncio.run(chat_loop())
        
    except ImportError as e:
        print(f"❌ 导入聊天服务失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 聊天服务启动失败: {e}")
        return False
    
    return True

def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🌸 九辞AI伴侣启动器 🌸                       ║
    ║                                                              ║
    ║  💕 青春可爱的AI女朋友                                          ║
    ║  🎵 支持语音合成和播放                                          ║
    ║  🧠 集成情感分析系统                                            ║
    ║  🌈 全新架构，更稳定更强大                                       ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="JiuCi AI伴侣启动器")
    parser.add_argument(
        'mode', 
        choices=['web', 'chat', 'install'],
        help='启动模式: web(Web服务), chat(命令行聊天), install(安装依赖)'
    )
    parser.add_argument(
        '--check', 
        action='store_true',
        help='检查环境和依赖'
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 检查或安装依赖
    if args.mode == 'install' or args.check:
        print("\n📋 检查依赖包...")
        if not check_dependencies():
            if args.mode == 'install':
                print("\n📦 安装依赖包...")
                if not install_dependencies():
                    sys.exit(1)
                print("\n✅ 依赖安装完成")
            else:
                sys.exit(1)
        else:
            print("\n✅ 所有依赖已满足")
        
        if args.mode == 'install':
            return
    
    # 启动对应服务
    if args.mode == 'web':
        start_web_service()
    elif args.mode == 'chat':
        start_chat_service()

if __name__ == '__main__':
    main()