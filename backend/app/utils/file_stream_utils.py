#!/usr/bin/env python3
"""
文件流式处理工具
用于解决大文件上传时的内存溢出问题
"""

import hashlib
from typing import Tuple, BinaryIO


def get_file_size_and_hash(file_obj: BinaryIO, chunk_size: int = 8192) -> Tuple[int, str]:
    """
    分块读取文件，同时计算大小和SHA256哈希值
    
    这个函数避免了一次性将整个文件加载到内存中，
    而是通过分块读取的方式处理文件，大大降低内存占用。
    
    Args:
        file_obj: 文件对象（支持read()方法）
        chunk_size: 每次读取的块大小（字节），默认8KB
        
    Returns:
        (file_size, file_hash): 文件大小（字节）和SHA256哈希值
        
    Usage:
        with open("large_file.pdf", "rb") as f:
            size, hash_value = get_file_size_and_hash(f)
            
        # 或用于UploadFile
        size, hash_value = get_file_size_and_hash(upload_file.file)
    """
    hasher = hashlib.sha256()
    size = 0
    
    # 确保从文件开头开始读取
    file_obj.seek(0)
    
    # 分块读取文件
    while True:
        chunk = file_obj.read(chunk_size)
        if not chunk:
            break
        size += len(chunk)
        hasher.update(chunk)
    
    # 重置文件指针到开头，以便后续操作
    file_obj.seek(0)
    
    return size, hasher.hexdigest()


def check_file_size_limit(file_obj: BinaryIO, max_size: int, chunk_size: int = 8192) -> Tuple[bool, int]:
    """
    检查文件大小是否超过限制，不读取整个文件到内存
    
    对于大文件，这个函数会在检测到超过限制时立即停止读取，
    避免不必要的内存消耗。
    
    Args:
        file_obj: 文件对象
        max_size: 最大允许大小（字节）
        chunk_size: 检查时的块大小（字节）
        
    Returns:
        (is_valid, actual_size): 是否在限制内，实际文件大小
        如果超过限制，actual_size可能是部分大小
    """
    file_obj.seek(0)
    total_size = 0
    
    while True:
        chunk = file_obj.read(chunk_size)
        if not chunk:
            break
            
        total_size += len(chunk)
        
        # 如果超过限制，立即停止并返回
        if total_size > max_size:
            file_obj.seek(0)  # 重置文件指针
            return False, total_size
    
    file_obj.seek(0)  # 重置文件指针
    return True, total_size


def safe_file_hash(file_path: str, chunk_size: int = 8192) -> str:
    """
    安全地计算文件哈希值（从磁盘文件）
    
    Args:
        file_path: 磁盘文件路径
        chunk_size: 读取块大小
        
    Returns:
        SHA256哈希值
        
    Raises:
        FileNotFoundError: 文件不存在
        IOError: 文件读取失败
    """
    hasher = hashlib.sha256()
    
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)
    
    return hasher.hexdigest()