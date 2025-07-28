系统健康检查/System Health Check


GET
/health
健康检查


GET
/
系统信息

认证/Authentication


POST
/api/v1/auth/register
用户注册


POST
/api/v1/auth/login
用户登录


GET
/api/v1/auth/me
获取当前用户信息



PUT
/api/v1/auth/me
更新用户信息



POST
/api/v1/auth/logout
用户登出



POST
/api/v1/auth/verify-email
验证邮箱


POST
/api/v1/auth/resend-verification
重发验证码

学期管理/Semesters


GET
/api/v1/semesters
Get Semesters



POST
/api/v1/semesters
Create Semester



PUT
/api/v1/semesters/{semester_id}
Update Semester



GET
/api/v1/semesters/{semester_id}
Get Semester



DELETE
/api/v1/semesters/{semester_id}
Delete Semester


课程管理/Course Management


GET
/api/v1/courses
Get Courses



POST
/api/v1/courses
Create Course



PUT
/api/v1/courses/{course_id}
Update Course



GET
/api/v1/courses/{course_id}
Get Course



DELETE
/api/v1/courses/{course_id}
Delete Course


文件夹管理/Folder Management


GET
/api/v1/courses/{course_id}/folders
Get Course Folders



POST
/api/v1/courses/{course_id}/folders
Create Folder



DELETE
/api/v1/folders/{folder_id}
Delete Folder


文件管理/File Management


POST
/api/v1/files/temporary
Upload Temporary File



POST
/api/v1/files/upload
Upload File



GET
/api/v1/folders/{folder_id}/files
Get Folder Files



GET
/api/v1/files/{file_id}/download
Download File



GET
/api/v1/files/temporary/{token}/download
Download Temporary File


DELETE
/api/v1/files/temporary/{file_id}
Delete Temporary File



DELETE
/api/v1/files/{file_id}
Delete File


聊天管理/Chat Management


GET
/api/v1/chats
Get Chats



POST
/api/v1/chats
Create Chat



PUT
/api/v1/chats/{chat_id}
Update Chat



DELETE
/api/v1/chats/{chat_id}
Delete Chat


消息管理/Message Management


GET
/api/v1/chats/{chat_id}/messages
Get Chat Messages



POST
/api/v1/chats/{chat_id}/messages
Send Message



PUT
/api/v1/messages/{message_id}
Edit Message



DELETE
/api/v1/messages/{message_id}
Delete Message


管理员管理/Admin Management


POST
/api/v1/invite-codes
创建邀请码



GET
/api/v1/invite-codes
获取邀请码列表



PUT
/api/v1/invite-codes/{invite_code_id}
更新邀请码



DELETE
/api/v1/invite-codes/{invite_code_id}
删除邀请码



POST
/api/v1/global-files/upload
上传全局文件



POST
/api/v1/files/{file_id}/reprocess-rag
重新处理文件RAG



GET
/api/v1/global-files
获取全局文件列表



DELETE
/api/v1/global-files/{file_id}
删除全局文件



