from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

from .config import settings
from .schemas import ErrorResponse, ErrorDetail

logger = logging.getLogger(__name__)


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    """处理时间中间件"""
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # 记录请求
        logger.info(f"Request: {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        # 记录响应
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} in {process_time:.2f}s")
        
        return response


def setup_middleware(app: FastAPI) -> None:
    """设置所有中间件"""
    if settings.debug:
        app.add_middleware(ProcessTimeMiddleware)
        app.add_middleware(LoggingMiddleware)