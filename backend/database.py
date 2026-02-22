from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base
from .config import settings
from typing import Generator

# データベースエンジン作成
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # SQLite用
)

# セッション作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# テーブル作成
def init_db():
    Base.metadata.create_all(bind=engine)

# 依存性注入用
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
