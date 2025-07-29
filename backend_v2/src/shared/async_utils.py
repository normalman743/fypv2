"""异步工具和装饰器"""
import asyncio
import functools
from typing import Callable, Any, Awaitable, Union
from concurrent.futures import ThreadPoolExecutor
from .logging import get_logger


def async_to_sync(async_func: Callable[..., Awaitable[Any]]) -> Callable[..., Any]:
    """将异步函数转换为同步函数的装饰器"""
    @functools.wraps(async_func)
    def wrapper(*args, **kwargs):
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        
        if loop is None:
            # 没有运行中的事件循环，直接运行
            return asyncio.run(async_func(*args, **kwargs))
        else:
            # 有运行中的事件循环，在线程池中运行
            with ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, 
                    async_func(*args, **kwargs)
                )
                return future.result()
    
    return wrapper


def sync_to_async(sync_func: Callable[..., Any]) -> Callable[..., Awaitable[Any]]:
    """将同步函数转换为异步函数的装饰器"""
    @functools.wraps(sync_func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_func, *args, **kwargs)
    
    return wrapper


class AsyncServiceMixin:
    """异步服务混入类，提供异步/同步兼容性"""
    
    def run_async_in_sync(self, coro: Awaitable[Any]) -> Any:
        """在同步环境中运行异步代码"""
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        
        if loop is None:
            return asyncio.run(coro)
        else:
            # 在线程池中运行新的事件循环
            with ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
    
    async def run_sync_in_async(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """在异步环境中运行同步代码"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)


def hybrid_method(async_method_name: str):
    """装饰器：为异步方法创建同步版本"""
    def decorator(async_method):
        @functools.wraps(async_method)
        def sync_wrapper(self, *args, **kwargs):
            return self.run_async_in_sync(async_method(self, *args, **kwargs))
        
        return async_method, sync_wrapper
    
    return decorator


class AsyncContextManager:
    """异步上下文管理器，用于资源管理"""
    
    def __init__(self, resource_factory: Callable[[], Any], cleanup_func: Callable[[Any], Awaitable[None]] = None):
        self.resource_factory = resource_factory
        self.cleanup_func = cleanup_func
        self.resource = None
    
    async def __aenter__(self):
        self.resource = self.resource_factory()
        return self.resource
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.cleanup_func and self.resource:
            await self.cleanup_func(self.resource)


def async_retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """异步重试装饰器"""
    def decorator(async_func):
        @functools.wraps(async_func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await async_func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        break
                    
                    logger = get_logger('async_retry')
                    logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying in {current_delay}s...")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
            
            raise last_exception
        
        return wrapper
    return decorator


async def gather_with_limit(limit: int, *awaitables):
    """限制并发数量的gather"""
    semaphore = asyncio.Semaphore(limit)
    
    async def limited_awaitable(awaitable):
        async with semaphore:
            return await awaitable
    
    return await asyncio.gather(*[limited_awaitable(aw) for aw in awaitables])


class AsyncBatch:
    """异步批处理工具"""
    
    def __init__(self, batch_size: int = 10, max_concurrency: int = 5):
        self.batch_size = batch_size
        self.max_concurrency = max_concurrency
    
    async def process_items(self, items: list, processor: Callable[[Any], Awaitable[Any]]):
        """批处理异步操作"""
        results = []
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_tasks = [processor(item) for item in batch]
            
            # 限制并发数量
            batch_results = await gather_with_limit(self.max_concurrency, *batch_tasks)
            results.extend(batch_results)
        
        return results