"""
文件验证工具函数 - 白名单验证系统
"""
import os
from typing import List, Tuple, Optional, Set
from pathlib import Path
from app.core.config import settings

# LangChain loaders for validation
from langchain_community.document_loaders import (
    PyPDFLoader, 
    Docx2txtLoader, 
    TextLoader,
    UnstructuredMarkdownLoader
)


class FileValidator:
    """文件验证器 - 基于白名单的文件类型验证"""
    
    # 支持的文档类型（普通文件上传）
    SUPPORTED_DOCUMENT_EXTENSIONS = {
        # 文档类型
        'pdf', 'doc', 'docx', 'txt', 'md',
        
        # 编程语言文件
        'py', 'js', 'html', 'css', 'json', 
        'c', 'cpp', 'java', 'xml',
        
        # 其他文本文件  
        'csv', 'yaml', 'yml', 'sql', 'sh', 
        'bat', 'ini', 'conf', 'log'
    }
    
    # 支持的图片类型（仅临时文件）
    SUPPORTED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    
    # 对应的解析器映射
    DOCUMENT_LOADERS = {
        # 需要专门解析器的格式
        '.pdf': PyPDFLoader,
        '.doc': Docx2txtLoader,
        '.docx': Docx2txtLoader,
        '.md': UnstructuredMarkdownLoader,
        
        # 其他都用 TextLoader
        '.txt': TextLoader,
        '.py': TextLoader,
        '.js': TextLoader,
        '.html': TextLoader,
        '.css': TextLoader,
        '.json': TextLoader,
        '.c': TextLoader,
        '.cpp': TextLoader,
        '.java': TextLoader,
        '.xml': TextLoader,
        '.csv': TextLoader,
        '.yaml': TextLoader,
        '.yml': TextLoader,
        '.sql': TextLoader,
        '.sh': TextLoader,
        '.bat': TextLoader,
        '.ini': TextLoader,
        '.conf': TextLoader,
        '.log': TextLoader
    }
    
    # 图片文件扩展名
    IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    
    @classmethod
    def get_supported_document_extensions(cls) -> List[str]:
        """获取支持的文档扩展名列表"""
        return list(cls.SUPPORTED_DOCUMENT_EXTENSIONS)
    
    @classmethod
    def get_supported_image_extensions(cls) -> List[str]:
        """获取支持的图片扩展名列表"""
        return list(cls.SUPPORTED_IMAGE_EXTENSIONS)
    
    @classmethod
    def is_supported_document(cls, filename: str) -> bool:
        """检查是否为支持的文档格式（普通文件上传）"""
        ext = Path(filename).suffix.lower().lstrip('.')
        return ext in cls.SUPPORTED_DOCUMENT_EXTENSIONS
    
    @classmethod
    def is_supported_image(cls, filename: str) -> bool:
        """检查是否为支持的图片格式（临时文件）"""
        ext = Path(filename).suffix.lower().lstrip('.')
        return ext in cls.SUPPORTED_IMAGE_EXTENSIONS
    
    @classmethod
    def is_supported_for_temporary_upload(cls, filename: str) -> bool:
        """检查是否支持临时文件上传（文档+图片）"""
        return cls.is_supported_document(filename) or cls.is_supported_image(filename)
    
    @classmethod
    def get_file_category(cls, filename: str) -> str:
        """
        获取文件分类
        Returns: 'document' | 'image' | 'unsupported'
        """
        if cls.is_supported_document(filename):
            return 'document'
        elif cls.is_supported_image(filename):
            return 'image'
        else:
            return 'unsupported'
    
    @classmethod
    def validate_for_regular_upload(cls, filename: str) -> Tuple[bool, Optional[str]]:
        """
        验证普通文件上传（仅文档，不包含图片）
        
        Args:
            filename: 文件名
            
        Returns:
            (是否允许, 错误信息)
        """
        if not cls.is_supported_document(filename):
            ext = Path(filename).suffix.lower()
            return False, f"暂时不支持 {ext} 格式的文件。如需支持此格式，请联系管理员。"
        
        return True, None
    
    @classmethod
    def validate_for_temporary_upload(cls, filename: str) -> Tuple[bool, Optional[str]]:
        """
        验证临时文件上传（文档+图片）
        
        Args:
            filename: 文件名
            
        Returns:
            (是否允许, 错误信息)
        """
        if not cls.is_supported_for_temporary_upload(filename):
            ext = Path(filename).suffix.lower()
            return False, f"暂时不支持 {ext} 格式的文件。如需支持此格式，请联系管理员。"
        
        return True, None
    
    @classmethod
    def validate_document_parsing(cls, file_path: str, filename: str) -> Tuple[bool, Optional[str]]:
        """
        验证文档是否可以被解析（仅用于文档类型）
        
        Args:
            file_path: 文件路径
            filename: 文件名
            
        Returns:
            (是否可解析, 错误信息)
        """
        # 先检查是否为支持的文档格式
        if not cls.is_supported_document(filename):
            return False, "不是支持的文档格式"
        
        ext = '.' + Path(filename).suffix.lower().lstrip('.')
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return False, "文件不存在"
        
        # 获取对应的解析器
        loader_class = cls.DOCUMENT_LOADERS.get(ext, TextLoader)
        
        # 尝试解析文件
        try:
            loader = loader_class(file_path)
            documents = loader.load()
            
            if not documents:
                return False, "文件内容为空或无法解析"
            
            # 检查是否有有效内容
            total_content = ''.join(doc.page_content for doc in documents)
            if len(total_content.strip()) == 0:
                return False, "文件内容为空"
            
            # 检查内容长度是否合理（避免过大文件）
            if len(total_content) > 10_000_000:  # 10MB 文本内容
                return False, "文件内容过大"
            
            return True, None
            
        except Exception as e:
            return False, f"您上传的 {Path(filename).name} 文件可能已损坏或格式不正确，无法解析。请检查文件完整性后重新上传。"
    

# 便捷函数
def validate_regular_file_upload(filename: str) -> Tuple[bool, Optional[str]]:
    """验证普通文件上传"""
    return FileValidator.validate_for_regular_upload(filename)


def validate_temporary_file_upload(filename: str) -> Tuple[bool, Optional[str]]:
    """验证临时文件上传"""
    return FileValidator.validate_for_temporary_upload(filename)


def is_parseable_document(file_path: str, filename: str) -> bool:
    """检查文档是否可解析"""
    valid, _ = FileValidator.validate_document_parsing(file_path, filename)
    return valid


def get_supported_document_extensions_string() -> str:
    """获取支持的文档扩展名字符串（用于配置）"""
    extensions = FileValidator.get_supported_document_extensions()
    return ','.join(extensions)


def get_supported_image_extensions_string() -> str:
    """获取支持的图片扩展名字符串（用于配置）"""
    extensions = FileValidator.get_supported_image_extensions()
    return ','.join(extensions)