#!/bin/bash

# 文件上传功能综合测试（使用 curl）
# 测试白名单验证、图片处理等功能

BASE_URL="http://localhost:8000"
TEST_FILES_DIR="/Users/mannormal/Downloads/fyp/test_file"

echo "============================================================"
echo "🚀 开始文件上传功能综合测试（curl版本）"
echo "============================================================"

# 1. 登录获取token
echo "🔐 正在登录..."
LOGIN_RESPONSE=$(curl -s --noproxy localhost \
  -X POST "${BASE_URL}/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "test123456"}')

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('data', {}).get('access_token', '') if data.get('success') else '')" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ 登录失败: $LOGIN_RESPONSE"
    exit 1
fi

echo "✅ 登录成功，Token: ${TOKEN:0:20}..."

# 2. 测试图片文件普通上传（应该拒绝）
echo ""
echo "🔍 测试1: 图片文件普通上传（应该拒绝）"
IMAGE_PATH="${TEST_FILES_DIR}/Screenshot 2025-07-25 at 8.21.53 AM.png"

if [ ! -f "$IMAGE_PATH" ]; then
    echo "❌ 图片文件不存在: $IMAGE_PATH"
else
    RESPONSE=$(curl -s --noproxy localhost \
      -X POST "${BASE_URL}/api/v1/global-files/upload" \
      -H "Authorization: Bearer $TOKEN" \
      -F "file=@\"${IMAGE_PATH}\";type=image/png" \
      -F "scope=global" \
      -F "description=测试图片上传" \
      -F "visibility=public")
    
    SUCCESS=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)
    if [ "$SUCCESS" = "False" ]; then
        ERROR_MSG=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('detail', 'Unknown error'))" 2>/dev/null)
        echo "✅ 符合预期: 图片文件被拒绝 - $ERROR_MSG"
    else
        echo "❌ 意外结果: 图片文件被接受了"
        echo "   响应: $RESPONSE"
    fi
fi

# 3. 测试图片文件临时上传（应该成功）
echo ""
echo "🔍 测试2: 图片文件临时上传（应该成功）"

TEMP_RESPONSE=$(curl -s --noproxy localhost \
  -X POST "${BASE_URL}/api/v1/files/temporary" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@\"${IMAGE_PATH}\";type=image/png" \
  -F "purpose=chat_upload" \
  -F "expiry_hours=5")

TEMP_TOKEN=$(echo $TEMP_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('data', {}).get('token', '') if data.get('success') else '')" 2>/dev/null)

if [ -n "$TEMP_TOKEN" ]; then
    echo "✅ 图片临时上传成功，Token: ${TEMP_TOKEN:0:10}..."
    IMAGE_TOKEN=$TEMP_TOKEN
else
    echo "❌ 图片临时上传失败: $TEMP_RESPONSE"
fi

# 4. 测试文档文件临时上传（应该成功）
echo ""
echo "🔍 测试3: 文档文件临时上传（应该成功）"
DOC_PATH="${TEST_FILES_DIR}/test_files/valid_text.txt"

if [ ! -f "$DOC_PATH" ]; then
    echo "❌ 文档文件不存在: $DOC_PATH"
else
    DOC_TEMP_RESPONSE=$(curl -s --noproxy localhost \
      -X POST "${BASE_URL}/api/v1/files/temporary" \
      -H "Authorization: Bearer $TOKEN" \
      -F "file=@${DOC_PATH};type=text/plain" \
      -F "purpose=chat_upload" \
      -F "expiry_hours=5")
    
    DOC_TEMP_TOKEN=$(echo $DOC_TEMP_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('data', {}).get('token', '') if data.get('success') else '')" 2>/dev/null)
    
    if [ -n "$DOC_TEMP_TOKEN" ]; then
        echo "✅ 文档临时上传成功，Token: ${DOC_TEMP_TOKEN:0:10}..."
    else
        echo "❌ 文档临时上传失败: $DOC_TEMP_RESPONSE"
    fi
fi

# 5. 测试文档文件普通上传（应该成功）
echo ""
echo "🔍 测试4: 文档文件普通上传（应该成功）"
PY_PATH="${TEST_FILES_DIR}/test_files/valid_python.py"

if [ ! -f "$PY_PATH" ]; then
    echo "❌ Python文件不存在: $PY_PATH"
else
    PY_RESPONSE=$(curl -s --noproxy localhost \
      -X POST "${BASE_URL}/api/v1/global-files/upload" \
      -H "Authorization: Bearer $TOKEN" \
      -F "file=@${PY_PATH};type=text/x-python" \
      -F "scope=global" \
      -F "description=测试Python文件上传" \
      -F "visibility=public")
    
    PY_SUCCESS=$(echo $PY_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)
    if [ "$PY_SUCCESS" = "True" ]; then
        echo "✅ Python文件上传成功"
    else
        echo "❌ Python文件上传失败: $PY_RESPONSE"
    fi
fi

# 6. 测试不支持格式文件上传（应该拒绝）
echo ""
echo "🔍 测试5: 不支持格式文件上传（应该拒绝）"
UNSUPPORTED_PATH="${TEST_FILES_DIR}/test_files/unsupported.xyz"

if [ ! -f "$UNSUPPORTED_PATH" ]; then
    echo "❌ 不支持格式文件不存在: $UNSUPPORTED_PATH"
else
    UNSUPPORTED_RESPONSE=$(curl -s --noproxy localhost \
      -X POST "${BASE_URL}/api/v1/global-files/upload" \
      -H "Authorization: Bearer $TOKEN" \
      -F "file=@${UNSUPPORTED_PATH};type=application/octet-stream" \
      -F "scope=global" \
      -F "description=测试不支持格式" \
      -F "visibility=public")
    
    UNSUPPORTED_SUCCESS=$(echo $UNSUPPORTED_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)
    if [ "$UNSUPPORTED_SUCCESS" = "False" ]; then
        ERROR_MSG=$(echo $UNSUPPORTED_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('detail', 'Unknown error'))" 2>/dev/null)
        echo "✅ 符合预期: 不支持格式被拒绝 - $ERROR_MSG"
    else
        echo "❌ 意外结果: 不支持格式被接受了"
        echo "   响应: $UNSUPPORTED_RESPONSE"
    fi
fi

echo ""
echo "============================================================"
echo "📊 测试完成！"
echo "============================================================"

if [ -n "$IMAGE_TOKEN" ]; then
    echo "🖼️ 图片Token可用于聊天测试: $IMAGE_TOKEN"
    echo ""
    echo "可以用以下命令测试图片聊天："
    echo "curl --noproxy localhost -X POST '${BASE_URL}/api/v1/chats' \\"
    echo "  -H 'Authorization: Bearer $TOKEN' \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"first_message\": \"请分析这张图片\", \"temporary_file_tokens\": [\"$IMAGE_TOKEN\"], \"chat_type\": \"general\", \"ai_model\": \"Star\"}'"
fi