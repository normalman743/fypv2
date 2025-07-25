#!/usr/bin/env python3
"""
Decimal序列化测试
专门测试流式响应中的Decimal类型序列化问题
"""

import json
import requests
from decimal import Decimal
from datetime import datetime
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TestConfig

def test_json_serialization():
    """测试不同数据类型的JSON序列化"""
    print("🔍 JSON序列化兼容性测试")
    print("=" * 50)
    
    # 测试各种数据类型
    test_data = {
        "string": "hello",
        "integer": 123,
        "float": 12.34,
        "decimal": Decimal('0.00123'),
        "datetime": datetime.now(),
        "boolean": True,
        "null": None,
        "list": [1, 2, 3],
        "nested": {
            "cost": Decimal('0.00567'),
            "tokens": 1500
        }
    }
    
    print("📋 原始测试数据:")
    for key, value in test_data.items():
        print(f"  {key}: {value} (类型: {type(value)})")
    
    # 尝试直接序列化
    print("\n🧪 直接JSON序列化测试...")
    try:
        json_str = json.dumps(test_data)
        print("✅ 直接序列化成功")
        print(f"  结果: {json_str}")
    except Exception as e:
        print(f"❌ 直接序列化失败: {e}")
        print(f"  错误类型: {type(e)}")
    
    # 测试自定义转换函数
    print("\n🔧 自定义转换函数测试...")
    
    def convert_for_json(obj):
        """自定义JSON转换函数"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return obj
    
    def serialize_data(data):
        """递归序列化数据"""
        if isinstance(data, dict):
            return {key: serialize_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [serialize_data(item) for item in data]
        else:
            return convert_for_json(data)
    
    try:
        converted_data = serialize_data(test_data)
        json_str = json.dumps(converted_data)
        print("✅ 自定义转换成功")
        print(f"  转换后数据: {converted_data}")
        print(f"  JSON结果: {json_str}")
    except Exception as e:
        print(f"❌ 自定义转换失败: {e}")

def test_streaming_response_simulation():
    """模拟流式响应序列化测试"""
    print("\n🌊 流式响应模拟测试")
    print("=" * 50)
    
    # 模拟各种流式事件数据
    events = [
        {
            "type": "user_message",
            "user_message": {
                "id": 123,
                "content": "测试消息",
                "created_at": datetime.now()
            }
        },
        {
            "type": "content",
            "content": "人工智能",
            "ai_message_id": 124
        },
        {
            "type": "ai_end",
            "tokens_used": 1500,
            "cost": Decimal('0.00123'),  # 这里是问题所在
            "message_id": 124,
            "timestamp": datetime.now()
        }
    ]
    
    def convert_for_json(obj):
        """转换函数"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return obj
    
    def serialize_event(event):
        """序列化事件数据"""
        if isinstance(event, dict):
            return {key: serialize_event(value) for key, value in event.items()}
        elif isinstance(event, list):
            return [serialize_event(item) for item in event]
        else:
            return convert_for_json(event)
    
    print("📋 模拟流式事件:")
    for i, event in enumerate(events):
        print(f"\n事件 {i+1}: {event['type']}")
        
        # 尝试直接序列化
        try:
            json_str = json.dumps(event)
            print(f"  ✅ 直接序列化成功: {json_str[:100]}...")
        except Exception as e:
            print(f"  ❌ 直接序列化失败: {e}")
            
            # 尝试转换后序列化
            try:
                converted_event = serialize_event(event)
                json_str = json.dumps(converted_event)
                print(f"  🔧 转换后成功: {json_str[:100]}...")
                print(f"  📝 转换详情: cost类型 {type(event.get('cost', 'N/A'))} -> {type(converted_event.get('cost', 'N/A'))}")
            except Exception as e2:
                print(f"  ❌ 转换后仍失败: {e2}")

def test_actual_api_message():
    """测试真实API消息流式响应"""
    print("\n📡 真实API消息测试")
    print("=" * 50)
    
    config = TestConfig()
    
    # 登录
    print("🔐 登录测试用户...")
    login_response = requests.post(
        f"{config.base_url}/api/v1/auth/login",
        json={"username": "testuser", "password": "testpass123"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.status_code}")
        return
    
    token = login_response.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    # 创建测试聊天
    print("💬 创建测试聊天...")
    chat_data = {
        "chat_type": "general",
        "first_message": "简单回答：1+1等于多少？",
        "course_id": None,
        "custom_prompt": None,
        "file_ids": [],
        "folder_ids": [],
        "ai_model": "Star",
        "search_enabled": False,
        "context_mode": "Economy",
        "temporary_file_tokens": [],
        "stream": True
    }
    
    try:
        with requests.post(f"{config.base_url}/api/v1/chats", 
                         json=chat_data, headers=headers, stream=True, timeout=30) as response:
            
            print(f"📥 响应状态: {response.status_code}")
            
            if response.status_code == 200:
                print("📨 接收流式数据...")
                
                decimal_errors = []
                successful_events = 0
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        
                        if line_str.startswith('data: '):
                            data_content = line_str[6:]
                            
                            if data_content.strip() == '[DONE]':
                                print("🏁 流结束")
                                break
                            
                            try:
                                data_json = json.loads(data_content)
                                successful_events += 1
                                
                                # 检查是否包含Decimal字段
                                if 'cost' in str(data_json):
                                    print(f"💰 发现成本字段: {data_json}")
                                    
                            except json.JSONDecodeError as e:
                                print(f"❌ JSON解析错误: {e}")
                                print(f"   原始数据: {repr(data_content)}")
                                
                                # 检查是否是Decimal序列化错误
                                if 'Decimal' in str(e) or 'Decimal' in data_content:
                                    decimal_errors.append({
                                        'error': str(e),
                                        'data': data_content
                                    })
                
                print(f"\n📊 测试结果:")
                print(f"  ✅ 成功事件: {successful_events}")
                print(f"  ❌ Decimal错误: {len(decimal_errors)}")
                
                if decimal_errors:
                    print("\n🔍 Decimal错误详情:")
                    for i, error in enumerate(decimal_errors):
                        print(f"  错误 {i+1}: {error['error']}")
                        print(f"    数据: {error['data'][:200]}...")
            
            else:
                print(f"❌ API调用失败: {response.text}")
                
    except Exception as e:
        print(f"❌ 测试异常: {e}")

if __name__ == "__main__":
    print("🧪 Decimal序列化问题诊断测试")
    print("=" * 80)
    
    # 1. 基础JSON序列化测试
    test_json_serialization()
    
    # 2. 流式响应模拟测试
    test_streaming_response_simulation()
    
    # 3. 真实API测试
    test_actual_api_message()
    
    print("\n" + "=" * 80)
    print("🎯 测试完成！")
    print("\n建议解决方案:")
    print("1. 在 convert_for_json() 函数中添加 Decimal -> float 转换")
    print("2. 确保所有流式事件数据在发送前都经过转换")
    print("3. 检查 app/services/chat_service.py 的序列化逻辑")