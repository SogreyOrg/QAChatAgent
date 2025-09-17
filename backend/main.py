from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import AsyncGenerator, Optional, Dict, Any
import asyncio
import logging
import os
import uuid
import threading
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# LangChain 相关导入
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage

# 加载环境变量
load_dotenv()

# 数据库配置
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chat.db")
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

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

# 配置日志
logger = logging.getLogger("main")
logger.setLevel(logging.INFO)

# 清除现有处理器
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# 配置日志处理器
file_handler = logging.FileHandler("log", encoding='utf-8')
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
console_handler = logging.StreamHandler(stream=sys.stdout)
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
logger.addHandler(file_handler)
logger.addHandler(console_handler)
logger.info("日志系统初始化成功")

# 确保pdf_to_markdown模块可以导入
try:
    # 直接导入方式
    from pdf_to_markdown import process_pdf_in_thread
    logger.info("成功导入 pdf_to_markdown 模块 (直接导入)")
except ImportError as e:
    try:
        # 备用方案：从上级目录导入
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from backend.pdf_to_markdown import process_pdf_in_thread
        logger.info("成功导入 pdf_to_markdown 模块 (绝对路径)")
    except ImportError:
        # 最终错误处理
        current_dir = os.path.dirname(os.path.abspath(__file__))
        error_msg = f"""
        无法导入 pdf_to_markdown 模块！
        已尝试：
        1. 直接导入: from pdf_to_markdown import...
        2. 绝对路径导入: from backend.pdf_to_markdown import...
        
        请检查：
        1. 文件是否存在: {os.path.join(current_dir, 'pdf_to_markdown.py')}
        2. 文件内容是否正确
        当前Python路径: {sys.path}
        """
        print(error_msg, file=sys.stderr)
        sys.stderr.flush()
        logger.error(error_msg)
        raise

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
        
        if file_ext.lower() in ['.pdf', '.pdfa', '.pdfx']:
            from pdf_to_markdown import process_pdf_in_thread
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

# 流式聊天接口
@app.get("/api/chat/stream")
async def stream_chat_response(session_id: str, message: str):
    """SSE流式响应端点"""
    db = SessionLocal()
    session = None
    full_response = ""
    try:
        logger.info(f"流式聊天：{session_id} - {message}")
        # 检查或创建会话
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if not session:
            session = Session(session_id=session_id)
            db.add(session)
            db.commit()
            db.refresh(session)
        
        # 存储用户消息
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
            
        user_message = Message(
            session_id=session.session_id,
            role="user",
            content=str(message)
        )
        db.add(user_message)
        db.commit()
        
        # 收集AI响应
        async def generate_response():
            nonlocal full_response
            try:
                async for chunk in generate_response_stream_with_context(message, session_id):
                    content = chunk.replace("data: ", "").strip()
                    # logger.info(f"AI响应: {content}")
                    full_response += content
                    yield chunk
                
                # 存储AI响应
                if full_response:
                    # 使用新的数据库会话存储AI响应
                    store_db = None
                    try:
                        store_db = SessionLocal()
                        ai_message = Message(
                            session_id=session_id,
                            role="assistant",
                            content=full_response
                        )
                        store_db.add(ai_message)
                        store_db.commit()
                        logger.info(f"成功存储AI响应: {full_response[:50]}...")
                    except Exception as e:
                        logger.error(f"存储AI响应失败: {str(e)}")
                        if store_db:
                            store_db.rollback()
                    finally:
                        if store_db:
                            store_db.close()
                    
            except Exception as e:
                logger.error(f"流式响应处理出错: {str(e)}")
                raise

        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream"
        )
        
    finally:
        db.close()

async def generate_response_stream_with_context(input_text: str, session_id: str) -> AsyncGenerator[str, None]:
    """流式生成大模型响应，包含历史消息上下文"""
    db = SessionLocal()
    try:
        # 获取当前会话
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if not session:
            yield "data: [ERROR] 会话不存在\n\n"
            return

        # 构建消息历史
        messages = [("system", "你是一个乐于助人的AI助手。")]
        
        # 获取历史消息
        db_messages = db.query(Message).filter(
            Message.session_id == session.id
        ).order_by(Message.created_at).all()
        
        for msg in db_messages:
            messages.append((str(msg.role), str(msg.content)))
        
        # 添加当前用户消息
        messages.append(("user", input_text))
        
        # 转换为LangChain消息格式
        langchain_messages = []
        for role, content in messages:
            if role == "user":
                langchain_messages.append(HumanMessage(content=content))
            else:
                langchain_messages.append(AIMessage(content=content))
        
        # 流式生成响应
        async for chunk in chat.astream(langchain_messages):
            content = chunk.content
            if content:
                yield f"data: {content}\n\n"
                await asyncio.sleep(0.02)  # 控制流式速度
                
    except Exception as e:
        logger.error(f"生成响应时出错: {str(e)}")
        yield "data: [ERROR] 生成响应时出错\n\n"
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)