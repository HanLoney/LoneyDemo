"""
TTS客户端
基于Volcengine TTS SDK的语音合成客户端
"""
import asyncio
import json
import uuid
import websockets
import io
import struct
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path
import logging
from enum import IntEnum
from dataclasses import dataclass

from shared.utils import get_all_config, get_logger, FileUtils, TimeUtils


class TTSClient:
    """TTS客户端"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_all_config()
        self.logger = get_logger(__name__)
        
        # TTS配置
        external_apis = self.config.get('external_apis', {})
        self.tts_config = external_apis.get('tts', {})
        self.auth_config = {
            'app_id': self.tts_config.get('app_id'),
            'access_token': self.tts_config.get('access_token')
        }
        
        # 调试日志 - 检查认证配置
        self.logger.debug(f"TTS认证配置 - app_id: {self.auth_config.get('app_id')}, "
                         f"access_token: {'***' + str(self.auth_config.get('access_token', ''))[-4:] if self.auth_config.get('access_token') else 'None'}")
        self.service_config = {
            'endpoint': self.tts_config.get('endpoint'),
            'max_message_size': 10485760
        }
        self.audio_config = {
            'params': {
                'format': self.tts_config.get('audio_format', 'wav'),
                'sample_rate': self.tts_config.get('sample_rate', 24000),
                'enable_timestamp': True
            },
            'additions': {
                'disable_markdown_filter': False
            }
        }
        
        # 语音配置文件
        self.voice_profiles = self.tts_config.get('voice_profiles', {})
        
        # 输出配置
        self.output_config = self.tts_config.get('output', {})
        self.default_output_dir = Path(self.output_config.get('default_dir', 'data/voice/output'))
        self.auto_save = self.output_config.get('auto_save', True)
        self.filename_template = self.output_config.get('filename_template', 'tts_{timestamp}.wav')
        
        # 确保输出目录存在
        self.default_output_dir.mkdir(parents=True, exist_ok=True)
        
        # 统计信息
        self.synthesis_count = 0
        self.total_characters = 0
        self.total_audio_bytes = 0
        self.error_count = 0
        
        self.logger.info("TTS客户端已初始化")
    
    async def synthesize_text(self, 
                             text: str, 
                             voice: Optional[str] = None,
                             output_file: Optional[str] = None,
                             save_audio: Optional[bool] = None) -> Dict[str, Any]:
        """
        将文本转换为语音
        
        Args:
            text: 要转换的文本
            voice: 语音类型或配置文件名
            output_file: 输出文件路径
            save_audio: 是否保存音频文件
            
        Returns:
            包含音频数据和元信息的字典
        """
        try:
            start_time = TimeUtils.now()
            
            # 获取语音配置
            speaker = self._get_speaker_id(voice)
            
            # 决定是否保存文件
            should_save = save_audio if save_audio is not None else self.auto_save
            
            # 生成输出文件路径
            if should_save and not output_file:
                output_file = self._generate_output_filename(text)
            
            # 准备WebSocket连接
            endpoint = self.service_config.get('endpoint')
            max_size = self.service_config.get('max_message_size', 10485760)
            
            self.logger.info(f"开始TTS合成 - 文本: '{text[:50]}{'...' if len(text) > 50 else ''}', 语音: {voice}")
            
            # 建立WebSocket连接（使用认证头部）
            headers = self._build_headers(speaker)
            websocket = await websockets.connect(
                endpoint, 
                additional_headers=headers, 
                max_size=max_size
            )
            
            try:
                self.logger.info(f"已连接到TTS服务，日志ID: {websocket.response.headers.get('x-tt-logid', 'N/A')}")
                
                # 发送TTS请求
                request = self._build_tts_request(text, speaker)
                await self._send_full_request(websocket, json.dumps(request).encode())
                
                # 接收音频数据
                audio_data = await self._receive_audio_data(websocket)
                
                # 保存音频文件
                if should_save and output_file:
                    FileUtils.write_bytes(Path(output_file), audio_data)
                
                # 更新统计
                self._update_stats(text, audio_data, TimeUtils.time_diff_seconds(TimeUtils.now(), start_time))
                
                result = {
                    "audio_data": audio_data,
                    "text": text,
                    "voice": voice,
                    "speaker": speaker,
                    "output_file": output_file if should_save else None,
                    "audio_size": len(audio_data),
                    "processing_time": TimeUtils.time_diff_seconds(TimeUtils.now(), start_time),
                    "timestamp": start_time.isoformat()
                }
                
                self.logger.info(f"TTS合成完成 - 音频大小: {len(audio_data)} 字节, "
                               f"耗时: {result['processing_time']:.2f}s")
                
                return result
                
            finally:
                await websocket.close()
                
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"TTS合成失败: {e}")
            raise
    
    async def batch_synthesize(self, 
                              texts: List[str], 
                              voice: Optional[str] = None,
                              output_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        批量文本转语音
        
        Args:
            texts: 文本列表
            voice: 语音类型
            output_dir: 输出目录
            
        Returns:
            合成结果列表
        """
        try:
            results = []
            output_path = Path(output_dir) if output_dir else self.default_output_dir
            output_path.mkdir(parents=True, exist_ok=True)
            
            for i, text in enumerate(texts):
                self.logger.info(f"批量合成进度: {i+1}/{len(texts)}")
                
                output_file = output_path / f"batch_{i+1:03d}_{TimeUtils.now().strftime('%Y%m%d_%H%M%S')}.wav"
                
                result = await self.synthesize_text(
                    text=text,
                    voice=voice,
                    output_file=str(output_file),
                    save_audio=True
                )
                
                results.append(result)
            
            self.logger.info(f"批量合成完成 - 共处理 {len(texts)} 个文本")
            return results
            
        except Exception as e:
            self.logger.error(f"批量合成失败: {e}")
            raise
    
    def get_available_voices(self) -> Dict[str, str]:
        """获取可用的语音配置"""
        return self.voice_profiles.copy()
    
    def get_voice_info(self, voice: str) -> Optional[Dict[str, Any]]:
        """获取语音信息"""
        if voice in self.voice_profiles:
            return {
                "name": voice,
                "speaker_id": self.voice_profiles[voice],
                "description": self._get_voice_description(voice)
            }
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "synthesis_count": self.synthesis_count,
            "total_characters": self.total_characters,
            "total_audio_bytes": self.total_audio_bytes,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.synthesis_count, 1),
            "average_audio_size": self.total_audio_bytes / max(self.synthesis_count, 1),
            "available_voices": len(self.voice_profiles)
        }
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self.synthesis_count = 0
        self.total_characters = 0
        self.total_audio_bytes = 0
        self.error_count = 0
        self.logger.info("TTS统计信息已重置")
    
    async def test_connection(self) -> bool:
        """测试TTS服务连接"""
        try:
            # 使用简单文本测试
            result = await self.synthesize_text(
                text="测试",
                save_audio=False
            )
            
            if result and result.get('audio_data'):
                self.logger.info("TTS连接测试成功")
                return True
            else:
                self.logger.error("TTS连接测试失败 - 无音频数据")
                return False
                
        except Exception as e:
            self.logger.error(f"TTS连接测试异常: {e}")
            return False
    
    def _get_speaker_id(self, voice: Optional[str]) -> str:
        """获取说话人ID"""
        if voice and voice in self.voice_profiles:
            return self.voice_profiles[voice]
        
        # 使用默认语音
        default_voice = self.audio_config.get('default_voice', 'sweet')
        if default_voice in self.voice_profiles:
            return self.voice_profiles[default_voice]
        
        # 使用配置中的默认speaker
        return self.tts_config.get('speaker', 'S_HLw7rGSx1')
    
    def _get_voice_description(self, voice: str) -> str:
        """获取语音描述"""
        descriptions = {
            "sweet": "甜美可爱的声音",
            "gentle": "温柔轻柔的声音",
            "lively": "活泼开朗的声音",
            "mature": "成熟稳重的声音",
            "professional": "专业正式的声音",
            "warm": "温暖亲切的声音"
        }
        return descriptions.get(voice, "自定义语音")
    
    def _build_headers(self, speaker: str) -> Dict[str, str]:
        """构建WebSocket请求头 - 与JiuCiVoice项目保持一致"""
        headers = {
            "X-Api-App-Key": self.auth_config.get('app_id'),
            "X-Api-Access-Key": self.auth_config.get('access_token'),
            "X-Api-Resource-Id": self._get_resource_id(speaker),
            "X-Api-Connect-Id": str(uuid.uuid4()),
        }
        
        self.logger.debug(f"构建的头部: {headers}")
        return headers
    
    def _get_resource_id(self, speaker: str) -> str:
        """获取资源ID - 根据JiuCiVoice的实现"""
        if speaker.startswith("S_"):
            return "volc.megatts.default"
        return "volc.service_type.10029"
    
    def _build_tts_request(self, text: str, speaker: str) -> Dict[str, Any]:
        """构建TTS请求 - 根据JiuCiVoice的实现"""
        return {
            "user": {
                "uid": str(uuid.uuid4()),
            },
            "req_params": {
                "speaker": speaker,
                "audio_params": {
                    "format": self.tts_config.get('audio_format', 'wav'),
                    "sample_rate": self.tts_config.get('sample_rate', 24000),
                    "enable_timestamp": True
                },
                "text": text,
                "additions": json.dumps({
                    "disable_markdown_filter": False
                }),
            },
        }
    
    async def _send_full_request(self, websocket, data: bytes) -> None:
        """发送完整请求 - 使用JiuCiVoice的协议"""
        await full_client_request(websocket, data)
    
    async def _receive_audio_data(self, websocket) -> bytes:
        """接收音频数据 - 使用JiuCiVoice的协议"""
        audio_data = bytearray()
        
        while True:
            try:
                message = await receive_message(websocket)
                
                # 使用与JiuCiVoice相同的简化处理逻辑
                if message.type == MsgType.FullServerResponse:
                    if message.event == EventType.SessionFinished:
                        self.logger.info("TTS合成完成")
                        break
                elif message.type == MsgType.AudioOnlyServer:
                    audio_data.extend(message.payload)
                    self.logger.debug(f"接收音频数据块: {len(message.payload)} 字节")
                else:
                    # 对于其他消息类型（包括FrontEndResultServer），记录但继续
                    self.logger.debug(f"收到消息: {message}")
                    continue
                    
            except websockets.exceptions.ConnectionClosed as e:
                self.logger.info(f"WebSocket连接已关闭: {e}")
                break
            except asyncio.TimeoutError:
                self.logger.error("接收音频数据超时")
                raise Exception("TTS服务器错误: 接收音频数据超时")
            except Exception as e:
                self.logger.error(f"接收音频数据时出现异常: {type(e).__name__}: {e}")
                # 如果没有接收到任何音频数据，抛出更具体的错误
                if not audio_data:
                    raise Exception(f"TTS服务器错误: {type(e).__name__}: {e}")
                else:
                    # 如果已经接收到部分音频数据，记录错误但不抛出异常
                    self.logger.warning(f"接收音频数据时出现异常，但已获得部分数据: {e}")
                    break
        
        return bytes(audio_data)
    
    def _generate_output_filename(self, text: str) -> str:
        """生成输出文件名"""
        timestamp = TimeUtils.now().strftime('%Y%m%d_%H%M%S')
        
        # 从文本生成简短的标识
        text_id = text[:20].replace(' ', '_').replace('\n', '_')
        # 移除特殊字符
        text_id = ''.join(c for c in text_id if c.isalnum() or c in '_-')
        
        filename = self.filename_template.format(
            timestamp=timestamp,
            text_id=text_id,
            synthesis_count=self.synthesis_count + 1
        )
        
        return str(self.default_output_dir / filename)
    
    def _update_stats(self, text: str, audio_data: bytes, processing_time: float) -> None:
        """更新统计信息"""
        self.synthesis_count += 1
        self.total_characters += len(text)
        self.total_audio_bytes += len(audio_data)
        
        self.logger.debug(f"TTS统计更新 - 合成次数: {self.synthesis_count}, "
                         f"总字符数: {self.total_characters}, "
                         f"总音频字节: {self.total_audio_bytes}, "
                         f"处理时间: {processing_time:.2f}s")


