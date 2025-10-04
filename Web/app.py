"""
Web版九辞AI伴侣 - Flask后端服务
集成JiuCiVoice功能，提供聊天和语音合成API
"""

import os
import sys
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import importlib.util

# 添加JiuCiVoice路径到系统路径
jiuci_voice_path = os.path.join(os.path.dirname(__file__), '..', 'LoneyDemo', 'JiuCiVoice')
sys.path.insert(0, jiuci_voice_path)

try:
    # 动态导入JiuCiVoiceBot
    from jiuci_voice_bot import JiuCiVoiceBot
    print("✅ 成功导入JiuCiVoiceBot")
except ImportError as e:
    print(f"❌ 导入JiuCiVoiceBot失败: {e}")
    JiuCiVoiceBot = None

# 创建Flask应用
app = Flask(__name__, static_folder='.', static_url_path='', template_folder='.')
CORS(app)  # 允许跨域请求

# 全局变量
jiuci_bot = None
audio_files = {}  # 存储音频文件映射

def initialize_jiuci_bot():
    """初始化JiuCiVoiceBot实例"""
    global jiuci_bot
    try:
        if JiuCiVoiceBot is None:
            return False, "JiuCiVoiceBot导入失败"
        
        # 切换到JiuCiVoice目录
        original_cwd = os.getcwd()
        os.chdir(jiuci_voice_path)
        
        try:
            jiuci_bot = JiuCiVoiceBot()
            print("✅ JiuCiVoiceBot初始化成功")
            return True, "初始化成功"
        finally:
            os.chdir(original_cwd)
            
    except Exception as e:
        print(f"❌ JiuCiVoiceBot初始化失败: {e}")
        return False, f"初始化失败: {str(e)}"

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """聊天API接口"""
    try:
        # 检查JiuCiVoiceBot是否已初始化
        if jiuci_bot is None:
            success, message = initialize_jiuci_bot()
            if not success:
                return jsonify({
                    'success': False,
                    'error': f'AI服务初始化失败: {message}',
                    'reply': '呜呜，我现在有点问题，请稍后再试试~'
                })
        
        # 获取请求数据
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': '请求数据格式错误',
                'reply': '我没有收到你的消息哦~'
            })
        
        user_message = data['message'].strip()
        voice_enabled = data.get('voice_enabled', True)
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': '消息内容为空',
                'reply': '你想说什么呢？'
            })
        
        print(f"📝 收到用户消息: {user_message}")
        print(f"🔊 语音功能: {'开启' if voice_enabled else '关闭'}")
        
        # 切换到JiuCiVoice目录进行处理
        original_cwd = os.getcwd()
        os.chdir(jiuci_voice_path)
        
        try:
            # 调用JiuCiVoiceBot处理消息
            if voice_enabled:
                # 启用语音合成（异步调用）
                import asyncio
                result = asyncio.run(jiuci_bot.chat_with_voice(user_message))
                ai_reply = result.get('text_reply', '呜呜，我好像出了一点小问题~')
                audio_file = result.get('audio_file')
                
                # 如果有音频文件，生成访问ID
                audio_id = None
                if audio_file:
                    # 确保使用绝对路径
                    if not os.path.isabs(audio_file):
                        audio_file = os.path.join(jiuci_voice_path, audio_file)
                    
                    if os.path.exists(audio_file):
                        audio_id = str(uuid.uuid4())
                        audio_files[audio_id] = audio_file
                        print(f"🎵 生成音频文件: {audio_file}")
                        print(f"🎵 音频ID: {audio_id}")
                
                return jsonify({
                    'success': True,
                    'reply': ai_reply,
                    'audio_file': audio_id,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                # 仅文本回复（使用JiuCi的chat方法）
                ai_reply = jiuci_bot.jiuci_bot.chat(user_message)
                
                return jsonify({
                    'success': True,
                    'reply': ai_reply,
                    'audio_file': None,
                    'timestamp': datetime.now().isoformat()
                })
                
        finally:
            os.chdir(original_cwd)
            
    except Exception as e:
        print(f"❌ 聊天处理错误: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'reply': '呜呜，我好像出了一点小问题，稍后再试试吧~'
        })

@app.route('/api/audio/<audio_id>')
def get_audio(audio_id):
    """获取音频文件"""
    try:
        if audio_id not in audio_files:
            return jsonify({'error': '音频文件不存在'}), 404
        
        audio_file = audio_files[audio_id]
        
        # 检查文件是否存在
        if not os.path.exists(audio_file):
            return jsonify({'error': '音频文件已被删除'}), 404
        
        print(f"🎵 发送音频文件: {audio_file}")
        return send_file(audio_file, mimetype='audio/wav')
        
    except Exception as e:
        print(f"❌ 音频文件发送错误: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def status():
    """服务状态检查"""
    try:
        # 检查JiuCiVoiceBot状态
        bot_status = jiuci_bot is not None
        
        # 检查JiuCiVoice目录
        jiuci_voice_exists = os.path.exists(jiuci_voice_path)
        
        return jsonify({
            'success': True,
            'bot_initialized': bot_status,
            'jiuci_voice_path': jiuci_voice_path,
            'jiuci_voice_exists': jiuci_voice_exists,
            'audio_files_count': len(audio_files),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/clear_audio')
def clear_audio():
    """清理音频文件缓存"""
    try:
        global audio_files
        cleared_count = len(audio_files)
        audio_files.clear()
        
        return jsonify({
            'success': True,
            'cleared_count': cleared_count,
            'message': f'已清理 {cleared_count} 个音频文件缓存'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({'error': '页面不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({'error': '服务器内部错误'}), 500

def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🌸 九辞AI伴侣 Web版 🌸                      ║
    ║                                                              ║
    ║  💕 青春可爱的AI女朋友聊天网页                                   ║
    ║  🎵 支持语音合成和播放                                          ║
    ║  🌈 集成JiuCiVoice完整功能                                      ║
    ║                                                              ║
    ║  🌐 访问地址: http://localhost:5000                            ║
    ║  📡 API文档: http://localhost:5000/api/status                 ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

if __name__ == '__main__':
    print_banner()
    
    # 检查JiuCiVoice路径
    if not os.path.exists(jiuci_voice_path):
        print(f"❌ JiuCiVoice路径不存在: {jiuci_voice_path}")
        print("请确保在正确的目录下运行此服务")
        sys.exit(1)
    
    print(f"📁 JiuCiVoice路径: {jiuci_voice_path}")
    
    # 预初始化JiuCiVoiceBot
    print("🚀 正在初始化AI服务...")
    success, message = initialize_jiuci_bot()
    if success:
        print("✅ AI服务初始化成功，准备启动Web服务")
    else:
        print(f"⚠️ AI服务初始化失败: {message}")
        print("Web服务仍将启动，但聊天功能可能不可用")
    
    # 启动Flask应用
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")