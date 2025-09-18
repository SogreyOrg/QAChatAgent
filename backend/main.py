import re
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import AsyncGenerator, Optional, Dict, Any
import asyncio
import os
import uuid
import threading
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

import bs4
# LangChain 相关导入
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.chat_models import ChatZhipuAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from zhipuai import ZhipuAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.logger import logger_init
from utils.pdf_to_markdown import process_pdf_in_thread

logger = logger_init("main")

# 加载环境变量
load_dotenv()

# 数据库配置
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chat.db")
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


humanRole = "human"
aiRole = "assistant"


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

def get_db():
    """
    创建一个实用程序函数来管理数据库会话。该函数将确保每个数据库会话正确打开和关闭。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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

def load_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    定义一个函数来从数据库加载聊天历史记录。此函数检索与给定会话 ID 关联的所有消息并重建聊天历史记录。
    """
    db = next(get_db())
    chat_history = ChatMessageHistory()
    try:
        # Retrieve the session
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if session:
            # Add each message to the chat history
            for message in session.messages:
                chat_history.add_message({"role": message.role, "content": message.content})
    except SQLAlchemyError:
        pass
    finally:
        db.close()

    return chat_history

### Statefully manage chat history ###
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    更新 get_session_history 函数以从数据库检索会话历史记录，而不是仅使用内存存储。
    """
    if session_id not in store:
        store[session_id] = load_session_history(session_id)
    return store[session_id]

def invoke_and_save(session_id, input_text):
    """
    修改链式调用函数，同时保存用户问题和AI答案。这确保了每次交互都被记录下来。
    """
    # Save the user question with role "human"
    save_message(session_id, "human", input_text)

    # Get the AI response
    result = conversational_rag_chain.invoke(
        {"input": input_text},
        config={"configurable": {"session_id": session_id}}
    )["answer"]

    logger.info(f"invoke_and_save:{result}")

    # Save the AI answer with role "ai"
    save_message(session_id, aiRole, result)

    return result

class EmbeddingGenerator:
    def __init__(self, model_name):
        self.model_name = model_name
        self.client = ZhipuAI()

    def embed_documents(self, texts):
        embeddings = []
        for text in texts:
            response = self.client.embeddings.create(model=self.model_name, input=text)
            if hasattr(response, 'data') and response.data:
                embeddings.append(response.data[0].embedding)
            else:
                # 如果获取嵌入失败，返回一个零向量
                embeddings.append([0] * 1024)  # 假设嵌入向量维度为 1024
        return embeddings


    def embed_query(self, query):
        # 使用相同的处理逻辑，只是这次只为单个查询处理
        response = self.client.embeddings.create(model=self.model_name, input=query)
        if hasattr(response, 'data') and response.data:
            return response.data[0].embedding
        return [0] * 1024  # 如果获取嵌入失败，返回零向量

app = FastAPI(
    title="QAChatAgent API",
    description="API服务为前端提供PDF处理和知识库管理功能",
    version="0.1.0"
)

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确保上传目录存在
os.makedirs("./uploads", exist_ok=True)

# 静态文件服务
app.mount("/api/uploads", StaticFiles(directory="./uploads"), name="uploads")

# 初始化ChatZhipuAI
chat = ChatZhipuAI(
    model="glm-4",
    streaming=True,
    temperature=0.7,
    max_tokens=2048
)

# 聊天提示模板
prompt_template = ChatPromptTemplate.from_messages([
    ("system", "你是一个乐于助人的AI助手。"),
    ("human", "{input}")
])

# 创建嵌入生成器实例
embedding_generator = EmbeddingGenerator(model_name="embedding-2")

def get_chroma_store(collection_name="default"):
    # 创建 Chroma VectorStore
    chroma_store = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_generator,  # 使用定义的嵌入生成器实例
        create_collection_if_not_exists=True,
        persist_directory="./chroma_langchain_db",
    )
    return chroma_store 

def chroma_store_add_docs(collection_name, path):
    # 创建 Chroma VectorStore
    chroma_store = get_chroma_store(collection_name)

    # # 根据不同文件类型调用不同的文档加载器
    from utils.document_loader import load_document

    texts = load_document(path)

    # 添加文本到 Chroma VectorStore
    IDs = chroma_store.add_texts(texts=texts)
    logger.info("Added documents with IDs:", IDs)

def load_chroma_store_retriever(collection_name):
    chroma_store = get_chroma_store(collection_name)
    # 使用 Chroma VectorStore 创建检索器
    retriever = chroma_store.as_retriever()
    return retriever

def get_conversational_rag_chain(collection_name):

    retriever = load_chroma_store_retriever(collection_name)

    ### Contextualize question ###
    contextualize_q_system_prompt = """Given a chat history and the latest user question \
    which might reference context in the chat history, formulate a standalone question \
    which can be understood without the chat history. Do NOT answer the question, \
    just reformulate it if needed and otherwise return it as is."""
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = create_history_aware_retriever(
        chat, retriever, contextualize_q_prompt
    )

    ### Answer question ###
    qa_system_prompt = """You are an assistant for question-answering tasks. \
    Use the following pieces of retrieved context to answer the question. \
    If you don't know the answer, just say that you don't know. \
    Use three sentences maximum and keep the answer concise.\

    {context}"""
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    question_answer_chain = create_stuff_documents_chain(chat, qa_prompt)

    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

    return conversational_rag_chain

def invoke_and_save(session_id, input_text, collection_name="default"):
    """
    修改链式调用函数，同时保存用户问题和AI答案。这确保了每次交互都被记录下来。
    """
    # Save the user question with role "human"
    save_message(session_id, humanRole, input_text)

    # Get the AI response
    conversational_rag_chain = get_conversational_rag_chain(collection_name)
    result = conversational_rag_chain.invoke(
        {"input": input_text},
        config={"configurable": {"session_id": session_id}}
    )["answer"]

    logger.info(f"invoke_and_save:{result}")

    # Save the AI answer with role "ai"
    save_message(session_id, aiRole, result)

    return result


class ChatMessage(BaseModel):
    session_id: str
    message: str
    datetime: Optional[str] = None

# 文件上传接口
@app.post("/api/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads"))
        os.makedirs(upload_dir, exist_ok=True)
        
        original_name = file.filename or "file"
        file_ext = os.path.splitext(original_name)[1] or ".bin"
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        with open(file_path, "wb") as f:
            while chunk := await file.read(16 * 1024 * 1024):
                f.write(chunk)
        
        file_size = os.path.getsize(file_path)

        # if file_ext.lower() in ['.md']:
        #     document_loader_markdown(file_path)
        
        if file_ext.lower() in ['.pdf', '.pdfa', '.pdfx']:
            background_tasks.add_task(process_pdf_in_thread, file_path)
            thread = threading.current_thread()
            return {
                "code": 200,
                "message": "文件上传成功，PDF处理中",
                "data": {
                    "originalName": file.filename,
                    "savedName": unique_filename,
                    "filePath": f"/api/uploads/{unique_filename}",
                    "size": file_size,
                    "processing": True,
                    "taskId": thread.ident
                }
            }
        
        return {
            "code": 200,
            "message": "文件上传成功",
            "data": {
                "originalName": file.filename,
                "savedName": unique_filename,
                "filePath": f"/api/uploads/{unique_filename}",
                "size": file_size
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

# 文件删除接口
@app.delete("/api/delete/{filename}")
async def delete_file(filename: str):
    try:
        from urllib.parse import unquote
        upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads"))
        decoded_filename = unquote(filename)
        file_path = os.path.join(upload_dir, decoded_filename)
        
        if not os.path.abspath(file_path).startswith(upload_dir):
            raise HTTPException(status_code=400, detail="非法文件路径")
            
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
            
        os.remove(file_path)
        return {
            "code": 200,
            "message": "文件删除成功",
            "data": {
                "deletedFile": filename
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件删除失败: {str(e)}")

# 任务状态查询接口
@app.get("/api/task/status/{task_id}")
async def get_task_status(task_id: int) -> Dict[str, Any]:
    try:
        thread = next((t for t in threading.enumerate() if t.ident == task_id), None)
        if thread:
            return {
                "code": 200,
                "message": "任务运行中",
                "data": {
                    "taskId": task_id,
                    "status": "running",
                    "isAlive": thread.is_alive()
                }
            }
        else:
            return {
                "code": 404,
                "message": "任务不存在或已完成",
                "data": {
                    "taskId": task_id,
                    "status": "not_found"
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询任务状态失败: {str(e)}")

# 新增RAG流式响应生成函数
async def generate_rag_response_stream_with_context(input_text: str, session_id: str, collection_name: str = "default") -> AsyncGenerator[str, None]:
    """流式生成基于RAG的大模型响应，包含历史消息上下文和知识库检索结果"""
    db = next(get_db())
    try:
        # 获取当前会话
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if not session:
            yield "data: [ERROR] 会话不存在\n\n"
            return

        # 获取历史消息
        db_messages = db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at).all()
        
        # 构建消息历史用于上下文感知检索
        chat_history = []
        for msg in db_messages:
            if str(msg.role) == humanRole:
                chat_history.append(HumanMessage(content=str(msg.content)))
            elif str(msg.role) == aiRole:
                chat_history.append(AIMessage(content=str(msg.content)))
            else:
                # 系统消息或其他类型
                chat_history.append(AIMessage(content=str(msg.content)))
        
        # 加载知识库检索器
        retriever = load_chroma_store_retriever(collection_name)
        
        # 创建上下文感知的问题
        contextualize_q_system_prompt = """Given a chat history and the latest user question \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history. Do NOT answer the question, \
        just reformulate it if needed and otherwise return it as is."""
        
        # 使用上下文感知检索器
        standalone_question = await chat.ainvoke(
            [
                {"role": "system", "content": contextualize_q_system_prompt},
                *[{"role": humanRole if isinstance(msg, HumanMessage) else aiRole, "content": msg.content} for msg in chat_history],
                {"role": humanRole, "content": input_text}
            ]
        )
        
        # 检索相关文档
        docs = retriever.get_relevant_documents(standalone_question.content)
        
        # 构建系统提示，包含检索到的上下文
        context_text = "\n\n".join([doc.page_content for doc in docs])
        system_prompt = f"""你是一个乐于助人的AI助手小Q。请使用以下检索到的上下文信息来回答问题。

        ## 限制
        如果上下文中没有相关信息，必须向用户说明`我翻阅了所有笔记但没找到相关资料。下面我将根据自己的知识回答。`，
        并且请基于你自己的知识回答，但不要编造信息。
        
        检索到的上下文:
        {context_text}
        """
        
        # 构建完整的消息历史
        langchain_messages = []
        
        # 添加系统消息
        langchain_messages.append(SystemMessage(content=system_prompt))
        
        # 添加历史消息
        for msg in db_messages:
            logger.info(f"添加历史消息: {str(msg.content)} - 角色: {str(msg.role)}")
            if str(msg.role) == humanRole:
                langchain_messages.append(HumanMessage(content=str(msg.content)))
            elif str(msg.role) == aiRole:
                langchain_messages.append(AIMessage(content=str(msg.content)))
            else:
                # 系统消息或其他类型
                langchain_messages.append(AIMessage(content=str(msg.content)))
        
        # 添加当前用户消息
        langchain_messages.append(HumanMessage(content=input_text))
        
        # 流式生成响应
        async for chunk in chat.astream(langchain_messages):
            content = chunk.content
            if content:
                yield f"data: {content}\n\n"
                await asyncio.sleep(0.01)  # 控制流式速度
                
    except Exception as e:
        logger.error(f"生成RAG响应时出错: {str(e)}")
        yield f"data: [ERROR] {str(e)}\n\n"
    finally:
        db.close()

# 修改流式聊天接口，添加知识库参数
@app.get("/api/chat/stream")
async def stream_chat_response(session_id: str, message: str, collection_name: str = "default"):
    """SSE流式响应端点，支持基于知识库的回答"""
    full_response = ""
    try:
        logger.info(f"流式聊天：{session_id} - {message} - 知识库：{collection_name}")
        # 收集用户消息
        save_message(session_id, humanRole, message)
        
        # 收集AI响应
        async def generate_response():
            nonlocal full_response
            try:
                # 使用RAG知识库增强的流式响应
                async for chunk in generate_rag_response_stream_with_context(message, session_id, collection_name):
                    content = chunk.replace("data: ", "").strip()
                    full_response += content
                    yield chunk

                if full_response:
                    # 收集AI响应消息
                    save_message(session_id, aiRole, full_response)
                
                # 发送结束标记
                yield "data: [DONE]\n\n"
                    
            except Exception as e:
                logger.error(f"流式响应处理出错: {str(e)}")
                yield f"data: [ERROR] {str(e)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"流式聊天接口错误: {str(e)}")
        # 返回错误响应
        async def error_response():
            yield f"data: [ERROR] {str(e)}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(
            error_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)