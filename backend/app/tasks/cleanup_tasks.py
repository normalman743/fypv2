from celery import shared_task
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.models.temporary_file import TemporaryFile
from app.models.physical_file import PhysicalFile
from app.services.file_service import FileService
import logging
import os

logger = logging.getLogger(__name__)

@shared_task
def cleanup_expired_temporary_files():
    """
    定时任务：清理过期的临时文件
    每小时运行一次，删除已过期的临时文件
    """
    db = SessionLocal()
    try:
        # 查找所有过期的临时文件
        expired_files = db.query(TemporaryFile).filter(
            TemporaryFile.expires_at < datetime.utcnow()
        ).all()
        
        deleted_count = 0
        for temp_file in expired_files:
            try:
                # 获取物理文件
                physical_file = temp_file.physical_file
                
                # 删除临时文件记录
                db.delete(temp_file)
                
                # 减少物理文件引用计数
                physical_file.reference_count -= 1
                
                # 如果引用计数为0，删除物理文件
                if physical_file.reference_count <= 0:
                    # 删除磁盘上的文件
                    if os.path.exists(physical_file.storage_path):
                        os.remove(physical_file.storage_path)
                    # 删除物理文件记录
                    db.delete(physical_file)
                
                deleted_count += 1
                
            except Exception as e:
                logger.error(f"Failed to delete temporary file {temp_file.id}: {str(e)}")
                continue
        
        db.commit()
        logger.info(f"Cleaned up {deleted_count} expired temporary files")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error in cleanup_expired_temporary_files: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

@shared_task
def cleanup_single_temporary_file(temp_file_id: int):
    """
    清理单个临时文件（可用于立即删除）
    """
    db = SessionLocal()
    try:
        temp_file = db.query(TemporaryFile).filter(TemporaryFile.id == temp_file_id).first()
        if not temp_file:
            logger.warning(f"Temporary file {temp_file_id} not found")
            return False
        
        # 获取物理文件
        physical_file = temp_file.physical_file
        
        # 删除临时文件记录
        db.delete(temp_file)
        
        # 减少物理文件引用计数
        physical_file.reference_count -= 1
        
        # 如果引用计数为0，删除物理文件
        if physical_file.reference_count <= 0:
            # 删除磁盘上的文件
            if os.path.exists(physical_file.storage_path):
                os.remove(physical_file.storage_path)
            # 删除物理文件记录
            db.delete(physical_file)
        
        db.commit()
        logger.info(f"Successfully deleted temporary file {temp_file_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting temporary file {temp_file_id}: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()