import os
import functools
from contextlib import contextmanager
from typing import List, Dict, Optional, Generator, Any, Callable, TypeVar, cast

from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, ForeignKey, Index
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session as SQLAlchemySession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from datetime import datetime, timezone
from .logger import logger_init

logger = logger_init("database")

# 数据库配置
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chat.db")
MAX_MESSAGES_PER_SESSION = int(os.getenv("MAX_MESSAGES_PER_SESSION", "100"))

# 创建数据库引擎，添加连接池配置
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 定义函数返回类型
T = TypeVar('T')

@contextmanager
def get_db() -> Generator[SQLAlchemySession, None, None]:
    """
    创建一个上下文管理器来管理数据库会话。
    
    Yields:
        SQLAlchemySession: 数据库会话对象
        
    Raises:
        SQLAlchemyError: 当数据库操作失败时
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"数据库操作失败: {str(e)}")
        raise
    finally:
        db.close()

def db_operation(func: Callable[..., T]) -> Callable[..., T]:
    """
    数据库操作装饰器，用于管理数据库会话和异常处理。
    
    Args:
        func: 要装饰的函数
        
    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with get_db() as db:
            try:
                return func(db, *args, **kwargs)
            except SQLAlchemyError as e:
                logger.error(f"数据库操作失败: {str(e)}")
                raise
    return wrapper

# 定义数据库模型
class Session(Base):
    """
    Session 类表示聊天会话
    
    Attributes:
        id: 主键ID
        session_id: 会话唯一标识符（字符串）
        title: 会话标题
        created_at: 会话创建时间
        updated_at: 会话最后更新时间
        messages: 与会话关联的消息列表
    """
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False, default="新的会话")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

