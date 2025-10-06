"""
缓存工具
"""
import time
import threading
from typing import Any, Dict, Optional, Callable, Union
from functools import wraps
import pickle
import hashlib


class CacheItem:
    """缓存项"""
    
    def __init__(self, value: Any, ttl: Optional[float] = None):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def get_remaining_ttl(self) -> Optional[float]:
        """获取剩余TTL"""
        if self.ttl is None:
            return None
        remaining = self.ttl - (time.time() - self.created_at)
        return max(0, remaining)


class MemoryCache:
    """内存缓存"""
    
    def __init__(self, default_ttl: Optional[float] = None, max_size: Optional[int] = None):
        self._cache: Dict[str, CacheItem] = {}
        self._lock = threading.RLock()
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._access_order: Dict[str, float] = {}  # LRU跟踪
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        with self._lock:
            if key not in self._cache:
                return default
            
            item = self._cache[key]
            if item.is_expired():
                del self._cache[key]
                if key in self._access_order:
                    del self._access_order[key]
                return default
            
            # 更新访问时间
            self._access_order[key] = time.time()
            return item.value
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """设置缓存值"""
        with self._lock:
            if ttl is None:
                ttl = self.default_ttl
            
            # 检查大小限制
            if self.max_size and len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
            
            self._cache[key] = CacheItem(value, ttl)
            self._access_order[key] = time.time()
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._access_order:
                    del self._access_order[key]
                return True
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        with self._lock:
            if key not in self._cache:
                return False
            
            item = self._cache[key]
            if item.is_expired():
                del self._cache[key]
                if key in self._access_order:
                    del self._access_order[key]
                return False
            
            return True
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
    
    def size(self) -> int:
        """获取缓存大小"""
        with self._lock:
            return len(self._cache)
    
    def keys(self) -> list:
        """获取所有键"""
        with self._lock:
            # 清理过期项
            expired_keys = []
            for key, item in self._cache.items():
                if item.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                if key in self._access_order:
                    del self._access_order[key]
            
            return list(self._cache.keys())
    
    def cleanup_expired(self) -> int:
        """清理过期项"""
        with self._lock:
            expired_keys = []
            for key, item in self._cache.items():
                if item.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                if key in self._access_order:
                    del self._access_order[key]
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total_items = len(self._cache)
            expired_count = 0
            
            for item in self._cache.values():
                if item.is_expired():
                    expired_count += 1
            
            return {
                'total_items': total_items,
                'expired_items': expired_count,
                'active_items': total_items - expired_count,
                'max_size': self.max_size,
                'default_ttl': self.default_ttl
            }
    
    def _evict_lru(self) -> None:
        """驱逐最近最少使用的项"""
        if not self._access_order:
            return
        
        # 找到最旧的访问时间
        oldest_key = min(self._access_order.keys(), key=lambda k: self._access_order[k])
        del self._cache[oldest_key]
        del self._access_order[oldest_key]


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self._caches: Dict[str, MemoryCache] = {}
        self._lock = threading.RLock()
    
    def get_cache(self, name: str, default_ttl: Optional[float] = None, max_size: Optional[int] = None) -> MemoryCache:
        """获取或创建缓存实例"""
        with self._lock:
            if name not in self._caches:
                self._caches[name] = MemoryCache(default_ttl, max_size)
            return self._caches[name]
    
    def remove_cache(self, name: str) -> bool:
        """移除缓存实例"""
        with self._lock:
            if name in self._caches:
                del self._caches[name]
                return True
            return False
    
    def clear_all(self) -> None:
        """清空所有缓存"""
        with self._lock:
            for cache in self._caches.values():
                cache.clear()
    
    def cleanup_all_expired(self) -> Dict[str, int]:
        """清理所有缓存的过期项"""
        with self._lock:
            results = {}
            for name, cache in self._caches.items():
                results[name] = cache.cleanup_expired()
            return results
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有缓存的统计信息"""
        with self._lock:
            stats = {}
            for name, cache in self._caches.items():
                stats[name] = cache.get_stats()
            return stats


# 全局缓存管理器实例
cache_manager = CacheManager()


def cached(cache_name: str = 'default', ttl: Optional[float] = None, key_func: Optional[Callable] = None):
    """
    缓存装饰器
    
    Args:
        cache_name: 缓存名称
        ttl: 生存时间
        key_func: 自定义键生成函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认键生成策略
                key_data = {
                    'func_name': func.__name__,
                    'args': args,
                    'kwargs': kwargs
                }
                key_str = pickle.dumps(key_data, protocol=pickle.HIGHEST_PROTOCOL)
                cache_key = hashlib.md5(key_str).hexdigest()
            
            # 获取缓存
            cache = cache_manager.get_cache(cache_name, ttl)
            
            # 尝试从缓存获取结果
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        # 添加缓存控制方法
        wrapper.cache_clear = lambda: cache_manager.get_cache(cache_name).clear()
        wrapper.cache_info = lambda: cache_manager.get_cache(cache_name).get_stats()
        
        return wrapper
    return decorator


def cache_result(ttl: Optional[float] = None, cache_name: str = 'default'):
    """
    简单的结果缓存装饰器
    
    Args:
        ttl: 生存时间
        cache_name: 缓存名称
    """
    return cached(cache_name=cache_name, ttl=ttl)


# 便捷函数
def get_cache(name: str = 'default', **kwargs) -> MemoryCache:
    """获取缓存实例"""
    return cache_manager.get_cache(name, **kwargs)


def clear_cache(name: str = 'default') -> None:
    """清空指定缓存"""
    cache_manager.get_cache(name).clear()


def clear_all_caches() -> None:
    """清空所有缓存"""
    cache_manager.clear_all()


def cleanup_expired_items() -> Dict[str, int]:
    """清理所有过期项"""
    return cache_manager.cleanup_all_expired()


def get_cache_stats() -> Dict[str, Dict[str, Any]]:
    """获取所有缓存统计"""
    return cache_manager.get_all_stats()