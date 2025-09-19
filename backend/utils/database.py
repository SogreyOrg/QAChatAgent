import os

from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from .logger import logger_init

logger = logger_init("database")

# 数据库配置
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chat.db")
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    创建一个实用程序函数来管理数据库会话。该函数将确保每个数据库会话正确打开和关闭。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 定义数据库模型
class Session(Base):
    """
    Session 类表示聊天会话
    """
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True, nullable=False)
    messages = relationship("Message", back_populates="session")

class Message(Base):
    """
    Message 类表示会话中的各个消息
    """
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    session = relationship("Session", back_populates="messages")

# 创建数据库表
Base.metadata.create_all(bind=engine)

### Statefully manage chat history ###
store: dict[str, list[Message]] = {}

def save_message(session_id: str, role: str, content: str):
    """
    定义一个函数将各个消息保存到数据库中。该函数检查会话是否存在；如果没有，它就会创建一个。然后它将消息保存到相应的会话中。
    """
    db = next(get_db())
    try:
        # 检查或创建会话
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if not session:
            # 会话不存在时创建一个
            session = Session(session_id=session_id)
            db.add(session)
            db.commit()
            db.refresh(session)

        # 存储会话消息
        db.add(Message(session_id=session_id, role=role, content=content))
        db.commit()
        logger.info(f"成功存储{role}消息: {content}")
    except SQLAlchemyError:
        db.rollback()
        logger.error(f"存储{role}消息失败: {content}")
    finally:
        db.close()

def load_session_history(session_id: str):
    """
    定义一个函数来从数据库加载聊天历史记录。此函数检索与给定会话 ID 关联的所有消息并重建聊天历史记录。
    """
    db = next(get_db())

    # 获取当前会话
    session = db.query(Session).filter(Session.session_id == session_id).first()
    if not session:
        return []

    # 获取历史消息
    db_messages: list[Message] = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.created_at).all()

    # for msg in db_messages:
    #     logger.info(f"角色: {str(msg.role)} : 消息: {str(msg.content)}")

    return db_messages

def get_session_history(session_id: str)  -> list[Message]:
    """
    更新 get_session_history 函数以从数据库检索会话历史记录，而不是仅使用内存存储。
    """
    store[session_id] = load_session_history(session_id)
    return store[session_id]