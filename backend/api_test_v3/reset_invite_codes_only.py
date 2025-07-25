#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仅重置邀请码数据工具
只重置 invite_codes 表，不影响其他数据
"""

import sys
import os
import time
from datetime import datetime, timedelta
from database import DatabaseManager
from config import test_config

def reset_invite_codes_only():
    """仅重置邀请码数据"""
    print("🎟️  开始重置邀请码数据...")
    
    db_manager = DatabaseManager()
    if not db_manager.connect():
        print("❌ 数据库连接失败")
        return False
    
    try:
        # 1. 清空 invite_codes 表
        print("🗑️  清空邀请码表...")
        if not db_manager.execute_query("DELETE FROM invite_codes"):
            print("❌ 清空邀请码表失败")
            return False
        
        # 2. 重置 invite_codes 表的自增ID
        print("🔄 重置邀请码表自增ID...")
        if not db_manager.execute_query("ALTER TABLE invite_codes AUTO_INCREMENT = 1"):
            print("❌ 重置邀请码表自增ID失败")
            return False
        
        # 3. 创建默认邀请码
        print("🎫 创建默认邀请码...")
        future_date = datetime.now() + timedelta(days=365)  # 设置1年后过期
        
        for invite_code in test_config.default_invite_codes:
            invite_query = """
            INSERT INTO invite_codes (code, description, is_active, expires_at, created_by) 
            VALUES (%s, %s, %s, %s, 1)
            """
            if not db_manager.execute_query(invite_query, (
                invite_code["code"], 
                invite_code["description"], 
                invite_code["is_active"],
                future_date
            )):
                print(f"❌ 创建邀请码 {invite_code['code']} 失败")
                return False
            
            print(f"✅ 创建邀请码: {invite_code['code']} - {invite_code['description']}")
        
        print(f"✅ 邀请码重置完成！")
        print(f"   - 总邀请码数: {len(test_config.default_invite_codes)}")
        return True
        
    except Exception as e:
        print(f"❌ 重置邀请码数据时出错: {e}")
        return False
    finally:
        db_manager.disconnect()

def verify_invite_codes():
    """验证邀请码重置结果"""
    print("\n🔍 验证邀请码重置结果...")
    
    db_manager = DatabaseManager()
    
    if db_manager.connect():
        try:
            # 查询所有邀请码
            invite_codes = db_manager.fetch_all("""
                SELECT code, description, is_active, is_used, expires_at, 
                       created_by, used_by, used_at
                FROM invite_codes 
                ORDER BY id
            """)
            
            print(f"\n📊 数据库中的邀请码:")
            print("-" * 80)
            
            active_count = 0
            used_count = 0
            
            for code in invite_codes:
                # 状态图标
                status_icon = "✅" if code["is_active"] else "❌"
                used_icon = "🔒" if code["is_used"] else "🔓"
                
                print(f"{status_icon} {used_icon} {code['code']} - {code['description']}")
                print(f"     有效期至: {code['expires_at']}")
                
                if code["is_used"]:
                    print(f"     已被用户ID {code['used_by']} 使用于 {code['used_at']}")
                    used_count += 1
                
                if code["is_active"]:
                    active_count += 1
                
                print()
            
            print("-" * 80)
            print(f"📈 统计:")
            print(f"  总邀请码数: {len(invite_codes)}")
            print(f"  有效邀请码: {active_count}")
            print(f"  已使用邀请码: {used_count}")
            print(f"  可用邀请码: {len(invite_codes) - used_count}")
            
        finally:
            db_manager.disconnect()
    
    return True

def main():
    """主函数"""
    print("🎟️  仅重置邀请码数据工具")
    print("=" * 50)
    
    # 显示操作说明
    print("⚠️  此操作将:")
    print("   - 删除所有邀请码数据")
    print("   - 重新创建配置文件中的默认邀请码")
    print("   - 不影响用户、课程、文件等其他数据")
    print("\n🚀 开始执行（无需确认）...")
    
    start_time = time.time()
    
    # 执行重置
    if not reset_invite_codes_only():
        print("❌ 邀请码数据重置失败")
        sys.exit(1)
    
    # 验证结果
    verify_invite_codes()
    
    end_time = time.time()
    print(f"\n⏱️ 总耗时: {end_time - start_time:.2f}秒")
    print("🎉 邀请码重置完成！")

if __name__ == "__main__":
    main()