"""统一错误码定义

所有模块必须使用这些预定义的错误码常量，禁止硬编码错误码字符串。
"""


class ErrorCodes:
    """统一错误码定义 - 所有模块必须使用这些预定义常量"""
    
    # === 认证相关错误码 ===
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"        # 登录凭据无效
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"              # 账户被禁用
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"                  # 账户被锁定
    USER_NOT_FOUND = "USER_NOT_FOUND"                  # 用户不存在
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"        # 用户已存在
    USERNAME_EXISTS = "USERNAME_EXISTS"                # 用户名已存在
    INVALID_PASSWORD = "INVALID_PASSWORD"              # 密码错误
    
    # === 邮箱验证相关 ===
    EMAIL_EXISTS = "EMAIL_EXISTS"                      # 邮箱已存在
    EMAIL_NOT_FOUND = "EMAIL_NOT_FOUND"                # 邮箱不存在
    EMAIL_ALREADY_VERIFIED = "EMAIL_ALREADY_VERIFIED"  # 邮箱已验证
    INVALID_VERIFICATION_CODE = "INVALID_VERIFICATION_CODE"  # 验证码无效
    INVALID_EMAIL_DOMAIN = "INVALID_EMAIL_DOMAIN"      # 邮箱域名不支持
    
    # === 邀请码相关 ===
    INVALID_INVITE_CODE = "INVALID_INVITE_CODE"        # 邀请码无效
    INVITE_CODE_EXPIRED = "INVITE_CODE_EXPIRED"        # 邀请码过期
    REGISTRATION_DISABLED = "REGISTRATION_DISABLED"    # 注册功能已关闭
    INVITE_CODE_NOT_FOUND = "INVITE_CODE_NOT_FOUND"    # 邀请码不存在
    INVITE_CODE_CONFLICT = "INVITE_CODE_CONFLICT"      # 邀请码生成冲突
    INVITE_CODE_ALREADY_USED = "INVITE_CODE_ALREADY_USED"  # 邀请码已被使用
    USED_INVITE_CODE_READONLY = "USED_INVITE_CODE_READONLY"  # 已使用邀请码为只读
    INVALID_EXPIRE_TIME = "INVALID_EXPIRE_TIME"        # 过期时间无效
    INVALID_DATE_RANGE = "INVALID_DATE_RANGE"          # 日期范围无效
    DATE_RANGE_TOO_LARGE = "DATE_RANGE_TOO_LARGE"      # 日期范围过大
    
    # === 课程管理相关 ===
    COURSE_NOT_FOUND = "COURSE_NOT_FOUND"              # 课程不存在
    COURSE_ACCESS_DENIED = "COURSE_ACCESS_DENIED"      # 课程访问被拒绝
    COURSE_UPDATE_DENIED = "COURSE_UPDATE_DENIED"      # 课程更新被拒绝
    COURSE_DELETE_DENIED = "COURSE_DELETE_DENIED"      # 课程删除被拒绝
    COURSE_CODE_EXISTS = "COURSE_CODE_EXISTS"          # 课程代码已存在
    SEMESTER_NOT_FOUND = "SEMESTER_NOT_FOUND"          # 学期不存在
    SEMESTER_CODE_EXISTS = "SEMESTER_CODE_EXISTS"      # 学期代码已存在
    SEMESTER_HAS_COURSES = "SEMESTER_HAS_COURSES"      # 学期包含课程
    
    # === 聊天相关 ===
    CHAT_NOT_FOUND = "CHAT_NOT_FOUND"                  # 聊天不存在
    MESSAGE_NOT_FOUND = "MESSAGE_NOT_FOUND"            # 消息不存在
    
    # === AI相关 ===
    AI_MODEL_NOT_FOUND = "AI_MODEL_NOT_FOUND"          # AI模型不存在
    AI_CONFIG_NOT_FOUND = "AI_CONFIG_NOT_FOUND"        # AI配置不存在
    
    # === 存储相关错误码 ===
    FOLDER_NOT_FOUND = "FOLDER_NOT_FOUND"              # 文件夹不存在
    FOLDER_NAME_EXISTS = "FOLDER_NAME_EXISTS"          # 文件夹名称已存在
    CANNOT_DELETE_DEFAULT_FOLDER = "CANNOT_DELETE_DEFAULT_FOLDER"  # 无法删除默认文件夹
    FOLDER_NOT_EMPTY = "FOLDER_NOT_EMPTY"              # 文件夹不为空
    
    FILE_NOT_FOUND = "FILE_NOT_FOUND"                  # 文件不存在
    FILE_MISSING = "FILE_MISSING"                      # 文件丢失
    FILE_TOO_LARGE = "FILE_TOO_LARGE"                  # 文件过大
    STORAGE_LIMIT_EXCEEDED = "STORAGE_LIMIT_EXCEEDED"  # 存储空间超限
    UPLOAD_ERROR = "UPLOAD_ERROR"                      # 上传错误
    STORAGE_ERROR = "STORAGE_ERROR"                    # 存储错误
    ACCESS_DENIED = "ACCESS_DENIED"                    # 访问被拒绝
    
    TEMP_FILE_NOT_FOUND = "TEMP_FILE_NOT_FOUND"        # 临时文件不存在
    TEMP_FILE_EXPIRED = "TEMP_FILE_EXPIRED"            # 临时文件已过期
    TEMP_FILE_MISSING = "TEMP_FILE_MISSING"            # 临时文件丢失
    
    GLOBAL_FILE_NOT_FOUND = "GLOBAL_FILE_NOT_FOUND"    # 全局文件不存在
    ADMIN_REQUIRED = "ADMIN_REQUIRED"                  # 需要管理员权限
    DATABASE_ERROR = "DATABASE_ERROR"                  # 数据库错误
    DELETE_ERROR = "DELETE_ERROR"                      # 删除错误
    QUERY_ERROR = "QUERY_ERROR"                        # 查询错误
    
    # === 新增错误码 ===
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"                # AI模型不存在
    CONFIG_NOT_FOUND = "CONFIG_NOT_FOUND"              # 配置不存在
    GENERATION_ERROR = "GENERATION_ERROR"              # 生成错误
    CREATE_ERROR = "CREATE_ERROR"                      # 创建错误
    UPDATE_ERROR = "UPDATE_ERROR"                      # 更新错误
    COMMIT_ERROR = "COMMIT_ERROR"                      # 提交错误
    SEND_ERROR = "SEND_ERROR"                          # 发送错误
    EDIT_ERROR = "EDIT_ERROR"                          # 编辑错误
    RATE_CHECK_ERROR = "RATE_CHECK_ERROR"              # 频率检查错误
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"              # 依赖错误
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"    # 不支持的文件类型
    INVALID_FILE_EXTENSION = "INVALID_FILE_EXTENSION"  # 无效的文件扩展名
    PROCESSING_ERROR = "PROCESSING_ERROR"              # 处理错误
    RETRIEVAL_ERROR = "RETRIEVAL_ERROR"                # 检索错误
    DELETION_ERROR = "DELETION_ERROR"                  # 删除错误
    STATS_ERROR = "STATS_ERROR"                        # 统计错误
    NETWORK_ERROR = "NETWORK_ERROR"                    # 网络错误
    BULK_SEND_ERROR = "BULK_SEND_ERROR"                # 批量发送错误
    API_CONNECTION_ERROR = "API_CONNECTION_ERROR"      # API连接错误
    API_CALL_ERROR = "API_CALL_ERROR"                  # API调用错误
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"        # 配置错误
    
    # === 系统相关 ===
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"        # 请求频率超限
    INVALID_RESET_TOKEN = "INVALID_RESET_TOKEN"        # 重置令牌无效
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"    # 服务器内部错误


