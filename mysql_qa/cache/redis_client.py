# cache/redis_client.py
# 导入 Redis 客户端
import os
import sys
import socket

import redis
# 导入 JSON 处理
import json
# 导入配置和日志
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from base import Config, logger


class RedisClient:
    def __init__(self):
        # 初始化日志
        self.logger = logger
        # 创建连接池，配置保活和重连参数
        self.pool = redis.ConnectionPool(
            host=Config().REDIS_HOST,
            port=Config().REDIS_PORT,
            password=Config().REDIS_PASSWORD,
            db=Config().REDIS_DB,
            decode_responses=True,
            # ---------- 保活配置 ----------
            # 每 30 秒自动 PING 一次，在服务端 timeout（通常 >=60s）之前保活
            health_check_interval=30,
            # TCP keepalive，操作系统层面探测死连接
            socket_keepalive=True,
            socket_keepalive_options={
                socket.TCP_KEEPIDLE: 30,    # 空闲 30 秒开始发 keepalive 探测包
                socket.TCP_KEEPINTVL: 5,    # 探测间隔 5 秒
                socket.TCP_KEEPCNT: 3,      # 3 次探测失败后判定断开
            },
            # ---------- 超时配置 ----------
            socket_connect_timeout=5,        # 建立连接超时 5 秒
            socket_timeout=5,                # 读写超时 5 秒
            retry_on_timeout=True,           # 超时自动重试一次
            # ---------- 连接池配置 ----------
            max_connections=10,
        )
        # 通过连接池创建客户端（懒连接，首次操作时才真正建连）
        self.client = redis.StrictRedis(connection_pool=self.pool)
        self.logger.info("Redis 客户端已创建（健康检查每30秒）")

    def _execute(self, operation, *args, **kwargs):
        """执行 Redis 操作，连接断开时自动重连一次"""
        try:
            return operation(*args, **kwargs)
        except redis.ConnectionError as e:
            self.logger.warning(f"Redis 连接断开，尝试重连: {e}")
            try:
                # 断开池中所有旧连接，下次请求自动重建
                self.pool.disconnect()
                return operation(*args, **kwargs)
            except redis.RedisError as e2:
                self.logger.error(f"Redis 重连后仍失败: {e2}")
                return None
        except redis.RedisError as e:
            self.logger.error(f"Redis 操作失败: {e}")
            return None

    def set_data(self, key, value):
        # 存储数据到 Redis
        result = self._execute(self.client.set, key, json.dumps(value))
        if result:
            self.logger.info(f"存储数据到 Redis: {key}")

    def get_data(self, key):
        # 从 Redis 获取数据
        data = self._execute(self.client.get, key)
        if data is not None:
            return json.loads(data)
        return None

    def get_answer(self, query):
        # 获取查询的缓存答案
        answer = self._execute(self.client.get, f"answer:{query}")
        if answer:
            self.logger.info(f"从 Redis 获取答案: {query}")
            return answer
        return None


if __name__ == '__main__':
    redcli = RedisClient()
    print(redcli)
