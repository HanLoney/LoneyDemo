"""
依赖注入容器
提供服务注册和解析功能
"""
from typing import Any, Dict, Type, TypeVar, Callable, Optional
from abc import ABC, abstractmethod
import inspect

T = TypeVar('T')


class ServiceContainer:
    """服务容器"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._interfaces: Dict[Type, str] = {}
    
    def register_singleton(self, service_type: Type[T], instance: T, name: Optional[str] = None):
        """
        注册单例服务
        
        Args:
            service_type: 服务类型
            instance: 服务实例
            name: 服务名称，默认为类名
        """
        service_name = name or service_type.__name__
        self._singletons[service_name] = instance
        self._interfaces[service_type] = service_name
    
    def register_transient(self, service_type: Type[T], factory: Callable[[], T], name: Optional[str] = None):
        """
        注册瞬态服务（每次获取都创建新实例）
        
        Args:
            service_type: 服务类型
            factory: 工厂函数
            name: 服务名称，默认为类名
        """
        service_name = name or service_type.__name__
        self._factories[service_name] = factory
        self._interfaces[service_type] = service_name
    
    def register_scoped(self, service_type: Type[T], factory: Callable[[], T], name: Optional[str] = None):
        """
        注册作用域服务（在同一作用域内为单例）
        
        Args:
            service_type: 服务类型
            factory: 工厂函数
            name: 服务名称，默认为类名
        """
        # 简化实现，暂时按单例处理
        service_name = name or service_type.__name__
        if service_name not in self._singletons:
            self._singletons[service_name] = factory()
        self._interfaces[service_type] = service_name
    
    def get(self, service_type: Type[T], name: Optional[str] = None) -> T:
        """
        获取服务实例
        
        Args:
            service_type: 服务类型
            name: 服务名称
            
        Returns:
            服务实例
            
        Raises:
            ValueError: 服务未注册
        """
        service_name = name or self._interfaces.get(service_type) or service_type.__name__
        
        # 检查单例
        if service_name in self._singletons:
            return self._singletons[service_name]
        
        # 检查工厂
        if service_name in self._factories:
            return self._factories[service_name]()
        
        # 尝试自动解析
        if hasattr(service_type, '__init__'):
            try:
                return self._auto_resolve(service_type)
            except Exception:
                pass
        
        raise ValueError(f"服务未注册: {service_name}")
    
    def _auto_resolve(self, service_type: Type[T]) -> T:
        """
        自动解析服务依赖
        
        Args:
            service_type: 服务类型
            
        Returns:
            服务实例
        """
        # 获取构造函数签名
        sig = inspect.signature(service_type.__init__)
        args = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            if param.annotation != inspect.Parameter.empty:
                # 尝试解析依赖
                try:
                    args[param_name] = self.get(param.annotation)
                except ValueError:
                    if param.default != inspect.Parameter.empty:
                        args[param_name] = param.default
                    else:
                        raise
        
        return service_type(**args)
    
    def has(self, service_type: Type, name: Optional[str] = None) -> bool:
        """
        检查服务是否已注册
        
        Args:
            service_type: 服务类型
            name: 服务名称
            
        Returns:
            是否已注册
        """
        service_name = name or self._interfaces.get(service_type) or service_type.__name__
        return service_name in self._singletons or service_name in self._factories
    
    def clear(self):
        """清空容器"""
        self._services.clear()
        self._singletons.clear()
        self._factories.clear()
        self._interfaces.clear()


# 全局服务容器
container = ServiceContainer()


def get_service(service_type: Type[T], name: Optional[str] = None) -> T:
    """
    获取服务的便捷函数
    
    Args:
        service_type: 服务类型
        name: 服务名称
        
    Returns:
        服务实例
    """
    return container.get(service_type, name)


def register_singleton(service_type: Type[T], instance: T, name: Optional[str] = None):
    """注册单例服务的便捷函数"""
    container.register_singleton(service_type, instance, name)


def register_transient(service_type: Type[T], factory: Callable[[], T], name: Optional[str] = None):
    """注册瞬态服务的便捷函数"""
    container.register_transient(service_type, factory, name)


def register_scoped(service_type: Type[T], factory: Callable[[], T], name: Optional[str] = None):
    """注册作用域服务的便捷函数"""
    container.register_scoped(service_type, factory, name)