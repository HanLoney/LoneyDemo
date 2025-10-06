"""
配置管理模块
提供统一的配置加载和管理功能
"""
import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为项目根目录下的config/config.yaml
        """
        self._config = {}
        self._config_path = config_path or self._get_default_config_path()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        project_root = Path(__file__).parent.parent.parent
        return str(project_root / "config" / "config.yaml")
    
    def _load_config(self):
        """加载配置文件"""
        # 加载环境变量
        env_path = Path(self._config_path).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        
        # 加载YAML配置文件
        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"配置文件未找到: {self._config_path}")
            self._config = {}
        except yaml.YAMLError as e:
            print(f"配置文件格式错误: {e}")
            self._config = {}
        
        # 用环境变量覆盖配置
        self._override_with_env()
    
    def _override_with_env(self):
        """用环境变量覆盖配置"""
        env_mappings = {
            'APP_ENV': 'app.env',
            'APP_DEBUG': 'app.debug',
            'APP_SECRET_KEY': 'app.secret_key',
            'APP_HOST': 'app.host',
            'APP_PORT': 'app.port',
            'OPENAI_API_KEY': 'external_apis.openai.api_key',
            'OPENAI_BASE_URL': 'external_apis.openai.base_url',
            'OPENAI_MODEL': 'external_apis.openai.model',
            'DATABASE_URL': 'database.url',
            'REDIS_URL': 'cache.url',
            'LOG_LEVEL': 'logging.level',
            'CORS_ORIGINS': 'security.cors_origins',
            'RATE_LIMIT': 'security.rate_limit',
        }
        
        for env_key, config_key in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                self._set_nested_value(config_key, env_value)
    
    def _set_nested_value(self, key_path: str, value: Any):
        """设置嵌套配置值"""
        keys = key_path.split('.')
        current = self._config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # 类型转换
        if isinstance(value, str):
            if value.lower() in ('true', 'false'):
                value = value.lower() == 'true'
            elif value.isdigit():
                value = int(value)
            elif ',' in value:  # 处理逗号分隔的列表
                value = [item.strip() for item in value.split(',')]
        
        current[keys[-1]] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key_path: 配置键路径，支持点分隔的嵌套路径，如 'app.debug'
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key_path.split('.')
        current = self._config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """
        设置配置值
        
        Args:
            key_path: 配置键路径
            value: 配置值
        """
        self._set_nested_value(key_path, value)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取配置段
        
        Args:
            section: 配置段名称
            
        Returns:
            配置段字典
        """
        return self.get(section, {})
    
    def reload(self):
        """重新加载配置"""
        self._load_config()
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取完整配置字典"""
        return self._config.copy()


# 全局配置实例
config = ConfigManager()


def get_config(key_path: str, default: Any = None) -> Any:
    """
    获取配置值的便捷函数
    
    Args:
        key_path: 配置键路径
        default: 默认值
        
    Returns:
        配置值
    """
    return config.get(key_path, default)


def get_database_config() -> Dict[str, Any]:
    """获取数据库配置"""
    return config.get_section('database')


def get_cache_config() -> Dict[str, Any]:
    """获取缓存配置"""
    return config.get_section('cache')


def get_openai_config() -> Dict[str, Any]:
    """获取OpenAI配置"""
    return config.get_section('external_apis.openai')


def get_logging_config() -> Dict[str, Any]:
    """获取日志配置"""
    return config.get_section('logging')


def is_debug_mode() -> bool:
    """是否为调试模式"""
    return config.get('app.debug', False)


def get_app_config() -> Dict[str, Any]:
    """获取应用配置"""
    return config.get_section('app')


def get_all_config() -> Dict[str, Any]:
    """获取完整配置"""
    return config._config