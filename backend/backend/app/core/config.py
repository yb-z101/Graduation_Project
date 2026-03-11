from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    # MySQL配置
    mysql_user: str = os.getenv("MYSQL_USER", "root")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "")
    mysql_host: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    mysql_port: int = int(os.getenv("MYSQL_PORT", 3306))
    mysql_db: str = os.getenv("MYSQL_DB", "chat_analysis_db")

    # 大模型配置（换回官方原始URL，中国大陆稳定可用）
    qwen_api_key: str = os.getenv("QWEN_API_KEY", "")
    # 原始端点：阿里云文档明确的标准地址
    qwen_api_url: str = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

    # 数据库连接URL
    @property
    def database_url(self):
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}?charset=utf8mb4"


settings = Settings()