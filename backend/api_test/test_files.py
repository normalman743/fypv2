"""
文件管理API测试
测试文件上传、下载、预览等功能
"""
import os
import tempfile
from utils import APIClient, print_response, check_response, extract_data
from config import TEST_USER, ADMIN_USER

def setup_auth(client: APIClient):
    """设置认证"""
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

def create_test_file():
    """创建测试文件"""
    content = """# 测试文档
    
这是一个用于API测试的文档文件。

## 内容
- 测试文本内容
- 支持中文字符
- 包含多行文本

## 结论
文件上传测试成功！
"""
    
    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
    temp_file.write(content)
    temp_file.close()
    
    return temp_file.name

def test_upload_file(client: APIClient, course_id: int, folder_id: int):
    """测试文件上传"""
    test_file_path = create_test_file()
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_document.txt', f, 'text/plain')}
            data = {
                'course_id': course_id,
                'folder_id': folder_id
            }
            
            response = client.post("/files/upload", data=data, files=files)
            print_response(response, "文件上传")
            
            if check_response(response):
                data = extract_data(response)
                return data.get("file") if data else None
    finally:
        # 清理临时文件
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)
    
    return None

def test_get_folder_files(client: APIClient, folder_id: int):
    """测试获取文件夹文件列表"""
    response = client.get(f"/folders/{folder_id}/files")
    print_response(response, "获取文件夹文件列表")
    
    if check_response(response):
        data = extract_data(response)
        return data.get("files", []) if data else []
    return []

def test_get_file_preview(client: APIClient, file_id: int):
    """测试文件预览"""
    response = client.get(f"/files/{file_id}/preview")
    print_response(response, "文件预览")
    return check_response(response)

def test_get_file_status(client: APIClient, file_id: int):
    """测试文件状态"""
    response = client.get(f"/files/{file_id}/status")
    print_response(response, "文件处理状态")
    return check_response(response)

def test_download_file(client: APIClient, file_id: int):
    """测试文件下载"""
    response = client.get(f"/files/{file_id}/download")
    print_response(response, "文件下载")
    return check_response(response)

def test_delete_file(client: APIClient, file_id: int):
    """测试删除文件"""
    response = client.delete(f"/files/{file_id}")
    print_response(response, "删除文件")
    return check_response(response)

def get_test_course_and_folder(client: APIClient):
    """获取测试用的课程和文件夹ID"""
    # 获取课程列表
    response = client.get("/courses")
    if not check_response(response):
        return None, None
    
    courses_data = extract_data(response)
    courses = courses_data.get("courses", []) if courses_data else []
    
    if not courses:
        print("❌ 没有找到课程，无法测试文件功能")
        return None, None
    
    course = courses[0]
    course_id = course.get("id")
    
    # 获取文件夹列表
    response = client.get(f"/courses/{course_id}/folders")
    if not check_response(response):
        return course_id, None
    
    folders_data = extract_data(response)
    folders = folders_data.get("folders", []) if folders_data else []
    
    if not folders:
        # 尝试创建一个文件夹
        folder_data = {
            "name": "API测试文件夹",
            "folder_type": "lecture"
        }
        response = client.post(f"/courses/{course_id}/folders", folder_data)
        if check_response(response):
            folder_data = extract_data(response)
            folder = folder_data.get("folder") if folder_data else None
            folder_id = folder.get("id") if folder else None
            return course_id, folder_id
        else:
            print("❌ 无法创建测试文件夹")
            return course_id, None
    
    folder_id = folders[0].get("id")
    return course_id, folder_id

def main():
    """运行文件管理测试"""
    print("📁 开始文件管理API测试")
    
    client = APIClient()
    
    # 认证
    if not setup_auth(client):
        print("❌ 无法获取认证，跳过文件测试")
        return False
    
    # 获取测试用的课程和文件夹
    course_id, folder_id = get_test_course_and_folder(client)
    
    if not course_id or not folder_id:
        print("❌ 无法获取测试课程或文件夹，跳过文件测试")
        return False
    
    print(f"📝 使用课程ID: {course_id}, 文件夹ID: {folder_id}")
    
    passed = 0
    total = 0
    file_id = None
    
    # 测试文件上传
    total += 1
    uploaded_file = test_upload_file(client, course_id, folder_id)
    if uploaded_file:
        file_id = uploaded_file.get("id")
        passed += 1
        print("✅ 文件上传 - 通过")
    else:
        print("❌ 文件上传 - 失败")
    
    # 测试获取文件列表
    total += 1
    files = test_get_folder_files(client, folder_id)
    if files is not None:
        passed += 1
        print("✅ 获取文件列表 - 通过")
        print(f"📄 文件夹中有 {len(files)} 个文件")
    else:
        print("❌ 获取文件列表 - 失败")
    
    # 如果文件上传成功，继续测试其他功能
    if file_id:
        # 测试文件预览
        total += 1
        if test_get_file_preview(client, file_id):
            passed += 1
            print("✅ 文件预览 - 通过")
        else:
            print("❌ 文件预览 - 失败")
        
        # 测试文件状态
        total += 1
        if test_get_file_status(client, file_id):
            passed += 1
            print("✅ 文件状态查询 - 通过")
        else:
            print("❌ 文件状态查询 - 失败")
        
        # 测试文件下载
        total += 1
        if test_download_file(client, file_id):
            passed += 1
            print("✅ 文件下载 - 通过")
        else:
            print("❌ 文件下载 - 失败")
        
        # 测试删除文件
        total += 1
        if test_delete_file(client, file_id):
            passed += 1
            print("✅ 删除文件 - 通过")
        else:
            print("❌ 删除文件 - 失败")
    
    print(f"\n📊 文件管理测试结果: {passed}/{total} 通过")
    return passed == total if total > 0 else False

if __name__ == "__main__":
    main()