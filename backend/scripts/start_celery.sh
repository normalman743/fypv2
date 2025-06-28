#!/bin/bash
# Celery Worker启动脚本

# 设置环境变量
export PYTHONPATH=/app:$PYTHONPATH

# 启动Celery Worker
celery -A app.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --queues=file_processing \
    --hostname=worker@%h \
    --max-tasks-per-child=1000 \
    --time-limit=1800 \
    --soft-time-limit=1200