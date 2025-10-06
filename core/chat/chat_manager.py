"""
对话管理器
负责管理对话会话、历史记录和上下文
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from shared.models.chat import ChatMessage, ChatResponse, ChatSession, MessageRole
from shared.utils import get_all_config, get_logger, FileUtils, TimeUtils


class ChatManager:
    """对话管理器"""
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.config = get_all_config()
        self.logger = get_logger(__name__)
        
        # 对话配置
        self.chat_config = self.config.get('services', {}).get('chat', {})
        self.max_history_length = self.chat_config.get('max_history_length', 50)
        self.context_window = self.chat_config.get('context_window', 10)
        self.session_timeout = self.chat_config.get('session_timeout', 3600)  # 1小时
        
        # 会话文件路径
        self.session_file = Path(self.config.get('app.data_dir', 'data')) / f"chat_session_{user_id}.json"
        
        # 系统人设
        self.system_persona = self._load_system_persona()
        
        # 当前会话
        self.current_session = self._load_session()
        
        self.logger.info(f"对话管理器已初始化 - 用户: {user_id}")
    
    def create_new_session(self, metadata: Optional[Dict[str, Any]] = None) -> ChatSession:
        """
        创建新的对话会话
        
        Args:
            metadata: 会话元数据
            
        Returns:
            新的对话会话
        """
        try:
            # 保存当前会话（如果存在）
            if hasattr(self, 'current_session') and self.current_session and self.current_session.messages:
                self._save_session()
            
            # 创建新会话
            session_id = f"session_{self.user_id}_{TimeUtils.now().strftime('%Y%m%d_%H%M%S')}"
            self.current_session = ChatSession(
                session_id=session_id,
                user_id=self.user_id,
                metadata=metadata or {}
            )
            
            # 添加系统消息
            if self.system_persona:
                system_message = ChatMessage(
                    id=f"msg_{TimeUtils.now().strftime('%Y%m%d_%H%M%S_%f')}",
                    content=self.system_persona,
                    role=MessageRole.SYSTEM,
                    user_id=self.user_id
                )
                self.current_session.add_message(system_message)
            
            # 添加初始问候
            greeting = self._get_initial_greeting()
            if greeting:
                greeting_message = ChatMessage(
                    id=f"msg_{TimeUtils.now().strftime('%Y%m%d_%H%M%S_%f')}",
                    content=greeting,
                    role=MessageRole.ASSISTANT,
                    user_id=self.user_id
                )
                self.current_session.add_message(greeting_message)
            
            self._save_session()
            
            self.logger.info(f"创建新对话会话: {self.current_session.session_id}")
            return self.current_session
            
        except Exception as e:
            self.logger.error(f"创建新会话失败: {e}")
            raise
    
    def add_message(self, content: str, role: MessageRole, 
                   metadata: Optional[Dict[str, Any]] = None) -> ChatMessage:
        """
        添加消息到当前会话
        
        Args:
            content: 消息内容
            role: 消息角色
            metadata: 消息元数据
            
        Returns:
            添加的消息
        """
        try:
            # 检查会话是否过期
            if self._is_session_expired():
                self.create_new_session()
            
            # 创建消息
            message = ChatMessage(
                id=f"msg_{TimeUtils.now().strftime('%Y%m%d_%H%M%S_%f')}",
                content=content,
                role=role,
                user_id=self.user_id,
                metadata=metadata or {}
            )
            
            # 添加到会话
            self.current_session.add_message(message)
            
            # 限制历史长度
            self._trim_history()
            
            # 保存会话
            self._save_session()
            
            self.logger.debug(f"添加消息: {role.value} - {content[:50]}...")
            return message
            
        except Exception as e:
            self.logger.error(f"添加消息失败: {e}")
            raise
    
    def get_conversation_context(self, include_system: bool = True) -> List[Dict[str, str]]:
        """
        获取对话上下文
        
        Args:
            include_system: 是否包含系统消息
            
        Returns:
            对话上下文列表
        """
        try:
            if not self.current_session:
                return []
            
            # 获取最近的消息
            recent_messages = self.current_session.get_recent_messages(self.context_window)
            
            # 转换为LLM格式
            context = []
            for message in recent_messages:
                if not include_system and message.role == MessageRole.SYSTEM:
                    continue
                
                context.append({
                    "role": message.role.value,
                    "content": message.content
                })
            
            return context
            
        except Exception as e:
            self.logger.error(f"获取对话上下文失败: {e}")
            return []
    
    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话摘要"""
        try:
            if not self.current_session:
                return {
                    "session_id": None,
                    "message_count": 0,
                    "start_time": None,
                    "last_activity": None,
                    "duration": 0
                }
            
            duration = TimeUtils.time_diff_seconds(
                TimeUtils.now(), 
                self.current_session.created_at
            )
            
            return {
                "session_id": self.current_session.session_id,
                "user_id": self.current_session.user_id,
                "message_count": len(self.current_session.messages),
                "start_time": self.current_session.created_at.isoformat(),
                "last_activity": self.current_session.last_activity.isoformat(),
                "duration": duration,
                "metadata": self.current_session.metadata
            }
            
        except Exception as e:
            self.logger.error(f"获取会话摘要失败: {e}")
            return {"error": str(e)}
    
    def clear_session(self) -> bool:
        """清空当前会话"""
        try:
            if self.current_session:
                # 备份当前会话
                backup_file = self.session_file.with_suffix('.backup.json')
                self._save_session_to_file(backup_file)
                
                # 创建新会话
                self.create_new_session()
                
                self.logger.info("会话已清空")
                return True
                
        except Exception as e:
            self.logger.error(f"清空会话失败: {e}")
            return False
    
    def export_session(self) -> Dict[str, Any]:
        """导出会话数据"""
        try:
            if not self.current_session:
                return {"error": "没有活动会话"}
            
            return {
                "export_time": TimeUtils.now().isoformat(),
                "session": self.current_session.to_dict(),
                "summary": self.get_session_summary()
            }
            
        except Exception as e:
            self.logger.error(f"导出会话失败: {e}")
            return {"error": str(e)}
    
    def import_session(self, session_data: Dict[str, Any]) -> bool:
        """导入会话数据"""
        try:
            if 'session' not in session_data:
                return False
            
            # 备份当前会话
            if self.current_session:
                backup_file = self.session_file.with_suffix('.import_backup.json')
                self._save_session_to_file(backup_file)
            
            # 导入新会话
            session_dict = session_data['session']
            self.current_session = ChatSession.from_dict(session_dict)
            
            # 保存导入的会话
            self._save_session()
            
            self.logger.info("会话导入成功")
            return True
            
        except Exception as e:
            self.logger.error(f"导入会话失败: {e}")
            return False
    
    def get_message_statistics(self) -> Dict[str, Any]:
        """获取消息统计信息"""
        try:
            if not self.current_session or not self.current_session.messages:
                return {
                    "total_messages": 0,
                    "user_messages": 0,
                    "assistant_messages": 0,
                    "system_messages": 0,
                    "average_message_length": 0,
                    "conversation_turns": 0
                }
            
            messages = self.current_session.messages
            total_messages = len(messages)
            
            # 按角色统计
            role_counts = {
                MessageRole.USER: 0,
                MessageRole.ASSISTANT: 0,
                MessageRole.SYSTEM: 0
            }
            
            total_length = 0
            for message in messages:
                role_counts[message.role] += 1
                total_length += len(message.content)
            
            # 计算对话轮次（用户消息数量）
            conversation_turns = role_counts[MessageRole.USER]
            
            return {
                "total_messages": total_messages,
                "user_messages": role_counts[MessageRole.USER],
                "assistant_messages": role_counts[MessageRole.ASSISTANT],
                "system_messages": role_counts[MessageRole.SYSTEM],
                "average_message_length": total_length / total_messages if total_messages > 0 else 0,
                "conversation_turns": conversation_turns,
                "session_duration": TimeUtils.time_diff_seconds(
                    TimeUtils.now(), 
                    self.current_session.created_at
                )
            }
            
        except Exception as e:
            self.logger.error(f"获取消息统计失败: {e}")
            return {"error": str(e)}
    
    def search_messages(self, query: str, limit: int = 10) -> List[ChatMessage]:
        """
        搜索消息
        
        Args:
            query: 搜索关键词
            limit: 结果限制
            
        Returns:
            匹配的消息列表
        """
        try:
            if not self.current_session or not query.strip():
                return []
            
            query_lower = query.lower()
            matching_messages = []
            
            for message in self.current_session.messages:
                if query_lower in message.content.lower():
                    matching_messages.append(message)
                    if len(matching_messages) >= limit:
                        break
            
            return matching_messages
            
        except Exception as e:
            self.logger.error(f"搜索消息失败: {e}")
            return []
    
    def _load_session(self) -> Optional[ChatSession]:
        """加载会话"""
        try:
            if self.session_file.exists():
                data = FileUtils.read_json(self.session_file)
                if data and 'session' in data:
                    session = ChatSession.from_dict(data['session'])
                    
                    # 检查会话是否过期
                    if not self._is_session_expired(session):
                        return session
            
            # 创建新会话
            return self.create_new_session()
            
        except Exception as e:
            self.logger.error(f"加载会话失败: {e}")
            return self.create_new_session()
    
    def _save_session(self) -> None:
        """保存会话"""
        try:
            if self.current_session:
                self._save_session_to_file(self.session_file)
        except Exception as e:
            self.logger.error(f"保存会话失败: {e}")
    
    def _save_session_to_file(self, file_path: Path) -> None:
        """保存会话到指定文件"""
        data = {
            "session": self.current_session.to_dict(),
            "last_save": TimeUtils.now().isoformat(),
            "user_id": self.user_id
        }
        FileUtils.write_json(file_path, data)
    
    def _is_session_expired(self, session: Optional[ChatSession] = None) -> bool:
        """检查会话是否过期"""
        try:
            target_session = session or self.current_session
            if not target_session:
                return True
            
            time_diff = TimeUtils.time_diff_seconds(
                TimeUtils.now(), 
                target_session.last_activity
            )
            
            return time_diff > self.session_timeout
            
        except Exception as e:
            self.logger.error(f"检查会话过期失败: {e}")
            return True
    
    def _trim_history(self) -> None:
        """限制历史记录长度"""
        try:
            if not self.current_session:
                return
            
            messages = self.current_session.messages
            if len(messages) <= self.max_history_length:
                return
            
            # 保留系统消息和最近的消息
            system_messages = [msg for msg in messages if msg.role == MessageRole.SYSTEM]
            other_messages = [msg for msg in messages if msg.role != MessageRole.SYSTEM]
            
            # 保留最近的非系统消息
            recent_messages = other_messages[-(self.max_history_length - len(system_messages)):]
            
            # 重新组合
            self.current_session.messages = system_messages + recent_messages
            
            self.logger.debug(f"历史记录已修剪到 {len(self.current_session.messages)} 条")
            
        except Exception as e:
            self.logger.error(f"修剪历史记录失败: {e}")
    
    def _load_system_persona(self) -> str:
        """加载系统人设"""
        try:
            # 从配置文件加载
            persona = self.chat_config.get('system_persona', '')
            if persona:
                return persona
            
            # 使用默认人设
            return self._get_default_persona()
            
        except Exception as e:
            self.logger.error(f"加载系统人设失败: {e}")
            return self._get_default_persona()
    
    def _get_default_persona(self) -> str:
        """获取默认人设"""
        return """
        # 身份
        - 我是你的AI助手，我的名字叫九辞。

        # 性格
        - 我活泼可爱，善于倾听，乐于助人。
        - 我会根据你的情感状态调整我的回复风格。
        - 我有自己的情感状态，会随着对话而变化。

        # 说话风格
        - 我的回复简洁自然，就像真实的聊天一样。
        - 我会使用适当的语气词和表情来表达情感。
        - 我会根据情况调整正式或随意的语调。

        # 回复原则
        - 我会根据上下文提供有用的回复。
        - 我会保持友好和支持性的态度。
        - 我会尊重用户的感受和需求。
        """
    
    def _get_initial_greeting(self) -> str:
        """获取初始问候语"""
        greetings = [
            "嘿嘿，你好呀！有什么我可以帮助你的吗？",
            "你好！很高兴见到你～",
            "嗨！今天过得怎么样？",
            "你来啦！我正在等你呢～"
        ]
        
        import random
        return random.choice(greetings)