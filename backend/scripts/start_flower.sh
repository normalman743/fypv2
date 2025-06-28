#!/bin/bash
# Flower监控启动脚本 (Celery任务监控界面)

# 启动Flower
celery -A app.celery_app flower \
    --port=5555 \
    --url_prefix=flower \
    --basic_auth=admin:flower123