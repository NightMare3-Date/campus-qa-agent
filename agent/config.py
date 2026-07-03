"""应用配置管理"""
from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    # API
    openai_api_key: str
    openai_base_url: str = "https://api.deepseek.com/v1"
    openai_model: str = "deepseek-chat"
    server_port: int = 8000

    # 存储路径
    knowledge_dir: str = ""
    vector_db_dir: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        base = Path(__file__).resolve().parent.parent
        if not self.knowledge_dir:
            self.knowledge_dir = str(base / "knowledge")
        if not self.vector_db_dir:
            self.vector_db_dir = str(base / "data" / "faiss_index")


settings = Settings()
