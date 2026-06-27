from db.mysql_client import MySQLClient
# 导入 Redis 客户端
from cache.redis_client import RedisClient
# 导入 BM25 搜索
from retrieval.bm25_search import BM25Search
# 导入日志
from base import logger
# 导入时间库
import time

class MySQLQASystem():
    def __init__(self):
        self.logger = logger
        self.mysql_client = MySQLClient()
        self.redis_client = RedisClient()
        self.bm25_search = BM25Search(self.redis_client, self.mysql_client)
        
    def query(self,question):
        # 查询问题
        start_time = time.time()
        answer,_ = self.bm25_search.search(question)
        if answer:
             # 记录 MySQL 答案
            self.logger.info(f"MySQL 答案: {answer}")
        else:
            self.logger.info("SQL中未找到答案, 需要调用RAG系统")
        end_time = time.time()
        processing_time  = end_time - start_time
        self.logger.info(f"查询耗时: {processing_time:.2f} 秒")
        return answer
    
def main():
    # 初始化系统
    mysql_system = MySQLQASystem()
    # 测试查询
    try:
          # 打印欢迎信息
        print("\n欢迎使用 MySQL 问答系统！")
        print("输入查询进行问答，输入 'exit' 退出。")
        while True:
            question = input("\n请输入查询：")
            if question.lower() == "exit":
                print("感谢使用！")
                break
            answer = mysql_system.query(question)
            if answer:
                print(f"答案：{answer}")
    except Exception as e:
        # 记录系统错误
        logger.error(f"系统错误: {e}")
        # 打印错误信息
        print(f"发生错误: {e}")
    finally:
        # 关闭数据库连接
        mysql_system.mysql_client.close()
    
if __name__ == "__main__":
    main()