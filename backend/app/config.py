import os
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "RecoEngine"
    APP_VERSION: str = "1.0.0"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./recoengine.db")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1")
    DEFAULT_HYBRID_BETA: float = 0.6  # 60% collaborative, 40% content
    CORS_ORIGINS: list[str] = ["*"]

settings = Settings()
