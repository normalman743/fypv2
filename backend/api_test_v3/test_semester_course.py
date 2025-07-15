#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学期和课程管理测试
使用前请先: source venv/bin/activate
运行: python api_test_v3/test_semester_course.py
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

def get_admin_token():
    """获取管理员token"""
    client = APIClient()
    admin_data = test_config.default_users["admin"]
    
    login_response = client.post("/api/v1/auth/login", json={
        "username": admin_data["username"],
        "password": admin_data["password"]
    })
    
    if login_response.status_code == 200:
        token = extract_token_from_response(login_response)
        if token:
            return token
    return None

def test_semester_management():
    """测试学期管理功能"""
    print("📅 学期管理测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取管理员权限
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ 无法获取管理员token，跳过测试")
        return
    
    client.set_auth_token(admin_token)
    
    # 1. 获取所有学期
    print("\n1️⃣ 获取所有学期")
    semesters_response = client.get("/api/v1/semesters")
    print_response(semesters_response, "获取学期列表")
    
    semester_id = None
    if semesters_response.status_code == 200:
        semesters_data = semesters_response.json()
        if semesters_data.get("success") and semesters_data["data"].get("semesters"):
            semester_id = semesters_data["data"]["semesters"][0]["id"]
            print(f"✅ 找到学期ID: {semester_id}")
    
    # 2. 创建新学期
    print("\n2️⃣ 创建新学期")
    new_semester_data = {
        "name": "2024-2025学年第二学期",
        "code": "2024-2",
        "is_active": True
    }
    
    create_semester_response = client.post("/api/v1/semesters", json=new_semester_data)
    print_response(create_semester_response, "创建学期")
    
    new_semester_id = None
    if create_semester_response.status_code == 200:
        result = create_semester_response.json()
        if result.get("success"):
            new_semester_id = result["data"]["semester"]["id"]
            print(f"✅ 创建学期成功，ID: {new_semester_id}")
    
    # 3. 获取特定学期信息
    if new_semester_id:
        print(f"\n3️⃣ 获取学期信息 (ID: {new_semester_id})")
        semester_detail_response = client.get(f"/api/v1/semesters/{new_semester_id}")
        print_response(semester_detail_response, "学期详情")
    
    # 4. 更新学期信息
    if new_semester_id:
        print(f"\n4️⃣ 更新学期信息")
        update_data = {
            "name": "2024-2025学年第二学期（更新）",
            "is_active": False
        }
        update_response = client.put(f"/api/v1/semesters/{new_semester_id}", json=update_data)
        print_response(update_response, "更新学期")
    
    return semester_id, new_semester_id

def test_course_management():
    """测试课程管理功能"""
    print("\n📚 课程管理测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取管理员权限
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ 无法获取管理员token，跳过测试")
        return
    
    client.set_auth_token(admin_token)
    
    # 获取学期ID
    semester_id, _ = test_semester_management()
    if not semester_id:
        print("❌ 无法获取学期ID，跳过课程测试")
        return
    
    # 1. 获取所有课程
    print("\n1️⃣ 获取所有课程")
    courses_response = client.get("/api/v1/courses")
    print_response(courses_response, "获取课程列表")
    
    # 2. 创建新课程
    print("\n2️⃣ 创建新课程")
    new_course_data = {
        "name": "软件工程",
        "code": "CS301",
        "description": "软件工程基础课程",
        "semester_id": semester_id
    }
    
    create_course_response = client.post("/api/v1/courses", json=new_course_data)
    print_response(create_course_response, "创建课程")
    
    course_id = None
    if create_course_response.status_code == 200:
        result = create_course_response.json()
        if result.get("success"):
            course_id = result["data"]["course"]["id"]
            print(f"✅ 创建课程成功，ID: {course_id}")
    
    # 3. 获取特定课程信息
    if course_id:
        print(f"\n3️⃣ 获取课程信息 (ID: {course_id})")
        course_detail_response = client.get(f"/api/v1/courses/{course_id}")
        print_response(course_detail_response, "课程详情")
    
    # 4. 更新课程信息
    if course_id:
        print(f"\n4️⃣ 更新课程信息")
        update_data = {
            "name": "高级软件工程",
            "description": "高级软件工程课程（更新）"
        }
        update_response = client.put(f"/api/v1/courses/{course_id}", json=update_data)
        print_response(update_response, "更新课程")
    
    # 5. 获取课程的文件夹
    if course_id:
        print(f"\n5️⃣ 获取课程文件夹")
        folders_response = client.get(f"/api/v1/courses/{course_id}/folders")
        print_response(folders_response, "课程文件夹")
    
    # 6. 在课程中创建文件夹
    if course_id:
        print(f"\n6️⃣ 在课程中创建文件夹")
        folder_data = {
            "name": "课程资料",
            "description": "存放课程相关资料",
            "course_id": course_id
        }
        create_folder_response = client.post("/api/v1/folders", json=folder_data)
        print_response(create_folder_response, "创建文件夹")
    
    return course_id

def test_semester_course_relationship():
    """测试学期课程关系"""
    print("\n🔗 学期课程关系测试")
    print("=" * 50)
    
    client = APIClient()
    
    # 获取管理员权限
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ 无法获取管理员token，跳过测试")
        return
    
    client.set_auth_token(admin_token)
    
    # 1. 获取学期下的所有课程
    print("\n1️⃣ 获取学期下的所有课程")
    semester_courses_response = client.get("/api/v1/semesters/1/courses")
    print_response(semester_courses_response, "学期课程列表")
    
    # 2. 按学期筛选课程
    print("\n2️⃣ 按学期筛选课程")
    filtered_courses_response = client.get("/api/v1/courses", params={"semester_id": 1})
    print_response(filtered_courses_response, "筛选课程")

if __name__ == "__main__":
    print("⚠️  请确保已执行: source venv/bin/activate")
    print("⚠️  请确保服务正在运行: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("⚠️  此测试需要管理员权限")
    input("按回车键继续...")
    
    try:
        test_semester_management()
        course_id = test_course_management()
        test_semester_course_relationship()
        print(f"\n🎉 学期和课程管理测试完成！")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()