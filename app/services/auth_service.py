import time
import secrets
import hashlib
import smtplib
import os
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from app.utils.timezone import now_tz
from typing import Optional
import jwt
import logging
from pydantic import BaseModel
from app.core.config import settings
from app.core.redis_client import get_redis_service

logger = logging.getLogger(__name__)


class TokenData(BaseModel):
    sub: str
    exp: int


class EmailVerificationCode(BaseModel):
    """邮箱验证码模型"""
    email: str
    code: str
    purpose: str  # "login" or "register"
    created_at: datetime
    expires_at: datetime


class AuthService:
    @staticmethod
    def create_access_token(sub: str, expires_minutes: int | None = None, expires_delta: int | None = None) -> str:
        if expires_delta:
            # 如果指定了秒数，使用秒数
            expire = now_tz() + timedelta(seconds=expires_delta)
        else:
            # 否则使用分钟数
            expire = now_tz() + timedelta(minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {"sub": sub, "exp": expire}
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return token

    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        logger = logging.getLogger(__name__)

        try:
            logger.debug(f"🔍 开始验证token")
            logger.debug(f"📝 Token长度: {len(token)}")
            logger.debug(f"🔑 JWT密钥: {settings.JWT_SECRET[:10]}...")
            logger.debug(f"🔧 JWT算法: {settings.JWT_ALGORITHM}")

            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            logger.debug(f"✅ Token解码成功")
            logger.debug(f"📋 Payload: {payload}")

            token_data = TokenData(sub=payload.get("sub"), exp=int(payload.get("exp", time.time())))
            logger.debug(f"🎯 Token数据: sub={token_data.sub}, exp={token_data.exp}")

            # 检查是否过期
            current_time = int(time.time())
            if token_data.exp < current_time:
                logger.warning(f"⏰ Token已过期: exp={token_data.exp}, now={current_time}")
                return None

            logger.debug(f"✅ Token验证成功")
            return token_data

        except jwt.ExpiredSignatureError:
            logger.warning("⏰ Token已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"❌ Token无效: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Token验证异常: {str(e)}")
            return None

    @staticmethod
    def normalize_email(email: str) -> str:
        """标准化邮箱地址"""
        return email.strip().lower()

    @staticmethod
    def generate_verification_code() -> str:
        """生成6位验证码"""
        return f"{secrets.randbelow(1000000):06d}"

    @staticmethod
    def hash_verification_code(email: str, code: str) -> str:
        """哈希验证码"""
        return hashlib.sha256(f"{AuthService.normalize_email(email)}:{code}:{settings.JWT_SECRET}".encode("utf-8")).hexdigest()

    @staticmethod
    async def request_verification_code(email: str, purpose: str = "login") -> tuple[str, bool]:
        """
        请求验证码
        返回: (dev_code或None, 是否为开发模式)
        dev_code在无SMTP配置或开发环境下返回
        """
        email = AuthService.normalize_email(email)
        redis_service = get_redis_service()

        # 生成验证码
        code = AuthService.generate_verification_code()
        code_hash = AuthService.hash_verification_code(email, code)

        # 5分钟有效期
        expires_at = now_tz() + timedelta(minutes=5)

        # 存储到Redis: verification:{email}:{purpose} -> {code_hash}:{expires_at}
        key = f"verification:{email}:{purpose}"
        value = f"{code_hash}:{expires_at.isoformat()}"

        await redis_service.set_with_ttl(key, value, ttl=300)  # 5分钟 TTL

        logger.info(f"📧 验证码已生成 for {email} ({purpose}): {code}")

        # 尝试发送邮件
        dev_code = AuthService._send_verification_email(email, code)

        return dev_code, dev_code is not None

    @staticmethod
    def _send_verification_email(email: str, code: str) -> Optional[str]:
        """发送验证码邮件，如果失败返回dev_code（在开发环境）"""
        smtp_host = os.getenv("MAIL_HOST", "").strip()
        is_production = os.getenv("APP_ENV", "development") == "production"

        if not smtp_host:
            # 无SMTP配置
            logger.info(f"📧 [DEV] 验证码 for {email}: {code}")
            if not is_production:
                return code  # 开发环境返回dev_code
            return None

        try:
            smtp_port = int(os.getenv("MAIL_PORT", "587"))
            smtp_user = os.getenv("MAIL_USER", "").strip()
            smtp_password = os.getenv("MAIL_PASS", "").strip()
            smtp_from = os.getenv("MAIL_FROM", smtp_user or "noreply@example.com").strip()
            smtp_starttls = os.getenv("MAIL_STARTTLS", "1").strip().lower() not in ("0", "false", "off", "no")
            smtp_ssl = os.getenv("MAIL_SSL", "0").strip().lower() in ("1", "true", "on", "yes")

            msg = EmailMessage()
            msg["Subject"] = "QuantScope 登录验证码"
            msg["From"] = smtp_from
            msg["To"] = email
            msg.set_content(f"你的 QuantScope 登录验证码是：{code}\n\n5 分钟内有效。")

            smtp_cls = smtplib.SMTP_SSL if smtp_ssl else smtplib.SMTP
            with smtp_cls(smtp_host, smtp_port, timeout=20) as server:
                if smtp_starttls and not smtp_ssl:
                    server.starttls()
                if smtp_user:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)

            logger.info(f"📧 验证码已发送到 {email}")
            return None  # 发送成功，不返回dev_code

        except Exception as e:
            logger.error(f"❌ 发送邮件失败: {e}")
            if not is_production:
                return code  # 开发环境返回dev_code
            return None

    @staticmethod
    async def verify_and_login(email: str, code: str) -> Optional[dict]:
        """
        验证验证码并登录
        返回: {"access_token", "user"} 或 None
        """
        from app.services.user_service import user_service
        from app.models.user import UserCreate

        email = AuthService.normalize_email(email)
        redis_service = get_redis_service()

        # 从Redis获取存储的验证码哈希
        key = f"verification:{email}:login"
        stored_value = await redis_service.redis.get(key)

        if not stored_value:
            logger.warning(f"❌ 验证码不存在或已过期: {email}")
            return None

        code_hash = stored_value[:64]
        expires_at_str = stored_value[65:]
        expires_at = datetime.fromisoformat(expires_at_str)

        # 检查是否过期
        if expires_at < now_tz():
            logger.warning(f"❌ 验证码已过期: {email}")
            await redis_service.redis.delete(key)
            return None

        # 验证验证码
        expected_hash = AuthService.hash_verification_code(email, code)
        if code_hash != expected_hash:
            logger.warning(f"❌ 验证码错误: {email}")
            return None

        # 验证码正确，删除已使用的验证码
        await redis_service.redis.delete(key)

        # 查找或创建用户
        user = await user_service.get_user_by_email(email)

        if not user:
            # 如果用户不存在，创建新用户（邮箱登录场景）
            # 生成随机用户名
            username = f"user_{email.split('@')[0]}_{secrets.randbelow(100000):05d}"
            user_create = UserCreate(
                username=username,
                email=email,
                password=AuthService.generate_verification_code()  # 随机密码，邮箱登录不需要
            )
            user = await user_service.create_user(user_create)

            if not user:
                logger.error(f"❌ 用户创建失败: {email}")
                return None

            logger.info(f"✅ 新用户创建: {username} ({email})")

        # 生成JWT token
        token = AuthService.create_access_token(sub=user.username)

        logger.info(f"✅ 邮箱登录成功: {email}")

        return {
            "access_token": token,
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin
            }
        }

    @staticmethod
    async def register_with_email(email: str, username: str, password: str) -> Optional[dict]:
        """
        邮箱注册用户
        返回: {"access_token", "user"} 或 None
        """
        from app.services.user_service import user_service
        from app.models.user import UserCreate

        email = AuthService.normalize_email(email)

        # 检查用户名和邮箱是否已存在
        existing_user = await user_service.get_user_by_username(username)
        if existing_user:
            logger.warning(f"❌ 用户名已存在: {username}")
            return None

        existing_email_user = await user_service.get_user_by_email(email)
        if existing_email_user:
            logger.warning(f"❌ 邮箱已被使用: {email}")
            return None

        # 创建用户
        user_create = UserCreate(
            username=username,
            email=email,
            password=password
        )
        user = await user_service.create_user(user_create)

        if not user:
            logger.error(f"❌ 用户注册失败: {username}")
            return None

        # 生成JWT token
        token = AuthService.create_access_token(sub=user.username)

        logger.info(f"✅ 用户注册成功: {username} ({email})")

        return {
            "access_token": token,
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin
            }
        }