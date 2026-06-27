import configparser 
import os

current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project = os.path.dirname(current_dir)
config_file = os.path.join(project, 'config.ini')
class Config():
    def __init__(self, config_file = config_file):
    #    config_file = os.path.join(os.path.dirname(__file__), config_file)
    #  1 创建配置文件解析器
        self.config = configparser.ConfigParser()
        # 2 读取配置文件
        self.config.read(config_file, encoding='utf-8-sig')
        # 3 获取配置项
        # 3.1 获取mysql配置项
        self.MYSQL_HOST = self.config.get('mysql', 'host')
        self.MYSQL_PORT = self.config.getint('mysql', 'port')
        self.MYSQL_USER = self.config.get('mysql', 'user')
        self.MYSQL_PASSWORD = self.config.get('mysql', 'password')
        self.MYSQL_DATABASE = self.config.get('mysql', 'database')
        
        # 3.2 获取redis配置项
        self.REDIS_HOST = self.config.get('redis', 'host')
        self.REDIS_PORT = self.config.getint('redis', 'port')
        self.REDIS_PASSWORD = self.config.get('redis', 'password')
        self.REDIS_DB = self.config.getint('redis', 'db',fallback=0)
        
        # Milvus 配置
        # Milvus 主机地址
        self.MILVUS_HOST = self.config.get('milvus', 'host', fallback='localhost')
        # Milvus 端口
        self.MILVUS_PORT = self.config.get('milvus', 'port', fallback='19530')
        # Milvus 数据库名
        self.MILVUS_DATABASE_NAME = self.config.get('milvus', 'database_name', fallback='itcast')
        # Milvus 集合名
        self.MILVUS_COLLECTION_NAME = self.config.get('milvus', 'collection_name', fallback='edurag_final')

        # LLM 配置
        # LLM 模型名
        self.LLM_MODEL = self.config.get('llm', 'model', fallback='qwen-plus')
        # DashScope API 密钥
        self.DASHSCOPE_API_KEY = self.config.get('llm', 'dashscope_api_key')
        # DashScope API 地址
        self.DASHSCOPE_BASE_URL = self.config.get('llm', 'dashscope_base_url',
                                                  fallback='https://dashscope.aliyuncs.com/compatible-mode/v1')

        # 检索参数
        # 父块大小
        self.PARENT_CHUNK_SIZE = self.config.getint('retrieval', 'parent_chunk_size', fallback=1200)
        # 子块大小
        self.CHILD_CHUNK_SIZE = self.config.getint('retrieval', 'child_chunk_size', fallback=300)
        # 块重叠大小
        self.CHUNK_OVERLAP = self.config.getint('retrieval', 'chunk_overlap', fallback=50)
        # 检索返回数量
        self.RETRIEVAL_K = self.config.getint('retrieval', 'retrieval_k', fallback=5)
        # 最终候选数量
        self.CANDIDATE_M = self.config.getint('retrieval', 'candidate_m', fallback=2)
        
        self.RERANK_MODEL = self.config.get('local', 'rerank_model', fallback=r"D:\model\bge-reranker-large")
        self.BGEM3_MODEL = self.config.get('local', 'bgem3_model', fallback=r"D:\model\bge-m3")
        # 3.3 获取日志路径
        self.LOG_FILE = self.config.get('logger', 'log_file', fallback='logs/app.log')
        self.CUSTOMER_SERVICE_PHONE = self.config.get('app', 'customer_service_phone', fallback='12345678')
        self.VALID_SOURCES = eval(self.config.get('app', 'valid_sources', fallback=["ai", "java", "test", "ops", "bigdata"]))
        