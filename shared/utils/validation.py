"""
数据验证工具
"""
import re
from typing import Any, Dict, List, Optional, Union, Callable
from email.utils import parseaddr


class ValidationError(Exception):
    """验证错误异常"""
    pass


class Validator:
    """数据验证器"""
    
    def __init__(self):
        self.errors: List[str] = []
    
    def clear_errors(self) -> None:
        """清空错误列表"""
        self.errors.clear()
    
    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0
    
    def get_errors(self) -> List[str]:
        """获取错误列表"""
        return self.errors.copy()
    
    def add_error(self, message: str) -> None:
        """添加错误"""
        self.errors.append(message)
    
    def validate_required(self, value: Any, field_name: str) -> bool:
        """验证必填字段"""
        if value is None or (isinstance(value, str) and not value.strip()):
            self.add_error(f"{field_name} 是必填字段")
            return False
        return True
    
    def validate_string(self, value: Any, field_name: str, min_length: int = 0, max_length: int = None) -> bool:
        """验证字符串"""
        if not isinstance(value, str):
            self.add_error(f"{field_name} 必须是字符串")
            return False
        
        if len(value) < min_length:
            self.add_error(f"{field_name} 长度不能少于 {min_length} 个字符")
            return False
        
        if max_length is not None and len(value) > max_length:
            self.add_error(f"{field_name} 长度不能超过 {max_length} 个字符")
            return False
        
        return True
    
    def validate_number(self, value: Any, field_name: str, min_value: float = None, max_value: float = None) -> bool:
        """验证数字"""
        if not isinstance(value, (int, float)):
            self.add_error(f"{field_name} 必须是数字")
            return False
        
        if min_value is not None and value < min_value:
            self.add_error(f"{field_name} 不能小于 {min_value}")
            return False
        
        if max_value is not None and value > max_value:
            self.add_error(f"{field_name} 不能大于 {max_value}")
            return False
        
        return True
    
    def validate_integer(self, value: Any, field_name: str, min_value: int = None, max_value: int = None) -> bool:
        """验证整数"""
        if not isinstance(value, int):
            self.add_error(f"{field_name} 必须是整数")
            return False
        
        if min_value is not None and value < min_value:
            self.add_error(f"{field_name} 不能小于 {min_value}")
            return False
        
        if max_value is not None and value > max_value:
            self.add_error(f"{field_name} 不能大于 {max_value}")
            return False
        
        return True
    
    def validate_email(self, value: Any, field_name: str) -> bool:
        """验证邮箱地址"""
        if not isinstance(value, str):
            self.add_error(f"{field_name} 必须是字符串")
            return False
        
        # 使用email.utils.parseaddr进行基本验证
        parsed = parseaddr(value)
        if not parsed[1] or '@' not in parsed[1]:
            self.add_error(f"{field_name} 不是有效的邮箱地址")
            return False
        
        # 更严格的正则验证
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            self.add_error(f"{field_name} 不是有效的邮箱地址")
            return False
        
        return True
    
    def validate_url(self, value: Any, field_name: str) -> bool:
        """验证URL"""
        if not isinstance(value, str):
            self.add_error(f"{field_name} 必须是字符串")
            return False
        
        url_pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$'
        if not re.match(url_pattern, value):
            self.add_error(f"{field_name} 不是有效的URL")
            return False
        
        return True
    
    def validate_phone(self, value: Any, field_name: str) -> bool:
        """验证手机号码（中国）"""
        if not isinstance(value, str):
            self.add_error(f"{field_name} 必须是字符串")
            return False
        
        # 中国手机号码正则
        phone_pattern = r'^1[3-9]\d{9}$'
        if not re.match(phone_pattern, value):
            self.add_error(f"{field_name} 不是有效的手机号码")
            return False
        
        return True
    
    def validate_choice(self, value: Any, field_name: str, choices: List[Any]) -> bool:
        """验证选择项"""
        if value not in choices:
            self.add_error(f"{field_name} 必须是以下选项之一: {', '.join(map(str, choices))}")
            return False
        
        return True
    
    def validate_list(self, value: Any, field_name: str, min_length: int = 0, max_length: int = None) -> bool:
        """验证列表"""
        if not isinstance(value, list):
            self.add_error(f"{field_name} 必须是列表")
            return False
        
        if len(value) < min_length:
            self.add_error(f"{field_name} 至少需要 {min_length} 个元素")
            return False
        
        if max_length is not None and len(value) > max_length:
            self.add_error(f"{field_name} 最多只能有 {max_length} 个元素")
            return False
        
        return True
    
    def validate_dict(self, value: Any, field_name: str, required_keys: List[str] = None) -> bool:
        """验证字典"""
        if not isinstance(value, dict):
            self.add_error(f"{field_name} 必须是字典")
            return False
        
        if required_keys:
            missing_keys = [key for key in required_keys if key not in value]
            if missing_keys:
                self.add_error(f"{field_name} 缺少必需的键: {', '.join(missing_keys)}")
                return False
        
        return True
    
    def validate_regex(self, value: Any, field_name: str, pattern: str, message: str = None) -> bool:
        """验证正则表达式"""
        if not isinstance(value, str):
            self.add_error(f"{field_name} 必须是字符串")
            return False
        
        if not re.match(pattern, value):
            error_msg = message or f"{field_name} 格式不正确"
            self.add_error(error_msg)
            return False
        
        return True
    
    def validate_custom(self, value: Any, field_name: str, validator_func: Callable[[Any], bool], message: str = None) -> bool:
        """自定义验证"""
        try:
            if not validator_func(value):
                error_msg = message or f"{field_name} 验证失败"
                self.add_error(error_msg)
                return False
            return True
        except Exception as e:
            self.add_error(f"{field_name} 验证时发生错误: {str(e)}")
            return False


