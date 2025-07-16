#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
课程文件夹测试 - 已整合到test_semester_course.py
使用前请先: source venv/bin/activate
运行: python api_test_v3/test_semester_course.py (推荐)
或: python api_test_v3/test_course_folders.py (独立运行)
"""

print("⚠️  课程文件夹测试已整合到 test_semester_course.py")
print("   请运行: python api_test_v3/test_semester_course.py")
print("   以获得完整的学期与课程管理测试体验")

# 如果用户坚持运行此文件，提供基本的课程文件夹测试
if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # 导入test_semester_course中的课程文件夹测试函数
    try:
        from test_semester_course import test_course_folders, get_user_token
        
        print("\n运行独立的课程文件夹测试...")
        print("=" * 50)
        
        test_course_folders()
        
        print(f"\n🎉 课程文件夹测试完成！")
        print("💡 建议运行完整测试: python api_test_v3/test_semester_course.py")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        print("💡 请尝试运行: python api_test_v3/test_semester_course.py")