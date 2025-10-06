"""
时间处理工具
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
import time


class TimeUtils:
    """时间处理工具类"""
    
    # 常用时间格式
    FORMAT_DATETIME = "%Y-%m-%d %H:%M:%S"
    FORMAT_DATE = "%Y-%m-%d"
    FORMAT_TIME = "%H:%M:%S"
    FORMAT_ISO = "%Y-%m-%dT%H:%M:%S"
    FORMAT_TIMESTAMP = "%Y%m%d_%H%M%S"
    
    @staticmethod
    def now() -> datetime:
        """
        获取当前时间
        
        Returns:
            当前时间
        """
        return datetime.now()
    
    @staticmethod
    def utc_now() -> datetime:
        """
        获取当前UTC时间
        
        Returns:
            当前UTC时间
        """
        return datetime.now(timezone.utc)
    
    @staticmethod
    def timestamp() -> float:
        """
        获取当前时间戳
        
        Returns:
            时间戳
        """
        return time.time()
    
    @staticmethod
    def format_datetime(dt: datetime, fmt: str = FORMAT_DATETIME) -> str:
        """
        格式化日期时间
        
        Args:
            dt: 日期时间对象
            fmt: 格式字符串
            
        Returns:
            格式化后的字符串
        """
        return dt.strftime(fmt)
    
    @staticmethod
    def parse_datetime(dt_str: str, fmt: str = FORMAT_DATETIME) -> Optional[datetime]:
        """
        解析日期时间字符串
        
        Args:
            dt_str: 日期时间字符串
            fmt: 格式字符串
            
        Returns:
            日期时间对象
        """
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            return None
    
    @staticmethod
    def from_timestamp(timestamp: float) -> datetime:
        """
        从时间戳创建日期时间
        
        Args:
            timestamp: 时间戳
            
        Returns:
            日期时间对象
        """
        return datetime.fromtimestamp(timestamp)
    
    @staticmethod
    def to_timestamp(dt: datetime) -> float:
        """
        转换为时间戳
        
        Args:
            dt: 日期时间对象
            
        Returns:
            时间戳
        """
        return dt.timestamp()
    
    @staticmethod
    def add_time(dt: datetime, **kwargs) -> datetime:
        """
        增加时间
        
        Args:
            dt: 日期时间对象
            **kwargs: 时间增量参数
            
        Returns:
            新的日期时间对象
        """
        return dt + timedelta(**kwargs)
    
    @staticmethod
    def subtract_time(dt: datetime, **kwargs) -> datetime:
        """
        减少时间
        
        Args:
            dt: 日期时间对象
            **kwargs: 时间增量参数
            
        Returns:
            新的日期时间对象
        """
        return dt - timedelta(**kwargs)
    
    @staticmethod
    def time_diff(dt1: datetime, dt2: datetime) -> timedelta:
        """
        计算时间差
        
        Args:
            dt1: 日期时间对象1
            dt2: 日期时间对象2
            
        Returns:
            时间差
        """
        return dt1 - dt2
    
    @staticmethod
    def time_diff_seconds(dt1: datetime, dt2: datetime) -> float:
        """
        计算时间差（秒）
        
        Args:
            dt1: 日期时间对象1
            dt2: 日期时间对象2
            
        Returns:
            时间差（秒）
        """
        return (dt1 - dt2).total_seconds()
    
    @staticmethod
    def is_same_day(dt1: datetime, dt2: datetime) -> bool:
        """
        判断是否为同一天
        
        Args:
            dt1: 日期时间对象1
            dt2: 日期时间对象2
            
        Returns:
            是否为同一天
        """
        return dt1.date() == dt2.date()
    
    @staticmethod
    def start_of_day(dt: datetime) -> datetime:
        """
        获取一天的开始时间
        
        Args:
            dt: 日期时间对象
            
        Returns:
            一天的开始时间
        """
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    
    @staticmethod
    def end_of_day(dt: datetime) -> datetime:
        """
        获取一天的结束时间
        
        Args:
            dt: 日期时间对象
            
        Returns:
            一天的结束时间
        """
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        格式化持续时间
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化后的持续时间字符串
        """
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}分钟"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.1f}小时"
        else:
            days = seconds / 86400
            return f"{days:.1f}天"
    
    @staticmethod
    def format_relative_time(dt: datetime, base_time: Optional[datetime] = None) -> str:
        """
        格式化相对时间
        
        Args:
            dt: 日期时间对象
            base_time: 基准时间，默认为当前时间
            
        Returns:
            相对时间字符串
        """
        if base_time is None:
            base_time = TimeUtils.now()
        
        diff = base_time - dt
        seconds = diff.total_seconds()
        
        if seconds < 0:
            # 未来时间
            seconds = abs(seconds)
            if seconds < 60:
                return f"{int(seconds)}秒后"
            elif seconds < 3600:
                return f"{int(seconds / 60)}分钟后"
            elif seconds < 86400:
                return f"{int(seconds / 3600)}小时后"
            else:
                return f"{int(seconds / 86400)}天后"
        else:
            # 过去时间
            if seconds < 60:
                return f"{int(seconds)}秒前"
            elif seconds < 3600:
                return f"{int(seconds / 60)}分钟前"
            elif seconds < 86400:
                return f"{int(seconds / 3600)}小时前"
            else:
                return f"{int(seconds / 86400)}天前"
    
    @staticmethod
    def sleep(seconds: float) -> None:
        """
        休眠指定秒数
        
        Args:
            seconds: 休眠秒数
        """
        time.sleep(seconds)
    
    @staticmethod
    def measure_time(func):
        """
        测量函数执行时间的装饰器
        
        Args:
            func: 要测量的函数
            
        Returns:
            装饰后的函数
        """
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"函数 {func.__name__} 执行时间: {execution_time:.4f}秒")
            return result
        return wrapper