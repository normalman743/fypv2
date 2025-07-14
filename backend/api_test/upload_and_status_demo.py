import requests
import json
from config import ADMIN_USER, TEST_USER

API_BASE = "http://127.0.0.1:8000/api/v1"

# 用户登录，获取token
def get_user_token():
    login_data = {
        "username": TEST_USER["username"],
        "password": TEST_USER["password"]
    }
    resp = requests.post(f"{API_BASE}/auth/login", json=login_data)
    if resp.status_code == 200 and resp.json().get("success"):
        token = resp.json()["data"]["access_token"]
        print(f"✅ 用户登录成功，token: {token[:16]}...")
        return token
    else:
        print("❌ 用户登录失败", resp.text)
        return None

def get_admin_token():
    login_data = {
        "username": ADMIN_USER["username"],
        "password": ADMIN_USER["password"]
    }
    resp = requests.post(f"{API_BASE}/auth/login", json=login_data)
    if resp.status_code == 200 and resp.json().get("success"):
        token = resp.json()["data"]["access_token"]
        print(f"✅ 管理员登录成功，token: {token[:16]}...")
        return token
    else:
        print("❌ 管理员登录失败", resp.text)
        return None
    

# 上传课程文件
def upload_course_file(token, file_path, course_id, folder_id):
    headers = {"Authorization": f"Bearer {token}"}
    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {"course_id": str(course_id), "folder_id": str(folder_id)}
        resp = requests.post(f"{API_BASE}/files/upload", headers=headers, files=files, data=data)
        print(f"上传课程文件: {file_path}")
        print(resp.status_code, resp.text)
        if resp.status_code == 200 and resp.json().get("success"):
            file_id = resp.json()["data"]["file"]["id"]
            return file_id
        return None

# 上传全局文件（管理员专用）
def upload_global_file(token, file_path, description=None, tags=None):
    headers = {"Authorization": f"Bearer {token}"}
    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {"description": description or "API测试全局文件", "tags": json.dumps(tags or ["API", "测试"])}
        resp = requests.post(f"{API_BASE}/admin/global-files/upload", headers=headers, files=files, data=data)
        print(f"上传全局文件: {file_path}")
        print(resp.status_code, resp.text)
        if resp.status_code == 200 and resp.json().get("success"):
            global_file_id = resp.json()["data"]["global_file"]["id"]
            return global_file_id
        return None

# 查询课程文件RAG处理状态
def check_course_file_status(token, file_id):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{API_BASE}/files/{file_id}/status", headers=headers)
    print(f"查询课程文件状态: file_id={file_id}")
    print(resp.status_code, resp.text)
    if resp.status_code == 200 and resp.json().get("success"):
        return resp.json()["data"]
    return None

# 查询全局文件RAG处理状态（可扩展为单独接口，如有）
def check_global_file_status(token, global_file_id):
    # 假设有 /admin/global-files/{id}/status 接口，若无可省略
    print(f"全局文件ID: {global_file_id}，请在后台或数据库查看处理状态")
    # 可根据实际API补充查询逻辑

if __name__ == "__main__":
    # 1. 用户登录获取token
    token = get_user_token()
    admin_token = get_admin_token()
    if not token:
        exit(1)

    file_path = "/Users/mannormal/Downloads/fyp/backend/GEJC_Research_proposal_Group2.pdf"

    # 2. 上传为课程文件（假设课程id=1，文件夹id=1）
    course_file_id = upload_course_file(token, file_path, course_id=1, folder_id=1)
    if course_file_id:
        # 3. 查询RAG处理状态
        status = check_course_file_status(token, course_file_id)
        print("课程文件RAG状态:", status)

    # 4. 上传为全局文件（管理员专用）
    global_file_id = upload_global_file(admin_token, file_path, description="API测试全局文件", tags=["API", "测试"])
    if global_file_id:
        check_global_file_status(admin_token, global_file_id) 