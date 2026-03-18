from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    user: str = os.getenv("MYSQL_USER", "root")
    password: str = os.getenv("MYSQL_PASSWORD", "")
    host: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    port: int = int(os.getenv("MYSQL_PORT", 3306))
    db: str = os.getenv("MYSQL_DB", "chat_analysis_db")
    
    @property
    def database_url(self):
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}?charset=utf8mb4"


class LLMSettings(BaseSettings):
    """大模型配置"""
    # Qwen 模型配置
    qwen_api_key: str = os.getenv("QWEN_API_KEY", "")
    qwen_api_url: str = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    
    # DeepSeek 模型配置
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_api_url: str = "https://api.deepseek.com/v1/chat/completions"
    
    # 火山引擎模型配置
    volcengine_api_key: str = os.getenv("VOLCENGINE_API_KEY", "")
    volcengine_api_url: str = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"


class AppSettings(BaseSettings):
    """应用配置"""
    name: str = "对话式数据分析系统"
    version: str = "1.0.0"
    debug: bool = True
    
    # CORS 配置
    cors_origins: list = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "http://localhost:8083",
        "http://127.0.0.1:8083",
        "http://localhost:8085",
        "http://127.0.0.1:8085"
    ]


class Settings(BaseSettings):
    """总配置类"""
    database: DatabaseSettings = DatabaseSettings()
    llm: LLMSettings = LLMSettings()
    app: AppSettings = AppSettings()


# 创建全局配置实例
settings = Settings()
