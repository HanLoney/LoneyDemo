"""
事件系统模块
"""
from .event_bus import EventBus, event_bus
from .base_event import BaseEvent

__all__ = ['EventBus', 'event_bus', 'BaseEvent']