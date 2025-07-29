  系统健康检查 / System Health Check

  - GET /health - 健康检查

  用户认证 / Authentication
  - POST /api/v1/auth/register - 用户注册
  - POST /api/v1/auth/login - 用户登录
  - 🔒 GET /api/v1/auth/me - 获取当前用户信息
  - 🔒 PUT /api/v1/auth/me - 更新用户信息
  - 🔒 POST /api/v1/auth/logout - 用户登出

  学期管理 / Semesters

  - 🔒 GET /api/v1/semesters - 获取学期列表
  - 🛡️ POST /api/v1/semesters - 创建学期
  - 🛡️ PUT /api/v1/semesters/{semester_id} - 更新学期
  - 🛡️ DELETE /api/v1/semesters/{semester_id} - 删除学期

  课程管理 / Course Management

  - 🔒 GET /api/v1/courses - 获取课程列表
  - 🔒 POST /api/v1/courses - 创建课程
  - 🔒 PUT /api/v1/courses/{course_id} - 更新课程
  - 🔒 DELETE /api/v1/courses/{course_id} - 删除课程

  文件夹管理 / Folder Management

  - 🔒 GET /api/v1/courses/{course_id}/folders - 获取课程文件夹
  - 🔒 POST /api/v1/courses/{course_id}/folders - 创建文件夹
  - 🔒 PUT /api/v1/folders/{folder_id} - 更新文件夹（你漏了path参数）
  - 🔒 DELETE /api/v1/folders/{folder_id} - 删除文件夹

  文件管理 / File Management

  - 🔒 POST /api/v1/files/upload - 上传文件到课程
  - 🔒 GET /api/v1/folders/{folder_id}/files - 获取文件夹文件
  - 🔒 GET /api/v1/files/{file_id}/download - 下载文件
  - 🔒 DELETE /api/v1/files/{file_id} - 删除文件
  - 🔒 POST /api/v1/tempfiles/upload - 上传临时文件（你写成temfile了）
  - 🛡️ POST /api/v1/globalfiles/upload - 上传全局文件
  - 🛡️ GET /api/v1/globalfiles - 获取全局文件列表（你写成files了）
  - 🛡️ DELETE /api/v1/globalfiles/{id} - 删除全局文件

  聊天管理 / Chat Management

  - 🔒 GET /api/v1/chats - 获取聊天列表
  - 🔒 POST /api/v1/chats - 创建聊天
  - 🔒 PUT /api/v1/chats/{chat_id} - 更新聊天
  - 🔒 DELETE /api/v1/chats/{chat_id} - 删除聊天

  消息管理 / Message Management

  - 🔒 GET /api/v1/chats/{chat_id}/messages - 获取聊天消息
  - 🔒 POST /api/v1/chats/{chat_id}/messages - 发送消息
  - 🔒 PUT /api/v1/messages/{message_id} - 编辑消息
  - 🔒 DELETE /api/v1/messages/{message_id} - 删除消息

  管理员管理 / Admin Management

  - 🛡️ POST /api/v1/invite-codes - 创建邀请码
  - 🛡️ GET /api/v1/invite-codes - 获取邀请码列表
  - 🛡️ PUT /api/v1/invite-codes/{invite_code_id} - 更新邀请码
  - 🛡️ DELETE /api/v1/invite-codes/{invite_code_id} - 删除邀请码

