
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Body
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import AsyncGenerator, Optional, Dict, Any
from pydantic import BaseModel
import os
import uuid
import threading
from dotenv import load_dotenv

from utils.logger import logger_init
from utils.pdf_to_markdown import process_pdf_in_thread
from utils.database import get_db, save_message, get_session_history, load_session_history, update_session_title, Session, Message
from utils.chroma_store import load_chroma_store_retriever
from utils.rag_chat import generate_rag_response_stream_with_context
from utils._config import humanRole, aiRole

logger = logger_init("main")

# 加载环境变量
load_dotenv()

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

# 定义请求模型
class SessionUpdateModel(BaseModel):
    title: str

# 会话标题更新接口
@app.put("/api/session/{session_id}")
async def update_session(session_id: str, session_data: SessionUpdateModel):
    """更新会话信息，如标题"""
    try:
        logger.info(f"更新会话: {session_id}, 标题: {session_data.title}")
        
        # 更新会话标题
        success = update_session_title(session_id, session_data.title)
        
        if success:
            return {
                "code": 200,
                "message": "会话更新成功",
                "data": {
                    "session_id": session_id,
                    "title": session_data.title
                }
            }
        else:
            raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在或更新失败")
            
    except Exception as e:
        logger.error(f"更新会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新会话失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)