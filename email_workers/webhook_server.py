#!/usr/bin/env python3
"""
邮件 Webhook 服务器
接收 Resend 的邮件事件并处理
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import json
import os
from email_processor import EmailProcessor
from typing import Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Email Processing Webhook", version="1.0.0")
email_processor = EmailProcessor()

@app.post("/webhook/email")
async def handle_email_webhook(request: Request):
    """处理邮件 Webhook 事件"""
    try:
        # 获取请求数据
        body = await request.body()
        data = json.loads(body)
        
        logger.info(f"收到邮件事件: {data.get('type', 'unknown')}")
        
        # 检查是否是邮件接收事件
        if data.get("type") == "email.received":
            email_data = data.get("data", {})
            
            # 提取邮件信息
            processed_email = {
                "from": email_data.get("from", ""),
                "to": email_data.get("to", ""),
                "subject": email_data.get("subject", ""),
                "content": email_data.get("text", ""),
                "html": email_data.get("html", "")
            }
            
            logger.info(f"处理邮件: {processed_email['subject']} from {processed_email['from']}")
            
            # 处理邮件
            result = email_processor.process_incoming_email(processed_email)
            
            logger.info(f"处理结果: {result}")
            
            return JSONResponse(content={
                "status": "success",
                "processed": True,
                "result": result
            })
        
        # 其他事件类型
        return JSONResponse(content={
            "status": "success", 
            "processed": False,
            "message": f"忽略事件类型: {data.get('type')}"
        })
        
    except Exception as e:
        logger.error(f"处理邮件事件时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "email-processor"}

@app.post("/test/process-email")
async def test_process_email(email_data: Dict[str, Any]):
    """测试邮件处理功能"""
    try:
        result = email_processor.process_incoming_email(email_data)
        return JSONResponse(content={
            "status": "success",
            "result": result
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)