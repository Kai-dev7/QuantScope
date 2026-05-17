"""
基于数据库的认证路由 - 改进版
替代原有的基于配置文件的认证机制
"""

import time
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel

from app.services.auth_service import AuthService
from app.services.user_service import user_service
from app.models.user import UserCreate, UserUpdate
from app.services.operation_log_service import log_operation
from app.models.operation_log import ActionType
from app.utils.timezone import now_tz
from app.core.redis_client import get_redis_service

# 尝试导入日志管理器
try:
    from tradingagents.utils.logging_manager import get_logger
except ImportError:
    # 如果导入失败，使用标准日志
    import logging
    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(name)

logger = get_logger('auth_db')

# 统一响应格式
class ApiResponse(BaseModel):
    success: bool = True
    data: dict = {}
    message: str = ""

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class ResetPasswordRequest(BaseModel):
    username: str
    new_password: str

class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
    is_admin: bool = False

async def get_current_user(authorization: Optional[str] = Header(default=None)) -> dict:
    """获取当前用户信息"""
    logger.debug(f"🔐 认证检查开始")
    logger.debug(f"📋 Authorization header: {authorization[:50] if authorization else 'None'}...")

    if not authorization:
        logger.warning("❌ 没有Authorization header")
        raise HTTPException(status_code=401, detail="No authorization header")

    if not authorization.lower().startswith("bearer "):
        logger.warning(f"❌ Authorization header格式错误: {authorization[:20]}...")
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    token = authorization.split(" ", 1)[1]
    logger.debug(f"🎫 提取的token长度: {len(token)}")
    logger.debug(f"🎫 Token前20位: {token[:20]}...")

    token_data = AuthService.verify_token(token)
    logger.debug(f"🔍 Token验证结果: {token_data is not None}")

    if not token_data:
        logger.warning("❌ Token验证失败")
        raise HTTPException(status_code=401, detail="Invalid token")

    # 从数据库获取用户信息
    user = await user_service.get_user_by_username(token_data.sub)
    if not user:
        logger.warning(f"❌ 用户不存在: {token_data.sub}")
        raise HTTPException(status_code=401, detail="User not found")

    if not user.is_active:
        logger.warning(f"❌ 用户已禁用: {token_data.sub}")
        raise HTTPException(status_code=401, detail="User is inactive")

    logger.debug(f"✅ 认证成功，用户: {token_data.sub}")

    # 返回完整的用户信息，包括偏好设置
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "name": user.username,
        "is_admin": user.is_admin,
        "roles": ["admin"] if user.is_admin else ["user"],
        "preferences": user.preferences.model_dump() if user.preferences else {}
    }

@router.post("/login")
async def login(payload: LoginRequest, request: Request):
    """用户登录"""
    start_time = time.time()

    # 获取客户端信息
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    logger.info(f"🔐 登录请求 - 用户名: {payload.username}, IP: {ip_address}")

    try:
        # 验证输入
        if not payload.username or not payload.password:
            logger.warning(f"❌ 登录失败 - 用户名或密码为空")
            await log_operation(
                user_id="unknown",
                username=payload.username or "unknown",
                action_type=ActionType.USER_LOGIN,
                action="用户登录",
                details={"reason": "用户名和密码不能为空"},
                success=False,
                error_message="用户名和密码不能为空",
                duration_ms=int((time.time() - start_time) * 1000),
                ip_address=ip_address,
                user_agent=user_agent
            )
            raise HTTPException(status_code=400, detail="用户名和密码不能为空")

        logger.info(f"🔍 开始认证用户: {payload.username}")

        # 使用数据库认证
        user = await user_service.authenticate_user(payload.username, payload.password)

        logger.info(f"🔍 认证结果: user={'存在' if user else '不存在'}")

        if not user:
            logger.warning(f"❌ 登录失败 - 用户名或密码错误: {payload.username}")
            await log_operation(
                user_id="unknown",
                username=payload.username,
                action_type=ActionType.USER_LOGIN,
                action="用户登录",
                details={"reason": "用户名或密码错误"},
                success=False,
                error_message="用户名或密码错误",
                duration_ms=int((time.time() - start_time) * 1000),
                ip_address=ip_address,
                user_agent=user_agent
            )
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        # 生成 token
        token = AuthService.create_access_token(sub=user.username)
        refresh_token = AuthService.create_access_token(sub=user.username, expires_delta=60*60*24*7)  # 7天有效期

        # 记录登录成功日志
        await log_operation(
            user_id=str(user.id),
            username=user.username,
            action_type=ActionType.USER_LOGIN,
            action="用户登录",
            details={"login_method": "password"},
            success=True,
            duration_ms=int((time.time() - start_time) * 1000),
            ip_address=ip_address,
            user_agent=user_agent
        )

        return {
            "success": True,
            "data": {
                "access_token": token,
                "refresh_token": refresh_token,
                "expires_in": 60 * 60,
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "name": user.username,
                    "is_admin": user.is_admin
                }
            },
            "message": "登录成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 登录异常: {e}")
        await log_operation(
            user_id="unknown",
            username=payload.username or "unknown",
            action_type=ActionType.USER_LOGIN,
            action="用户登录",
            details={"error": str(e)},
            success=False,
            error_message=f"系统错误: {str(e)}",
            duration_ms=int((time.time() - start_time) * 1000),
            ip_address=ip_address,
            user_agent=user_agent
        )
        raise HTTPException(status_code=500, detail="登录过程中发生系统错误")

