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
        self.config.read(config_file)
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
        
        # 3.3 获取日志路径
        self.LOG_FILE = self.config.get('logger', 'log_file', fallback='logs/app.log')