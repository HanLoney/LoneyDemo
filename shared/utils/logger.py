"""
日志管理模块
提供统一的日志配置和管理功能
"""
import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional
from .config import get_logging_config


class LoggerManager:
    """日志管理器"""
    
    _loggers = {}
    _configured = False
    
    @classmethod
    def setup_logging(cls):
        """设置全局日志配置"""
        if cls._configured:
            return
            
        log_config = get_logging_config()
        
        # 创建日志目录
        log_file = log_config.get('file', 'logs/jiuci.log')
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_config.get('level', 'INFO')))
        
        # 清除现有处理器
        root_logger.handlers.clear()
        
        # 创建格式器
        formatter = logging.Formatter(
            log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # 文件处理器（带轮转）
        try:
            max_size = cls._parse_size(log_config.get('max_size', '10MB'))
            backup_count = log_config.get('backup_count', 5)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"无法创建文件日志处理器: {e}")
        
        cls._configured = True
    
    @classmethod
    def _parse_size(cls, size_str: str) -> int:
        """解析大小字符串，如 '10MB' -> 10485760"""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        获取日志器
        
        Args:
            name: 日志器名称
            
        Returns:
            日志器实例
        """
        if not cls._configured:
            cls.setup_logging()
            
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)
            
        return cls._loggers[name]


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取日志器的便捷函数
    
    Args:
        name: 日志器名称，默认为调用模块名
        
    Returns:
        日志器实例
    """
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return LoggerManager.get_logger(name)


# 设置日志
LoggerManager.setup_logging()