class TTSClientManager:
    """TTS客户端管理器"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._clients: Dict[str, TTSClient] = {}
        self._default_client: Optional[TTSClient] = None
    
    def get_client(self, client_id: str = "default") -> TTSClient:
        """获取TTS客户端"""
        if client_id not in self._clients:
            self._clients[client_id] = TTSClient()
            
            if client_id == "default":
                self._default_client = self._clients[client_id]
        
        return self._clients[client_id]
    
    def get_default_client(self) -> TTSClient:
        """获取默认客户端"""
        if not self._default_client:
            self._default_client = self.get_client("default")
        return self._default_client
    
    def remove_client(self, client_id: str) -> bool:
        """移除客户端"""
        if client_id in self._clients:
            del self._clients[client_id]
            self.logger.info(f"移除TTS客户端: {client_id}")
            return True
        return False
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有客户端统计"""
        return {
            client_id: client.get_stats()
            for client_id, client in self._clients.items()
        }
    
    def reset_all_stats(self) -> None:
        """重置所有客户端统计"""
        for client in self._clients.values():
            client.reset_stats()
        self.logger.info("所有TTS客户端统计已重置")


# 全局TTS客户端管理器
tts_manager = TTSClientManager()


# 从JiuCiVoice复制的协议定义
class MsgType(IntEnum):
    """Message type"""
    Invalid = 0
    FullClientRequest = 0b1
    AudioOnlyClient = 0b10
    FullServerResponse = 0b1001
    AudioOnlyServer = 0b1011
    FrontEndResultServer = 0b1100
    Error = 0b1111

    # Aliases
    ServerACK = AudioOnlyServer