class Message(Base):
    """
    Message 类表示会话中的各个消息
    
    Attributes:
        id: 主键ID
        session_id: 关联的会话ID（字符串）
        role: 消息发送者角色
        content: 消息内容
        created_at: 消息创建时间
        session: 关联的会话对象
    """
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    session_id = Column(String(64), ForeignKey("sessions.session_id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    session = relationship("Session", back_populates="messages")
    
    # 添加索引以提高查询性能
    __table_args__ = (
        Index('idx_messages_session_id_created_at', session_id, created_at),
    )

# 创建数据库表
try:
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表创建成功")
except OperationalError as e:
    logger.error(f"创建数据库表失败: {str(e)}")
    raise

# 缓存机制，使用LRU缓存策略
class LRUCache:
    """
    LRU (Least Recently Used) 缓存实现
    """
    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        self.cache: Dict[str, Any] = {}
        self.usage_order: List[str] = []
        
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项，并更新使用顺序"""
        if key in self.cache:
            # 更新使用顺序
            self.usage_order.remove(key)
            self.usage_order.append(key)
            return self.cache[key]
        return None
        
    def put(self, key: str, value: Any) -> None:
        """添加或更新缓存项"""
        if key in self.cache:
            self.usage_order.remove(key)
        elif len(self.cache) >= self.capacity:
            # 移除最久未使用的项
            oldest = self.usage_order.pop(0)
            del self.cache[oldest]
            
        self.cache[key] = value
        self.usage_order.append(key)
        
    def invalidate(self, key: str) -> None:
        """使缓存项无效"""
        if key in self.cache:
            del self.cache[key]
            self.usage_order.remove(key)
            
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.usage_order.clear()

# 创建消息缓存
message_cache = LRUCache(capacity=50)

@db_operation
def save_message(db: SQLAlchemySession, session_id: str, role: str, content: str) -> bool:
    """
    将消息保存到数据库中。
    
    Args:
        db: 数据库会话
        session_id: 会话ID
        role: 消息发送者角色
        content: 消息内容
        
    Returns:
        bool: 操作是否成功
        
    Raises:
        ValueError: 当输入参数无效时
        SQLAlchemyError: 当数据库操作失败时
    """
    # 输入验证
    if not session_id or not role or not content:
        raise ValueError("会话ID、角色和内容不能为空")
        
    try:
        # 检查或创建会话
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if not session:
            # 会话不存在时创建一个
            session = Session(session_id=session_id)
            db.add(session)
            db.flush()  # 使用flush而不是commit，保持在同一事务中
            
        # 存储会话消息
        message = Message(session_id=session_id, role=role, content=content)
        db.add(message)
        
        # 触发会话的更新时间自动更新
        # SQLAlchemy 会在 commit 时通过 onupdate 参数自动更新 updated_at 字段
        db.flush()
        
        # 清除该会话的缓存
        message_cache.invalidate(session_id)
        
        logger.info(f"成功存储{role}消息，会话ID: {session_id}")
        return True
        
    except IntegrityError as e:
        logger.error(f"存储消息失败，完整性错误: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"存储消息失败: {str(e)}")
        raise

@db_operation
def load_session_history(db: SQLAlchemySession, session_id: str, limit: int = MAX_MESSAGES_PER_SESSION, use_cache: bool = True) -> List[Dict[str, Any]]:
    """
    从数据库加载聊天历史记录。
    
    Args:
        db: 数据库会话
        session_id: 会话ID
        limit: 返回的最大消息数量
        use_cache: 是否使用缓存
        
    Returns:
        List[Dict[str, Any]]: 消息字典列表，包含id、role、content、created_at等字段
    """
    # 输入验证
    if not session_id:
        logger.warning("尝试加载历史记录时会话ID为空")
        return []
        
    try:
        # 检查缓存（如果启用）
        if use_cache:
            cached_messages = message_cache.get(session_id)
            if cached_messages is not None:
                logger.debug(f"从缓存加载会话 {session_id} 的历史记录")
                # 确保返回的是字典列表而不是ORM对象
                if cached_messages and isinstance(cached_messages[0], Message):
                    return [{"id": msg.id, "role": msg.role, "content": msg.content, 
                             "created_at": msg.created_at, "session_id": msg.session_id} 
                            for msg in cached_messages]
                return cached_messages
            
        # 直接查询需要的字段，避免返回ORM对象
        query = db.query(
            Message.id, 
            Message.role, 
            Message.content, 
            Message.created_at,
            Message.session_id
        ).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at).limit(limit)
        
        # 将查询结果转换为字典列表
        messages = [
            {
                "id": row.id,
                "role": row.role,
                "content": row.content,
                "created_at": row.created_at,
                "session_id": row.session_id
            }
            for row in query.all()
        ]
        
        # 更新缓存
        if use_cache and messages:
            message_cache.put(session_id, messages)
        
        logger.info(f"从数据库加载会话 {session_id} 的历史记录，共 {len(messages)} 条消息")
        return messages
        
    except Exception as e:
        logger.error(f"加载会话历史记录失败: {str(e)}")
        return []

def get_session_history(session_id: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
    """
    获取会话历史记录，优先使用缓存。
    
    Args:
        session_id: 会话ID
        force_refresh: 是否强制从数据库刷新数据
        
    Returns:
        List[Dict[str, Any]]: 消息字典列表，包含id、role、content、created_at等字段
    """
    try:
        # 如果不强制刷新，先检查缓存
        if not force_refresh:
            cached_messages = message_cache.get(session_id)
            if cached_messages is not None:
                logger.debug(f"从缓存获取会话 {session_id} 的历史记录")
                # 确保返回的是字典列表而不是ORM对象
                if cached_messages and isinstance(cached_messages[0], Message):
                    return [{"id": msg.id, "role": msg.role, "content": msg.content, 
                             "created_at": msg.created_at, "session_id": msg.session_id} 
                            for msg in cached_messages]
                return cached_messages
            
        # 从数据库加载（不使用缓存检查，避免递归）
        with get_db() as db:
            # 直接查询需要的字段，避免返回ORM对象
            query = db.query(
                Message.id, 
                Message.role, 
                Message.content, 
                Message.created_at,
                Message.session_id
            ).filter(
                Message.session_id == session_id
            ).order_by(Message.created_at).limit(MAX_MESSAGES_PER_SESSION)
            
            # 将查询结果转换为字典列表
            messages = [
                {
                    "id": row.id,
                    "role": row.role,
                    "content": row.content,
                    "created_at": row.created_at,
                    "session_id": row.session_id
                }
                for row in query.all()
            ]
            
            # 更新缓存
            if messages:
                message_cache.put(session_id, messages)
                logger.debug(f"更新缓存：会话 {session_id} 的历史记录，共 {len(messages)} 条消息")
            
            return messages
            
    except Exception as e:
        logger.error(f"获取会话历史记录失败: {str(e)}")
        return []

@db_operation
def create_session(db: SQLAlchemySession, session_id: str) -> Optional[Session]:
    """
    创建新的会话。
    
    Args:
        db: 数据库会话
        session_id: 会话ID
        
    Returns:
        Optional[Session]: 创建的会话对象，如果失败则返回None
    """
    try:
        session = Session(session_id=session_id)
        db.add(session)
        db.flush()
        logger.info(f"创建新会话: {session_id}")
        return session
    except IntegrityError:
        logger.warning(f"会话 {session_id} 已存在")
        return db.query(Session).filter(Session.session_id == session_id).first()
    except Exception as e:
        logger.error(f"创建会话失败: {str(e)}")
        return None

@db_operation
def delete_session(db: SQLAlchemySession, session_id: str) -> bool:
    """
    删除会话及其所有消息。
    
    Args:
        db: 数据库会话
        session_id: 会话ID
        
    Returns:
        bool: 操作是否成功
    """
    try:
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if session:
            db.delete(session)
            # 清除缓存
            message_cache.invalidate(session_id)
            logger.info(f"删除会话: {session_id}")
            return True
        else:
            logger.warning(f"尝试删除不存在的会话: {session_id}")
            return False
    except Exception as e:
        logger.error(f"删除会话失败: {str(e)}")
        return False

@db_operation
def list_sessions(db: SQLAlchemySession, limit: int = 100, offset: int = 0) -> List[Session]:
    """
    列出所有会话，按最后更新时间排序。
    
    Args:
        db: 数据库会话
        limit: 返回的最大会话数量
        offset: 分页偏移量
        
    Returns:
        List[Session]: 会话对象列表
    """
    try:
        return db.query(Session).order_by(Session.updated_at.desc()).offset(offset).limit(limit).all()
    except Exception as e:
        logger.error(f"列出会话失败: {str(e)}")
        return []

@db_operation
def update_session_title(db: SQLAlchemySession, session_id: str, title: str) -> bool:
    """
    更新会话标题。
    
    Args:
        db: 数据库会话
        session_id: 会话ID
        title: 新的会话标题
        
    Returns:
        bool: 操作是否成功
    """
    try:
        if not session_id or not title:
            logger.warning("会话ID或标题为空")
            return False
            
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if not session:
            logger.warning(f"尝试更新不存在的会话: {session_id}")
            return False
            
        session.title = title
        db.flush()
        logger.info(f"更新会话标题: {session_id} -> {title}")
        return True
    except Exception as e:
        logger.error(f"更新会话标题失败: {str(e)}")
        return False