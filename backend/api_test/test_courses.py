"""
课程管理API测试
测试学期、课程、文件夹等管理功能
"""
from utils import APIClient, print_response, check_response, extract_data
from config import TEST_USER, ADMIN_USER, TEST_SEMESTER, TEST_COURSE, TEST_FOLDER
import time

def setup_auth(client: APIClient):
    """设置认证"""
    # 尝试登录现有用户
    login_data = {
        "username": TEST_USER["username"],
        "password": TEST_USER["password"]   
    }
    
    response = client.post("/auth/login", login_data)
    if check_response(response):
        data = extract_data(response)
        if data and "access_token" in data:
            client.set_token(data["access_token"])
            return True
    return False

def setup_admin_auth(client: APIClient):
    """设置管理员认证"""
    login_data = {
        "username": ADMIN_USER["username"],
        "password": ADMIN_USER["password"]   
    }
    
    response = client.post("/auth/login", login_data)
    if check_response(response):
        data = extract_data(response)
        if data and "access_token" in data:
            client.set_token(data["access_token"])
            return True
    return False

def test_get_semesters(client: APIClient):
    """测试获取学期列表"""
    response = client.get("/semesters")
    print_response(response, "获取学期列表")
    
    if check_response(response):
        data = extract_data(response)
        return data.get("semesters", []) if data else []
    return []

def test_create_semester(client: APIClient):
    """测试创建学期（管理员功能）"""
    timestamp = str(int(time.time()))
    semester_data = {
        "name": f"{TEST_SEMESTER['name']}_{timestamp}",
        "code": f"{TEST_SEMESTER['code']}_{timestamp}",
        "start_date": TEST_SEMESTER["start_date"],
        "end_date": TEST_SEMESTER["end_date"]
    }
    
    response = client.post("/semesters", semester_data)
    print_response(response, "创建学期")
    
    if check_response(response):
        data = extract_data(response)
        return data.get("semester") if data else None
    return None

def test_get_courses(client: APIClient):
    """测试获取课程列表"""
    response = client.get("/courses")
    print_response(response, "获取课程列表")
    
    if check_response(response):
        data = extract_data(response)
        return data.get("courses", []) if data else []
    return []

def test_create_course(client: APIClient, semester_id: int):
    """测试创建课程"""
    timestamp = str(int(time.time()))
    course_data = {
        "name": f"{TEST_COURSE['name']}_{timestamp}",
        "code": f"{TEST_COURSE['code']}_{timestamp}",
        "description": TEST_COURSE["description"],
        "semester_id": semester_id
    }
    
    response = client.post("/courses", course_data)
    print_response(response, "创建课程")
    
    if check_response(response):
        data = extract_data(response)
        return data.get("course") if data else None
    return None

def test_get_course_folders(client: APIClient, course_id: int):
    """测试获取课程文件夹"""
    response = client.get(f"/courses/{course_id}/folders")
    print_response(response, "获取课程文件夹")
    
    if check_response(response):
        data = extract_data(response)
        return data.get("folders", []) if data else []
    return []

def test_create_folder(client: APIClient, course_id: int):
    """测试创建文件夹"""
    timestamp = str(int(time.time()))
    folder_data = {
        "name": f"{TEST_FOLDER['name']}_{timestamp}",
        "folder_type": TEST_FOLDER["folder_type"]
    }
    
    response = client.post(f"/courses/{course_id}/folders", folder_data)
    print_response(response, "创建文件夹")
    
    if check_response(response):
        data = extract_data(response)
        return data.get("folder") if data else None
    return None

def test_update_course(client: APIClient, course_id: int):
    """测试更新课程"""
    update_data = {
        "description": "更新后的课程描述"
    }
    
    response = client.put(f"/courses/{course_id}", update_data)
    print_response(response, "更新课程")
    return check_response(response)

def test_delete_folder(client: APIClient, folder_id: int):
    """测试删除文件夹"""
    response = client.delete(f"/folders/{folder_id}")
    print_response(response, "删除文件夹")
    return check_response(response)

def main():
    """运行课程管理测试"""
    print("📚 开始课程管理API测试")
    
    client = APIClient()
    admin_client = APIClient()
    
    # 先尝试普通用户认证
    if not setup_auth(client):
        print("❌ 无法获取普通用户认证，跳过需要认证的测试")
    
    # 尝试管理员认证
    admin_auth = setup_admin_auth(admin_client)
    if not admin_auth:
        print("❌ 无法获取管理员认证，跳过管理员测试")
        
    passed = 0
    total = 0
    
    # 测试获取学期列表（不需要认证）
    print("\n--- 测试学期相关功能 ---")
    total += 1
    semesters = test_get_semesters(client)
    if semesters is not None:
        passed += 1
        print("✅ 获取学期列表 - 通过")
    else:
        print("❌ 获取学期列表 - 失败")
    
    # 如果有管理员认证，测试创建学期
    semester_id = None
    if semesters:
        semester_id = semesters[0].get("id") if semesters else None
    
    if admin_auth:
        # 测试创建学期（需要管理员权限）
        total += 1
        try:
            new_semester = test_create_semester(admin_client)
            if new_semester:
                semester_id = new_semester.get("id")
                passed += 1
                print("✅ 创建学期 - 通过")
            else:
                print("❌ 创建学期 - 失败")
        except Exception as e:
            print(f"❌ 创建学期 - 异常: {e}")
    else:
        print("⚠️ 跳过创建学期测试（无管理员权限）")
    
    # 如果有普通用户认证，继续测试课程功能
    if client.token:
        # 测试课程相关功能
        print("\n--- 测试课程相关功能 ---")
        total += 1
        courses = test_get_courses(client)
        if courses is not None:
            passed += 1
            print("✅ 获取课程列表 - 通过")
        else:
            print("❌ 获取课程列表 - 失败")
        
        # 如果有学期ID，测试创建课程
        if semester_id:
            total += 1
            course = test_create_course(client, semester_id)
            if course:
                passed += 1
                print("✅ 创建课程 - 通过")
                
                course_id = course.get("id")
                if course_id:
                    # 测试文件夹功能
                    print("\n--- 测试文件夹相关功能 ---")
                    total += 1
                    folders = test_get_course_folders(client, course_id)
                    if folders is not None:
                        passed += 1
                        print("✅ 获取课程文件夹 - 通过")
                    else:
                        print("❌ 获取课程文件夹 - 失败")
                    
                    total += 1
                    folder = test_create_folder(client, course_id)
                    if folder:
                        passed += 1
                        print("✅ 创建文件夹 - 通过")
                        
                        folder_id = folder.get("id")
                        if folder_id:
                            total += 1
                            if test_delete_folder(client, folder_id):
                                passed += 1
                                print("✅ 删除文件夹 - 通过")
                            else:
                                print("❌ 删除文件夹 - 失败")
                    else:
                        print("❌ 创建文件夹 - 失败")
                    
                    # 测试更新课程
                    total += 1
                    if test_update_course(client, course_id):
                        passed += 1
                        print("✅ 更新课程 - 通过")
                    else:
                        print("❌ 更新课程 - 失败")
            else:
                print("❌ 创建课程 - 失败")
        else:
            print("⚠️ 跳过创建课程测试（无有效学期ID）")
    
    print(f"\n📊 课程管理测试结果: {passed}/{total} 通过")
    return passed == total if total > 0 else False

if __name__ == "__main__":
    main()