class SchemaValidator:
    """模式验证器"""
    
    @staticmethod
    def validate(data: Dict[str, Any], schema: Dict[str, Dict[str, Any]]) -> Validator:
        """
        根据模式验证数据
        
        Args:
            data: 要验证的数据
            schema: 验证模式
            
        Returns:
            验证器对象
        """
        validator = Validator()
        
        for field_name, rules in schema.items():
            value = data.get(field_name)
            
            # 检查必填字段
            if rules.get('required', False):
                if not validator.validate_required(value, field_name):
                    continue
            
            # 如果值为空且不是必填字段，跳过其他验证
            if value is None or (isinstance(value, str) and not value.strip()):
                continue
            
            # 类型验证
            field_type = rules.get('type')
            if field_type == 'string':
                validator.validate_string(
                    value, field_name,
                    rules.get('min_length', 0),
                    rules.get('max_length')
                )
            elif field_type == 'number':
                validator.validate_number(
                    value, field_name,
                    rules.get('min_value'),
                    rules.get('max_value')
                )
            elif field_type == 'integer':
                validator.validate_integer(
                    value, field_name,
                    rules.get('min_value'),
                    rules.get('max_value')
                )
            elif field_type == 'email':
                validator.validate_email(value, field_name)
            elif field_type == 'url':
                validator.validate_url(value, field_name)
            elif field_type == 'phone':
                validator.validate_phone(value, field_name)
            elif field_type == 'list':
                validator.validate_list(
                    value, field_name,
                    rules.get('min_length', 0),
                    rules.get('max_length')
                )
            elif field_type == 'dict':
                validator.validate_dict(
                    value, field_name,
                    rules.get('required_keys')
                )
            
            # 选择项验证
            if 'choices' in rules:
                validator.validate_choice(value, field_name, rules['choices'])
            
            # 正则验证
            if 'pattern' in rules:
                validator.validate_regex(
                    value, field_name,
                    rules['pattern'],
                    rules.get('pattern_message')
                )
            
            # 自定义验证
            if 'custom' in rules:
                validator.validate_custom(
                    value, field_name,
                    rules['custom'],
                    rules.get('custom_message')
                )
        
        return validator