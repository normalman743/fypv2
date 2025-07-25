"""
Rate limiting middleware for resource protection
"""
import time
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class InMemoryRateLimiter:
    """简单的内存速率限制器（生产环境建议使用Redis）"""
    
    def __init__(self):
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, key: str, limit: int, window: int) -> Tuple[bool, int]:
        """
        检查是否允许请求
        
        Args:
            key: 限制键（通常是IP地址或用户ID）
            limit: 时间窗口内的最大请求数
            window: 时间窗口（秒）
        
        Returns:
            (是否允许, 重试等待时间)
        """
        now = time.time()
        
        # 清理过期的请求记录
        if key in self.requests:
            self.requests[key] = [
                timestamp for timestamp in self.requests[key]
                if now - timestamp < window
            ]
        else:
            self.requests[key] = []
        
        # 检查是否超过限制
        if len(self.requests[key]) >= limit:
            # 计算需要等待的时间
            oldest_request = min(self.requests[key])
            retry_after = int(window - (now - oldest_request)) + 1
            return False, retry_after
        
        # 记录当前请求
        self.requests[key].append(now)
        return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""
    
    def __init__(self, app, calls_per_minute: int = 120, calls_per_hour: int = 1000):
        super().__init__(app)
        self.limiter = InMemoryRateLimiter()
        self.calls_per_minute = calls_per_minute
        self.calls_per_hour = calls_per_hour
        
        # 特殊路径的限制（更严格）
        self.upload_calls_per_minute = 10
        self.upload_calls_per_hour = 100
    
    async def dispatch(self, request: Request, call_next):
        """处理请求速率限制"""
        
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        
        # 检查是否为上传端点（更严格限制）
        is_upload = self._is_upload_endpoint(request.url.path)
        
        if is_upload:
            # 上传端点的严格限制
            minute_allowed, minute_retry = self.limiter.is_allowed(
                f"upload:{client_ip}:minute", 
                self.upload_calls_per_minute, 
                60
            )
            hour_allowed, hour_retry = self.limiter.is_allowed(
                f"upload:{client_ip}:hour", 
                self.upload_calls_per_hour, 
                3600
            )
            
            if not minute_allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="上传请求过于频繁，请稍后再试",
                    headers={"Retry-After": str(minute_retry)}
                )
            
            if not hour_allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="今日上传次数已达上限，请明天再试",
                    headers={"Retry-After": str(hour_retry)}
                )
        else:
            # 一般API端点的限制
            minute_allowed, minute_retry = self.limiter.is_allowed(
                f"api:{client_ip}:minute", 
                self.calls_per_minute, 
                60
            )
            hour_allowed, hour_retry = self.limiter.is_allowed(
                f"api:{client_ip}:hour", 
                self.calls_per_hour, 
                3600
            )
            
            if not minute_allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="请求过于频繁，请稍后再试",
                    headers={"Retry-After": str(minute_retry)}
                )
            
            if not hour_allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="今日请求次数已达上限，请明天再试",
                    headers={"Retry-After": str(hour_retry)}
                )
        
        # 继续处理请求
        response = await call_next(request)
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头部（如果使用了反向代理）
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 默认使用客户端IP
        return request.client.host if request.client else "unknown"
    
    def _is_upload_endpoint(self, path: str) -> bool:
        """检查是否为上传端点"""
        upload_endpoints = [
            "/api/v1/files/upload",
            "/api/v1/files/temporary",
            "/api/v1/unified-files/upload"
        ]
        return any(path.startswith(endpoint) for endpoint in upload_endpoints)