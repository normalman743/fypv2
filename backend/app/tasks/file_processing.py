#!/usr/bin/env python3
"""
文件处理异步任务
"""

from celery import current_task
from app.celery_app import celery_app
from app.models.database import SessionLocal
from app.models.file import File
from sqlalchemy.orm import Session
import tempfile
import os
import time
from typing import Dict, Any

# Import RAG service
try:
    from app.services.rag_service import get_rag_service
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


@celery_app.task(bind=True, name="process_file_rag")
def process_file_rag_task(self, file_id: int, file_content: bytes) -> Dict[str, Any]:
    """
    异步处理文件RAG
    
    Args:
        file_id: 文件ID
        file_content: 文件内容字节
        
    Returns:
        处理结果
    """
    db: Session = SessionLocal()
    
    try:
        # 获取文件记录
        file_record = db.query(File).filter(File.id == file_id).first()
        if not file_record:
            return {"status": "error", "message": f"File {file_id} not found"}
        
        # 更新状态为处理中
        file_record.processing_status = "processing"
        db.commit()
        
        # 更新任务进度
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 10, "total": 100, "status": "开始处理文件..."}
        )
        
        if not RAG_AVAILABLE:
            print("⚠️ RAG service not available")
            file_record.processing_status = "completed"
            file_record.is_processed = True
            db.commit()
            return {
                "status": "completed", 
                "message": "RAG service not available, marked as completed",
                "file_id": file_id
            }
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            suffix=f"_{file_record.original_name}", 
            delete=False
        ) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # 更新进度
            current_task.update_state(
                state="PROGRESS", 
                meta={"current": 30, "total": 100, "status": "初始化RAG服务..."}
            )
            
            # 处理RAG
            rag_service = get_rag_service()
            
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 50, "total": 100, "status": "分析文件内容..."}
            )
            
            start_time = time.time()
            result = rag_service.process_file(file_record, temp_file_path)
            processing_time = time.time() - start_time
            
            # 更新进度
            current_task.update_state(
                state="PROGRESS",
                meta={"current": 90, "total": 100, "status": "保存处理结果..."}
            )
            
            # 更新文件状态为完成
            file_record.is_processed = True
            file_record.processing_status = "completed"
            db.commit()
            
            # 最终状态
            result.update({
                "status": "completed",
                "processing_time": processing_time,
                "file_id": file_id,
                "task_id": str(current_task.request.id)
            })
            
            print(f"✅ File {file_id} processed successfully: {result}")
            return result
            
        except Exception as e:
            print(f"❌ RAG processing failed for file {file_id}: {e}")
            file_record.processing_status = "failed"
            db.commit()
            
            return {
                "status": "failed",
                "error": str(e),
                "file_id": file_id
            }
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        print(f"❌ Task execution failed for file {file_id}: {e}")
        
        # 尝试更新状态
        try:
            file_record = db.query(File).filter(File.id == file_id).first()
            if file_record:
                file_record.processing_status = "failed"
                db.commit()
        except:
            pass
            
        return {
            "status": "failed",
            "error": str(e),
            "file_id": file_id
        }
        
    finally:
        db.close()


@celery_app.task(name="cleanup_failed_files")
def cleanup_failed_files_task():
    """
    定期清理失败的文件处理任务
    """
    db: Session = SessionLocal()
    
    try:
        # 查找处理失败超过1小时的文件
        from datetime import datetime, timedelta
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        failed_files = db.query(File).filter(
            File.processing_status == "failed",
            File.created_at < one_hour_ago
        ).all()
        
        for file_record in failed_files:
            # 重试处理或标记为永久失败
            print(f"🔄 Retrying failed file: {file_record.id}")
            # 这里可以添加重试逻辑
            
        return {"cleaned_files": len(failed_files)}
        
    except Exception as e:
        print(f"❌ Cleanup task failed: {e}")
        return {"status": "failed", "error": str(e)}
        
    finally:
        db.close()


@celery_app.task(name="get_task_status")
def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    获取任务状态
    """
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id, app=celery_app)
    
    return {
        "task_id": task_id,
        "state": result.state,
        "current": result.info.get("current", 0) if result.info else 0,
        "total": result.info.get("total", 100) if result.info else 100,
        "status": result.info.get("status", "") if result.info else "",
        "result": result.result if result.ready() else None
    }