class MsgTypeFlagBits(IntEnum):
    """Message type flag bits"""
    NoSeq = 0  # Non-terminal packet with no sequence
    PositiveSeq = 0b1  # Non-terminal packet with sequence > 0
    LastNoSeq = 0b10  # Last packet with no sequence
    NegativeSeq = 0b11  # Last packet with sequence < 0
    WithEvent = 0b100  # Payload contains event number (int32)

class VersionBits(IntEnum):
    """Version bits"""
    Version1 = 1
    Version2 = 2
    Version3 = 3
    Version4 = 4

class HeaderSizeBits(IntEnum):
    """Header size bits"""
    HeaderSize4 = 1
    HeaderSize8 = 2
    HeaderSize12 = 3
    HeaderSize16 = 4

class SerializationBits(IntEnum):
    """Serialization bits"""
    Raw = 0
    JSON = 0b1
    Thrift = 0b11
    Custom = 0b1111

class CompressionBits(IntEnum):
    """Compression bits"""
    None_ = 0
    Gzip = 0b1
    Custom = 0b1111

class EventType(IntEnum):
    """Event type"""
    None_ = 0  # Default event
    
    # Connection events
    StartConnection = 1
    StartTask = 1  # Alias of StartConnection
    FinishConnection = 2
    FinishTask = 2  # Alias of FinishConnection
    
    # Connection status events
    ConnectionStarted = 50  # Connection established successfully
    TaskStarted = 50  # Alias of ConnectionStarted
    ConnectionFailed = 51  # Connection failed (possibly due to authentication failure)
    TaskFailed = 51  # Alias of ConnectionFailed
    ConnectionFinished = 52  # Connection ended
    TaskFinished = 52  # Alias of ConnectionFinished
    
    # Session events
    StartSession = 100
    CancelSession = 101
    FinishSession = 102
    
    # Session status events
    SessionStarted = 150
    SessionCanceled = 151
    SessionFinished = 152
    SessionFailed = 153
    UsageResponse = 154  # Usage response
    ChargeData = 154  # Alias of UsageResponse
    
    # Task events
    TaskRequest = 200
    UpdateConfig = 201
    
    # Audio events
    AudioMuted = 250
    
    # Greeting events
    SayHello = 300
    
    # TTS events
    TTSSentenceStart = 350
    TTSSentenceEnd = 351
    TTSResponse = 352
    TTSEnded = 359

