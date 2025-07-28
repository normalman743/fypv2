"""
API装饰器模块 - 基于FastAPI最佳实践的自动化响应文档生成

提供 @service_api 装饰器，根据Service层声明的异常自动生成OpenAPI响应文档
"""
from functools import wraps
from typing import Type, Set, Any, Dict, Optional, Union, List, get_type_hints
from fastapi import HTTPException
from pydantic import BaseModel
import inspect

from .exceptions import BaseAPIException, ErrorResponse


class APIResponses:
    """API响应生成器 - 基于Service异常自动生成OpenAPI响应配置"""
    
    @staticmethod
    def create_with_examples(
        success_status: int = 200,
        success_model: Optional[Type[BaseModel]] = None,
        service_exceptions: Optional[Set[Type[BaseAPIException]]] = None,
        **custom_responses
    ) -> Dict[Union[int, str], Dict[str, Any]]:
        """
        基于Service异常和自定义配置创建OpenAPI响应文档
        
        Args:
            success_status: 成功响应状态码
            success_model: 成功响应模型
            service_exceptions: Service层可能抛出的异常集合
            **custom_responses: 自定义响应配置
            
        Returns:
            FastAPI responses配置字典
        """
        responses = {}
        
        # 添加成功响应
        if success_model:
            success_response = {
                "model": success_model,
                "description": "操作成功"
            }
            
            # 如果模型有示例，添加到响应中
            if hasattr(success_model, 'model_config') and success_model.model_config:
                config = success_model.model_config
                if isinstance(config, dict) and 'json_schema_extra' in config:
                    json_extra = config['json_schema_extra']
                    if isinstance(json_extra, dict) and 'examples' in json_extra:
                        success_response["content"] = {
                            "application/json": {
                                "examples": {
                                    "success": {
                                        "summary": "成功响应示例",
                                        "value": json_extra['examples'][0]
                                    }
                                }
                            }
                        }
            
            responses[success_status] = success_response
        
        # 添加基于Service异常的错误响应
        if service_exceptions:
            for exc_class in service_exceptions:
                # 创建异常实例来获取默认状态码和错误码
                try:
                    temp_exc = exc_class()
                    status_code = temp_exc.status_code
                    error_code = temp_exc.code
                except:
                    # 如果实例化失败，使用默认值
                    status_code = getattr(exc_class, 'status_code', 400)
                    error_code = exc_class.__name__.replace('Error', '').upper()
                
                description = exc_class.__doc__ or f"{status_code} 错误"
                
                responses[status_code] = {
                    "model": ErrorResponse,
                    "description": description.strip(),
                    "content": {
                        "application/json": {
                            "example": {
                                "success": False,
                                "error": {
                                    "code": error_code,
                                    "message": description.strip()
                                }
                            }
                        }
                    }
                }
        
        # 添加自定义响应
        responses.update(custom_responses)
        
        return responses


def create_service_route_config(
    service_class: Type,
    method_name: str,
    response_model: Optional[Type[BaseModel]] = None,
    success_status: int = 200,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    operation_id: Optional[str] = None,
    **additional_config
) -> Dict[str, Any]:
    """
    为Service方法创建FastAPI路由配置
    
    根据Service类的METHOD_EXCEPTIONS声明自动生成完整的路由配置，
    包括响应模型、错误响应文档等。
    
    Args:
        service_class: Service类
        method_name: Service方法名
        response_model: 成功响应模型
        success_status: 成功响应状态码
        summary: API摘要
        description: API详细描述
        **additional_config: 额外的路由配置
        
    Returns:
        完整的FastAPI路由配置字典
        
    Usage:
        @router.post("/register", **create_service_route_config(
            AuthService, 'register', RegisterResponse, 
            success_status=201, summary="用户注册"
        ))
        async def register(user_data: UserRegister, db: Session = Depends(get_db)):
            service = AuthService(db)
            result = service.register(user_data)
            return RegisterResponse(success=True, data=result)
    """
    # 获取Service方法的异常声明
    method_exceptions = getattr(service_class, 'METHOD_EXCEPTIONS', {}).get(method_name, set())
    
    # 生成响应配置
    responses = APIResponses.create_with_examples(
        success_status=success_status,
        success_model=response_model,
        service_exceptions=method_exceptions
    )
    
    # 构建路由配置
    route_config = {
        'status_code': success_status,
        'responses': responses,
        'summary': summary,
        'description': description,
        'tags': tags,
        'operation_id': operation_id,
    }
    
    # 添加响应模型（如果提供）
    if response_model:
        route_config['response_model'] = response_model
    
    # 移除None值
    route_config = {k: v for k, v in route_config.items() if v is not None}
    
    # 合并额外配置
    route_config.update(additional_config)
    
    return route_config


def service_api_handler(
    service_class: Type,
    method_name: str
):
    """
    Service API异常处理装饰器
    
    为路由函数添加统一的异常处理，确保Service层异常正确传播。
    通常与 create_service_route_config 配合使用。
    
    Usage:
        @service_api_handler(AuthService, 'register')
        async def register(user_data: UserRegister, db: Session = Depends(get_db)):
            service = AuthService(db)
            result = service.register(user_data)
            return RegisterResponse(success=True, data=result)
    """
    def decorator(route_func):
        @wraps(route_func)
        async def wrapper(*args, **kwargs):
            try:
                return await route_func(*args, **kwargs)
            except BaseAPIException:
                # Service层异常直接向上传播，由FastAPI异常处理器处理
                raise
            except Exception as e:
                # 未预期的异常转换为500错误
                from .logging import get_logger
                logger = get_logger(__name__)
                logger.error(f"Unexpected exception in {route_func.__name__}: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                from .exceptions import InternalServerError
                raise InternalServerError(f"服务器内部错误: {str(e)}")
        
        return wrapper
    return decorator


def get_service_api_config(func) -> Dict[str, Any]:
    """
    从装饰器修饰的函数中提取路由配置
    
    用于在路由注册时获取 @service_api 装饰器设置的配置
    """
    config = {}
    
    if hasattr(func, '__service_api_responses__'):
        config['responses'] = func.__service_api_responses__
    
    if hasattr(func, '__service_api_response_model__'):
        config['response_model'] = func.__service_api_response_model__
    
    if hasattr(func, '__service_api_summary__'):
        config['summary'] = func.__service_api_summary__
    
    if hasattr(func, '__service_api_description__'):
        config['description'] = func.__service_api_description__
        
    return config


def apply_service_api_metadata(router, route_func, **additional_kwargs):
    """
    将service_api装饰器收集的元数据应用到FastAPI路由
    
    这个函数用于在路由注册时应用装饰器收集的元数据，
    确保OpenAPI文档正确生成。
    
    Args:
        router: FastAPI路由器
        route_func: 路由函数
        **additional_kwargs: 额外的路由参数
    """
    route_kwargs = {}
    
    # 应用响应配置
    if hasattr(route_func, '__route_responses__'):
        route_kwargs['responses'] = route_func.__route_responses__
    
    # 应用响应模型
    if hasattr(route_func, '__route_response_model__'):
        route_kwargs['response_model'] = route_func.__route_response_model__
    
    # 应用摘要和描述
    if hasattr(route_func, '__route_summary__'):
        route_kwargs['summary'] = route_func.__route_summary__
        
    if hasattr(route_func, '__route_description__'):
        route_kwargs['description'] = route_func.__route_description__
    
    # 合并额外参数
    route_kwargs.update(additional_kwargs)
    
    return route_kwargs


# 向后兼容的旧版本API（如果CLAUDE.md中提到了这个）
create_with_examples = APIResponses.create_with_examples