@router.post("/refresh")
async def refresh_token(payload: RefreshTokenRequest):
    """刷新访问令牌"""
    try:
        logger.debug(f"🔄 收到refresh token请求")
        logger.debug(f"📝 Refresh token长度: {len(payload.refresh_token) if payload.refresh_token else 0}")

        if not payload.refresh_token:
            logger.warning("❌ Refresh token为空")
            raise HTTPException(status_code=401, detail="Refresh token is required")

        # 验证refresh token
        token_data = AuthService.verify_token(payload.refresh_token)
        logger.debug(f"🔍 Token验证结果: {token_data is not None}")

        if not token_data:
            logger.warning("❌ Refresh token验证失败")
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # 验证用户是否仍然存在且激活
        user = await user_service.get_user_by_username(token_data.sub)
        if not user or not user.is_active:
            logger.warning(f"❌ 用户不存在或已禁用: {token_data.sub}")
            raise HTTPException(status_code=401, detail="User not found or inactive")

        logger.debug(f"✅ Token验证成功，用户: {token_data.sub}")

        # 生成新的tokens
        new_token = AuthService.create_access_token(sub=token_data.sub)
        new_refresh_token = AuthService.create_access_token(sub=token_data.sub, expires_delta=60*60*24*7)

        logger.debug(f"🎉 新token生成成功")

        return {
            "success": True,
            "data": {
                "access_token": new_token,
                "refresh_token": new_refresh_token,
                "expires_in": 60 * 60
            },
            "message": "Token刷新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Refresh token处理异常: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Token refresh failed: {str(e)}")

@router.post("/logout")
async def logout(request: Request, user: dict = Depends(get_current_user)):
    """用户登出"""
    start_time = time.time()

    # 获取客户端信息
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    try:
        # 记录登出日志
        await log_operation(
            user_id=user["id"],
            username=user["username"],
            action_type=ActionType.USER_LOGOUT,
            action="用户登出",
            details={"logout_method": "manual"},
            success=True,
            duration_ms=int((time.time() - start_time) * 1000),
            ip_address=ip_address,
            user_agent=user_agent
        )

        return {
            "success": True,
            "data": {},
            "message": "登出成功"
        }
    except Exception as e:
        logger.error(f"记录登出日志失败: {e}")
        return {
            "success": True,
            "data": {},
            "message": "登出成功"
        }

@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "success": True,
        "data": user,
        "message": "获取用户信息成功"
    }

@router.put("/me")
async def update_me(
    payload: dict,
    user: dict = Depends(get_current_user)
):
    """更新当前用户信息"""
    try:
        from app.models.user import UserUpdate, UserPreferences

        # 构建更新数据
        update_data = {}

        # 更新邮箱
        if "email" in payload:
            update_data["email"] = payload["email"]

        # 更新偏好设置（支持部分更新）
        if "preferences" in payload:
            # 获取当前偏好
            current_prefs = user.get("preferences", {})

            # 合并新的偏好设置
            merged_prefs = {**current_prefs, **payload["preferences"]}

            # 创建 UserPreferences 对象
            update_data["preferences"] = UserPreferences(**merged_prefs)

        # 如果有语言设置，更新到偏好中
        if "language" in payload:
            if "preferences" not in update_data:
                # 获取当前偏好
                current_prefs = user.get("preferences", {})
                update_data["preferences"] = UserPreferences(**current_prefs)
            update_data["preferences"].language = payload["language"]

        # 如果有时区设置，更新到偏好中（如果需要）
        # 注意：时区通常是系统级设置，不是用户级设置

        # 调用服务更新用户
        user_update = UserUpdate(**update_data)
        updated_user = await user_service.update_user(user["username"], user_update)

        if not updated_user:
            raise HTTPException(status_code=400, detail="更新失败，邮箱可能已被使用")

        # 返回更新后的用户信息
        return {
            "success": True,
            "data": updated_user.model_dump(by_alias=True),
            "message": "用户信息更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户信息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新用户信息失败: {str(e)}")

