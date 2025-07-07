"""
API测试工具函数
"""
import requests
import json
from typing import Dict, Any, Optional
from config import BASE_URL, API_BASE, HEADERS, TIMEOUT

class APIClient:
    """API客户端类"""
    
    def __init__(self):
        self.token = None
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
    def set_token(self, token: str):
        """设置认证token"""
        self.token = token
        self.session.headers.update({
            "Authorization": f"Bearer {token}"
        })
    
    def get(self, endpoint: str, params: Dict = None) -> requests.Response:
        """GET请求"""
        url = f"{API_BASE}{endpoint}"
        return self.session.get(url, params=params, timeout=TIMEOUT)
    
    def post(self, endpoint: str, data: Dict = None, files: Dict = None) -> requests.Response:
        """POST请求"""
        url = f"{API_BASE}{endpoint}"
        if files:
            # 文件上传时不设置Content-Type
            headers = {k: v for k, v in self.session.headers.items() if k != "Content-Type"}
            return requests.post(url, data=data, files=files, headers=headers, timeout=TIMEOUT)
        return self.session.post(url, json=data, timeout=TIMEOUT)
    
    def put(self, endpoint: str, data: Dict = None) -> requests.Response:
        """PUT请求"""
        url = f"{API_BASE}{endpoint}"
        return self.session.put(url, json=data, timeout=TIMEOUT)
    
    def delete(self, endpoint: str) -> requests.Response:
        """DELETE请求"""
        url = f"{API_BASE}{endpoint}"
        return self.session.delete(url, timeout=TIMEOUT)

def print_response(response: requests.Response, test_name: str):
    """打印响应信息"""
    print(f"\n{'='*50}")
    print(f"测试: {test_name}")
    print(f"状态码: {response.status_code}")
    print(f"URL: {response.url}")
    
    try:
        data = response.json()
        print(f"响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    except:
        print(f"响应内容: {response.text}")
    
    if response.status_code < 400:
        print("✅ 成功")
    else:
        print("❌ 失败")
    print(f"{'='*50}")

def check_response(response: requests.Response, expected_status: int = 200) -> bool:
    """检查响应状态"""
    return response.status_code == expected_status

def extract_data(response: requests.Response, key: str = "data") -> Any:
    """提取响应数据"""
    try:
        data = response.json()
        if key in data:
            return data[key]
        return data
    except:
        return None