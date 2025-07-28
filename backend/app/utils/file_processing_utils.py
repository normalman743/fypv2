from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.temporary_file import TemporaryFile
from app.models.physical_file import PhysicalFile
# from app.tasks.cleanup_tasks import cleanup_single_temporary_file
import logging
import os

logger = logging.getLogger(__name__)


class FileProcessingUtils:
    """文件处理工具类，提供文件和临时文件的统一处理方法"""
    
    @staticmethod
    def process_temporary_files(
        db: Session, 
        tokens: List[str], 
        user_id: int
    ) -> Tuple[List[TemporaryFile], List[str]]:
        """
        处理临时文件tokens，返回有效的临时文件和过期信息
        
        Args:
            db: 数据库会话
            tokens: 临时文件token列表
            user_id: 当前用户ID
            
        Returns:
            (valid_temp_files, expired_messages): 有效的临时文件列表和过期文件消息
        """
        valid_temp_files = []
        expired_messages = []
        
        for token in tokens:
            temp_file = db.query(TemporaryFile).filter(
                TemporaryFile.token == token,
                TemporaryFile.user_id == user_id
            ).first()
            
            if not temp_file:
                logger.warning(f"临时文件未找到或无权访问: token={token}, user_id={user_id}")
                continue
                
            if temp_file.is_expired:
                # 记录过期文件信息
                expired_messages.append(
                    f"临时文件 '{temp_file.original_name}' 已过期（过期时间：{temp_file.expires_at}）"
                )
                # 触发异步清理任务（暂时注释掉）
                # cleanup_single_temporary_file.delay(temp_file.id)
                logger.info(f"临时文件已过期: file_id={temp_file.id}")
                continue
                
            valid_temp_files.append(temp_file)
            
        return valid_temp_files, expired_messages
    
    @staticmethod
    def get_temporary_file_contents_for_ai(
        temp_files: List[TemporaryFile], 
        db: Session
    ) -> str:
        """
        获取临时文件内容用于AI处理 - 直接从磁盘读取
        
        Args:
            temp_files: 临时文件列表
            db: 数据库会话
            
        Returns:
            格式化的文件内容字符串
        """
        contents = []
        
        for temp_file in temp_files:
            # 获取物理文件路径
            physical_file = db.query(PhysicalFile).filter(
                PhysicalFile.id == temp_file.physical_file_id
            ).first()
            
            if physical_file:
                try:
                    # 检查文件路径并读取内容
                    logger.info(f"尝试读取文件: {physical_file.storage_path}")
                    if os.path.exists(physical_file.storage_path):
                        with open(physical_file.storage_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content_preview = f.read(2000)  # 读取前2000个字符
                        
                        contents.append(
                            f"文件: {temp_file.original_name}\n"
                            f"类型: 临时文件\n"
                            f"用途: {temp_file.purpose or '未指定'}\n"
                            f"内容:\n{content_preview}\n"
                        )
                    else:
                        logger.error(f"文件不存在: {physical_file.storage_path}")
                        contents.append(f"文件: {temp_file.original_name} (文件不存在: {physical_file.storage_path})\n")
                except Exception as e:
                    logger.error(f"无法读取临时文件内容: {temp_file.original_name}, 路径: {physical_file.storage_path}, 错误: {str(e)}")
                    # 如果无法读取，至少添加文件名
                    contents.append(f"文件: {temp_file.original_name} (读取失败: {str(e)})\n")
        
        return "\n---\n".join(contents) if contents else ""