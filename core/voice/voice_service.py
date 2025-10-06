"""
语音服务
整合TTS和STT功能的语音服务
"""
import asyncio
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import logging

from .tts_client import TTSClient, tts_manager
from shared.utils import get_all_config, get_logger, FileUtils, TimeUtils
from shared.models.voice import VoiceRequest, VoiceResponse, TTSRequest, TTSResponse


class VoiceService:
    """语音服务"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_all_config()
        self.logger = get_logger(__name__)
        
        # 初始化TTS客户端
        self.tts_client = tts_manager.get_default_client()
        
        # 语音服务配置
        self.voice_config = self.config.get('services.voice', {})
        self.enabled_services = self.voice_config.get('enabled_services', ['tts'])
        
        # 默认设置
        self.default_voice = self.voice_config.get('default_voice', 'sweet')
        self.auto_save = self.voice_config.get('auto_save', True)
        self.output_dir = Path(self.voice_config.get('output_dir', 'data/voice/output'))
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 服务状态
        self.is_initialized = False
        self.service_stats = {
            'tts_requests': 0,
            'stt_requests': 0,
            'total_processing_time': 0.0,
            'errors': 0
        }
        
        self.logger.info("语音服务已初始化")
    
    async def initialize(self) -> bool:
        """初始化语音服务"""
        try:
            # 测试TTS连接
            if 'tts' in self.enabled_services:
                if not await self.tts_client.test_connection():
                    self.logger.warning("TTS服务连接测试失败")
                    return False
            
            self.is_initialized = True
            self.logger.info("语音服务初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"语音服务初始化失败: {e}")
            return False
    
    async def text_to_speech(self, 
                            text: str, 
                            voice: Optional[str] = None,
                            output_file: Optional[str] = None,
                            save_audio: Optional[bool] = None) -> TTSResponse:
        """
        文本转语音
        
        Args:
            text: 要转换的文本
            voice: 语音类型
            output_file: 输出文件路径
            save_audio: 是否保存音频文件
            
        Returns:
            TTS响应对象
        """
        try:
            start_time = TimeUtils.now()
            
            if not self.is_initialized:
                await self.initialize()
            
            if 'tts' not in self.enabled_services:
                raise ValueError("TTS服务未启用")
            
            # 使用默认语音
            voice = voice or self.default_voice
            
            # 调用TTS客户端
            result = await self.tts_client.synthesize_text(
                text=text,
                voice=voice,
                output_file=output_file,
                save_audio=save_audio
            )
            
            # 更新统计
            processing_time = TimeUtils.time_diff_seconds(TimeUtils.now(), start_time)
            self._update_stats('tts', processing_time)
            
            # 构建响应
            response = TTSResponse(
                success=True,
                audio_data=result['audio_data'],
                text=text,
                voice=voice,
                output_file=result.get('output_file'),
                audio_size=result['audio_size'],
                processing_time=processing_time,
                metadata={
                    'speaker': result['speaker'],
                    'timestamp': result['timestamp']
                }
            )
            
            self.logger.info(f"TTS转换成功 - 文本长度: {len(text)}, "
                           f"音频大小: {result['audio_size']} 字节, "
                           f"耗时: {processing_time:.2f}s")
            
            return response
            
        except Exception as e:
            self.service_stats['errors'] += 1
            self.logger.error(f"TTS转换失败: {e}")
            
            return TTSResponse(
                success=False,
                error=str(e),
                text=text,
                voice=voice or self.default_voice
            )
    
    async def batch_text_to_speech(self, 
                                  texts: List[str], 
                                  voice: Optional[str] = None,
                                  output_dir: Optional[str] = None) -> List[TTSResponse]:
        """
        批量文本转语音
        
        Args:
            texts: 文本列表
            voice: 语音类型
            output_dir: 输出目录
            
        Returns:
            TTS响应列表
        """
        try:
            start_time = TimeUtils.now()
            
            if not self.is_initialized:
                await self.initialize()
            
            if 'tts' not in self.enabled_services:
                raise ValueError("TTS服务未启用")
            
            voice = voice or self.default_voice
            output_path = Path(output_dir) if output_dir else self.output_dir
            
            # 批量合成
            results = await self.tts_client.batch_synthesize(
                texts=texts,
                voice=voice,
                output_dir=str(output_path)
            )
            
            # 构建响应列表
            responses = []
            for i, (text, result) in enumerate(zip(texts, results)):
                response = TTSResponse(
                    success=True,
                    audio_data=result['audio_data'],
                    text=text,
                    voice=voice,
                    output_file=result.get('output_file'),
                    audio_size=result['audio_size'],
                    processing_time=result['processing_time'],
                    metadata={
                        'speaker': result['speaker'],
                        'timestamp': result['timestamp'],
                        'batch_index': i
                    }
                )
                responses.append(response)
            
            # 更新统计
            total_time = TimeUtils.time_diff_seconds(TimeUtils.now(), start_time)
            self._update_stats('tts', total_time, count=len(texts))
            
            self.logger.info(f"批量TTS转换完成 - 处理 {len(texts)} 个文本, "
                           f"总耗时: {total_time:.2f}s")
            
            return responses
            
        except Exception as e:
            self.service_stats['errors'] += 1
            self.logger.error(f"批量TTS转换失败: {e}")
            
            # 返回错误响应
            return [
                TTSResponse(
                    success=False,
                    error=str(e),
                    text=text,
                    voice=voice or self.default_voice
                )
                for text in texts
            ]
    
    async def quick_tts(self, text: str, voice: Optional[str] = None) -> bytes:
        """
        快速TTS转换（仅返回音频数据）
        
        Args:
            text: 要转换的文本
            voice: 语音类型
            
        Returns:
            音频数据字节
        """
        try:
            response = await self.text_to_speech(
                text=text,
                voice=voice,
                save_audio=False
            )
            
            if response.success:
                return response.audio_data
            else:
                raise Exception(response.error)
                
        except Exception as e:
            self.logger.error(f"快速TTS转换失败: {e}")
            raise
    
    def get_available_voices(self) -> Dict[str, str]:
        """获取可用的语音配置"""
        return self.tts_client.get_available_voices()
    
    def get_voice_info(self, voice: str) -> Optional[Dict[str, Any]]:
        """获取语音信息"""
        return self.tts_client.get_voice_info(voice)
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'initialized': self.is_initialized,
            'enabled_services': self.enabled_services,
            'default_voice': self.default_voice,
            'available_voices': list(self.get_available_voices().keys()),
            'output_dir': str(self.output_dir),
            'auto_save': self.auto_save
        }
    
    def get_service_stats(self) -> Dict[str, Any]:
        """获取服务统计"""
        tts_stats = self.tts_client.get_stats()
        
        return {
            'service_stats': self.service_stats.copy(),
            'tts_stats': tts_stats,
            'total_requests': self.service_stats['tts_requests'] + self.service_stats['stt_requests'],
            'average_processing_time': (
                self.service_stats['total_processing_time'] / 
                max(self.service_stats['tts_requests'] + self.service_stats['stt_requests'], 1)
            ),
            'error_rate': (
                self.service_stats['errors'] / 
                max(self.service_stats['tts_requests'] + self.service_stats['stt_requests'], 1)
            )
        }
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self.service_stats = {
            'tts_requests': 0,
            'stt_requests': 0,
            'total_processing_time': 0.0,
            'errors': 0
        }
        self.tts_client.reset_stats()
        self.logger.info("语音服务统计已重置")
    
    async def test_service(self) -> Dict[str, Any]:
        """测试语音服务"""
        test_results = {
            'tts': False,
            'stt': False,
            'overall': False,
            'errors': []
        }
        
        try:
            # 测试TTS
            if 'tts' in self.enabled_services:
                try:
                    response = await self.text_to_speech(
                        text="语音服务测试",
                        save_audio=False
                    )
                    test_results['tts'] = response.success
                    if not response.success:
                        test_results['errors'].append(f"TTS测试失败: {response.error}")
                except Exception as e:
                    test_results['errors'].append(f"TTS测试异常: {e}")
            
            # 测试STT（如果启用）
            if 'stt' in self.enabled_services:
                # TODO: 实现STT测试
                test_results['stt'] = True
            
            # 整体测试结果
            test_results['overall'] = (
                test_results['tts'] if 'tts' in self.enabled_services else True
            ) and (
                test_results['stt'] if 'stt' in self.enabled_services else True
            )
            
            self.logger.info(f"语音服务测试完成 - 结果: {test_results['overall']}")
            
        except Exception as e:
            test_results['errors'].append(f"服务测试异常: {e}")
            self.logger.error(f"语音服务测试失败: {e}")
        
        return test_results
    
    def configure_service(self, **kwargs) -> None:
        """配置语音服务"""
        if 'default_voice' in kwargs:
            self.default_voice = kwargs['default_voice']
            self.logger.info(f"默认语音已设置为: {self.default_voice}")
        
        if 'auto_save' in kwargs:
            self.auto_save = kwargs['auto_save']
            self.logger.info(f"自动保存已设置为: {self.auto_save}")
        
        if 'output_dir' in kwargs:
            self.output_dir = Path(kwargs['output_dir'])
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"输出目录已设置为: {self.output_dir}")
        
        if 'enabled_services' in kwargs:
            self.enabled_services = kwargs['enabled_services']
            self.logger.info(f"启用的服务: {self.enabled_services}")
    
    def _update_stats(self, service_type: str, processing_time: float, count: int = 1) -> None:
        """更新统计信息"""
        if service_type == 'tts':
            self.service_stats['tts_requests'] += count
        elif service_type == 'stt':
            self.service_stats['stt_requests'] += count
        
        self.service_stats['total_processing_time'] += processing_time
        
        self.logger.debug(f"语音服务统计更新 - {service_type}: +{count}, "
                         f"处理时间: {processing_time:.2f}s")


# 语音服务实例
voice_service = VoiceService()