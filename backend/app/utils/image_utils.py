"""
图片处理工具函数
"""
import base64
import os
from typing import Optional


def image_to_base64(file_path: str) -> Optional[str]:
    """
    将图片文件转换为base64编码
    
    Args:
        file_path: 图片文件路径
        
    Returns:
        base64编码的字符串，如果失败返回None
    """
    try:
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_string
    except Exception as e:
        print(f"Error encoding image to base64: {e}")
        return None


def get_image_mime_type(filename: str) -> str:
    """
    根据文件扩展名获取MIME类型
    
    Args:
        filename: 文件名
        
    Returns:
        MIME类型字符串
    """
    ext = filename.lower().split('.')[-1]
    mime_types = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'webp': 'image/webp'
    }
    return mime_types.get(ext, 'image/jpeg')


def is_image_file(filename: str) -> bool:
    """
    检查文件是否为支持的图片格式
    
    Args:
        filename: 文件名
        
    Returns:
        是否为图片文件
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    ext = os.path.splitext(filename.lower())[1]
    return ext in image_extensions