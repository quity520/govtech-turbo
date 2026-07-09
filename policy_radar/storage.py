"""政策雷达 · 数据存储（SQLite）"""
import json, os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Text, DateTime, Integer, Boolean
)
from sqlalchemy.orm import declarative_base, Session
from dotenv import load_dotenv
from loguru import logger

load_dotenv()
Base = declarative_base()


class Policy(Base):
    """数据库表：policies"""
    __tablename__ = "policies"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    title        = Column(String(500))
    category     = Column(String(50))
    issuer       = Column(String(200))
    deadline     = Column(String(50))
    reward       = Column(Text)
    conditions   = Column(Text)      # JSON字符串存储
    required_docs = Column(Text)     # JSON字符串存储
    summary      = Column(Text)
    source_url   = Column(String(500), unique=True)  # 防重复
    source_site  = Column(String(100))
    created_at   = Column(DateTime, default=datetime.now)


class PolicyStorage:

    def __init__(self):
        db_url = os.getenv("DATABASE_URL", "sqlite:///./govtech.db")
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)  # 自动建表
        logger.info("数据库初始化完成")

    def save(self, parsed: dict) -> bool:
        """保存一条解析结果，已存在则跳过"""
        with Session(self.engine) as s:
            # 检查是否已存在（按URL去重）
            exists = s.query(Policy).filter_by(
                source_url=parsed.get("source_url")
            ).first()
            if exists:
                logger.debug(f"已存在，跳过: {parsed.get('title','')[:30]}")
                return False

            policy = Policy(
                title        = parsed.get("title") or parsed.get("raw_title", ""),
                category     = parsed.get("category", "其他"),
                issuer       = parsed.get("issuer", ""),
                deadline     = str(parsed.get("deadline") or ""),
                reward       = parsed.get("reward", ""),
                conditions   = json.dumps(parsed.get("conditions", []), ensure_ascii=False),
                required_docs = json.dumps(parsed.get("required_docs", []), ensure_ascii=False),
                summary      = parsed.get("summary", ""),
                source_url   = parsed.get("source_url", ""),
                source_site  = parsed.get("source_site", ""),
            )
            s.add(policy)
            s.commit()
            logger.success(f"✓ 已存入数据库: {policy.title[:30]}")
            return True

    def save_batch(self, parsed_list: list[dict]) -> int:
        """批量保存，返回新增条数"""
        count = sum(self.save(p) for p in parsed_list)
        logger.success(f"批量保存完成：新增 {count} 条")
        return count

    def query_all(self) -> list[Policy]:
        with Session(self.engine) as s:
            return s.query(Policy).order_by(Policy.created_at.desc()).all()