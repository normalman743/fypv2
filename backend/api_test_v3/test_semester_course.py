#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学期与课程管理测试 - 基于api_semester_course.md文档
使用前请先: source venv/bin/activate
运行: python api_test_v3/test_semester_course.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import APIClient, print_response, extract_token_from_response
from config import test_config
import logging
from datetime import datetime, timedelta

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

def test_semester_management():
    """测试学期管理 - 基于api_semester_course.md"""
    print("📅 学期管理测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 1. 获取学期列表 - GET /api/v1/semesters (无需认证)
    print("\n1️⃣ 获取学期列表")
    semesters_response = client.get("/api/v1/semesters")
    print_response(semesters_response, "获取学期列表")
    
    # 获取管理员权限进行管理操作
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ 无法获取管理员token，跳过管理员测试")
        return None
    
    client.set_auth_token(admin_token)
    
    # 2. 创建学期 - POST /api/v1/semesters (admin)
    print("\n2️⃣ 创建学期")
    future_start = datetime.now() + timedelta(days=30)
    future_end = future_start + timedelta(days=120)
    
    create_semester_data = {
        "name": "2025测试学期",
        "code": "2025TEST",
        "start_date": future_start.isoformat() + "Z",
        "end_date": future_end.isoformat() + "Z"
    }
    
    create_response = client.post("/api/v1/semesters", json=create_semester_data)
    print_response(create_response, "创建学期")
    
    semester_id = None
    if create_response.status_code == 200:
        result = create_response.json()
        if result.get("success"):
            semester_id = result["data"]["semester"]["id"]
            print(f"✅ 创建学期成功，ID: {semester_id}")
    
    # 3. 获取学期详情 - GET /api/v1/semesters/{id}
    if semester_id:
        print(f"\n3️⃣ 获取学期详情 (ID: {semester_id})")
        detail_response = client.get(f"/api/v1/semesters/{semester_id}")
        print_response(detail_response, "获取学期详情")
    
    # 4. 更新学期 - PUT /api/v1/semesters/{id} (admin)
    if semester_id:
        print(f"\n4️⃣ 更新学期 (ID: {semester_id})")
        update_data = {
            "name": "2025测试学期-更新",
            "start_date": future_start.isoformat() + "Z",
            "end_date": future_end.isoformat() + "Z",
            "is_active": True
        }
        
        update_response = client.put(f"/api/v1/semesters/{semester_id}", json=update_data)
        print_response(update_response, "更新学期")
    
    return semester_id

def test_course_management(semester_id=None):
    """测试课程管理 - 基于api_semester_course.md"""
    print("\n📚 课程管理测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限（课程列表可能需要认证）
    user_token = get_user_token("user")
    if user_token:
        client.set_auth_token(user_token)
    
    # 1. 获取课程列表 - GET /api/v1/courses
    print("\n1️⃣ 获取课程列表")
    courses_response = client.get("/api/v1/courses")
    print_response(courses_response, "获取课程列表")
    
    # 按学期筛选课程
    if semester_id:
        print(f"\n1.1️⃣ 按学期筛选课程 (学期ID: {semester_id})")
        filtered_response = client.get("/api/v1/courses", params={"semester_id": semester_id})
        print_response(filtered_response, "按学期筛选课程")
    
    # 获取管理员权限进行课程创建
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ 无法获取管理员token，跳过课程创建测试")
        return None
    
    client.set_auth_token(admin_token)
    
    # 2. 创建课程 - POST /api/v1/courses
    print("\n2️⃣ 创建课程")
    create_course_data = {
        "name": "测试课程",
        "code": "TEST101",
        "description": "这是一个测试课程",
        "semester_id": semester_id or 1  # 使用创建的学期ID或默认值
    }
    
    create_course_response = client.post("/api/v1/courses", json=create_course_data)
    print_response(create_course_response, "创建课程")
    
    course_id = None
    if create_course_response.status_code == 200:
        result = create_course_response.json()
        if result.get("success"):
            course_id = result["data"]["course"]["id"]
            print(f"✅ 创建课程成功，ID: {course_id}")
    
    # 3. 获取课程详情 - GET /api/v1/courses/{id}
    if course_id:
        print(f"\n3️⃣ 获取课程详情 (ID: {course_id})")
        course_detail_response = client.get(f"/api/v1/courses/{course_id}")
        print_response(course_detail_response, "获取课程详情")
    
    # 4. 更新课程 - PUT /api/v1/courses/{id}
    if course_id:
        print(f"\n4️⃣ 更新课程 (ID: {course_id})")
        update_course_data = {
            "name": "测试课程-更新",
            "description": "这是一个更新后的测试课程"
        }
        
        update_course_response = client.put(f"/api/v1/courses/{course_id}", json=update_course_data)
        print_response(update_course_response, "更新课程")
    
    return course_id

def test_semester_course_relationship(semester_id=None):
    """测试学期课程关联 - 基于api_semester_course.md"""
    print("\n🔗 学期课程关联测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if user_token:
        client.set_auth_token(user_token)
    
    # 获取学期下的课程 - GET /api/v1/semesters/{id}/courses
    if semester_id:
        print(f"\n1️⃣ 获取学期下的课程 (学期ID: {semester_id})")
        semester_courses_response = client.get(f"/api/v1/semesters/{semester_id}/courses")
        print_response(semester_courses_response, "获取学期下的课程")
    else:
        print("\n❌ 没有可用的学期ID，跳过学期课程关联测试")

def test_course_folders(course_id=None):
    """测试课程文件夹功能 - 基于api_folder_file.md中的课程文件夹部分"""
    print("\n📁 课程文件夹测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取用户权限
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    if not course_id:
        # 如果没有课程ID，尝试获取一个
        courses_response = client.get("/api/v1/courses")
        if courses_response.status_code == 200:
            result = courses_response.json()
            if result.get("success") and result["data"]["courses"]:
                course_id = result["data"]["courses"][0]["id"]
                print(f"✅ 使用现有课程ID: {course_id}")
    
    if course_id:
        # 获取课程文件夹 - GET /api/v1/courses/{id}/folders
        print(f"\n1️⃣ 获取课程文件夹 (课程ID: {course_id})")
        folders_response = client.get(f"/api/v1/courses/{course_id}/folders")
        print_response(folders_response, "获取课程文件夹")
        
        # 创建课程文件夹 - POST /api/v1/courses/{id}/folders
        print(f"\n2️⃣ 创建课程文件夹 (课程ID: {course_id})")
        folder_data = {
            "name": "测试文件夹",
            "folder_type": "assignment"
        }
        
        create_folder_response = client.post(f"/api/v1/courses/{course_id}/folders", json=folder_data)
        print_response(create_folder_response, "创建课程文件夹")
    else:
        print("❌ 没有可用的课程ID，跳过课程文件夹测试")

def test_deletion_operations(semester_id=None, course_id=None):
    """测试删除操作 - 基于api_semester_course.md"""
    print("\n🗑️ 删除操作测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取管理员权限
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ 无法获取管理员token，跳过删除测试")
        return
    
    client.set_auth_token(admin_token)
    
    # 删除课程 - DELETE /api/v1/courses/{id}
    if course_id:
        print(f"\n1️⃣ 删除课程 (ID: {course_id})")
        delete_course_response = client.delete(f"/api/v1/courses/{course_id}")
        print_response(delete_course_response, "删除课程")
    
    # 删除学期 - DELETE /api/v1/semesters/{id}
    if semester_id:
        print(f"\n2️⃣ 删除学期 (ID: {semester_id})")
        delete_semester_response = client.delete(f"/api/v1/semesters/{semester_id}")
        print_response(delete_semester_response, "删除学期")

if __name__ == "__main__":
    print("⚠️  请确保已执行: source venv/bin/activate")
    print("⚠️  请确保服务正在运行: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("📋 基于 api_semester_course.md 文档的测试")
    input("按回车键继续...")
    
    try:
        # 测试学期管理
        semester_id = test_semester_management()
        
        # 测试课程管理
        course_id = test_course_management(semester_id)
        
        # 测试学期课程关联
        test_semester_course_relationship(semester_id)
        
        # 测试课程文件夹
        test_course_folders(course_id)
        
        # 测试删除操作
        test_deletion_operations(semester_id, course_id)
        
        print(f"\n🎉 学期与课程管理测试完成！")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()