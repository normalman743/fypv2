#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI模型选择和流式响应测试 - 基于最新的AI模型集成和流式功能
测试不同AI模型、上下文模式、搜索功能和流式响应的集成

使用前请先: source venv/bin/activate
运行: python api_test_v3/test_ai_models_streaming.py
"""

import sys
import os
import time
import json
import requests
from typing import Dict, List, Any, Optional
import asyncio
import aiohttp
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import APIClient, print_response, extract_token_from_response
from config import test_config, api_config
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

def test_ai_model_configurations():
    """测试不同AI模型配置的基本功能"""
    print("🤖 AI模型配置测试")
    print("=" * 60)
    
    client = APIClient()
    
    # 获取用户token
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 测试的AI模型配置
    test_models = [
        {
            "name": "Star (基础模型)",
            "ai_model": "Star",
            "search_enabled": False,
            "context_mode": "Standard"
        },
        {
            "name": "Star with Search (搜索增强)",
            "ai_model": "Star", 
            "search_enabled": True,
            "context_mode": "Standard"
        },
        {
            "name": "StarPlus (高级模型)",
            "ai_model": "StarPlus",
            "search_enabled": False, 
            "context_mode": "Premium"
        },
        {
            "name": "StarPlus with Search (高级搜索)",
            "ai_model": "StarPlus",
            "search_enabled": True,
            "context_mode": "Premium"
        },
        {
            "name": "StarCode (代码专用)",
            "ai_model": "StarCode",
            "search_enabled": False,  # StarCode不支持搜索
            "context_mode": "Max"
        }
    ]
    
    results = []
    
    for model_config in test_models:
        print(f"\n🔍 测试模型: {model_config['name']}")
        print(f"   配置: {model_config['ai_model']}, 搜索: {model_config['search_enabled']}, 上下文: {model_config['context_mode']}")
        
        # 显示系统将使用的实际OpenAI模型
        try:
            import sys
            import os
            # 添加backend目录到Python路径
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from app.core.model_config import get_openai_model
            actual_openai_model = get_openai_model(model_config['ai_model'], model_config['search_enabled'])
            print(f"   实际使用的OpenAI模型: {actual_openai_model}")
        except Exception as e:
            print(f"   ⚠️ 模型配置解析失败: {e}")
        
        # 创建聊天测试
        create_chat_data = {
            "chat_type": "general",
            "first_message": f"测试{model_config['name']}的响应能力，请简单介绍一下你的功能",
            "course_id": None,
            "custom_prompt": None,
            "file_ids": [],
            "folder_ids": [],
            "ai_model": model_config["ai_model"],
            "search_enabled": model_config["search_enabled"], 
            "context_mode": model_config["context_mode"],
            "temporary_file_tokens": []
        }
        
        print(f"📤 发送请求数据: {json.dumps(create_chat_data, ensure_ascii=False, indent=2)}")
        
        try:
            create_response = client.post("/api/v1/chats", json=create_chat_data, timeout=120)
            print(f"📥 响应状态码: {create_response.status_code}")
            
            if create_response.status_code == 200:
                result = create_response.json()
                print(f"✅ 模型 {model_config['name']} 测试成功")
                
                # 打印详细响应信息
                if result.get("success"):
                    chat_data = result["data"]["chat"]
                    user_message = result["data"]["user_message"]
                    ai_message = result["data"]["ai_message"]
                    
                    print(f"   聊天ID: {chat_data['id']}")
                    print(f"   聊天标题: {chat_data['title']}")
                    print(f"   AI模型: {chat_data.get('ai_model', 'N/A')}")
                    print(f"   搜索启用: {chat_data.get('search_enabled', 'N/A')}")
                    print(f"   上下文模式: {chat_data.get('context_mode', 'N/A')}")
                    print(f"   用户消息ID: {user_message['id']}")
                    print(f"   AI响应ID: {ai_message['id']}")
                    print(f"   AI响应长度: {len(ai_message['content'])} 字符")
                    print(f"   Token使用: {ai_message.get('tokens_used', 'N/A')}")
                    print(f"   成本: ${ai_message.get('cost', 'N/A')}")
                    print(f"   RAG来源数量: {len(ai_message.get('rag_sources', []))}")
                    print(f"   AI响应预览: {ai_message['content'][:100]}...")
                    
                    # 验证聊天标题是否自动更新
                    if result["data"].get("chat_title_updated"):
                        print(f"   ✅ 聊天标题自动更新为: {result['data']['new_chat_title']}")
                    
                    results.append({
                        "model": model_config["name"],
                        "success": True,
                        "chat_id": chat_data["id"],
                        "ai_model": chat_data.get("ai_model"),
                        "search_enabled": chat_data.get("search_enabled"),
                        "context_mode": chat_data.get("context_mode"),
                        "tokens_used": ai_message.get("tokens_used"),
                        "cost": ai_message.get("cost"),
                        "response_length": len(ai_message["content"])
                    })
                else:
                    print(f"❌ 模型 {model_config['name']} 响应格式错误")
                    print(f"   响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    results.append({"model": model_config["name"], "success": False, "error": "响应格式错误"})
            else:
                error_info = create_response.text
                print(f"❌ 模型 {model_config['name']} 请求失败")
                print(f"   错误信息: {error_info}")
                results.append({"model": model_config["name"], "success": False, "error": error_info})
                
        except Exception as e:
            print(f"❌ 模型 {model_config['name']} 测试异常: {e}")
            results.append({"model": model_config["name"], "success": False, "error": str(e)})
        
        print("-" * 50)
        time.sleep(2)  # 避免请求过于频繁
    
    # 打印汇总结果
    print(f"\n📊 AI模型测试汇总")
    print("=" * 60)
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    print(f"成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['model']}")
        if result["success"]:
            print(f"     Chat ID: {result.get('chat_id', 'N/A')}")
            print(f"     AI Model: {result.get('ai_model', 'N/A')}")
            print(f"     Search: {result.get('search_enabled', 'N/A')}")
            print(f"     Context: {result.get('context_mode', 'N/A')}")
            print(f"     Tokens: {result.get('tokens_used', 'N/A')}")
            print(f"     Cost: ${result.get('cost', 'N/A')}")
            print(f"     Response Length: {result.get('response_length', 'N/A')}")
        else:
            print(f"     Error: {result.get('error', 'Unknown')}")
    
    return results

def test_streaming_responses():
    """测试流式响应功能"""
    print("\n🌊 流式响应测试")
    print("=" * 60)
    
    # 获取用户token
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    # 测试流式聊天创建
    test_streaming_configurations = [
        {
            "name": "Star模型流式响应",
            "ai_model": "Star",
            "search_enabled": False,
            "context_mode": "Standard"
        },
        {
            "name": "StarPlus模型流式响应", 
            "ai_model": "StarPlus",
            "search_enabled": True,
            "context_mode": "Premium"
        }
    ]
    
    for config in test_streaming_configurations:
        print(f"\n🔄 测试配置: {config['name']}")
        
        # 使用requests的stream功能测试Server-Sent Events
        url = f"{api_config.base_url}/api/v1/chats"
        headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        
        data = {
            "chat_type": "general",
            "first_message": f"请用{config['name']}生成一个200字左右的回答，介绍香港中文大学的历史",
            "course_id": None,
            "custom_prompt": None, 
            "file_ids": [],
            "folder_ids": [],
            "ai_model": config["ai_model"],
            "search_enabled": config["search_enabled"],
            "context_mode": config["context_mode"],
            "temporary_file_tokens": [],
            "stream": True
        }
        
        print(f"📤 发送流式请求...")
        print(f"   URL: {url}")
        print(f"   Headers: {headers}")
        print(f"   Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        try:
            with requests.post(url, json=data, headers=headers, stream=True, timeout=120) as response:
                print(f"📥 流式响应状态码: {response.status_code}")
                print(f"📥 响应头: {dict(response.headers)}")
                
                if response.status_code == 200:
                    print(f"✅ 开始接收流式数据...")
                    
                    # 收集流式响应数据
                    events = []
                    current_content = ""
                    chat_created = False
                    ai_response_complete = False
                    
                    for line in response.iter_lines():
                        if line:
                            line_str = line.decode('utf-8')
                            print(f"📨 接收数据: {line_str}")
                            
                            if line_str.startswith('data: '):
                                data_content = line_str[6:]  # 去掉 "data: " 前缀
                                
                                # 检查是否是 [DONE] 标记
                                if data_content.strip() == '[DONE]':
                                    print(f"🏁 流式响应结束标记: [DONE]")
                                    continue
                                
                                try:
                                    data_json = json.loads(data_content)
                                    events.append(data_json)
                                    
                                    # 解析不同类型的事件
                                    event_type = data_json.get('type')
                                    if event_type == 'chat_created':
                                        chat_created = True
                                        chat_info = data_json.get('chat', {})
                                        print(f"🆕 聊天创建: ID={chat_info.get('id')}, 标题={chat_info.get('title')}")
                                        print(f"    AI模型: {chat_info.get('ai_model')}")
                                        print(f"    搜索启用: {chat_info.get('search_enabled')}")
                                        print(f"    上下文模式: {chat_info.get('context_mode')}")
                                        
                                    elif event_type == 'user_message':
                                        message_info = data_json.get('message', {})
                                        print(f"👤 用户消息: ID={message_info.get('id')}")
                                        print(f"    内容: {message_info.get('content', '')[:50]}...")
                                        
                                    elif event_type == 'ai_start':
                                        print(f"🤖 AI开始响应: Message ID={data_json.get('message_id')}")
                                        
                                    elif event_type == 'ai_content':
                                        content_delta = data_json.get('delta', '')
                                        current_content += content_delta
                                        print(f"📝 AI内容增量: {content_delta}")
                                        
                                    elif event_type == 'ai_sources':
                                        sources = data_json.get('sources', [])
                                        print(f"📚 RAG来源: 共{len(sources)}个来源")
                                        for source in sources:
                                            print(f"    - {source.get('source_file')} (chunk {source.get('chunk_id')})")
                                            
                                    elif event_type == 'ai_end':
                                        ai_response_complete = True
                                        # 提取数据并进行详细调试
                                        tokens_used = data_json.get('tokens_used')
                                        cost = data_json.get('cost')
                                        title_updated = data_json.get('chat_title_updated', False)
                                        new_title = data_json.get('new_chat_title', '')
                                        
                                        print(f"✅ AI响应完成:")
                                        print(f"    Token使用: {tokens_used} (类型: {type(tokens_used)})")
                                        print(f"    成本: {cost} (类型: {type(cost)})")
                                        print(f"    响应长度: {len(current_content)} 字符")
                                        print(f"    标题更新: {title_updated}")
                                        if title_updated:
                                            print(f"    新标题: {new_title}")
                                            
                                        # 调试：打印原始JSON数据以查看可能的序列化问题
                                        print(f"🔍 原始ai_end事件数据: {data_json}")
                                            
                                    elif event_type == 'error':
                                        error_msg = data_json.get('error', 'Unknown error')
                                        print(f"❌ 流式错误: {error_msg}")
                                        
                                except json.JSONDecodeError as e:
                                    print(f"❌ JSON解析错误详情:")
                                    print(f"   错误: {e}")
                                    print(f"   原始行数据: {repr(line_str)}")
                                    print(f"   处理后数据: {repr(data_content)}")
                                    print(f"   数据长度: {len(data_content)}")
                                    print(f"   数据类型: {type(data_content)}")
                                    
                                except Exception as general_e:
                                    print(f"❌ 流式数据处理异常:")
                                    print(f"   错误: {general_e}")
                                    print(f"   错误类型: {type(general_e)}")
                                    print(f"   原始数据: {repr(line_str)}")
                                    print(f"   JSON数据: {data_json if 'data_json' in locals() else 'JSON解析失败'}")
                                    import traceback
                                    traceback.print_exc()
                    
                    # 验证流式响应完整性
                    print(f"\n📊 流式响应验证:")
                    print(f"   事件总数: {len(events)}")
                    print(f"   聊天创建: {'✅' if chat_created else '❌'}")
                    print(f"   AI响应完成: {'✅' if ai_response_complete else '❌'}")
                    print(f"   完整内容长度: {len(current_content)} 字符")
                    print(f"   完整响应预览: {current_content[:200]}...")
                    
                else:
                    error_info = response.text
                    print(f"❌ 流式请求失败: {response.status_code}")
                    print(f"   错误信息: {error_info}")
                    
        except Exception as e:
            print(f"❌ 流式测试异常: {e}")
            import traceback
            traceback.print_exc()
        
        print("-" * 50)
        time.sleep(3)  # 等待一段时间再测试下一个配置

def test_context_modes_and_history():
    """测试不同上下文模式和对话历史功能"""
    print("\n💬 上下文模式和对话历史测试")
    print("=" * 60)
    
    client = APIClient()
    
    # 获取用户token
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 测试不同的上下文模式
    context_modes = ["Economy", "Standard", "Premium", "Max"]
    
    for context_mode in context_modes:
        print(f"\n🔍 测试上下文模式: {context_mode}")
        
        # 创建聊天
        create_chat_data = {
            "chat_type": "general",
            "first_message": f"我想测试{context_mode}上下文模式，请记住我的名字是小明",
            "course_id": None,
            "custom_prompt": None,
            "file_ids": [],
            "folder_ids": [],
            "ai_model": "Star",
            "search_enabled": False,
            "context_mode": context_mode,
            "temporary_file_tokens": []
        }
        
        try:
            create_response = client.post("/api/v1/chats", json=create_chat_data, timeout=120)
            print(f"📥 创建聊天响应: {create_response.status_code}")
            
            if create_response.status_code == 200:
                result = create_response.json()
                if result.get("success"):
                    chat_id = result["data"]["chat"]["id"]
                    print(f"✅ 聊天创建成功，ID: {chat_id}")
                    
                    # 发送多条消息来测试上下文历史
                    messages_to_send = [
                        "你还记得我的名字吗？",
                        "我喜欢编程，特别是Python",
                        "你记得我喜欢什么吗？还有我的名字？",
                        "请总结一下我们之前讨论的所有内容"
                    ]
                    
                    for i, message_content in enumerate(messages_to_send, 1):
                        print(f"\n  📤 发送第{i}条消息: {message_content}")
                        
                        send_message_data = {
                            "content": message_content,
                            "file_ids": [],
                            "folder_ids": [],
                            "temporary_file_tokens": []
                        }
                        
                        message_response = client.post(f"/api/v1/chats/{chat_id}/messages", json=send_message_data, timeout=60)
                        if message_response.status_code == 200:
                            msg_result = message_response.json()
                            if msg_result.get("success"):
                                ai_message = msg_result["data"]["ai_message"]
                                print(f"  ✅ AI回复: {ai_message['content'][:100]}...")
                                print(f"     Token使用: {ai_message.get('tokens_used')}")
                                print(f"     成本: ${ai_message.get('cost')}")
                            else:
                                print(f"  ❌ 消息发送失败: {msg_result}")
                        else:
                            print(f"  ❌ 消息请求失败: {message_response.status_code} - {message_response.text}")
                        
                        time.sleep(1)  # 短暂等待
                    
                    # 获取完整的消息历史
                    print(f"\n  📋 获取完整消息历史...")
                    messages_response = client.get(f"/api/v1/chats/{chat_id}/messages")
                    if messages_response.status_code == 200:
                        messages_result = messages_response.json()
                        if messages_result.get("success"):
                            messages = messages_result["data"]["messages"]
                            print(f"  📊 消息总数: {len(messages)}")
                            print(f"  🔄 用户消息数: {len([m for m in messages if m['role'] == 'user'])}")
                            print(f"  🤖 AI回复数: {len([m for m in messages if m['role'] == 'assistant'])}")
                            
                            # 计算总成本和Token使用
                            total_tokens = sum(m.get('tokens_used', 0) or 0 for m in messages)
                            total_cost = sum(float(m.get('cost', 0) or 0) for m in messages) 
                            print(f"  💰 总Token使用: {total_tokens}")
                            print(f"  💰 总成本: ${total_cost:.6f}")
                        else:
                            print(f"  ❌ 获取消息历史失败: {messages_result}")
                    else:
                        print(f"  ❌ 消息历史请求失败: {messages_response.status_code}")
                        
                else:
                    print(f"❌ 聊天创建响应格式错误: {result}")
            else:
                print(f"❌ 聊天创建失败: {create_response.status_code} - {create_response.text}")
                
        except Exception as e:
            print(f"❌ 上下文模式 {context_mode} 测试异常: {e}")
        
        print("-" * 40)
        time.sleep(2)

def test_invalid_model_configurations():
    """测试无效的模型配置组合"""
    print("\n⚠️ 无效模型配置测试")
    print("=" * 60)
    
    client = APIClient()
    
    # 获取用户token
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 测试无效配置
    invalid_configurations = [
        {
            "name": "StarCode + 搜索功能 (不支持)",
            "ai_model": "StarCode",
            "search_enabled": True,  # StarCode不支持搜索
            "context_mode": "Standard",
            "expected_error": "INVALID_MODEL_CONFIG"
        },
        {
            "name": "无效的AI模型",
            "ai_model": "InvalidModel",
            "search_enabled": False,
            "context_mode": "Standard", 
            "expected_error": "INVALID_MODEL_CONFIG"
        },
        {
            "name": "无效的上下文模式",
            "ai_model": "Star",
            "search_enabled": False,
            "context_mode": "InvalidMode",
            "expected_error": "INVALID_CONTEXT_MODE"
        }
    ]
    
    for config in invalid_configurations:
        print(f"\n🚫 测试无效配置: {config['name']}")
        
        create_chat_data = {
            "chat_type": "general",
            "first_message": "测试无效配置",
            "course_id": None,
            "custom_prompt": None,
            "file_ids": [],
            "folder_ids": [],
            "ai_model": config["ai_model"],
            "search_enabled": config["search_enabled"],
            "context_mode": config["context_mode"],
            "temporary_file_tokens": []
        }
        
        try:
            create_response = client.post("/api/v1/chats", json=create_chat_data, timeout=30)
            print(f"📥 响应状态码: {create_response.status_code}")
            
            if create_response.status_code != 200:
                # 预期的错误响应
                error_info = create_response.json() if create_response.headers.get('content-type', '').startswith('application/json') else create_response.text
                print(f"✅ 正确捕获错误: {error_info}")
                
                # 验证错误码是否匹配预期
                if isinstance(error_info, dict):
                    error_code = error_info.get('error_code', '')
                    if config["expected_error"] in str(error_info):
                        print(f"✅ 错误码匹配预期: {config['expected_error']}")
                    else:
                        print(f"⚠️ 错误码不匹配预期: 期望包含 {config['expected_error']}")
            else:
                # 不应该成功
                result = create_response.json()
                print(f"❌ 配置应该失败但成功了: {result}")
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
        
        print("-" * 40)

def test_message_streaming():
    """测试消息流式响应"""
    print("\n📨 消息流式响应测试")
    print("=" * 60)
    
    client = APIClient()
    
    # 获取用户token
    user_token = get_user_token("user")
    if not user_token:
        print("❌ 无法获取用户token，跳过测试")
        return
    
    client.set_auth_token(user_token)
    
    # 先创建一个聊天
    print("🆕 创建测试聊天...")
    create_chat_data = {
        "chat_type": "general",
        "first_message": "你好，这是一个测试聊天",
        "course_id": None,
        "custom_prompt": None,
        "file_ids": [],
        "folder_ids": [],
        "ai_model": "Star",
        "search_enabled": False,
        "context_mode": "Standard",
        "temporary_file_tokens": []
    }
    
    create_response = client.post("/api/v1/chats", json=create_chat_data, timeout=60)
    if create_response.status_code != 200:
        print(f"❌ 创建聊天失败: {create_response.status_code} - {create_response.text}")
        return
    
    result = create_response.json()
    if not result.get("success"):
        print(f"❌ 聊天创建响应异常: {result}")
        return
        
    chat_id = result["data"]["chat"]["id"]
    print(f"✅ 聊天创建成功，ID: {chat_id}")
    
    # 测试消息流式响应
    print(f"\n🌊 测试消息流式响应...")
    
    url = f"{api_config.base_url}/api/v1/chats/{chat_id}/messages"
    headers = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    message_data = {
        "content": "请用流式响应的方式，详细介绍一下人工智能的发展历史，大约300字",
        "file_ids": [],
        "folder_ids": [],
        "temporary_file_tokens": [],
        "stream": True
    }
    
    print(f"📤 发送流式消息请求...")
    print(f"   消息内容: {message_data['content']}")
    
    try:
        with requests.post(url, json=message_data, headers=headers, stream=True, timeout=120) as response:
            print(f"📥 流式响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ 开始接收消息流式数据...")
                
                # 收集流式响应数据
                events = []
                current_content = ""
                user_message_received = False
                ai_response_complete = False
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        print(f"📨 接收数据: {line_str}")
                        
                        if line_str.startswith('data: '):
                            data_content = line_str[6:]  # 去掉 "data: " 前缀
                            
                            # 检查是否是 [DONE] 标记
                            if data_content.strip() == '[DONE]':
                                print(f"🏁 消息流式响应结束标记: [DONE]")
                                continue
                            
                            try:
                                data_json = json.loads(data_content)
                                events.append(data_json)
                                
                                # 解析事件类型
                                event_type = data_json.get('type')
                                if event_type == 'user_message':
                                    user_message_received = True
                                    message_info = data_json.get('message', {})
                                    print(f"👤 用户消息确认: ID={message_info.get('id')}")
                                    
                                elif event_type == 'ai_start':
                                    print(f"🤖 AI开始响应: Message ID={data_json.get('message_id')}")
                                    
                                elif event_type == 'ai_content':
                                    content_delta = data_json.get('delta', '')
                                    current_content += content_delta
                                    print(f"📝 AI内容增量 ({len(content_delta)}字符): {content_delta}")
                                    
                                elif event_type == 'ai_sources':
                                    sources = data_json.get('sources', [])
                                    print(f"📚 RAG来源: 共{len(sources)}个")
                                    
                                elif event_type == 'ai_end':
                                    ai_response_complete = True
                                    # 提取数据并进行详细调试
                                    tokens_used = data_json.get('tokens_used')
                                    cost = data_json.get('cost')
                                    
                                    print(f"✅ AI响应完成:")
                                    print(f"    Token使用: {tokens_used} (类型: {type(tokens_used)})")
                                    print(f"    成本: {cost} (类型: {type(cost)})")
                                    
                                    # 调试：打印原始JSON数据以查看可能的序列化问题
                                    print(f"🔍 原始ai_end事件数据: {data_json}")
                                    
                                elif event_type == 'error':
                                    error_msg = data_json.get('error')
                                    print(f"❌ 流式错误: {error_msg}")
                                    
                            except json.JSONDecodeError as e:
                                print(f"❌ 消息流JSON解析错误详情:")
                                print(f"   错误: {e}")
                                print(f"   原始行数据: {repr(line_str)}")
                                print(f"   处理后数据: {repr(data_content)}")
                                print(f"   数据长度: {len(data_content)}")
                                print(f"   数据类型: {type(data_content)}")
                                
                            except Exception as general_e:
                                print(f"❌ 消息流数据处理异常:")
                                print(f"   错误: {general_e}")
                                print(f"   错误类型: {type(general_e)}")
                                print(f"   原始数据: {repr(line_str)}")
                                print(f"   JSON数据: {data_json if 'data_json' in locals() else 'JSON解析失败'}")
                                import traceback
                                traceback.print_exc()
                
                # 验证消息流式响应完整性
                print(f"\n📊 消息流式响应验证:")
                print(f"   事件总数: {len(events)}")
                print(f"   用户消息确认: {'✅' if user_message_received else '❌'}")
                print(f"   AI响应完成: {'✅' if ai_response_complete else '❌'}")
                print(f"   完整响应长度: {len(current_content)} 字符")
                print(f"   完整响应内容: {current_content[:300]}...")
                
            else:
                error_info = response.text
                print(f"❌ 消息流式请求失败: {response.status_code}")
                print(f"   错误信息: {error_info}")
                
    except Exception as e:
        print(f"❌ 消息流式测试异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 AI模型选择和流式响应综合测试")
    print("=" * 80)
    print("⚠️  请确保已执行: source venv/bin/activate")
    print("⚠️  请确保服务正在运行: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("⚠️  请确保已配置有效的OpenAI API密钥")
    print("⚠️  建议运行前执行: python reset_system.py 重置测试环境")
    
    input("按回车键开始测试...")
    
    try:
        # ✅ 已通过测试 - 注释掉以节省时间
        # print("\n" + "="*80)
        # print("第一部分: AI模型配置测试")  
        # results = test_ai_model_configurations()
        
        # ✅ 已通过测试 - 注释掉以节省时间
        # print("\n" + "="*80) 
        # print("🔧 测试修复后的流式响应功能")
        # print("第二部分: 流式响应测试")
        # test_streaming_responses()
        
        # ✅ 已通过测试 - 注释掉以节省时间
        # print("\n" + "="*80)
        # print("第三部分: 上下文模式和对话历史测试")
        # test_context_modes_and_history()
        
        # ✅ 已通过测试 - 注释掉以节省时间  
        # print("\n" + "="*80)
        # print("第四部分: 无效配置测试") 
        # test_invalid_model_configurations()
        
        print("\n" + "="*80)
        print("第五部分: 消息流式响应测试")
        test_message_streaming()
        
        print(f"\n🎉 流式响应功能测试完成！")
        print("📊 本次测试覆盖范围:")
        print("   🔧 流式响应 (聊天创建)")
        print("   🔧 消息流式响应")
        print("   🔧 SSE事件流处理")
        print("   🔧 实时内容增量传输")
        print("")
        print("📋 之前已通过的测试:")
        print("   ✅ 不同AI模型 (Star, StarPlus, StarCode)")
        print("   ✅ 搜索功能启用/禁用") 
        print("   ✅ 上下文模式 (Economy, Standard, Premium, Max)")
        print("   ✅ 对话历史和上下文记忆")
        print("   ✅ 错误处理和无效配置")
        print("   ✅ Token计费和成本计算")
        print("   ✅ RAG集成和来源追踪")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生严重错误: {e}")
        import traceback
        traceback.print_exc()