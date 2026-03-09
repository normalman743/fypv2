# -*- coding: utf-8 -*-
"""
AI Context Utilities - 共享的文件处理和AI上下文构建工具函数。
从 ChatService 和 MessageService 中提取的公共逻辑，消除代码重复。
"""

from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
import os
import logging

from app.models.file import File
from app.models.folder import Folder
from app.models.course import Course
from app.models.temporary_file import TemporaryFile
from app.core.exceptions import BadRequestError, ForbiddenError
from app.utils.image_utils import image_to_base64, get_image_mime_type, is_image_file

logger = logging.getLogger(__name__)


def get_files_from_folders_and_files(
    db: Session,
    file_ids: List[int],
    folder_ids: List[int],
    user_id: int
) -> Tuple[List[File], List[int]]:
    """
    获取文件夹中的文件和直接指定的文件，合并去重。
    
    Args:
        db: 数据库会话
        file_ids: 文件ID列表
        folder_ids: 文件夹ID列表
        user_id: 当前用户ID
        
    Returns:
        (unique_files, unique_file_ids): 去重后的文件列表和ID列表
    """
    all_files = []
    all_file_ids = []
    
    # 处理直接指定的文件
    if file_ids:
        files = db.query(File).filter(File.id.in_(file_ids)).all()
        if len(files) != len(file_ids):
            raise BadRequestError("Some files not found", "FILE_NOT_FOUND")
        all_files.extend(files)
        all_file_ids.extend(file_ids)
    
    # 处理文件夹中的文件
    if folder_ids:
        folders = db.query(Folder).filter(Folder.id.in_(folder_ids)).all()
        if len(folders) != len(folder_ids):
            raise BadRequestError("Some folders not found", "FOLDER_NOT_FOUND")
        
        # 验证文件夹权限
        for folder in folders:
            course = db.query(Course).filter(
                Course.id == folder.course_id,
                Course.user_id == user_id
            ).first()
            if not course:
                raise ForbiddenError("Access denied to some folders")
        
        # 获取文件夹中的文件
        for folder_id in folder_ids:
            folder_files = db.query(File).filter(File.folder_id == folder_id).all()
            all_files.extend(folder_files)
            all_file_ids.extend([f.id for f in folder_files])
    
    # 去重
    unique_files = []
    seen_ids = set()
    
    for file in all_files:
        if file.id not in seen_ids:
            unique_files.append(file)
            seen_ids.add(file.id)
    
    unique_file_ids = list(seen_ids)
    
    # 验证所有文件的权限
    for file in unique_files:
        if file.course_id:
            course = db.query(Course).filter(
                Course.id == file.course_id,
                Course.user_id == user_id
            ).first()
            if not course:
                raise ForbiddenError("Access denied to some files")
    
    return unique_files, unique_file_ids


def extract_file_content(file_path: str, file_ext: str, original_name: str) -> str:
    """
    使用与RAG服务相同的文件解析逻辑提取文件内容。
    
    Args:
        file_path: 文件完整路径
        file_ext: 文件扩展名 (如 '.pdf')
        original_name: 原始文件名
        
    Returns:
        截断后的文件内容文本
    """
    try:
        from langchain_community.document_loaders import (
            PyPDFLoader, 
            Docx2txtLoader, 
            TextLoader,
            UnstructuredMarkdownLoader
        )
        
        specialized_loaders = {
            '.pdf': PyPDFLoader,
            '.docx': Docx2txtLoader,
            '.doc': Docx2txtLoader,
            '.md': UnstructuredMarkdownLoader,
        }
        
        if file_ext in specialized_loaders:
            loader_class = specialized_loaders[file_ext]
            logger.debug(f"使用专门解析器: {loader_class.__name__} for {file_ext}")
        else:
            loader_class = TextLoader
            logger.debug(f"使用通用TextLoader for {file_ext}")
        
        loader = loader_class(file_path)
        documents = loader.load()
        
        full_content = "\n\n".join([doc.page_content for doc in documents])
        
        if len(full_content) > 2000:
            content_preview = full_content[:2000] + "\n\n[内容已截断...]"
        else:
            content_preview = full_content
            
        return content_preview
        
    except Exception as e:
        logger.error(f"使用专门解析器失败 {original_name}: {e}")
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(2000)
        except Exception as fallback_e:
            logger.error(f"回退文本读取也失败 {original_name}: {fallback_e}")
            return f"[无法读取文件内容: {str(fallback_e)}]"


def get_file_contents_for_ai(files: List[File]) -> str:
    """
    获取文件内容用于AI上下文 - 直接从磁盘读取。
    
    Args:
        files: File模型列表
        
    Returns:
        格式化的文件内容字符串
    """
    if not files:
        return ""
    
    context_parts = []
    for file in files:
        try:
            if file.physical_file and file.physical_file.storage_path:
                from app.core.config import settings
                full_path = os.path.join(settings.upload_dir, file.physical_file.storage_path)
                
                if os.path.exists(full_path):
                    file_ext = os.path.splitext(file.original_name)[1].lower()
                    content_preview = extract_file_content(full_path, file_ext, file.original_name)
                    
                    context_parts.append(
                        f"文件: {file.original_name}\n"
                        f"类型: 正式文件\n"
                        f"内容:\n{content_preview}\n"
                    )
                else:
                    if file.is_processed and file.content_preview:
                        context_parts.append(f"文件名: {file.original_name}\n内容预览:\n{file.content_preview}\n")
            else:
                if file.is_processed and file.content_preview:
                    context_parts.append(f"文件名: {file.original_name}\n内容预览:\n{file.content_preview}\n")
        except Exception as e:
            logger.error(f"无法读取文件内容: {file.original_name}, 错误: {str(e)}")
            if file.is_processed and file.content_preview:
                context_parts.append(f"文件名: {file.original_name}\n内容预览:\n{file.content_preview}\n")
    
    return "\n---\n".join(context_parts) if context_parts else ""


def prepare_images_for_ai(temporary_files: List[TemporaryFile]) -> List[Dict[str, Any]]:
    """
    准备图片文件用于AI处理。
    
    Args:
        temporary_files: 临时文件列表
        
    Returns:
        图片数据列表，格式适合AI API调用
    """
    images = []
    image_count = 0
    
    for temp_file in temporary_files:
        if is_image_file(temp_file.original_name):
            image_count += 1
            if temp_file.physical_file and temp_file.physical_file.storage_path:
                storage_path = temp_file.physical_file.storage_path
                
                if not os.path.isabs(storage_path):
                    from app.services.local_file_storage import local_file_storage
                    base_dir = str(local_file_storage.base_dir)
                    
                    if storage_path.startswith('storage/uploads/'):
                        file_path = os.path.join(os.getcwd(), storage_path)
                    else:
                        file_path = os.path.join(base_dir, storage_path)
                else:
                    file_path = storage_path
                
                base64_image = image_to_base64(file_path)
                if base64_image:
                    mime_type = get_image_mime_type(temp_file.original_name)
                    images.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    })
                    logger.info(f"准备图片 {image_count}: {temp_file.original_name} ({mime_type})")
                else:
                    logger.warning(f"图片 {image_count}: {temp_file.original_name} 转换base64失败")
            else:
                logger.warning(f"图片 {image_count}: {temp_file.original_name} 物理文件路径缺失")
    
    if image_count > 0:
        logger.info(f"图片处理总结: 发现 {image_count} 个图片文件，成功准备 {len(images)} 个")
    
    return images