# 为了方便使用，提供分组访问
class AuthErrorCodes:
    """认证相关错误码"""
    INVALID_CREDENTIALS = ErrorCodes.INVALID_CREDENTIALS
    ACCOUNT_DISABLED = ErrorCodes.ACCOUNT_DISABLED
    ACCOUNT_LOCKED = ErrorCodes.ACCOUNT_LOCKED
    USER_NOT_FOUND = ErrorCodes.USER_NOT_FOUND
    USER_ALREADY_EXISTS = ErrorCodes.USER_ALREADY_EXISTS
    USERNAME_EXISTS = ErrorCodes.USERNAME_EXISTS
    INVALID_PASSWORD = ErrorCodes.INVALID_PASSWORD


class EmailErrorCodes:
    """邮箱验证相关错误码"""
    EMAIL_EXISTS = ErrorCodes.EMAIL_EXISTS
    EMAIL_NOT_FOUND = ErrorCodes.EMAIL_NOT_FOUND
    EMAIL_ALREADY_VERIFIED = ErrorCodes.EMAIL_ALREADY_VERIFIED
    INVALID_VERIFICATION_CODE = ErrorCodes.INVALID_VERIFICATION_CODE
    INVALID_EMAIL_DOMAIN = ErrorCodes.INVALID_EMAIL_DOMAIN


