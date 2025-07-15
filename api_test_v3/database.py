# -*- coding: utf-8 -*-
"""
数据库操作模块
V3.0 模块化版本
"""

import mysql.connector
import shutil
import os
from typing import List, Dict, Any, Optional
from config import db_config, test_config, STORAGE_DIR, CHROMA_DIR
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def connect(self) -> bool:
        """连接数据库"""
        try:
            self.connection = mysql.connector.connect(
                host=db_config.host,
                user=db_config.user,
                password=db_config.password,
                database=db_config.database,
                port=db_config.port
            )
            self.cursor = self.connection.cursor()
            logger.info("✅ 数据库连接成功")
            return True
        except mysql.connector.Error as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("🔌 数据库连接已断开")
    
    def execute_query(self, query: str, params: tuple = None) -> bool:
        """执行SQL查询"""
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            return True
        except mysql.connector.Error as e:
            logger.error(f"❌ SQL执行失败: {e}")
            self.connection.rollback()
            return False
    
    def fetch_all(self, query: str, params: tuple = None) -> List[Dict]:
        """获取查询结果"""
        try:
            self.cursor.execute(query, params)
            columns = [desc[0] for desc in self.cursor.description]
            rows = self.cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except mysql.connector.Error as e:
            logger.error(f"❌ 查询失败: {e}")
            return []
    
    def get_table_dependencies(self) -> List[str]:
        """获取表删除的安全顺序（基于外键依赖）"""
        # 基于数据库分析文档的依赖层级
        return [
            # Level 5 - 最深层依赖
            "document_chunks",
            "file_access_logs", 
            "file_shares",
            "message_file_references",
            "message_rag_sources",
            
            # Level 4
            "file_group_members",
            "files", 
            "messages",
            
            # Level 3
            "chats",
            "file_groups", 
            "folders",
            
            # Level 2
            "audit_logs",
            "courses", 
            "invite_codes",
            "permissions",
            "subject_roles",
            "system_config",
            
            # Level 1
            "users",
            
            # Level 0 - 独立表
            "physical_files",
            "roles",
            "semesters"
        ]
    
    def clear_all_tables(self) -> bool:
        """清空所有表数据"""
        logger.info("🧹 开始清空所有表数据...")
        
        # 禁用外键检查
        if not self.execute_query("SET FOREIGN_KEY_CHECKS = 0"):
            return False
        
        tables = self.get_table_dependencies()
        success_count = 0
        
        for table in tables:
            if table == "document_chunks_backup_20250714":
                continue  # 跳过备份表
                
            logger.info(f"清空表: {table}")
            if self.execute_query(f"DELETE FROM {table}"):
                success_count += 1
            else:
                logger.warning(f"⚠️ 清空表 {table} 失败")
        
        # 重新启用外键检查
        self.execute_query("SET FOREIGN_KEY_CHECKS = 1")
        
        logger.info(f"✅ 成功清空 {success_count}/{len(tables)} 个表")
        return success_count > 0
    
    def reset_auto_increment(self) -> bool:
        """重置所有表的自增ID"""
        logger.info("🔄 重置自增ID...")
        
        tables_with_auto_increment = [
            "audit_logs", "chats", "courses", "document_chunks", "file_access_logs",
            "file_group_members", "file_groups", "file_shares", "files", "folders",
            "invite_codes", "message_file_references", "message_rag_sources", 
            "messages", "permissions", "physical_files", "roles", "semesters",
            "subject_roles", "system_config", "users"
        ]
        
        success_count = 0
        for table in tables_with_auto_increment:
            if self.execute_query(f"ALTER TABLE {table} AUTO_INCREMENT = 1"):
                success_count += 1
        
        logger.info(f"✅ 成功重置 {success_count}/{len(tables_with_auto_increment)} 个表的自增ID")
        return success_count > 0
    
    def create_default_data(self) -> bool:
        """创建默认数据"""
        logger.info("📝 创建默认数据...")
        
        # 创建默认学期
        semester_query = """
        INSERT INTO semesters (name, code, is_active) 
        VALUES ('2024-2025学年第一学期', '2024-1', 1)
        """
        
        if not self.execute_query(semester_query):
            logger.error("❌ 创建默认学期失败")
            return False
        
        # 创建默认用户
        users_data = [
            ("admin", "admin@test.com", "admin123456", "admin", 100.00),
            ("user", "user@test.com", "user123456", "user", 50.00)
        ]
        
        for username, email, password, role, balance in users_data:
            # 这里使用明文密码，实际应用中应该使用哈希
            user_query = """
            INSERT INTO users (username, email, password_hash, role, balance) 
            VALUES (%s, %s, %s, %s, %s)
            """
            if not self.execute_query(user_query, (username, email, password, role, balance)):
                logger.error(f"❌ 创建用户 {username} 失败")
                return False
        
        # 创建默认邀请码
        for invite_code in test_config.default_invite_codes:
            invite_query = """
            INSERT INTO invite_codes (code, description, is_active, created_by) 
            VALUES (%s, %s, %s, 1)
            """
            if not self.execute_query(invite_query, (
                invite_code["code"], 
                invite_code["description"], 
                invite_code["is_active"]
            )):
                logger.error(f"❌ 创建邀请码 {invite_code['code']} 失败")
                return False
        
        logger.info("✅ 默认数据创建完成")
        return True

def clear_storage_directory():
    """清空本地存储目录"""
    logger.info("🗂️ 清空本地存储目录...")
    
    if os.path.exists(STORAGE_DIR):
        try:
            shutil.rmtree(STORAGE_DIR)
            os.makedirs(STORAGE_DIR, exist_ok=True)
            logger.info("✅ 本地存储目录已清空")
            return True
        except Exception as e:
            logger.error(f"❌ 清空存储目录失败: {e}")
            return False
    else:
        logger.info("ℹ️ 存储目录不存在，创建新目录")
        os.makedirs(STORAGE_DIR, exist_ok=True)
        return True

def clear_chroma_directory():
    """清空向量数据库目录"""
    logger.info("🔍 清空向量数据库目录...")
    
    if os.path.exists(CHROMA_DIR):
        try:
            shutil.rmtree(CHROMA_DIR)
            os.makedirs(CHROMA_DIR, exist_ok=True)
            logger.info("✅ 向量数据库目录已清空")
            return True
        except Exception as e:
            logger.error(f"❌ 清空向量数据库目录失败: {e}")
            return False
    else:
        logger.info("ℹ️ 向量数据库目录不存在，创建新目录")
        os.makedirs(CHROMA_DIR, exist_ok=True)
        return True

def full_reset() -> bool:
    """完整重置系统"""
    logger.info("🔄 开始完整重置系统...")
    
    # 数据库重置
    db_manager = DatabaseManager()
    if not db_manager.connect():
        return False
    
    try:
        # 清空数据库
        if not db_manager.clear_all_tables():
            logger.error("❌ 数据库清空失败")
            return False
        
        # 重置自增ID
        if not db_manager.reset_auto_increment():
            logger.error("❌ 重置自增ID失败")
            return False
        
        # 创建默认数据
        if not db_manager.create_default_data():
            logger.error("❌ 创建默认数据失败")
            return False
        
        # 清空存储目录
        if not clear_storage_directory():
            logger.error("❌ 清空存储目录失败")
            return False
        
        # 清空向量数据库
        if not clear_chroma_directory():
            logger.error("❌ 清空向量数据库失败")
            return False
        
        logger.info("✅ 系统重置完成")
        return True
        
    finally:
        db_manager.disconnect()

if __name__ == "__main__":
    # 测试重置功能
    full_reset()