#!/usr/bin/env python3
"""
Celery异步任务配置
"""

from celery import Celery
from app.core.config import settings
import os

# 创建Celery应用
celery_app = Celery(
    "campus_llm",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=["app.tasks.file_processing", "app.tasks.cleanup_tasks"]
)

# Celery配置
celery_app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    
    # 任务路由
    task_routes={
        "app.tasks.file_processing.*": {"queue": "file_processing"},
        "app.tasks.cleanup_tasks.*": {"queue": "cleanup"},
    },
    
    # 工作进程配置
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # 结果配置
    result_expires=3600,  # 1小时后删除结果
    task_track_started=True,
    task_send_sent_event=True,
    
    # 重试配置
    task_default_retry_delay=60,  # 重试延迟60秒
    task_max_retries=3,
)

# 配置定时任务
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'cleanup-expired-temporary-files': {
        'task': 'app.tasks.cleanup_tasks.cleanup_expired_temporary_files',
        'schedule': crontab(minute='0'),  # 每小时执行一次
    },
}