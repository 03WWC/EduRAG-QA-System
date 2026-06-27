import os
import sys
import jwt
import hashlib
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

JWT_SECRET = "eduraag-secret-key-2026"  # 生产环境应使用环境变量
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

security = HTTPBearer()


def create_token(user_id: int, username: str, role: str) -> str:
    """签发 JWT token"""
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """解析 JWT token，无效则抛出异常"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的 Token，请重新登录")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """依赖注入：从 Authorization Header 提取当前用户信息"""
    return decode_token(credentials.credentials)


def get_admin_user(user: dict = Depends(get_current_user)) -> dict:
    """依赖注入：验证当前用户为管理员"""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


def verify_token_ws(token: str) -> dict | None:
    """WebSocket 用：验证 token，失败返回 None 而不抛 HTTP 异常"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None
