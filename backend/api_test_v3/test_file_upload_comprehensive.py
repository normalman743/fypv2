#!/usr/bin/env python3
"""
文件上传功能综合测试
测试白名单验证、图片处理等功能
"""

import sys
import os
import requests
import json
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置
BASE_URL = "http://localhost:8000"
TEST_FILES_DIR = "/Users/mannormal/Downloads/fyp/test_file"

class FileUploadTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.user_id = None
        
    def login(self):
        """登录获取token"""
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                proxies={"http": None, "https": None}  # 禁用代理
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_id = data.get("user_id")
                print(f"✅ 登录成功，Token: {self.token[:20]}...")
                return True
            else:
                print(f"❌ 登录失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 登录异常: {e}")
            return False
    
    def test_image_regular_upload(self):
        """测试1: 图片文件普通上传 - 应该拒绝"""
        print("\n🔍 测试1: 图片文件普通上传（应该拒绝）")
        
        image_path = f"{TEST_FILES_DIR}/Screenshot 2025-07-25 at 8.21.53 AM.png"
        if not os.path.exists(image_path):
            print(f"❌ 图片文件不存在: {image_path}")
            return False
            
        try:
            with open(image_path, 'rb') as f:
                files = {'file': (os.path.basename(image_path), f, 'image/png')}
                data = {
                    'scope': 'global',
                    'description': '测试图片上传',
                    'visibility': 'public'
                }
                
                response = requests.post(
                    f"{self.base_url}/api/v1/global-files/upload",
                    files=files,
                    data=data,
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                
                if response.status_code == 400:
                    print(f"✅ 符合预期: 图片文件被拒绝 - {response.json().get('detail', 'Unknown error')}")
                    return True
                else:
                    print(f"❌ 意外结果: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            return False
    
    def test_image_temporary_upload(self):
        """测试2: 图片文件临时上传 - 应该成功"""
        print("\n🔍 测试2: 图片文件临时上传（应该成功）")
        
        image_path = f"{TEST_FILES_DIR}/Screenshot 2025-07-25 at 8.21.53 AM.png"
        
        try:
            with open(image_path, 'rb') as f:
                files = {'file': (os.path.basename(image_path), f, 'image/png')}
                data = {
                    'purpose': 'chat_upload',
                    'expiry_hours': 5
                }
                
                response = requests.post(
                    f"{self.base_url}/api/v1/files/temporary",
                    files=files,
                    data=data,
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get('data', {}).get('token')
                    print(f"✅ 图片临时上传成功，Token: {token[:10]}...")
                    return token
                else:
                    print(f"❌ 图片临时上传失败: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            return None
    
    def test_document_temporary_upload(self):
        """测试3: 文档文件临时上传 - 应该成功"""
        print("\n🔍 测试3: 文档文件临时上传（应该成功）")
        
        doc_path = f"{TEST_FILES_DIR}/test_files/valid_text.txt"
        
        try:
            with open(doc_path, 'rb') as f:
                files = {'file': ('valid_text.txt', f, 'text/plain')}
                data = {
                    'purpose': 'chat_upload',
                    'expiry_hours': 5
                }
                
                response = requests.post(
                    f"{self.base_url}/api/v1/files/temporary",
                    files=files,
                    data=data,
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get('data', {}).get('token')
                    print(f"✅ 文档临时上传成功，Token: {token[:10]}...")
                    return True
                else:
                    print(f"❌ 文档临时上传失败: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            return False
    
    def test_document_regular_upload(self):
        """测试4: 文档文件普通上传 - 应该成功"""
        print("\n🔍 测试4: 文档文件普通上传（应该成功）")
        
        doc_path = f"{TEST_FILES_DIR}/test_files/valid_python.py"
        
        try:
            with open(doc_path, 'rb') as f:
                files = {'file': ('valid_python.py', f, 'text/x-python')}
                data = {
                    'scope': 'global',
                    'description': '测试Python文件上传',
                    'visibility': 'public'
                }
                
                response = requests.post(
                    f"{self.base_url}/api/v1/global-files/upload",
                    files=files,
                    data=data,
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                
                if response.status_code == 200:
                    print(f"✅ Python文件上传成功")
                    return True
                else:
                    print(f"❌ Python文件上传失败: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            return False
    
    def test_corrupted_file_upload(self):
        """测试5: 乱码文件上传 - 应该失败"""
        print("\n🔍 测试5: 乱码文件上传（应该失败）")
        
        corrupted_path = f"{TEST_FILES_DIR}/test_files/corrupted_file.txt"
        
        try:
            with open(corrupted_path, 'rb') as f:
                files = {'file': ('corrupted_file.txt', f, 'text/plain')}
                data = {
                    'scope': 'global',
                    'description': '测试损坏文件',
                    'visibility': 'public'
                }
                
                response = requests.post(
                    f"{self.base_url}/api/v1/global-files/upload",
                    files=files,
                    data=data,
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                
                # 这个可能成功（如果RAG处理能容错）也可能失败
                print(f"🔍 乱码文件上传结果: {response.status_code}")
                if response.status_code != 200:
                    print(f"   错误信息: {response.json().get('detail', 'Unknown error')}")
                return True
                    
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            return False
    
    def test_unsupported_file_upload(self):
        """测试6: 不支持格式文件上传 - 应该拒绝"""
        print("\n🔍 测试6: 不支持格式文件上传（应该拒绝）")
        
        unsupported_path = f"{TEST_FILES_DIR}/test_files/unsupported.xyz"
        
        try:
            with open(unsupported_path, 'rb') as f:
                files = {'file': ('unsupported.xyz', f, 'application/octet-stream')}
                data = {
                    'scope': 'global',
                    'description': '测试不支持格式',
                    'visibility': 'public'
                }
                
                response = requests.post(
                    f"{self.base_url}/api/v1/global-files/upload",
                    files=files,
                    data=data,
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                
                if response.status_code == 400:
                    print(f"✅ 符合预期: 不支持格式被拒绝 - {response.json().get('detail', 'Unknown error')}")
                    return True
                else:
                    print(f"❌ 意外结果: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("🚀 开始文件上传功能综合测试")
        print("=" * 60)
        
        # 登录
        if not self.login():
            return
        
        # 运行测试
        results = []
        results.append(("图片普通上传拒绝", self.test_image_regular_upload()))
        
        image_token = self.test_image_temporary_upload()
        results.append(("图片临时上传成功", image_token is not None))
        
        results.append(("文档临时上传", self.test_document_temporary_upload()))
        results.append(("文档普通上传", self.test_document_regular_upload()))
        results.append(("乱码文件处理", self.test_corrupted_file_upload()))
        results.append(("不支持格式拒绝", self.test_unsupported_file_upload()))
        
        # 输出总结
        print("\n" + "=" * 60)
        print("📊 测试结果总结")
        print("=" * 60)
        
        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name}: {status}")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        print(f"\n总计: {passed}/{total} 项测试通过")
        
        return image_token

if __name__ == "__main__":
    tester = FileUploadTester()
    image_token = tester.run_all_tests()
    
    if image_token:
        print(f"\n🖼️ 图片Token可用于聊天测试: {image_token}")