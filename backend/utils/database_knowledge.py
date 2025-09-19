import os
import functools
from contextlib import contextmanager
from typing import List, Dict, Optional, Generator, Any, Callable, TypeVar
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, ForeignKey, Index
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session as SQLAlchemySession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from .logger import logger_init

logger = logger_init("knowledge_db")

# 确保数据库目录存在
os.makedirs("dbs", exist_ok=True)

# 数据库配置
KNOWLEDGE_DB_URL = os.getenv("KNOWLEDGE_DB_URL", "sqlite:///./dbs/knowledge.db")

# 创建数据库引擎
engine = create_engine(
    KNOWLEDGE_DB_URL,
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
    """数据库会话上下文管理器"""
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
    """数据库操作装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with get_db() as db:
            try:
                return func(db, *args, **kwargs)
            except SQLAlchemyError as e:
                logger.error(f"数据库操作失败: {str(e)}")
                raise
    return wrapper

# 知识库表模型
class KnowledgeBase(Base):
    """知识库表"""
    __tablename__ = "knowledgeBases"
    
    id: Column[str] = Column(String(64), primary_key=True)
    name: Column[str] = Column(String(255), nullable=False)
    description: Column[str] = Column(Text, default="")
    created_at: Column[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Column[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                                       onupdate=lambda: datetime.now(timezone.utc))
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")

# 文档表模型
class Document(Base):
    """文档表"""
    __tablename__ = "documents"
    
    id: Column[str] = Column(String(64), primary_key=True)
    knowledge_base_id: Column[str] = Column(String(64), ForeignKey("knowledgeBases.id"), nullable=False)
    name: Column[str] = Column(String(255), nullable=False)  # 原始文件名
    saved_name: Column[str] = Column(String(255), nullable=False)  # 存储文件名
    path: Column[str] = Column(String(512), nullable=False)  # 文件访问路径
    annotated_path: Column[str] = Column(String(512), default="")  # 批注文件路径(仅PDF)
    md_path: Column[str] = Column(String(512), default="")  # Markdown文件路径(仅PDF)
    size: Column[int] = Column(Integer, nullable=False)  # 文件大小(字节)
    uploaded_at: Column[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    
    # 添加索引
    __table_args__ = (
        Index('idx_documents_knowledge_base', knowledge_base_id),
        Index('idx_documents_uploaded_at', uploaded_at),
    )

# 创建表
try:
    Base.metadata.create_all(bind=engine)
    logger.info("知识库数据库表创建成功")
except OperationalError as e:
    logger.error(f"创建知识库表失败: {str(e)}")
    raise

# 缓存实现
class KnowledgeCache:
    """知识库缓存"""
    def __init__(self, capacity=100):
        self.capacity = capacity
        self.cache: Dict[str, Any] = {}
        self.usage_order: List[str] = []
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            self.usage_order.remove(key)
            self.usage_order.append(key)
            return self.cache[key]
        return None
    
    def put(self, key: str, value: Any) -> None:
        if key in self.cache:
            self.usage_order.remove(key)
        elif len(self.cache) >= self.capacity:
            oldest = self.usage_order.pop(0)
            del self.cache[oldest]
        self.cache[key] = value
        self.usage_order.append(key)
    
    def invalidate(self, key: str) -> None:
        if key in self.cache:
            del self.cache[key]
            self.usage_order.remove(key)
    
    def clear(self) -> None:
        self.cache.clear()
        self.usage_order.clear()

# 初始化缓存
knowledge_cache = KnowledgeCache(capacity=50)

# 知识库操作
@db_operation
def create_knowledge_base(db: SQLAlchemySession, kb_id: str, name: str, description: str = "") -> Optional[KnowledgeBase]:
    """创建知识库"""
    try:
        kb = KnowledgeBase(id=kb_id, name=name, description=description)
        db.add(kb)
        db.flush()
        logger.info(f"创建知识库: {name} (ID: {kb_id})")
        return kb
    except IntegrityError:
        logger.warning(f"知识库 {kb_id} 已存在")
        return db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    except Exception as e:
        logger.error(f"创建知识库失败: {str(e)}")
        return None

@db_operation
def delete_knowledge_base(db: SQLAlchemySession, kb_id: str) -> bool:
    """删除知识库及其所有文档"""
    try:
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if kb:
            db.delete(kb)
            knowledge_cache.invalidate(kb_id)
            logger.info(f"删除知识库: {kb_id}")
            return True
        logger.warning(f"尝试删除不存在的知识库: {kb_id}")
        return False
    except Exception as e:
        logger.error(f"删除知识库失败: {str(e)}")
        return False

@db_operation
def list_knowledge_bases(db: SQLAlchemySession, limit: int = 100, offset: int = 0) -> List[KnowledgeBase]:
    """列出所有知识库"""
    try:
        return db.query(KnowledgeBase).order_by(KnowledgeBase.updated_at.desc()).offset(offset).limit(limit).all()
    except Exception as e:
        logger.error(f"列出知识库失败: {str(e)}")
        return []

@db_operation
def get_knowledge_base(db: SQLAlchemySession, kb_id: str) -> Optional[KnowledgeBase]:
    """获取单个知识库"""
    try:
        return db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    except Exception as e:
        logger.error(f"获取知识库失败: {str(e)}")
        return None

# 文档操作
@db_operation
def add_document(
    db: SQLAlchemySession,
    doc_id: str,
    kb_id: str,
    name: str,
    saved_name: str,
    path: str,
    size: int,
    annotated_path: str = "",
    md_path: str = ""
) -> Optional[Document]:
    """添加文档到知识库"""
    try:
        # 检查知识库是否存在
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        
        # 如果是默认知识库且不存在，则自动创建
        if not kb and kb_id == "0":
            kb = KnowledgeBase(id="0", name="默认知识库", description="系统默认知识库")
            db.add(kb)
            db.flush()
            logger.info(f"自动创建默认知识库: {kb_id}")
        elif not kb:
            logger.error(f"知识库不存在: {kb_id}")
            return None
            
        # 添加文档
        doc = Document(
            id=doc_id,
            knowledge_base_id=kb_id,
            name=name,
            saved_name=saved_name,
            path=path,
            annotated_path=annotated_path,
            md_path=md_path,
            size=size
        )
        db.add(doc)
        db.flush()
        knowledge_cache.invalidate(kb_id)
        logger.info(f"添加文档到知识库 {kb_id}: {name} (ID: {doc_id})")
        return doc
    except IntegrityError as e:
        logger.error(f"文档 {doc_id} 已存在: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"添加文档失败: {str(e)}")
        return None

@db_operation
def delete_document(db: SQLAlchemySession, doc_id: str, kb_id: Optional[str] = None) -> bool:
    """删除文档及其相关文件，可选验证知识库ID"""
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            logger.warning(f"尝试删除不存在的文档: {doc_id}")
            return False
            
        # 验证知识库ID（如果提供）
        if kb_id is not None and doc.knowledge_base_id != kb_id:
            logger.error(f"文档不属于指定知识库 - 文档ID: {doc_id}, 请求知识库ID: {kb_id}, 实际知识库ID: {doc.knowledge_base_id}")
            return False
            
        upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
        
        # 删除主文件
        saved_name = str(doc.saved_name) if doc.saved_name else None
        if saved_name:
            file_path = os.path.join(upload_dir, saved_name)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # 删除PDF批注文件
        annotated_path = str(doc.annotated_path) if doc.annotated_path else None
        if annotated_path:
            annotated_file = os.path.join(upload_dir, os.path.basename(annotated_path))
            if os.path.exists(annotated_file):
                os.remove(annotated_file)
                
        # 删除pdf解析Markdown文件
        md_path = str(doc.md_path) if doc.md_path else None
        if md_path:
            md_file = os.path.join(upload_dir, os.path.basename(md_path))
            if os.path.exists(md_file):
                os.remove(md_file)
        
        # 删除同名文件夹及其内容
        if saved_name:
            try:
                file_base = os.path.splitext(saved_name)[0]
                dir_path = os.path.join(upload_dir, file_base)
                if os.path.exists(dir_path) and os.path.isdir(dir_path):
                    import shutil
                    shutil.rmtree(dir_path)
            except Exception as e:
                logger.warning(f"删除同名文件夹失败: {str(e)}")
        
        db.delete(doc)
        knowledge_cache.invalidate(str(doc.knowledge_base_id))
        logger.info(f"删除文档及相关文件: {doc_id}")
        return True
        
    except Exception as e:
        logger.error(f"删除文档失败: {str(e)}")
        return False


@db_operation
def list_documents(db: SQLAlchemySession, kb_id: str, limit: int = 100, offset: int = 0) -> List[Document]:
    """列出知识库中的所有文档"""
    try:
        return db.query(Document).filter(Document.knowledge_base_id == kb_id)\
            .order_by(Document.uploaded_at.desc())\
            .offset(offset).limit(limit).all()
    except Exception as e:
        logger.error(f"列出文档失败: {str(e)}")
        return []

@db_operation
def get_document(db: SQLAlchemySession, doc_id: str) -> Optional[Document]:
    """获取单个文档"""
    try:
        return db.query(Document).filter(Document.id == doc_id).first()
    except Exception as e:
        logger.error(f"获取文档失败: {str(e)}")
        return None

@db_operation
def update_document_paths(
    db: SQLAlchemySession, 
    doc_id: str, 
    annotated_path: Optional[str] = None, 
    md_path: Optional[str] = None
) -> bool:
    """更新文档处理后的路径(PDF专用)"""
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            logger.warning(f"尝试更新不存在的文档: {doc_id}")
            return False
            
        if annotated_path is not None:
            doc.annotated_path = annotated_path if annotated_path is not None else ""  # type: ignore[assignment]
        if md_path is not None:
            doc.md_path = md_path if md_path is not None else ""  # type: ignore[assignment]
            
        db.flush()
        knowledge_cache.invalidate(str(doc.knowledge_base_id))
        logger.info(f"更新文档路径: {doc_id}")
        return True
    except Exception as e:
        logger.error(f"更新文档路径失败: {str(e)}")
        return False