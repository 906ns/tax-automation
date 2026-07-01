import os
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # API Keys
    anthropic_api_key: str = ""
    
    # Directories
    base_dir: Path = Path(__file__).parent.parent
    upload_dir: Path = base_dir / "uploads"
    output_dir: Path = base_dir / "outputs"
    data_dir: Path = base_dir / "data"
    template_dir: Path = base_dir / "frontend" / "templates"
    static_dir: Path = base_dir / "frontend" / "static"
    
    # Database
    database_url: str = "sqlite:///./data/data.db"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# ディレクトリ作成
def ensure_directories():
    settings = Settings()
    for directory in [settings.upload_dir, settings.output_dir, settings.data_dir]:
        directory.mkdir(parents=True, exist_ok=True)

settings = Settings()
