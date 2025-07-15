#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
课程文件夹创建测试
使用前请先: source venv/bin/activate
运行: python api_test_v3/test_course_folders.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import APIClient, print_response, extract_token_from_response
from config import test_config
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_user_token(user_type="user"):
    """获取用户token"""
    client = APIClient()
    user_data = test_config.default_users[user_type]
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    
    if login_response.status_code == 200:
        token = extract_token_from_response(login_response)
        if token:
            return token
    return None

def get_admin_token():
    """获取管理员token"""
    return get_user_token("admin")

def create_test_course():
    """创建测试课程"""
    client = APIClient()
    
    # 获取管理员权限
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ 无法获取管理员token")
        return None
    
    client.set_auth_token(admin_token)
    
    # 获取第一个学期
    semesters_response = client.get("/api/v1/semesters")
    if semesters_response.status_code != 200:
        print("❌ 无法获取学期列表")
        return None
    
    semesters_data = semesters_response.json()
    if not semesters_data.get("success") or not semesters_data["data"].get("semesters"):
        print("❌ 没有找到学期")
        return None
    
    semester_id = semesters_data["data"]["semesters"][0]["id"]
    
    # 创建课程
    course_data = {
        "name": "文件夹测试课程",
        "code": "FOLDER-TEST",
        "description": "用于测试课程文件夹功能",
        "semester_id": semester_id
    }
    
    course_response = client.post("/api/v1/courses", json=course_data)
    if course_response.status_code == 200:
        result = course_response.json()
        if result.get("success"):
            return result["data"]["course"]["id"]
    
    return None

def test_course_folders():
    """测试课程文件夹功能"""
    print("📁 课程文件夹测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 1. 创建测试课程
    print("\n1️⃣ 创建测试课程")
    course_id = create_test_course()
    if not course_id:
        print("❌ 无法创建测试课程")
        return
    
    print(f"✅ 创建课程成功，ID: {course_id}")
    
    # 2. 获取课程文件夹（应该为空）
    print(f"\n2️⃣ 获取课程文件夹 (Course ID: {course_id})")
    folders_response = client.get(f"/api/v1/courses/{course_id}/folders")
    print_response(folders_response, "获取课程文件夹")
    
    # 3. 在课程中创建文件夹 (使用课程专用API)
    print(f"\n3️⃣ 在课程中创建文件夹 (Course ID: {course_id})")
    folder_data = {
        "name": "课程讲义",
        "folder_type": "lecture"
    }
    
    create_folder_response = client.post(f"/api/v1/courses/{course_id}/folders", json=folder_data)
    print_response(create_folder_response, "创建课程文件夹")
    
    folder_id = None
    if create_folder_response.status_code == 200:
        result = create_folder_response.json()
        if result.get("success"):
            folder_id = result["data"]["folder"]["id"]
            print(f"✅ 创建文件夹成功，ID: {folder_id}")
    
    # 4. 再次获取课程文件夹（应该有一个）
    print(f"\n4️⃣ 再次获取课程文件夹")
    folders_response2 = client.get(f"/api/v1/courses/{course_id}/folders")
    print_response(folders_response2, "获取课程文件夹")
    
    # 5. 创建更多类型的文件夹
    print(f"\n5️⃣ 创建更多类型的文件夹")
    folder_types = [
        {"name": "作业", "folder_type": "assignment"},
        {"name": "实验", "folder_type": "lab"},
        {"name": "考试", "folder_type": "exam"}
    ]
    
    for folder_info in folder_types:
        response = client.post(f"/api/v1/courses/{course_id}/folders", json=folder_info)
        print_response(response, f"创建{folder_info['name']}文件夹")
    
    # 6. 最终获取所有课程文件夹
    print(f"\n6️⃣ 获取所有课程文件夹")
    final_folders_response = client.get(f"/api/v1/courses/{course_id}/folders")
    print_response(final_folders_response, "获取所有课程文件夹")
    
    # 7. 测试通用文件夹API创建课程文件夹
    print(f"\n7️⃣ 使用通用API创建课程文件夹")
    general_folder_data = {
        "name": "通用API创建的文件夹",
        "description": "使用通用文件夹API创建的课程文件夹",
        "scope": "course",
        "course_id": course_id
    }
    
    general_folder_response = client.post("/api/v1/folders", json=general_folder_data)
    print_response(general_folder_response, "通用API创建文件夹")

if __name__ == "__main__":
    print("⚠️  请确保已执行: source venv/bin/activate")
    print("⚠️  请确保服务正在运行: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("⚠️  此测试需要管理员权限创建课程")
    input("按回车键继续...")
    
    try:
        test_course_folders()
        print(f"\n🎉 课程文件夹测试完成！")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()