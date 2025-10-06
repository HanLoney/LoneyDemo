"""
文件操作工具
"""
import os
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import hashlib


class FileUtils:
    """文件操作工具类"""
    
    @staticmethod
    def ensure_dir(path: Union[str, Path]) -> Path:
        """
        确保目录存在
        
        Args:
            path: 目录路径
            
        Returns:
            目录路径对象
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def read_json(file_path: Union[str, Path], default: Any = None) -> Any:
        """
        读取JSON文件
        
        Args:
            file_path: 文件路径
            default: 默认值
            
        Returns:
            JSON数据
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default
    
    @staticmethod
    def write_json(file_path: Union[str, Path], data: Any, indent: int = 2) -> bool:
        """
        写入JSON文件
        
        Args:
            file_path: 文件路径
            data: 数据
            indent: 缩进
            
        Returns:
            是否成功
        """
        try:
            file_path = Path(file_path)
            FileUtils.ensure_dir(file_path.parent)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=indent)
            return True
        except Exception:
            return False
    
    @staticmethod
    def read_text(file_path: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
        """
        读取文本文件
        
        Args:
            file_path: 文件路径
            encoding: 编码
            
        Returns:
            文本内容
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception:
            return None
    
    @staticmethod
    def write_text(file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
        """
        写入文本文件
        
        Args:
            file_path: 文件路径
            content: 文本内容
            encoding: 编码
            
        Returns:
            是否成功
        """
        try:
            file_path = Path(file_path)
            FileUtils.ensure_dir(file_path.parent)
            
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            return True
        except Exception:
            return False

    @staticmethod
    def write_bytes(file_path: Union[str, Path], data: bytes) -> bool:
        """
        写入二进制文件
        
        Args:
            file_path: 文件路径
            data: 二进制数据
            
        Returns:
            是否成功
        """
        try:
            file_path = Path(file_path)
            FileUtils.ensure_dir(file_path.parent)
            
            with open(file_path, 'wb') as f:
                f.write(data)
            return True
        except Exception:
            return False
    
    @staticmethod
    def copy_file(src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """
        复制文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            
        Returns:
            是否成功
        """
        try:
            dst = Path(dst)
            FileUtils.ensure_dir(dst.parent)
            shutil.copy2(src, dst)
            return True
        except Exception:
            return False
    
    @staticmethod
    def move_file(src: Union[str, Path], dst: Union[str, Path]) -> bool:
        """
        移动文件
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            
        Returns:
            是否成功
        """
        try:
            dst = Path(dst)
            FileUtils.ensure_dir(dst.parent)
            shutil.move(src, dst)
            return True
        except Exception:
            return False
    
    @staticmethod
    def delete_file(file_path: Union[str, Path]) -> bool:
        """
        删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功
        """
        try:
            Path(file_path).unlink(missing_ok=True)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> int:
        """
        获取文件大小
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件大小（字节）
        """
        try:
            return Path(file_path).stat().st_size
        except Exception:
            return 0
    
    @staticmethod
    def get_file_hash(file_path: Union[str, Path], algorithm: str = 'md5') -> Optional[str]:
        """
        获取文件哈希值
        
        Args:
            file_path: 文件路径
            algorithm: 哈希算法
            
        Returns:
            哈希值
        """
        try:
            hash_obj = hashlib.new(algorithm)
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception:
            return None
    
    @staticmethod
    def list_files(directory: Union[str, Path], pattern: str = "*", recursive: bool = False) -> List[Path]:
        """
        列出目录中的文件
        
        Args:
            directory: 目录路径
            pattern: 文件模式
            recursive: 是否递归
            
        Returns:
            文件路径列表
        """
        try:
            directory = Path(directory)
            if recursive:
                return list(directory.rglob(pattern))
            else:
                return list(directory.glob(pattern))
        except Exception:
            return []
    
    @staticmethod
    def clean_old_files(directory: Union[str, Path], days: int = 7, pattern: str = "*") -> int:
        """
        清理旧文件
        
        Args:
            directory: 目录路径
            days: 保留天数
            pattern: 文件模式
            
        Returns:
            删除的文件数量
        """
        try:
            directory = Path(directory)
            cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
            deleted_count = 0
            
            for file_path in directory.glob(pattern):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
            
            return deleted_count
        except Exception:
            return 0
    
    @staticmethod
    def get_directory_size(directory: Union[str, Path]) -> int:
        """
        获取目录大小
        
        Args:
            directory: 目录路径
            
        Returns:
            目录大小（字节）
        """
        try:
            total_size = 0
            for file_path in Path(directory).rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
        except Exception:
            return 0