@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """修改密码"""
    try:
        # 使用数据库服务修改密码
        success = await user_service.change_password(
            user["username"], 
            payload.old_password, 
            payload.new_password
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="旧密码错误")

        return {
            "success": True,
            "data": {},
            "message": "密码修改成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改密码失败: {e}")
        raise HTTPException(status_code=500, detail=f"修改密码失败: {str(e)}")

@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """重置密码（管理员操作）"""
    try:
        # 检查权限
        if not user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="权限不足")

        # 重置密码
        success = await user_service.reset_password(payload.username, payload.new_password)
        
        if not success:
            raise HTTPException(status_code=404, detail="用户不存在")

        return {
            "success": True,
            "data": {},
            "message": f"用户 {payload.username} 的密码已重置"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置密码失败: {e}")
        raise HTTPException(status_code=500, detail=f"重置密码失败: {str(e)}")

@router.post("/create-user")
async def create_user(
    payload: CreateUserRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """创建用户（管理员操作）"""
    try:
        # 检查权限
        if not user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="权限不足")

        # 创建用户
        user_create = UserCreate(
            username=payload.username,
            email=payload.email,
            password=payload.password
        )
        
        new_user = await user_service.create_user(user_create)
        
        if not new_user:
            raise HTTPException(status_code=400, detail="用户名或邮箱已存在")

        # 如果需要设置为管理员
        if payload.is_admin:
            from pymongo import MongoClient
            from app.core.config import settings
            client = MongoClient(settings.MONGO_URI)
            db = client[settings.MONGO_DB]
            db.users.update_one(
                {"username": payload.username},
                {"$set": {"is_admin": True}}
            )

        return {
            "success": True,
            "data": {
                "id": str(new_user.id),
                "username": new_user.username,
                "email": new_user.email,
                "is_admin": payload.is_admin
            },
            "message": f"用户 {payload.username} 创建成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建用户失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建用户失败: {str(e)}")

@router.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    """获取用户列表（管理员操作）"""
    try:
        # 检查权限
        if not user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="权限不足")

        users = await user_service.list_users(skip=skip, limit=limit)

        return {
            "success": True,
            "data": {
                "users": [user.model_dump() for user in users],
                "total": len(users)
            },
            "message": "获取用户列表成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户列表失败: {str(e)}")


# ==================== 邮箱验证码登录相关接口 ====================

class SendCodeRequest(BaseModel):
    """发送验证码请求"""
    email: str
    purpose: str = "login"  # "login" or "register"


class VerifyCodeRequest(BaseModel):
    """验证验证码请求"""
    email: str
    code: str


class RegisterEmailRequest(BaseModel):
    """邮箱注册请求"""
    email: str
    username: str
    password: str
    code: str  # 注册时也需要验证码验证


