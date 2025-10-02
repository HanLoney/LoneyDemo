"""
JiuCiVoice - 语音合成模块
基于Volcengine TTS SDK的独立语音合成实现
"""

import asyncio
import json
import logging
import uuid
import websockets
from typing import Optional, Dict, Any
import sys
import os

from protocols import EventType, MsgType, full_client_request, receive_message

logger = logging.getLogger(__name__)


class TTSSynthesizer:
    """语音合成器类 - 封装Volcengine TTS功能"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化语音合成器
        
        Args:
            config: 配置字典，包含认证信息、服务配置和TTS参数
        """
        self.config = config
        self.auth_config = config["authentication"]
        self.service_config = config["service"]
        self.tts_config = config["tts"]
        
    def get_resource_id(self, voice: str) -> str:
        """
        根据音色类型获取对应的资源ID
        
        Args:
            voice: 音色类型标识符
            
        Returns:
            对应的资源ID字符串
        """
        if voice.startswith("S_"):
            return "volc.megatts.default"
        return "volc.service_type.10029"
    
    async def synthesize_text(self, text: str, speaker: Optional[str] = None, 
                            output_file: Optional[str] = None) -> bytes:
        """
        将文本转换为语音
        
        Args:
            text: 要转换的文本
            speaker: 音色类型（可选，默认使用配置中的音色）
            output_file: 输出文件路径（可选）
            
        Returns:
            音频数据的字节流
            
        Raises:
            RuntimeError: 当TTS转换失败时
        """
        # 使用传入的参数或配置中的默认值
        speaker = speaker or self.tts_config["speaker"]
        
        # 准备WebSocket连接的请求头
        headers = {
            "X-Api-App-Key": self.auth_config["app_id"],
            "X-Api-Access-Key": self.auth_config["access_token"],
            "X-Api-Resource-Id": self.get_resource_id(speaker),
            "X-Api-Connect-Id": str(uuid.uuid4()),
        }
        
        # 建立WebSocket连接
        endpoint = self.service_config["endpoint"]
        max_size = self.service_config["max_message_size"]
        
        logger.info(f"正在连接到TTS服务: {endpoint}")
        websocket = await websockets.connect(
            endpoint, 
            additional_headers=headers, 
            max_size=max_size
        )
        
        try:
            logger.info(f"已连接到TTS服务，日志ID: {websocket.response.headers.get('x-tt-logid', 'N/A')}")
            
            # 准备TTS合成请求
            request = {
                "user": {
                    "uid": str(uuid.uuid4()),
                },
                "req_params": {
                    "speaker": speaker,
                    "audio_params": self.tts_config["audio_params"],
                    "text": text,
                    "additions": json.dumps(self.tts_config["additions"]),
                },
            }
            
            # 发送TTS请求
            logger.info(f"发送TTS请求 - 音色: {speaker}, 文本: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            await full_client_request(websocket, json.dumps(request).encode())
            
            # 接收音频数据
            audio_data = bytearray()
            logger.info("开始接收音频数据...")
            
            while True:
                msg = await receive_message(websocket)
                
                if msg.type == MsgType.FullServerResponse:
                    if msg.event == EventType.SessionFinished:
                        logger.info("TTS合成完成")
                        break
                elif msg.type == MsgType.AudioOnlyServer:
                    audio_data.extend(msg.payload)
                    logger.debug(f"接收音频数据块: {len(msg.payload)} 字节")
                else:
                    raise RuntimeError(f"TTS转换失败: {msg}")
            
            if not audio_data:
                raise RuntimeError("未接收到任何音频数据")
            
            # 保存到文件（如果指定了输出文件）
            if output_file:
                with open(output_file, "wb") as f:
                    f.write(audio_data)
                logger.info(f"音频已保存到: {output_file} ({len(audio_data)} 字节)")
            
            logger.info(f"语音合成成功: {len(audio_data)} 字节")
            return bytes(audio_data)
            
        finally:
            await websocket.close()
            logger.debug("WebSocket连接已关闭")
    
    async def synthesize_with_config_override(self, text: str, **kwargs) -> bytes:
        """
        使用配置覆盖进行语音合成
        
        Args:
            text: 要转换的文本
            **kwargs: 可覆盖的配置参数（speaker, output_file等）
            
        Returns:
            音频数据的字节流
        """
        return await self.synthesize_text(
            text=text,
            speaker=kwargs.get('speaker'),
            output_file=kwargs.get('output_file')
        )


class AsyncTTSManager:
    """异步TTS管理器 - 提供简化的接口"""
    
    def __init__(self, config_path: str = None):
        """
        初始化TTS管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), "config.json")
        self.synthesizer = None
        
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件未找到: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")
    
    async def initialize(self):
        """初始化TTS合成器"""
        config = self.load_config()
        self.synthesizer = TTSSynthesizer(config)
        logger.info("TTS管理器初始化完成")
    
    async def text_to_speech(self, text: str, speaker: str = None, 
                           output_file: str = None) -> bytes:
        """
        文本转语音的简化接口
        
        Args:
            text: 要转换的文本
            speaker: 音色（可选）
            output_file: 输出文件（可选）
            
        Returns:
            音频数据字节流
        """
        if not self.synthesizer:
            await self.initialize()
        
        return await self.synthesizer.synthesize_text(text, speaker, output_file)


# 便捷函数
async def quick_tts(text: str, config_path: str = None, **kwargs) -> bytes:
    """
    快速文本转语音函数
    
    Args:
        text: 要转换的文本
        config_path: 配置文件路径
        **kwargs: 其他参数（speaker, output_file等）
        
    Returns:
        音频数据字节流
    """
    manager = AsyncTTSManager(config_path)
    return await manager.text_to_speech(text, **kwargs)


if __name__ == "__main__":
    # 测试代码
    async def test():
        try:
            audio_data = await quick_tts(
                "你好，我是九辞，很高兴认识你！",
                output_file="test_jiuci_voice.wav"
            )
            print(f"语音合成成功，生成了 {len(audio_data)} 字节的音频数据")
        except Exception as e:
            print(f"测试失败: {e}")
    
    asyncio.run(test())