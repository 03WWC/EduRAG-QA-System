import os
import sys
import hashlib
import pymysql

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base import Config, logger

conf = Config()


class UserService:
    def __init__(self, mysql_client):
        self.mysql = mysql_client
        self._ensure_table()

    def _ensure_table(self):
        """确保 users 表存在，不存在则创建"""
        try:
            self.mysql.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role ENUM('user', 'admin') DEFAULT 'user',
                    created_at DATETIME DEFAULT NOW()
                )
            """)
            self.mysql.connection.commit()
            # 检查是否需要创建默认管理员
            self.mysql.cursor.execute("SELECT COUNT(*) FROM users")
            count = self.mysql.cursor.fetchone()[0]
            if count == 0:
                self.create_user("admin", "admin123", "admin")
                logger.info("已创建默认管理员账号: admin / admin123")
        except pymysql.MySQLError as e:
            logger.error(f"初始化 users 表失败: {e}")

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username: str, password: str) -> dict | None:
        """验证用户名密码，成功返回用户信息字典"""
        try:
            self.mysql.cursor.execute(
                "SELECT id, username, role FROM users WHERE username=%s AND password_hash=%s",
                (username, self._hash_password(password)),
            )
            row = self.mysql.cursor.fetchone()
            if row:
                return {"user_id": row[0], "username": row[1], "role": row[2]}
            return None
        except pymysql.MySQLError as e:
            logger.error(f"登录验证失败: {e}")
            return None

    def create_user(self, username: str, password: str, role: str = "user") -> bool:
        """创建用户，成功返回 True"""
        try:
            self.mysql.cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                (username, self._hash_password(password), role),
            )
            self.mysql.connection.commit()
            logger.info(f"创建用户成功: {username} ({role})")
            return True
        except pymysql.IntegrityError:
            logger.warning(f"用户名已存在: {username}")
            return False
        except pymysql.MySQLError as e:
            logger.error(f"创建用户失败: {e}")
            return False

    def list_users(self) -> list:
        """列出所有用户"""
        try:
            self.mysql.cursor.execute(
                "SELECT id, username, role, created_at FROM users ORDER BY created_at DESC"
            )
            return [
                {"id": row[0], "username": row[1], "role": row[2], "created_at": str(row[3])}
                for row in self.mysql.cursor.fetchall()
            ]
        except pymysql.MySQLError as e:
            logger.error(f"获取用户列表失败: {e}")
            return []

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """修改密码，需验证原密码"""
        try:
            self.mysql.cursor.execute(
                "SELECT id FROM users WHERE username=%s AND password_hash=%s",
                (username, self._hash_password(old_password)),
            )
            if not self.mysql.cursor.fetchone():
                return False
            self.mysql.cursor.execute(
                "UPDATE users SET password_hash=%s WHERE username=%s",
                (self._hash_password(new_password), username),
            )
            self.mysql.connection.commit()
            logger.info(f"用户 {username} 密码已修改")
            return True
        except pymysql.MySQLError as e:
            logger.error(f"修改密码失败: {e}")
            return False

    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        try:
            self.mysql.cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
            self.mysql.connection.commit()
            return self.mysql.cursor.rowcount > 0
        except pymysql.MySQLError as e:
            logger.error(f"删除用户失败: {e}")
            return False