class CourseErrorCodes:
    """课程管理相关错误码"""
    COURSE_NOT_FOUND = ErrorCodes.COURSE_NOT_FOUND
    COURSE_ACCESS_DENIED = ErrorCodes.COURSE_ACCESS_DENIED
    COURSE_UPDATE_DENIED = ErrorCodes.COURSE_UPDATE_DENIED
    COURSE_DELETE_DENIED = ErrorCodes.COURSE_DELETE_DENIED
    COURSE_CODE_EXISTS = ErrorCodes.COURSE_CODE_EXISTS
    SEMESTER_NOT_FOUND = ErrorCodes.SEMESTER_NOT_FOUND
    SEMESTER_CODE_EXISTS = ErrorCodes.SEMESTER_CODE_EXISTS
    SEMESTER_HAS_COURSES = ErrorCodes.SEMESTER_HAS_COURSES


class StorageErrorCodes:
    """存储相关错误码"""
    FOLDER_NOT_FOUND = ErrorCodes.FOLDER_NOT_FOUND
    FOLDER_NAME_EXISTS = ErrorCodes.FOLDER_NAME_EXISTS
    CANNOT_DELETE_DEFAULT_FOLDER = ErrorCodes.CANNOT_DELETE_DEFAULT_FOLDER
    FOLDER_NOT_EMPTY = ErrorCodes.FOLDER_NOT_EMPTY
    FILE_NOT_FOUND = ErrorCodes.FILE_NOT_FOUND
    FILE_MISSING = ErrorCodes.FILE_MISSING
    UPLOAD_ERROR = ErrorCodes.UPLOAD_ERROR
    STORAGE_ERROR = ErrorCodes.STORAGE_ERROR
    ACCESS_DENIED = ErrorCodes.ACCESS_DENIED
    TEMP_FILE_NOT_FOUND = ErrorCodes.TEMP_FILE_NOT_FOUND
    TEMP_FILE_EXPIRED = ErrorCodes.TEMP_FILE_EXPIRED
    TEMP_FILE_MISSING = ErrorCodes.TEMP_FILE_MISSING
    GLOBAL_FILE_NOT_FOUND = ErrorCodes.GLOBAL_FILE_NOT_FOUND
    ADMIN_REQUIRED = ErrorCodes.ADMIN_REQUIRED
    DATABASE_ERROR = ErrorCodes.DATABASE_ERROR
    DELETE_ERROR = ErrorCodes.DELETE_ERROR
    QUERY_ERROR = ErrorCodes.QUERY_ERROR


class SystemErrorCodes:
    """系统相关错误码"""
    RATE_LIMIT_EXCEEDED = ErrorCodes.RATE_LIMIT_EXCEEDED
    INVALID_RESET_TOKEN = ErrorCodes.INVALID_RESET_TOKEN
    INTERNAL_SERVER_ERROR = ErrorCodes.INTERNAL_SERVER_ERROR