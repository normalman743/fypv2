#!/bin/bash
# RAG功能测试脚本
# 测试文件上传和AI聊天功能

set -e  # 遇到错误立即退出

echo "🚀 开始RAG功能测试"
echo "===================="

# 配置
BASE_URL="http://localhost:8000"
TEST_FILE_DIR="/Users/mannormal/Downloads/fyp/test_file"

# 1. 获取admin token
echo "📝 1. 获取admin登录token..."
LOGIN_RESPONSE=$(curl --noproxy '*' -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123456"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['access_token'])" 2>/dev/null || echo "")

if [ -z "$TOKEN" ]; then
  echo "❌ 登录失败，无法获取token"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✅ 登录成功，token: ${TOKEN:0:20}..."

# 2. 上传测试文件
echo
echo "📁 2. 上传测试文件..."

# 上传txt文件
echo "📄 上传 post_messages.txt..."
TXT_RESPONSE=$(curl --noproxy '*' -s -X POST "$BASE_URL/api/v1/files/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@$TEST_FILE_DIR/post_messages.txt" \
  -F "scope=general")

echo "TXT上传响应: $TXT_RESPONSE"

# 上传PDF文件
echo "📄 上传PDF文件..."
PDF_RESPONSE=$(curl --noproxy '*' -s -X POST "$BASE_URL/api/v1/files/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@$TEST_FILE_DIR/Res - 大學核心課程選課一年級學生須知.pdf" \
  -F "scope=general")

echo "PDF上传响应: $PDF_RESPONSE"

# 上传DOCX文件
echo "📄 上传DOCX文件..."
DOCX_RESPONSE=$(curl --noproxy '*' -s -X POST "$BASE_URL/api/v1/files/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@$TEST_FILE_DIR/数据收集/入学前/临时身份证.docx" \
  -F "scope=general")

echo "DOCX上传响应: $DOCX_RESPONSE"

# 3. 等待文件处理
echo
echo "⏳ 3. 等待文件处理完成..."
sleep 10

# 4. 创建聊天会话并测试RAG
echo
echo "💬 4. 创建聊天会话并测试RAG功能..."

# 创建聊天会话
CHAT_RESPONSE=$(curl --noproxy '*' -s -X POST "$BASE_URL/api/v1/chats" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，我想了解一下上传的文件内容，能帮我总结一下吗？",
    "file_context_scope": "general"
  }')

echo "聊天创建响应: $CHAT_RESPONSE"

# 提取chat_id
CHAT_ID=$(echo $CHAT_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('chat', {}).get('id', ''))" 2>/dev/null || echo "")

if [ -z "$CHAT_ID" ]; then
  echo "❌ 无法获取chat_id"
  exit 1
fi

echo "✅ 聊天会话创建成功，chat_id: $CHAT_ID"

# 5. 发送具体问题测试RAG
echo
echo "🤖 5. 发送具体问题测试RAG..."

# 问题1：关于选课
echo "❓ 问题1：关于选课信息..."
MESSAGE1_RESPONSE=$(curl --noproxy '*' -s -X POST "$BASE_URL/api/v1/chats/$CHAT_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "文件中有关于选课的信息吗？请详细说明。",
    "file_context_scope": "general"
  }')

echo "回答1: $MESSAGE1_RESPONSE"

# 问题2：关于临时身份证
echo
echo "❓ 问题2：关于临时身份证..."
MESSAGE2_RESPONSE=$(curl --noproxy '*' -s -X POST "$BASE_URL/api/v1/chats/$CHAT_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "临时身份证的相关信息是什么？",
    "file_context_scope": "general"
  }')

echo "回答2: $MESSAGE2_RESPONSE"

# 问题3：关于post_messages内容
echo
echo "❓ 问题3：关于post_messages内容..."
MESSAGE3_RESPONSE=$(curl --noproxy '*' -s -X POST "$BASE_URL/api/v1/chats/$CHAT_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "post_messages.txt文件里说了什么内容？",
    "file_context_scope": "general"
  }')

echo "回答3: $MESSAGE3_RESPONSE"

# 6. 查看聊天历史
echo
echo "📜 6. 查看聊天历史..."
HISTORY_RESPONSE=$(curl --noproxy '*' -s -X GET "$BASE_URL/api/v1/chats/$CHAT_ID/messages" \
  -H "Authorization: Bearer $TOKEN")

echo "聊天历史: $HISTORY_RESPONSE"

echo
echo "🎉 RAG功能测试完成！"
echo "===================="