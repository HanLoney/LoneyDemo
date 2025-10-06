"""
Web版九辞AI伴侣 - Flask后端服务
集成新的聊天和语音服务，提供现代化的API接口
"""

import os
import sys
import json
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    # 导入新的服务模块
    from core.chat import ChatService
    from core.voice import VoiceService, voice_service
    from core.emotion import EmotionService
    from shared.utils import get_all_config, get_logger, TimeUtils
    print("✅ 成功导入新的服务模块")
    
    # 初始化服务
    chat_service = ChatService()
    emotion_service = EmotionService()
    
    # 配置和日志
    config = get_all_config()
    logger = get_logger(__name__)
    
except ImportError as e:
    print(f"❌ 导入服务模块失败: {e}")
    print("将使用简化模式运行Web服务")
    chat_service = None
    voice_service = None
    emotion_service = None
    config = {}
    
    # 简单的日志记录器
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__, static_folder='.', static_url_path='', template_folder='.')
CORS(app)  # 允许跨域请求

# 全局变量
audio_files = {}  # 用于存储音频文件的信息
service_initialized = False  # 服务初始化标志

async def initialize_services():
    """初始化所有服务"""
    global service_initialized
    
    if chat_service is None or emotion_service is None:
        return False, "服务模块未导入"
    
    try:
        # 初始化语音服务
        voice_init_success = await voice_service.initialize()
        if not voice_init_success:
            logger.warning("语音服务初始化失败，但Web服务仍可正常运行")
        
        service_initialized = True
        logger.info("服务初始化完成")
        return True, "服务初始化成功"
        
    except Exception as e:
        logger.error(f"服务初始化失败: {e}")
        return False, str(e)

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """聊天API接口"""
    try:
        # 检查服务是否已初始化
        if not service_initialized:
            # 尝试初始化服务
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success, message = loop.run_until_complete(initialize_services())
            loop.close()
            
            if not success:
                return jsonify({
                    'success': False,
                    'error': f'服务初始化失败: {message}',
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
        debug_mode = data.get('debug_mode', False)
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': '消息内容为空',
                'reply': '你想说什么呢？'
            })
        
        logger.info(f"收到用户消息: {user_message}")
        logger.info(f"语音功能: {'开启' if voice_enabled else '关闭'}")
        logger.info(f"开发者模式: {'开启' if debug_mode else '关闭'}")
        
        # 初始化调试信息
        debug_info = {} if debug_mode else None
        
        # 使用新的聊天服务处理消息
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 记录LLM调用开始时间
            llm_start_time = datetime.now()
            
            # 异步调用聊天服务
            chat_response = loop.run_until_complete(
                chat_service.async_chat(user_message)
            )
            
            # 记录LLM调用结束时间
            llm_end_time = datetime.now()
            llm_duration = int((llm_end_time - llm_start_time).total_seconds() * 1000)
            
            if debug_mode:
                debug_info['llm_info'] = {
                    'prompt': user_message,
                    'duration': llm_duration,
                    'start_time': llm_start_time.isoformat(),
                    'end_time': llm_end_time.isoformat()
                }
            
            if not chat_response.success:
                return jsonify({
                    'success': False,
                    'error': getattr(chat_response, 'error', '未知错误'),
                    'reply': '抱歉，我现在遇到了一些问题，请稍后再试试~',
                    'debug_info': debug_info
                })
            
            reply = chat_response.message.content
            audio_id = None
            
            # 情感分析（始终执行）
            emotion_info = None
            if emotion_service:
                try:
                    emotion_start_time = datetime.now()
                    
                    # 分析用户情感
                    user_emotion_result = loop.run_until_complete(
                        emotion_service.analyze_emotion(user_message)
                    )
                    
                    # 分析AI回复情感
                    ai_emotion_result = loop.run_until_complete(
                        emotion_service.analyze_emotion(reply)
                    )
                    logger.info(f"AI情感分析结果: {ai_emotion_result}")
                    if ai_emotion_result:
                        logger.info(f"AI主要情感: {ai_emotion_result.primary_emotion.value}, 置信度: {ai_emotion_result.confidence}")
                    else:
                        logger.warning("AI情感分析返回None")
                    
                    # 更新AI情感状态（基于用户输入）
                    emotion_transition = emotion_service.update_emotion_from_input(
                        user_message, user_emotion_result
                    )
                    
                    # 获取更新后的情感状态
                    current_state = emotion_service.get_current_state()
                    emotion_stats = emotion_service.get_emotion_statistics()
                    
                    emotion_end_time = datetime.now()
                    emotion_duration = int((emotion_end_time - emotion_start_time).total_seconds() * 1000)
                    
                    # 存储情感信息（始终可用）
                    emotion_info = {
                        'user_emotion': {
                            'text': user_message,
                            'primary_emotion': user_emotion_result.primary_emotion.value if user_emotion_result else 'unknown',
                            'confidence': user_emotion_result.confidence if user_emotion_result else 0.0,
                            'sentiment_score': user_emotion_result.sentiment_score if user_emotion_result else 0.0,
                            'detected_emotions': {k.value: v for k, v in user_emotion_result.detected_emotions.items()} if user_emotion_result else {},
                            'analysis_time': user_emotion_result.analysis_time if user_emotion_result else 0.0
                        },
                        'ai_emotion': {
                            'text': reply,
                            'primary_emotion': ai_emotion_result.primary_emotion.value if ai_emotion_result else 'unknown',
                            'confidence': ai_emotion_result.confidence if ai_emotion_result else 0.0,
                            'sentiment_score': ai_emotion_result.sentiment_score if ai_emotion_result else 0.0,
                            'detected_emotions': {k.value: v for k, v in ai_emotion_result.detected_emotions.items()} if ai_emotion_result else {},
                            'analysis_time': ai_emotion_result.analysis_time if ai_emotion_result else 0.0
                        },
                        'current_state': {
                            'primary_emotion': current_state.primary_emotion.value if current_state else 'neutral',
                            'intensity': current_state.intensity if current_state else 0.0,
                            'stability': current_state.stability if current_state else 0.7,
                            'emotions': {k.value: v for k, v in current_state.emotions.items()} if current_state else {}
                        },
                        'statistics': emotion_stats if emotion_stats else {},
                        'duration': emotion_duration,
                        'success': True
                    }
                except Exception as e:
                    logger.error(f"情感分析异常: {e}")
                    emotion_info = {
                        'error': str(e),
                        'success': False,
                        'user_emotion': {'text': user_message, 'primary_emotion': 'undefined', 'confidence': 0.0},
                        'ai_emotion': {'text': reply, 'primary_emotion': 'undefined', 'confidence': 0.0}
                    }
            
            # 时间分析（如果开启调试模式）
            if debug_mode:
                try:
                    # 简单的时间信息提取
                    time_keywords = ['今天', '明天', '昨天', '现在', '今晚', '早上', '下午', '晚上']
                    found_time_keywords = [kw for kw in time_keywords if kw in user_message]
                    
                    debug_info['time_info'] = {
                        'current_time': datetime.now().isoformat(),
                        'found_keywords': found_time_keywords,
                        'has_time_reference': len(found_time_keywords) > 0
                    }
                except Exception as e:
                    logger.error(f"时间分析异常: {e}")
                    debug_info['time_info'] = {
                        'error': str(e),
                        'success': False
                    }
            
            # 如果启用语音，生成语音
            voice_success = False
            if voice_enabled:
                try:
                    voice_start_time = datetime.now()
                    tts_response = loop.run_until_complete(
                        voice_service.text_to_speech(
                            text=reply,
                            save_audio=True
                        )
                    )
                    voice_end_time = datetime.now()
                    voice_duration = int((voice_end_time - voice_start_time).total_seconds() * 1000)
                    
                    if tts_response.success and tts_response.output_file:
                        audio_id = str(uuid.uuid4())
                        # 确保使用绝对路径
                        audio_file_path = tts_response.output_file
                        if not os.path.isabs(audio_file_path):
                            # 如果是相对路径，则相对于项目根目录
                            audio_file_path = os.path.join(project_root, audio_file_path)
                        
                        audio_files[audio_id] = {
                            'file_path': audio_file_path,
                            'created_at': datetime.now(),
                            'original_name': os.path.basename(tts_response.output_file),
                            'audio_size': tts_response.audio_size
                        }
                        logger.info(f"音频文件已生成: {tts_response.output_file}")
                        voice_success = True
                    else:
                        logger.warning(f"语音合成失败: {tts_response.error}")
                    
                    if debug_mode:
                        debug_info['voice_info'] = {
                            'success': voice_success,
                            'duration': voice_duration,
                            'audio_size': tts_response.audio_size if voice_success else 0,
                            'error': tts_response.error if not voice_success else None
                        }
                        
                except Exception as e:
                    logger.error(f"语音合成异常: {e}")
                    if debug_mode:
                        debug_info['voice_info'] = {
                            'success': False,
                            'error': str(e)
                        }
            
            response_data = {
                'success': True,
                'reply': reply,
                'audio_id': audio_id,
                'has_audio': audio_id is not None,
                'timestamp': datetime.now().isoformat(),
                'session_id': getattr(chat_response.message, 'user_id', 'default'),
                'message_id': chat_response.message.id
            }
            
            # 确保情感信息始终被包含在调试信息中
            if emotion_info:
                if debug_info is None:
                    debug_info = {}
                debug_info['emotion_info'] = emotion_info
            
            if debug_mode:
                response_data['debug_info'] = debug_info
            elif emotion_info:
                # 即使不在调试模式下，也要包含情感信息供前端使用
                response_data['debug_info'] = {'emotion_info': emotion_info}
            
            return jsonify(response_data)
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"聊天处理失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'reply': '抱歉，我现在遇到了一些问题，请稍后再试试~'
        })