@dataclass
class Message:
    """Message object"""
    version: VersionBits = VersionBits.Version1
    header_size: HeaderSizeBits = HeaderSizeBits.HeaderSize4
    type: MsgType = MsgType.Invalid
    flag: MsgTypeFlagBits = MsgTypeFlagBits.NoSeq
    serialization: SerializationBits = SerializationBits.JSON
    compression: CompressionBits = CompressionBits.None_

    event: EventType = EventType.None_
    session_id: str = ""
    connect_id: str = ""
    sequence: int = 0
    error_code: int = 0

    payload: bytes = b""

    @classmethod
    def from_bytes(cls, data: bytes) -> "Message":
        """Create message object from bytes"""
        if len(data) < 3:
            raise ValueError(
                f"Data too short: expected at least 3 bytes, got {len(data)}"
            )

        type_and_flag = data[1]
        msg_type = MsgType(type_and_flag >> 4)
        flag = MsgTypeFlagBits(type_and_flag & 0b00001111)

        msg = cls(type=msg_type, flag=flag)
        msg.unmarshal(data)
        return msg

    def marshal(self) -> bytes:
        """Serialize message to bytes"""
        buffer = io.BytesIO()

        # Write header
        header = [
            (self.version << 4) | self.header_size,
            (self.type << 4) | self.flag,
            (self.serialization << 4) | self.compression,
        ]

        header_size = 4 * self.header_size
        if padding := header_size - len(header):
            header.extend([0] * padding)

        buffer.write(bytes(header))

        # Write other fields
        writers = self._get_writers()
        for writer in writers:
            writer(buffer)

        return buffer.getvalue()

    def unmarshal(self, data: bytes) -> None:
        """Deserialize message from bytes"""
        buffer = io.BytesIO(data)

        # Read version and header size
        version_and_header_size = buffer.read(1)[0]
        self.version = VersionBits(version_and_header_size >> 4)
        self.header_size = HeaderSizeBits(version_and_header_size & 0b00001111)

        # Skip second byte
        buffer.read(1)

        # Read serialization and compression methods
        serialization_compression = buffer.read(1)[0]
        self.serialization = SerializationBits(serialization_compression >> 4)
        self.compression = CompressionBits(serialization_compression & 0b00001111)

        # Skip header padding
        header_size = 4 * self.header_size
        read_size = 3
        if padding_size := header_size - read_size:
            buffer.read(padding_size)

        # Read other fields
        readers = self._get_readers()
        for reader in readers:
            reader(buffer)

        # Check for remaining data
        remaining = buffer.read()
        if remaining:
            raise ValueError(f"Unexpected data after message: {remaining}")

    def _get_writers(self) -> List[Callable[[io.BytesIO], None]]:
        """Get list of writer functions"""
        writers = []

        if self.flag == MsgTypeFlagBits.WithEvent:
            writers.extend([self._write_event, self._write_session_id])

        if self.type in [
            MsgType.FullClientRequest,
            MsgType.FullServerResponse,
            MsgType.FrontEndResultServer,
            MsgType.AudioOnlyClient,
            MsgType.AudioOnlyServer,
        ]:
            if self.flag in [MsgTypeFlagBits.PositiveSeq, MsgTypeFlagBits.NegativeSeq]:
                writers.append(self._write_sequence)
        elif self.type == MsgType.Error:
            writers.append(self._write_error_code)
        else:
            raise ValueError(f"Unsupported message type: {self.type}")

        writers.append(self._write_payload)
        return writers

    def _get_readers(self) -> List[Callable[[io.BytesIO], None]]:
        """Get list of reader functions"""
        readers = []

        if self.type in [
            MsgType.FullClientRequest,
            MsgType.FullServerResponse,
            MsgType.FrontEndResultServer,
            MsgType.AudioOnlyClient,
            MsgType.AudioOnlyServer,
        ]:
            if self.flag in [MsgTypeFlagBits.PositiveSeq, MsgTypeFlagBits.NegativeSeq]:
                readers.append(self._read_sequence)
        elif self.type == MsgType.Error:
            readers.append(self._read_error_code)
        else:
            raise ValueError(f"Unsupported message type: {self.type}")

        if self.flag == MsgTypeFlagBits.WithEvent:
            readers.extend(
                [self._read_event, self._read_session_id, self._read_connect_id]
            )

        readers.append(self._read_payload)
        return readers

    def _write_event(self, buffer: io.BytesIO) -> None:
        """Write event"""
        buffer.write(struct.pack(">i", self.event))

    def _write_session_id(self, buffer: io.BytesIO) -> None:
        """Write session ID"""
        if self.event in [
            EventType.StartConnection,
            EventType.FinishConnection,
            EventType.ConnectionStarted,
            EventType.ConnectionFailed,
        ]:
            return

        session_id_bytes = self.session_id.encode("utf-8")
        size = len(session_id_bytes)
        if size > 0xFFFFFFFF:
            raise ValueError(f"Session ID size ({size}) exceeds max(uint32)")

        buffer.write(struct.pack(">I", size))
        if size > 0:
            buffer.write(session_id_bytes)

    def _write_sequence(self, buffer: io.BytesIO) -> None:
        """Write sequence number"""
        buffer.write(struct.pack(">i", self.sequence))

    def _write_error_code(self, buffer: io.BytesIO) -> None:
        """Write error code"""
        buffer.write(struct.pack(">I", self.error_code))

    def _write_payload(self, buffer: io.BytesIO) -> None:
        """Write payload"""
        size = len(self.payload)
        if size > 0xFFFFFFFF:
            raise ValueError(f"Payload size ({size}) exceeds max(uint32)")

        buffer.write(struct.pack(">I", size))
        buffer.write(self.payload)

    def _read_event(self, buffer: io.BytesIO) -> None:
        """Read event"""
        event_bytes = buffer.read(4)
        if event_bytes:
            self.event = EventType(struct.unpack(">i", event_bytes)[0])

    def _read_session_id(self, buffer: io.BytesIO) -> None:
        """Read session ID"""
        if self.event in [
            EventType.StartConnection,
            EventType.FinishConnection,
            EventType.ConnectionStarted,
            EventType.ConnectionFailed,
            EventType.ConnectionFinished,
        ]:
            return

        size_bytes = buffer.read(4)
        if size_bytes:
            size = struct.unpack(">I", size_bytes)[0]
            if size > 0:
                session_id_bytes = buffer.read(size)
                if len(session_id_bytes) == size:
                    self.session_id = session_id_bytes.decode("utf-8")

    def _read_connect_id(self, buffer: io.BytesIO) -> None:
        """Read connection ID"""
        if self.event in [
            EventType.ConnectionStarted,
            EventType.ConnectionFailed,
            EventType.ConnectionFinished,
        ]:
            size_bytes = buffer.read(4)
            if size_bytes:
                size = struct.unpack(">I", size_bytes)[0]
                if size > 0:
                    self.connect_id = buffer.read(size).decode("utf-8")

    def _read_sequence(self, buffer: io.BytesIO) -> None:
        """Read sequence number"""
        sequence_bytes = buffer.read(4)
        if sequence_bytes:
            self.sequence = struct.unpack(">i", sequence_bytes)[0]

    def _read_error_code(self, buffer: io.BytesIO) -> None:
        """Read error code"""
        error_code_bytes = buffer.read(4)
        if error_code_bytes:
            self.error_code = struct.unpack(">I", error_code_bytes)[0]

    def _read_payload(self, buffer: io.BytesIO) -> None:
        """Read payload"""
        size_bytes = buffer.read(4)
        if size_bytes:
            size = struct.unpack(">I", size_bytes)[0]
            if size > 0:
                self.payload = buffer.read(size)

    def __str__(self) -> str:
        """String representation"""
        if self.type in [MsgType.AudioOnlyServer, MsgType.AudioOnlyClient]:
            if self.flag in [MsgTypeFlagBits.PositiveSeq, MsgTypeFlagBits.NegativeSeq]:
                return f"MsgType: {self.type}, EventType:{self.event}, Sequence: {self.sequence}, PayloadSize: {len(self.payload)}"
            return f"MsgType: {self.type}, EventType:{self.event}, PayloadSize: {len(self.payload)}"
        elif self.type == MsgType.Error:
            return f"MsgType: {self.type}, EventType:{self.event}, ErrorCode: {self.error_code}, Payload: {self.payload.decode('utf-8', 'ignore')}"
        else:
            if self.flag in [MsgTypeFlagBits.PositiveSeq, MsgTypeFlagBits.NegativeSeq]:
                return f"MsgType: {self.type}, EventType:{self.event}, Sequence: {self.sequence}, Payload: {self.payload.decode('utf-8', 'ignore')}"
            return f"MsgType: {self.type}, EventType:{self.event}, Payload: {self.payload.decode('utf-8', 'ignore')}"

# 协议辅助函数
# 协议辅助函数
logger = get_logger(__name__)

async def receive_message(websocket: websockets.WebSocketClientProtocol) -> Message:
    """Receive message from websocket"""
    try:
        data = await websocket.recv()
        if isinstance(data, str):
            raise ValueError(f"Unexpected text message: {data}")
        elif isinstance(data, bytes):
            msg = Message.from_bytes(data)
            logger.info(f"Received: {msg}")
            return msg
        else:
            raise ValueError(f"Unexpected message type: {type(data)}")
    except Exception as e:
        logger.error(f"Failed to receive message: {e}")
        raise

async def full_client_request(
    websocket: websockets.WebSocketClientProtocol, payload: bytes
) -> None:
    """Send full client message"""
    msg = Message(type=MsgType.FullClientRequest, flag=MsgTypeFlagBits.NoSeq)
    msg.payload = payload
    logger.info(f"Sending: {msg}")
    await websocket.send(msg.marshal())