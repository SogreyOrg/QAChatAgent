
from typing import List, Dict, Any, Optional
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from .embeding import EmbeddingGenerator, get_embedding_generator
from .logger import logger_init
import os
from datetime import datetime
from typing_extensions import Protocol

logger = logger_init("chroma_store")

# 从环境变量或配置文件中读取配置
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "embedding-2")
CHROMA_STORE_PATHDIRECTORY = os.getenv("CHROMA_STORE_PATHDIRECTORY", "./chroma_langchain_db")

# 创建嵌入生成器实例
embedding_generator = get_embedding_generator(model_name=EMBEDDING_MODEL_NAME)
if not hasattr(embedding_generator, 'embed_documents') or not hasattr(embedding_generator, 'embed_query'):
    logger.warning("Embedding generator does not implement required methods")
    embedding_generator = None

def get_chroma_store(kb_id: str = "0") -> Chroma:
    """
    获取或创建Chroma向量存储
    
    Args:
        kb_id: 知识库ID，默认为"0"(系统知识库)
        
    Returns:
        Chroma向量存储实例
    """
    # 确保嵌入生成器实现了Embeddings接口
    embedding_func = embedding_generator if isinstance(embedding_generator, Embeddings) else None
    
    return Chroma(
        collection_name=f"chroma_{kb_id}",
        embedding_function=embedding_func,
        create_collection_if_not_exists=True,
        persist_directory=CHROMA_STORE_PATHDIRECTORY,
    )

def chroma_store_add_docs(kb_id: str, path: str) -> List[str]:
    """
    添加文档到ChromaDB向量存储，保留完整元数据
    
    Args:
        kb_id: 知识库ID
        path: 文件路径
        
    Returns:
        存储的文档ID列表
    """
    chroma_store = get_chroma_store(kb_id)
    from .document_loader import load_document
    from datetime import datetime
    import os
    
    # 获取文本和元数据
    texts, metadatas = load_document(path)
    
    # 添加基础元数据
    base_metadata = {
        'source': os.path.basename(path),
        'kb_id': kb_id,
        'timestamp': datetime.now().isoformat(),
        'file_path': path
    }
    
    # 合并元数据 (确保类型安全)
    full_metadatas: List[Dict[str, Any]] = []
    for md in metadatas:
        if not isinstance(md, dict):
            md = {}
        full_metadata = {**base_metadata, **md}
        full_metadatas.append(full_metadata)
    
    # 存储文档和元数据
    try:
        doc_ids = chroma_store.add_texts(
            texts=texts,
            metadatas=full_metadatas,
            embedding_function=embedding_generator if isinstance(embedding_generator, Embeddings) else None
        )
        logger.info(f"成功存储 {len(doc_ids)} 个文档到知识库 {kb_id}")
        return doc_ids
    except Exception as e:
        logger.error(f"存储文档到ChromaDB失败: {str(e)}")
        logger.error(f"元数据内容: {full_metadatas}")
        raise

def load_chroma_store_retriever(kb_id: str):
    """
    创建带元数据的ChromaDB检索器
    
    Args:
        kb_id: 知识库ID
        
    Returns:
        配置好的检索器实例
    """
    chroma_store = get_chroma_store(kb_id)
    return chroma_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": 10,
            "score_threshold": 0.5,
            "include": ["metadatas", "documents", "distances"]
        }
    )