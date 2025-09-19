
from langchain_chroma import Chroma
from .embeding import EmbeddingGenerator, get_embedding_generator
from .logger import logger_init
import os

logger = logger_init("chroma_store")

# 从环境变量或配置文件中读取配置
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "embedding-2")
CHROMA_STORE_PATHDIRECTORY = os.getenv("CHROMA_STORE_PATHDIRECTORY", "./chroma_langchain_db")

# 创建嵌入生成器实例
embedding_generator: EmbeddingGenerator = get_embedding_generator(model_name=EMBEDDING_MODEL_NAME)

def get_chroma_store(collection_name="default"):
    # 创建 Chroma VectorStore
    chroma_store = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_generator,  # 使用定义的嵌入生成器实例
        create_collection_if_not_exists=True,
        persist_directory=CHROMA_STORE_PATHDIRECTORY,
    )
    return chroma_store 

def chroma_store_add_docs(collection_name, path):
    # 创建 Chroma VectorStore
    chroma_store = get_chroma_store(collection_name)

    # # 根据不同文件类型调用不同的文档加载器
    from .document_loader import load_document

    texts = load_document(path)

    # 添加文本到 Chroma VectorStore
    IDs = chroma_store.add_texts(texts=texts)
    logger.info("Added documents with IDs:", IDs)

def load_chroma_store_retriever(collection_name):
    chroma_store = get_chroma_store(collection_name)
    # 使用 Chroma VectorStore 创建检索器
    retriever = chroma_store.as_retriever()
    return retriever