@app.route('/api/audio/<audio_id>')
def get_audio(audio_id):
    """获取音频文件"""
    try:
        if audio_id not in audio_files:
            return jsonify({'error': '音频文件不存在'}), 404
        
        audio_info = audio_files[audio_id]
        audio_file = audio_info['file_path']
        
        # 检查文件是否存在
        if not os.path.exists(audio_file):
            # 清理无效的音频文件记录
            del audio_files[audio_id]
            return jsonify({'error': '音频文件已失效'}), 404
        
        # 确定MIME类型
        file_ext = os.path.splitext(audio_file)[1].lower()
        mime_type = {
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac'
        }.get(file_ext, 'audio/wav')
        
        # 返回音频文件
        return send_file(
            audio_file,
            as_attachment=False,
            mimetype=mime_type,
            download_name=audio_info.get('original_name', f'audio_{audio_id}.wav')
        )
        
    except Exception as e:
        logger.error(f"获取音频文件失败: {e}")
        return jsonify({'error': '获取音频文件失败'}), 500

@app.route('/api/status')
def status():
    """服务状态检查"""
    try:
        status_data = {
            'success': True,
            'service_status': 'running',
            'services_initialized': service_initialized,
            'timestamp': datetime.now().isoformat(),
            'audio_files_count': len(audio_files)
        }
        
        # 如果服务已初始化，获取更多状态信息
        if service_initialized:
            try:
                # 获取聊天服务状态
                if chat_service:
                    chat_status = chat_service.get_service_status() if hasattr(chat_service, 'get_service_status') else 'available'
                    status_data['chat_service'] = chat_status
                
                # 获取语音服务状态
                if voice_service:
                    voice_status = voice_service.get_service_status() if hasattr(voice_service, 'get_service_status') else 'available'
                    status_data['voice_service'] = voice_status
                
                # 获取情感服务状态
                if emotion_service:
                    emotion_status = emotion_service.get_service_status() if hasattr(emotion_service, 'get_service_status') else 'available'
                    status_data['emotion_service'] = emotion_status
                
            except Exception as e:
                status_data['service_error'] = str(e)
                logger.error(f"获取服务状态失败: {e}")
        else:
            status_data['chat_service'] = 'not_initialized'
            status_data['voice_service'] = 'not_initialized'
            status_data['emotion_service'] = 'not_initialized'
        
        return jsonify(status_data)
        
    except Exception as e:
        logger.error(f"状态API错误: {e}")
        return jsonify({
            'success': False,
            'service_status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/clear_audio')
def clear_audio():
    """清理音频文件"""
    try:
        # 删除所有音频文件
        deleted_count = 0
        for audio_id, audio_info in list(audio_files.items()):
            try:
                audio_file = audio_info['file_path']
                if os.path.exists(audio_file):
                    os.remove(audio_file)
                    logger.info(f"已删除音频文件: {audio_file}")
                del audio_files[audio_id]
                deleted_count += 1
            except Exception as e:
                logger.warning(f"删除音频文件失败: {audio_file}, 错误: {e}")
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'已清理 {deleted_count} 个音频文件'
        })
        
    except Exception as e:
        logger.error(f"清理音频文件失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    logger.warning(f"404错误: {request.url}")
    return jsonify({'error': '页面未找到'}), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logger.error(f"500错误: {error}")
    return jsonify({'error': '服务器内部错误'}), 500

def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🌸 九辞AI伴侣 Web版 🌸                      ║
    ║                                                              ║
    ║  💕 青春可爱的AI女朋友聊天网页                                   ║
    ║  🎵 支持语音合成和播放                                          ║
    ║  🧠 集成情感分析系统                                            ║
    ║  🌈 全新架构，更稳定更强大                                       ║
    ║                                                              ║
    ║  🌐 访问地址: http://localhost:5000                            ║
    ║  📡 API文档: http://localhost:5000/api/status                 ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

if __name__ == '__main__':
    print_banner()
    
    # 初始化服务
    logger.info("正在初始化服务...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        success, message = loop.run_until_complete(initialize_services())
        if success:
            logger.info("✅ 服务初始化成功，准备启动Web服务")
            print("✅ 服务初始化成功，准备启动Web服务")
        else:
            logger.warning(f"⚠️ 服务初始化部分失败: {message}")
            print(f"⚠️ 服务初始化部分失败: {message}")
            print("Web服务仍将启动，但部分功能可能不可用")
    except Exception as e:
        logger.error(f"服务初始化异常: {e}")
        print(f"❌ 服务初始化异常: {e}")
        print("Web服务仍将启动，但功能可能受限")
    finally:
        loop.close()
    
    # 启动Flask应用
    try:
        logger.info("启动Web服务器...")
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,  # 生产环境建议关闭debug
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
        logger.info("服务已停止")
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
        logger.error(f"服务启动失败: {e}")