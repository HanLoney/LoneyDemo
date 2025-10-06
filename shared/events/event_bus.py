"""
事件总线
提供事件发布和订阅功能
"""
from typing import Dict, List, Callable, Type, Any
from collections import defaultdict
import asyncio
import threading
from .base_event import BaseEvent
from ..utils.logger import get_logger

logger = get_logger(__name__)


class EventBus:
    """事件总线"""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._async_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.RLock()
    
    def subscribe(self, event_type: Type[BaseEvent], handler: Callable[[BaseEvent], None]):
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        event_name = event_type.__name__
        with self._lock:
            self._handlers[event_name].append(handler)
        logger.debug(f"订阅事件: {event_name}, 处理器: {handler.__name__}")
    
    def subscribe_async(self, event_type: Type[BaseEvent], handler: Callable[[BaseEvent], Any]):
        """
        订阅异步事件
        
        Args:
            event_type: 事件类型
            handler: 异步事件处理器
        """
        event_name = event_type.__name__
        with self._lock:
            self._async_handlers[event_name].append(handler)
        logger.debug(f"订阅异步事件: {event_name}, 处理器: {handler.__name__}")
    
    def unsubscribe(self, event_type: Type[BaseEvent], handler: Callable):
        """
        取消订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        event_name = event_type.__name__
        with self._lock:
            if handler in self._handlers[event_name]:
                self._handlers[event_name].remove(handler)
            if handler in self._async_handlers[event_name]:
                self._async_handlers[event_name].remove(handler)
        logger.debug(f"取消订阅事件: {event_name}, 处理器: {handler.__name__}")
    
    def publish(self, event: BaseEvent):
        """
        发布事件
        
        Args:
            event: 事件实例
        """
        event_name = event.event_type
        logger.debug(f"发布事件: {event}")
        
        # 同步处理器
        with self._lock:
            handlers = self._handlers[event_name].copy()
        
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"事件处理器执行失败: {handler.__name__}, 错误: {e}")
        
        # 异步处理器
        with self._lock:
            async_handlers = self._async_handlers[event_name].copy()
        
        if async_handlers:
            # 在新线程中运行异步处理器
            threading.Thread(
                target=self._run_async_handlers,
                args=(async_handlers, event),
                daemon=True
            ).start()
    
    def _run_async_handlers(self, handlers: List[Callable], event: BaseEvent):
        """运行异步处理器"""
        async def run_handlers():
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    logger.error(f"异步事件处理器执行失败: {handler.__name__}, 错误: {e}")
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_handlers())
        except Exception as e:
            logger.error(f"异步事件处理失败: {e}")
        finally:
            loop.close()
    
    def clear(self):
        """清空所有订阅"""
        with self._lock:
            self._handlers.clear()
            self._async_handlers.clear()
        logger.debug("清空所有事件订阅")
    
    def get_subscribers_count(self, event_type: Type[BaseEvent]) -> int:
        """
        获取事件订阅者数量
        
        Args:
            event_type: 事件类型
            
        Returns:
            订阅者数量
        """
        event_name = event_type.__name__
        with self._lock:
            return len(self._handlers[event_name]) + len(self._async_handlers[event_name])


# 全局事件总线
event_bus = EventBus()


def subscribe(event_type: Type[BaseEvent], handler: Callable[[BaseEvent], None]):
    """订阅事件的便捷函数"""
    event_bus.subscribe(event_type, handler)


def subscribe_async(event_type: Type[BaseEvent], handler: Callable[[BaseEvent], Any]):
    """订阅异步事件的便捷函数"""
    event_bus.subscribe_async(event_type, handler)


def publish(event: BaseEvent):
    """发布事件的便捷函数"""
    event_bus.publish(event)


def unsubscribe(event_type: Type[BaseEvent], handler: Callable):
    """取消订阅事件的便捷函数"""
    event_bus.unsubscribe(event_type, handler)