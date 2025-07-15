# -*- coding: utf-8 -*-
"""
API测试工具通用工具函数
V3.0 模块化版本
"""

import requests
import json
import time
import logging
from typing import Dict, Any, Optional, Union
from config import api_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIClient:
    """API客户端封装类"""
    
    def __init__(self, base_url: str = None, timeout: int = None):
        self.base_url = base_url or api_config.base_url
        self.timeout = timeout or api_config.timeout
        self.session = requests.Session()
        self.session.headers.update(api_config.headers)
        self.token = None
    
    def set_auth_token(self, token: str):
        """设置认证令牌"""
        self.token = token
        self.session.headers.update({
            "Authorization": f"Bearer {token}"
        })
    
    def clear_auth_token(self):
        """清除认证令牌"""
        self.token = None
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
    
    def request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """统一请求方法"""
        url = f"{self.base_url}{endpoint}"
        
        # 添加--noproxy支持
        if 'proxies' not in kwargs:
            kwargs['proxies'] = {'http': '', 'https': ''}
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            
            # 记录请求信息
            logger.info(f"{method} {url} - Status: {response.status_code}")
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {method} {url} - {str(e)}")
            raise
    
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """GET请求"""
        return self.request("GET", endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """POST请求"""
        return self.request("POST", endpoint, **kwargs)
    
    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """PUT请求"""
        return self.request("PUT", endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """DELETE请求"""
        return self.request("DELETE", endpoint, **kwargs)

def format_response(response: requests.Response) -> Dict[str, Any]:
    """格式化响应信息"""
    result = {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "url": response.url
    }
    
    try:
        result["data"] = response.json()
    except json.JSONDecodeError:
        result["data"] = response.text
    
    return result

def print_response(response: requests.Response, title: str = "API Response"):
    """打印响应信息"""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(f"Status Code: {response.status_code}")
    print(f"URL: {response.url}")
    
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    except json.JSONDecodeError:
        print(f"Response: {response.text}")
    
    print(f"{'='*50}\n")

def wait_for_service(client: APIClient, max_retries: int = 30, retry_interval: int = 2) -> bool:
    """等待服务启动"""
    print(f"等待服务启动中...")
    
    for i in range(max_retries):
        try:
            response = client.get("/health")
            if response.status_code == 200:
                print(f"✅ 服务已启动")
                return True
        except Exception:
            pass
        
        if i < max_retries - 1:
            print(f"⏳ 等待中... ({i+1}/{max_retries})")
            time.sleep(retry_interval)
    
    print(f"❌ 服务启动超时")
    return False

def extract_token_from_response(response: requests.Response) -> Optional[str]:
    """从响应中提取token"""
    try:
        data = response.json()
        if data.get("success") and "data" in data:
            return data["data"].get("access_token")
    except:
        pass
    return None

def safe_json_parse(text: str) -> Union[Dict, str]:
    """安全的JSON解析"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text