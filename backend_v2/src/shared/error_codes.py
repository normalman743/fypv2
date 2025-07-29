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
    
    # === 课程管理相关 ===
    COURSE_NOT_FOUND = "COURSE_NOT_FOUND"              # 课程不存在
    COURSE_ACCESS_DENIED = "COURSE_ACCESS_DENIED"      # 课程访问被拒绝
    COURSE_UPDATE_DENIED = "COURSE_UPDATE_DENIED"      # 课程更新被拒绝
    COURSE_DELETE_DENIED = "COURSE_DELETE_DENIED"      # 课程删除被拒绝
    COURSE_CODE_EXISTS = "COURSE_CODE_EXISTS"          # 课程代码已存在
    SEMESTER_NOT_FOUND = "SEMESTER_NOT_FOUND"          # 学期不存在
    SEMESTER_CODE_EXISTS = "SEMESTER_CODE_EXISTS"      # 学期代码已存在
    SEMESTER_HAS_COURSES = "SEMESTER_HAS_COURSES"      # 学期包含课程
    
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


class SystemErrorCodes:
    """系统相关错误码"""
    RATE_LIMIT_EXCEEDED = ErrorCodes.RATE_LIMIT_EXCEEDED
    INVALID_RESET_TOKEN = ErrorCodes.INVALID_RESET_TOKEN
    INTERNAL_SERVER_ERROR = ErrorCodes.INTERNAL_SERVER_ERROR