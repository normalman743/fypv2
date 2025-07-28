"""
API 装饰器 - 自动处理响应文档和异常
"""
from functools import wraps
from typing import Type, Dict, Any, Set, Callable, Optional
from fastapi import HTTPException
from app.schemas.common import ErrorResponse
from app.core.exceptions import BaseAPIException


class APIResponses:
    """API 响应配置管理"""
    
    # 预定义的错误描述
    ERROR_DESCRIPTIONS = {
        400: "Bad Request - 请求参数错误",
        401: "Unauthorized - 未认证或认证失败",
        402: "Payment Required - 余额不足",
        403: "Forbidden - 无权限访问",
        404: "Not Found - 资源不存在",
        409: "Conflict - 资源冲突",
        413: "Payload Too Large - 请求体过大",
        415: "Unsupported Media Type - 不支持的媒体类型",
        422: "Validation Error - 数据验证失败",
        429: "Too Many Requests - 请求过于频繁",
        500: "Internal Server Error - 服务器内部错误",
        502: "Bad Gateway - 网关错误",
        503: "Service Unavailable - 服务不可用",
        504: "Gateway Timeout - 网关超时"
    }
    
    @classmethod
    def create(cls, *status_codes: int) -> Dict[int, Dict[str, Any]]:
        """创建响应配置"""
        responses = {}
        
        for code in status_codes:
            responses[code] = {
                "model": ErrorResponse,
                "description": cls.ERROR_DESCRIPTIONS.get(code, f"Error {code}")
            }
            
        return responses
    
    @classmethod
    def create_with_examples(cls, **config) -> Dict[int, Dict[str, Any]]:
        """
        创建带有详细示例的响应配置
        
        Args:
            **config: 状态码 -> 示例配置的映射
            
        Example:
            responses = APIResponses.create_with_examples(
                400=[
                    {"code": "INVALID_INVITE", "message": "邀请码无效", "summary": "邀请码无效"},
                    {"code": "INVALID_EMAIL", "message": "邮箱域名无效", "summary": "邮箱域名无效"}
                ],
                403={"code": "REGISTRATION_DISABLED", "message": "注册功能已关闭"}
            )
        """
        responses = {}
        
        for status_code, examples_config in config.items():
            status_code = int(status_code)
            
            response = {
                "model": ErrorResponse,
                "description": cls.ERROR_DESCRIPTIONS.get(status_code, f"Error {status_code}"),
                "content": {
                    "application/json": {}
                }
            }
            
            if isinstance(examples_config, list):
                # 多个示例
                examples = {}
                for i, example in enumerate(examples_config):
                    key = example.get('summary', f'example_{i}').lower().replace(' ', '_')
                    examples[key] = {
                        "summary": example.get('summary', f"Example {i+1}"),
                        "value": {
                            "success": False,
                            "error": {
                                "code": example['code'],
                                "message": example['message'],
                                **({"details": example['details']} if 'details' in example else {})
                            }
                        }
                    }
                response["content"]["application/json"]["examples"] = examples
            else:
                # 单个示例
                response["content"]["application/json"]["example"] = {
                    "success": False,
                    "error": {
                        "code": examples_config['code'],
                        "message": examples_config['message'],
                        **({"details": examples_config['details']} if 'details' in examples_config else {})
                    }
                }
            
            responses[status_code] = response
            
        return responses


def get_exception_status_codes(exceptions: Set[Type[Exception]]) -> Set[int]:
    """从异常类集合中提取状态码"""
    status_codes = set()
    
    for exc_class in exceptions:
        if issubclass(exc_class, BaseAPIException):
            # 创建临时实例获取状态码
            try:
                temp_instance = exc_class("temp")
                status_codes.add(temp_instance.status_code)
            except:
                # 如果创建失败，尝试从类属性获取
                if hasattr(exc_class, 'status_code'):
                    status_codes.add(exc_class.status_code)
                    
    return status_codes


def get_service_responses(service_class: Type, method_name: str) -> Dict[int, Dict[str, Any]]:
    """
    从 Service 类的 METHOD_EXCEPTIONS 获取响应配置
    
    Args:
        service_class: Service 类
        method_name: Service 方法名
        
    Returns:
        FastAPI responses 字典
        
    Example:
        responses = get_service_responses(AuthService, 'register')
        # 返回: {400: {"model": ErrorResponse, "description": "..."}, ...}
    """
    method_exceptions = set()
    if hasattr(service_class, 'METHOD_EXCEPTIONS'):
        method_exceptions = service_class.METHOD_EXCEPTIONS.get(method_name, set())
    
    # 从异常获取状态码
    status_codes = get_exception_status_codes(method_exceptions)
    
    # 生成响应配置
    return APIResponses.create(*status_codes)


def service_api(service_class: Type, method_name: str, response_model: Type = None, **router_kwargs):
    """
    增强版 Service API 装饰器
    
    自动处理：
    1. 异常捕获和处理
    2. OpenAPI 响应文档生成 
    3. response_model 配置
    
    Args:
        service_class: Service 类
        method_name: Service 方法名
        response_model: 响应模型类型
        **router_kwargs: 其他路由参数（summary, description等）
        
    Example:
        @router.post("/register")
        @service_api(AuthService, 'register', RegisterResponse, summary="用户注册")
        async def register(...):
    """
    def decorator(func: Callable):
        # 获取 Service 方法可能的异常
        method_exceptions = set()
        if hasattr(service_class, 'METHOD_EXCEPTIONS'):
            method_exceptions = service_class.METHOD_EXCEPTIONS.get(method_name, set())
        
        # 包装原始函数
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except tuple(method_exceptions) as e:
                # 重新抛出声明的异常（FastAPI 会处理）
                raise e
            except Exception as e:
                # 未声明的异常，记录并返回 500
                import logging
                logging.error(f"Unexpected error in {service_class.__name__}.{method_name}: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail={
                        "success": False,
                        "error": {
                            "code": "INTERNAL_ERROR",
                            "message": "服务器内部错误"
                        }
                    }
                )
        
        return wrapper
    
    return decorator


# 预定义的响应组合（可选）
class CommonResponses:
    """常用的响应组合"""
    
    # 公开 API（无需认证）
    PUBLIC = APIResponses.create(400, 422, 429)
    
    # 需要认证的 API
    AUTHENTICATED = APIResponses.create(400, 401, 422, 429)
    
    # 管理员 API
    ADMIN_ONLY = APIResponses.create(400, 401, 403, 422, 429)
    
    # CRUD 资源操作
    RESOURCE_CRUD = APIResponses.create(400, 401, 403, 404, 409, 422)
    
    # 文件操作
    FILE_OPERATIONS = APIResponses.create(400, 401, 403, 404, 413, 415, 422)
    
    # AI 聊天
    AI_CHAT = APIResponses.create(400, 401, 402, 403, 422, 429)