@router.post("/send-code")
async def send_verification_code(payload: SendCodeRequest, request: Request):
    """发送验证码"""
    start_time = time.time()
    ip_address = request.client.host if request.client else "unknown"

    try:
        # 验证邮箱格式
        import re
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', payload.email):
            raise HTTPException(status_code=400, detail="邮箱格式不正确")

        # 发送验证码
        dev_code, is_dev_mode = await AuthService.request_verification_code(
            payload.email,
            purpose=payload.purpose
        )

        await log_operation(
            user_id="unknown",
            username=payload.email,
            action_type=ActionType.USER_LOGIN,
            action="发送验证码",
            details={"purpose": payload.purpose, "ip": ip_address},
            success=True,
            duration_ms=int((time.time() - start_time) * 1000),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent", "")
        )

        # 返回响应
        if is_dev_mode:
            # 开发环境：返回验证码
            return {
                "success": True,
                "data": {
                    "dev_code": dev_code,
                    "message": "验证码已生成（开发模式）"
                },
                "message": "发送成功"
            }
        else:
            # 生产环境：提示已发送
            return {
                "success": True,
                "data": {
                    "message": "验证码已发送到邮箱"
                },
                "message": "发送成功"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送验证码失败: {e}")
        raise HTTPException(status_code=500, detail=f"发送验证码失败: {str(e)}")


@router.post("/verify-code")
async def verify_code(payload: VerifyCodeRequest, request: Request):
    """验证验证码并登录"""
    start_time = time.time()
    ip_address = request.client.host if request.client else "unknown"

    try:
        # 验证邮箱格式
        import re
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', payload.email):
            raise HTTPException(status_code=400, detail="邮箱格式不正确")

        # 验证验证码并登录
        result = await AuthService.verify_and_login(payload.email, payload.code)

        if not result:
            await log_operation(
                user_id="unknown",
                username=payload.email,
                action_type=ActionType.USER_LOGIN,
                action="验证码登录",
                details={"reason": "验证码错误或已过期", "ip": ip_address},
                success=False,
                error_message="验证码错误或已过期",
                duration_ms=int((time.time() - start_time) * 1000),
                ip_address=ip_address,
                user_agent=request.headers.get("user-agent", "")
            )
            raise HTTPException(status_code=401, detail="验证码错误或已过期")

        await log_operation(
            user_id=result["user"]["id"],
            username=result["user"]["username"],
            action_type=ActionType.USER_LOGIN,
            action="验证码登录",
            details={"login_method": "email_code", "ip": ip_address},
            success=True,
            duration_ms=int((time.time() - start_time) * 1000),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent", "")
        )

        return {
            "success": True,
            "data": {
                "access_token": result["access_token"],
                "expires_in": 60 * 60,
                "user": result["user"]
            },
            "message": "登录成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证码登录失败: {e}")
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")


@router.post("/register-email")
async def register_with_email(payload: RegisterEmailRequest, request: Request):
    """邮箱注册"""
    start_time = time.time()
    ip_address = request.client.host if request.client else "unknown"

    try:
        # 验证邮箱格式
        import re
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', payload.email):
            raise HTTPException(status_code=400, detail="邮箱格式不正确")

        # 验证用户名格式
        if len(payload.username) < 3 or len(payload.username) > 50:
            raise HTTPException(status_code=400, detail="用户名长度为3-50个字符")

        # 验证密码格式
        if len(payload.password) < 6:
            raise HTTPException(status_code=400, detail="密码至少6个字符")

        # 先验证注册验证码
        from app.services.auth_service import AuthService
        redis_service = get_redis_service()
        email = AuthService.normalize_email(payload.email)

        key = f"verification:{email}:register"
        stored_value = await redis_service.redis.get(key)

        if not stored_value:
            raise HTTPException(status_code=401, detail="验证码不存在或已过期")

        code_hash, expires_at_str = stored_value.split(":")
        expires_at = datetime.fromisoformat(expires_at_str)

        if expires_at < now_tz():
            await redis_service.redis.delete(key)
            raise HTTPException(status_code=401, detail="验证码已过期")

        expected_hash = AuthService.hash_verification_code(email, payload.code)
        if code_hash != expected_hash:
            raise HTTPException(status_code=401, detail="验证码错误")

        # 验证码正确，删除已使用的验证码
        await redis_service.redis.delete(key)

        # 注册用户
        result = await AuthService.register_with_email(
            email=payload.email,
            username=payload.username,
            password=payload.password
        )

        if not result:
            await log_operation(
                user_id="unknown",
                username=payload.username,
                action_type=ActionType.USER_REGISTER,
                action="邮箱注册",
                details={"reason": "用户名或邮箱已存在", "ip": ip_address},
                success=False,
                error_message="用户名或邮箱已存在",
                duration_ms=int((time.time() - start_time) * 1000),
                ip_address=ip_address,
                user_agent=request.headers.get("user-agent", "")
            )
            raise HTTPException(status_code=400, detail="用户名或邮箱已被使用")

        await log_operation(
            user_id=result["user"]["id"],
            username=result["user"]["username"],
            action_type=ActionType.USER_REGISTER,
            action="邮箱注册",
            details={"email": payload.email, "ip": ip_address},
            success=True,
            duration_ms=int((time.time() - start_time) * 1000),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent", "")
        )

        return {
            "success": True,
            "data": {
                "access_token": result["access_token"],
                "expires_in": 60 * 60,
                "user": result["user"]
            },
            "message": "注册成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"邮箱注册失败: {e}")
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")
