#!/usr/bin/env python3
"""
九辞AI伴侣Web版启动脚本
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """检查依赖是否安装"""
    try:
        import flask
        import flask_cors
        print("✅ Flask依赖检查通过")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("正在安装依赖...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ 依赖安装完成")
            return True
        except subprocess.CalledProcessError:
            print("❌ 依赖安装失败")
            return False



def start_web_server():
    """启动Web服务器"""
    print("\n🚀 启动九辞AI伴侣Web服务...")
    
    # 设置环境变量
    os.environ['FLASK_APP'] = 'app.py'
    os.environ['FLASK_ENV'] = 'development'
    
    try:
        # 启动Flask应用
        from app import app
        
        print("\n" + "="*60)
        print("🌸 九辞AI伴侣Web版已启动 🌸")
        print("🌐 访问地址: http://localhost:5000")
        print("📱 手机访问: http://你的IP地址:5000")
        print("⏹️  按 Ctrl+C 停止服务")
        print("="*60 + "\n")
        
        # 自动打开浏览器
        time.sleep(1)
        try:
            webbrowser.open('http://localhost:5000')
            print("🌐 已自动打开浏览器")
        except:
            print("💡 请手动打开浏览器访问: http://localhost:5000")
        
        # 启动服务
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True,
            use_reloader=False  # 避免重复启动
        )
        
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("🌸 九辞AI伴侣Web版启动器 🌸\n")
    
    # 检查当前目录
    current_dir = Path(__file__).parent
    print(f"📁 当前目录: {current_dir.resolve()}")
    
    # 检查依赖
    if not check_dependencies():
        print("❌ 依赖检查失败，请手动安装依赖")
        return
    
    # 启动Web服务器
    start_web_server()

if __name__ == "__main__":
    main()