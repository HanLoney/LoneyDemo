"""
对话服务
整合对话管理、情感分析和LLM调用
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, AsyncGenerator, Tuple

from shared.models.chat import ChatMessage, ChatResponse, MessageRole
from shared.utils import get_all_config, get_logger, TimeUtils
from core.emotion import EmotionService
from .chat_manager import ChatManager
from .llm_client import llm_manager


class ChatService:
    """对话服务"""
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.config = get_all_config()
        self.logger = get_logger(__name__)
        
        # 初始化组件
        self.chat_manager = ChatManager(user_id)
        self.emotion_service = EmotionService(user_id)
        self.llm_client = llm_manager.get_default_client()
        
        # 服务配置
        self.chat_config = self.config.get('services.chat', {})
        self.enable_emotion = self.chat_config.get('enable_emotion', True)
        self.enable_time_analysis = self.chat_config.get('enable_time_analysis', True)
        self.response_style = self.chat_config.get('response_style', 'adaptive')
        
        self.logger.info(f"对话服务已初始化 - 用户: {user_id}")
    
    def chat(self, user_input: str, **kwargs) -> ChatResponse:
        """
        处理用户输入并生成回复
        
        Args:
            user_input: 用户输入
            **kwargs: 其他参数
            
        Returns:
            聊天响应
        """
        try:
            start_time = TimeUtils.now()
            
            # 1. 分析用户情感
            user_emotion = None
            if self.enable_emotion:
                user_emotion = self.emotion_service.analyze_text_emotion_sync(user_input)
                self.logger.debug(f"用户情感分析: {user_emotion}")
            
            # 2. 更新AI情感状态
            ai_emotion_change = None
            if self.enable_emotion and user_emotion:
                ai_emotion_change = self.emotion_service.update_emotion_from_input(
                    user_input, user_emotion
                )
                self.logger.debug(f"AI情感变化: {ai_emotion_change}")
            
            # 3. 添加用户消息
            user_message = self.chat_manager.add_message(
                content=user_input,
                role=MessageRole.USER,
                metadata={
                    "emotion": user_emotion,
                    "timestamp": start_time.isoformat()
                }
            )
            
            # 4. 构建系统提示
            system_prompt = self._build_system_prompt(user_emotion, ai_emotion_change)
            
            # 5. 获取对话上下文
            context = self.chat_manager.get_conversation_context()
            
            # 6. 构建LLM消息
            llm_messages = self._build_llm_messages(system_prompt, context)
            
            # 7. 调用LLM生成回复
            llm_response = self.llm_client.chat_completion(
                messages=llm_messages,
                **kwargs
            )
            
            if not llm_response:
                raise Exception("LLM调用失败")
            
            # 8. 提取回复内容
            assistant_content = self.llm_client.extract_response_content(llm_response)
            
            # 9. 应用情感表达
            if self.enable_emotion:
                assistant_content = self.emotion_service.apply_emotion_to_response(
                    assistant_content
                )
            
            # 10. 添加助手消息
            assistant_message = self.chat_manager.add_message(
                content=assistant_content,
                role=MessageRole.ASSISTANT,
                metadata={
                    "llm_response": {
                        "model": llm_response.model,
                        "usage": llm_response.usage.model_dump() if llm_response.usage else None,
                        "finish_reason": llm_response.choices[0].finish_reason if llm_response.choices else None
                    },
                    "emotion_applied": self.enable_emotion,
                    "timestamp": TimeUtils.now().isoformat()
                }
            )
            
            # 11. 构建响应
            response = ChatResponse(
                message=assistant_message,
                processing_time=TimeUtils.time_diff_seconds(TimeUtils.now(), start_time),
                token_usage=getattr(llm_response, 'usage', {}).model_dump() if hasattr(llm_response, 'usage') else {},
                emotion_state=self.emotion_service.get_current_emotion_state_sync().to_dict() if self.enable_emotion else None,
                confidence=1.0
            )
            
            self.logger.info(f"对话处理完成 - 耗时: {response.processing_time:.2f}s")
            return response
            
        except Exception as e:
            self.logger.error(f"对话处理失败: {e}")
            
            # 返回错误响应
            error_content = "抱歉，我现在遇到了一些问题，请稍后再试。"
            error_message = self.chat_manager.add_message(
                content=error_content,
                role=MessageRole.ASSISTANT,
                metadata={
                    "error": str(e),
                    "timestamp": TimeUtils.now().isoformat()
                }
            )
            
            return ChatResponse(
                message=error_message,
                processing_time=TimeUtils.time_diff_seconds(TimeUtils.now(), start_time),
                confidence=0.0
            )
    
    async def async_chat(self, user_input: str, **kwargs) -> ChatResponse:
        """
        异步处理用户输入并生成回复
        
        Args:
            user_input: 用户输入
            **kwargs: 其他参数
            
        Returns:
            聊天响应
        """
        try:
            start_time = TimeUtils.now()
            
            # 1. 分析用户情感
            user_emotion = None
            if self.enable_emotion:
                user_emotion = await self.emotion_service.analyze_text_emotion(user_input)
            
            # 2. 更新AI情感状态
            ai_emotion_change = None
            if self.enable_emotion and user_emotion:
                ai_emotion_change = self.emotion_service.update_emotion_from_input(
                    user_input, user_emotion
                )
            
            # 3. 添加用户消息
            user_message = self.chat_manager.add_message(
                content=user_input,
                role=MessageRole.USER,
                metadata={
                    "emotion": user_emotion,
                    "timestamp": start_time.isoformat()
                }
            )
            
            # 4. 构建系统提示
            system_prompt = self._build_system_prompt(user_emotion, ai_emotion_change)
            
            # 5. 获取对话上下文
            context = self.chat_manager.get_conversation_context()
            
            # 6. 构建LLM消息
            llm_messages = self._build_llm_messages(system_prompt, context)
            
            # 7. 异步调用LLM
            llm_response = await self.llm_client.async_chat_completion(
                messages=llm_messages,
                **kwargs
            )
            
            if not llm_response:
                raise Exception("异步LLM调用失败")
            
            # 8. 提取回复内容
            assistant_content = self.llm_client.extract_response_content(llm_response)
            
            # 9. 应用情感表达
            if self.enable_emotion:
                assistant_content = self.emotion_service.apply_emotion_to_response(
                    assistant_content
                )
            
            # 10. 添加助手消息
            assistant_message = self.chat_manager.add_message(
                content=assistant_content,
                role=MessageRole.ASSISTANT,
                metadata={
                    "llm_response": {
                        "model": llm_response.model,
                        "usage": llm_response.usage.model_dump() if llm_response.usage else None,
                        "finish_reason": llm_response.choices[0].finish_reason if llm_response.choices else None
                    },
                    "emotion_applied": self.enable_emotion,
                    "timestamp": TimeUtils.now().isoformat()
                }
            )
            
            # 11. 构建响应
            response = ChatResponse(
                message=assistant_message,
                processing_time=TimeUtils.time_diff_seconds(TimeUtils.now(), start_time),
                token_usage=getattr(llm_response, 'usage', {}).model_dump() if hasattr(llm_response, 'usage') else {},
                emotion_state=self.emotion_service.get_emotion_state().to_dict() if self.enable_emotion else None,
                confidence=1.0
            )
            
            self.logger.info(f"异步对话处理完成 - 耗时: {response.processing_time:.2f}s")
            return response
            
        except Exception as e:
            self.logger.error(f"异步对话处理失败: {e}")
            
            # 返回错误响应
            error_content = "抱歉，我现在遇到了一些问题，请稍后再试。"
            error_message = self.chat_manager.add_message(
                content=error_content,
                role=MessageRole.ASSISTANT,
                metadata={
                    "error": str(e),
                    "timestamp": TimeUtils.now().isoformat()
                }
            )
            
            return ChatResponse(
                message=error_message,
                processing_time=TimeUtils.time_diff_seconds(TimeUtils.now(), start_time),
                confidence=0.0
            )
    
    async def stream_chat(self, user_input: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        流式对话
        
        Args:
            user_input: 用户输入
            **kwargs: 其他参数
            
        Yields:
            响应内容片段
        """
        try:
            start_time = TimeUtils.now()
            
            # 1. 分析用户情感
            user_emotion = None
            if self.enable_emotion:
                user_emotion = await self.emotion_service.analyze_text_emotion(user_input)
            
            # 2. 更新AI情感状态
            ai_emotion_change = None
            if self.enable_emotion and user_emotion:
                ai_emotion_change = self.emotion_service.update_emotion_from_input(
                    user_input, user_emotion
                )
            
            # 3. 添加用户消息
            user_message = self.chat_manager.add_message(
                content=user_input,
                role=MessageRole.USER,
                metadata={
                    "emotion": user_emotion,
                    "timestamp": start_time.isoformat()
                }
            )
            
            # 4. 构建系统提示
            system_prompt = self._build_system_prompt(user_emotion, ai_emotion_change)
            
            # 5. 获取对话上下文
            context = self.chat_manager.get_conversation_context()
            
            # 6. 构建LLM消息
            llm_messages = self._build_llm_messages(system_prompt, context)
            
            # 7. 流式调用LLM
            stream = await self.llm_client.async_stream_chat_completion(
                messages=llm_messages,
                **kwargs
            )
            
            if not stream:
                yield "抱歉，我现在遇到了一些问题，请稍后再试。"
                return
            
            # 8. 处理流式响应
            full_content = ""
            async for chunk in stream:
                content = self.llm_client.extract_stream_content(chunk)
                if content:
                    full_content += content
                    yield content
            
            # 9. 应用情感表达（对完整内容）
            if self.enable_emotion and full_content:
                enhanced_content = self.emotion_service.apply_emotion_to_response(
                    full_content
                )
                # 如果有增强，发送增强部分
                if enhanced_content != full_content:
                    additional_content = enhanced_content[len(full_content):]
                    if additional_content:
                        yield additional_content
                        full_content = enhanced_content
            
            # 10. 添加助手消息
            self.chat_manager.add_message(
                content=full_content,
                role=MessageRole.ASSISTANT,
                metadata={
                    "stream_response": True,
                    "emotion_applied": self.enable_emotion,
                    "timestamp": TimeUtils.now().isoformat()
                }
            )
            
            self.logger.info(f"流式对话处理完成 - 耗时: {TimeUtils.time_diff_seconds(TimeUtils.now(), start_time):.2f}s")
            
        except Exception as e:
            self.logger.error(f"流式对话处理失败: {e}")
            yield f"抱歉，我现在遇到了一些问题：{str(e)}"
    
    def get_session_info(self) -> Dict[str, Any]:
        """获取会话信息"""
        try:
            session_summary = self.chat_manager.get_session_summary()
            emotion_state = None
            
            if self.enable_emotion:
                emotion_state = self.emotion_service.get_emotion_state()
            
            return {
                "session": session_summary,
                "emotion_state": emotion_state,
                "service_config": {
                    "emotion_enabled": self.enable_emotion,
                    "time_analysis_enabled": self.enable_time_analysis,
                    "response_style": self.response_style
                },
                "llm_stats": self.llm_client.get_usage_stats()
            }
            
        except Exception as e:
            self.logger.error(f"获取会话信息失败: {e}")
            return {"error": str(e)}
    
    def reset_session(self) -> bool:
        """重置会话"""
        try:
            # 清空对话会话
            self.chat_manager.clear_session()
            
            # 重置情感状态
            if self.enable_emotion:
                self.emotion_service.reset_emotion()
            
            self.logger.info("会话已重置")
            return True
            
        except Exception as e:
            self.logger.error(f"重置会话失败: {e}")
            return False
    
    def export_session_data(self) -> Dict[str, Any]:
        """导出会话数据"""
        try:
            chat_data = self.chat_manager.export_session()
            emotion_data = None
            
            if self.enable_emotion:
                emotion_data = self.emotion_service.export_emotion_data()
            
            return {
                "export_time": TimeUtils.now().isoformat(),
                "user_id": self.user_id,
                "chat_data": chat_data,
                "emotion_data": emotion_data,
                "service_config": {
                    "emotion_enabled": self.enable_emotion,
                    "time_analysis_enabled": self.enable_time_analysis,
                    "response_style": self.response_style
                }
            }
            
        except Exception as e:
            self.logger.error(f"导出会话数据失败: {e}")
            return {"error": str(e)}
    
    def import_session_data(self, data: Dict[str, Any]) -> bool:
        """导入会话数据"""
        try:
            # 导入对话数据
            if 'chat_data' in data:
                self.chat_manager.import_session(data['chat_data'])
            
            # 导入情感数据
            if self.enable_emotion and 'emotion_data' in data:
                self.emotion_service.import_emotion_data(data['emotion_data'])
            
            self.logger.info("会话数据导入成功")
            return True
            
        except Exception as e:
            self.logger.error(f"导入会话数据失败: {e}")
            return False
    
    def _build_system_prompt(self, 
                           user_emotion: Optional[Any] = None,
                           ai_emotion_change: Optional[Dict[str, Any]] = None) -> str:
        """构建系统提示"""
        try:
            # 基础系统提示
            base_prompt = self.chat_manager.system_persona
            
            # 添加时间信息
            if self.enable_time_analysis:
                current_time = TimeUtils.now().strftime("%Y年%m月%d日 %H:%M:%S")
                base_prompt += f"\n\n当前时间: {current_time}"
            
            # 添加情感信息
            if self.enable_emotion:
                emotion_prompt = self._build_emotion_prompt(user_emotion, ai_emotion_change)
                if emotion_prompt:
                    base_prompt += f"\n\n{emotion_prompt}"
            
            return base_prompt
            
        except Exception as e:
            self.logger.error(f"构建系统提示失败: {e}")
            return self.chat_manager.system_persona
    
    def _build_emotion_prompt(self, 
                            user_emotion: Optional[Any] = None,
                            ai_emotion_change: Optional[Dict[str, Any]] = None) -> str:
        """构建情感提示"""
        try:
            emotion_parts = []
            
            # 用户情感信息
            if user_emotion:
                emotion_parts.append(f"用户情感分析:")
                # 处理EmotionAnalysisResult对象
                if hasattr(user_emotion, 'primary_emotion'):
                    emotion_parts.append(f"- 情感类型: {user_emotion.primary_emotion.value}")
                    emotion_parts.append(f"- 置信度: {user_emotion.confidence:.2f}")
                    emotion_parts.append(f"- 情感分数: {user_emotion.sentiment_score:.2f}")
                    # 计算主要情感的强度
                    primary_intensity = user_emotion.detected_emotions.get(user_emotion.primary_emotion, 0.0)
                    emotion_parts.append(f"- 强度: {primary_intensity:.2f}")
                # 兼容字典格式
                elif isinstance(user_emotion, dict):
                    emotion_parts.append(f"- 情感类型: {user_emotion.get('emotion', '未知')}")
                    emotion_parts.append(f"- 强度: {user_emotion.get('intensity', 0):.2f}")
                    emotion_parts.append(f"- 置信度: {user_emotion.get('confidence', 0):.2f}")
                    if user_emotion.get('keywords'):
                        emotion_parts.append(f"- 关键词: {', '.join(user_emotion['keywords'])}")
            
            # AI情感状态
            if self.emotion_service:
                ai_emotion = self.emotion_service.get_current_emotion_state_sync()
                if ai_emotion:
                    emotion_parts.append(f"\n你的当前情感状态:")
                    emotion_parts.append(f"- 主导情感: {ai_emotion.primary_emotion.value}")
                    emotion_parts.append(f"- 强度: {ai_emotion.intensity:.2f}")
                    emotion_parts.append(f"- 稳定性: {ai_emotion.stability:.2f}")
            
            # AI情感变化
            if ai_emotion_change:
                emotion_parts.append(f"\n情感变化:")
                # 处理EmotionTransition对象
                if hasattr(ai_emotion_change, 'from_emotion') and hasattr(ai_emotion_change, 'to_emotion'):
                    # 计算情感变化
                    from_emotions = ai_emotion_change.from_emotion.emotions
                    to_emotions = ai_emotion_change.to_emotion.emotions
                    
                    for emotion_type in from_emotions:
                        if emotion_type in to_emotions:
                            change = to_emotions[emotion_type] - from_emotions[emotion_type]
                            if abs(change) > 0.1:  # 只显示显著变化
                                emotion_parts.append(f"- {emotion_type.value}: {change:+.2f}")
                # 兼容字典格式
                elif isinstance(ai_emotion_change, dict):
                    if 'emotion_changes' in ai_emotion_change:
                        for emotion, change in ai_emotion_change['emotion_changes'].items():
                            if abs(change) > 0.1:  # 只显示显著变化
                                emotion_parts.append(f"- {emotion}: {change:+.2f}")
                    else:
                        # 处理其他字典格式
                        for key, value in ai_emotion_change.items():
                            if isinstance(value, (int, float)) and abs(value) > 0.1:
                                emotion_parts.append(f"- {key}: {value:+.2f}")
            
            if emotion_parts:
                emotion_parts.append(f"\n请根据以上情感信息调整你的回复风格和语调。")
                return "\n".join(emotion_parts)
            
            return ""
            
        except Exception as e:
            self.logger.error(f"构建情感提示失败: {e}")
            return ""
    
    def _build_llm_messages(self, 
                          system_prompt: str, 
                          context: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """构建LLM消息"""
        try:
            messages = []
            
            # 添加系统消息
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # 添加对话上下文
            messages.extend(context)
            
            return messages
            
        except Exception as e:
            self.logger.error(f"构建LLM消息失败: {e}")
            return context