# 校园LLM系统 API 索引

## 概述
校园LLM系统提供一套完整的RESTful API，用于管理用户、学期、课程、文件、聊天、消息以及AI交互。所有API都遵循一致的JSON响应格式。

## 基础URL
所有API都以 `/api/v1/` 为前缀。

## 通用响应格式
```json
{
  "success": true,
  "data": {...},
  "message" : str
}
```

错误响应：
```json
{
  "success": false,
  "error": str
}
```

## API模块目录

1. [认证与用户管理 API](api_auth.md)
   - 用户注册、登录、个人资料管理

2. [学期与课程管理 API](api_semester_course.md)
   - 学期管理、课程创建与管理

3. [文件夹与文件管理 API](api_folder_file.md)
   - 文件夹操作、文件上传与管理

4. [聊天、消息与AI功能 API](api_chat_message_rag.md)
   - 聊天创建与管理
   - 消息发送与检索
   - AI对话与RAG检索功能

5. [系统管理 API](api_admin.md)
   - 用户管理、系统配置、统计信息

## 认证方式
所有API（除了登录和注册）都需要在请求头中包含以下认证信息：
```
Authorization: Bearer {token}
```

## 主要功能亮点

- **无缝集成的RAG系统**：根据聊天类型自动从不同知识库检索相关信息
- **聊天标题自动生成**：基于首条消息内容智能生成聊天标题
- **文件智能去重**：通过SHA256哈希实现物理文件去重，节省存储空间
- **支持流式响应**：AI对话支持流式响应，提供更好的用户体验
- **细粒度权限控制**：基于用户角色和课程所有权的访问控制
