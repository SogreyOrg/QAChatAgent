from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
import threading
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import io
import uuid
import logging
import sys

# 强制标准输出和错误输出使用UTF-8编码
try:
    if not sys.stdout or sys.stdout.closed:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if not sys.stderr or sys.stderr.closed:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except (AttributeError, io.UnsupportedOperation):
    pass

# 配置日志
logger = logging.getLogger("main")
logger.setLevel(logging.INFO)

# 清除现有处理器
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# 确保日志处理器使用UTF-8编码
try:
    # 文件处理器 - 强制UTF-8编码
    file_handler = logging.FileHandler("log", encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    
    # 控制台处理器 - 确保UTF-8输出
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # 测试日志编码 - 使用ASCII字符确保兼容性
    logger.info("日志系统初始化成功 (编码测试: ASCII only)")
except Exception as e:
    error_msg = f"严重错误: 日志系统初始化失败 - {str(e)}"
    print(error_msg, file=sys.stderr)
    sys.stderr.flush()  # 确保错误信息立即输出
    raise

# 禁用第三方库的冗余日志
logging.getLogger('pikepdf').setLevel(logging.WARNING)
logging.getLogger('pdfminer').setLevel(logging.WARNING)
logging.getLogger('unstructured_inference').setLevel(logging.WARNING)
logging.getLogger('timm').setLevel(logging.WARNING)

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

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "QAChatAgent API服务运行中"}

from fastapi.staticfiles import StaticFiles

# 添加静态文件服务（放在路由定义之前）
app.mount("/api/uploads", StaticFiles(directory="./uploads"), name="uploads")

@app.post("/api/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """标准化文件上传接口（带进度反馈）"""
    try:
        # 上传目录路径改为backend/uploads
        upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads"))
        os.makedirs(upload_dir, exist_ok=True)
        if not os.path.isdir(upload_dir):
            raise Exception(f"上传目录创建失败: {upload_dir}")
        logger.info(f"文件将保存到: {upload_dir}")
        
        # 安全处理文件名：uuidv4.原文件后缀名
        import uuid
        original_name = file.filename or "file"
        file_ext = os.path.splitext(original_name)[1] or ".bin"  # 获取文件后缀，默认.bin
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        print(f"准备保存文件到: {file_path}")  # 调试日志
        
        # 使用临时内存文件加速写入
        from tempfile import SpooledTemporaryFile
        with SpooledTemporaryFile(max_size=16*1024*1024) as temp_file:
            # 快速写入内存
            while chunk := await file.read(16 * 1024 * 1024):  # 16MB/块
                temp_file.write(chunk)
            
            # 一次性写入磁盘
            temp_file.seek(0)
            with open(file_path, "wb") as f:
                f.write(temp_file.read())
        
        # 快速验证并获取大小
        if not os.path.exists(file_path):
            raise Exception("文件保存失败")
        file_size = os.path.getsize(file_path)
        
        # 检测是否为PDF文件，如果是则在后台处理
        if file_ext.lower() in ['.pdf', '.pdfa', '.pdfx']:  # 支持更多PDF变种
            # 减少日志输出提升性能
            logger.debug(f"检测到PDF文件({file_ext})")
            
            try:
                # 使用后台任务处理PDF（更可靠的异步方式）
                background_tasks.add_task(process_pdf_in_thread, file_path)
                thread = threading.current_thread()
                
                # 简化响应，不等待处理完成
                return {
                    "code": 200,
                    "message": "文件上传成功，PDF处理中",
                    "data": {
                        "originalName": file.filename,
                        "savedName": unique_filename,
                        "fileKey": unique_filename,
                        "filePath": f"/api/uploads/{unique_filename}",
                        "downloadUrl": f"/api/uploads/{unique_filename}",
                        "size": file_size,
                        "processing": True,
                        "taskId": thread.ident
                    }
                }
                
            except Exception as e:
                logger.error(f"PDF处理启动失败: {str(e)}", exc_info=True)
                # 即使PDF处理失败，仍然返回上传成功
                return {
                    "code": 200,
                    "message": "文件上传成功，PDF处理启动失败",
                    "data": {
                        "originalName": file.filename,
                        "savedName": unique_filename,
                        "fileKey": unique_filename,
                        "filePath": f"/api/uploads/{unique_filename}",
                        "downloadUrl": f"/api/uploads/{unique_filename}",
                        "size": file_size,
                        "processing": False,
                        "error": str(e)
                    }
                }
        
        return {
            "code": 200,
            "message": "文件上传成功",
            "data": {
                "originalName": file.filename,  # 原始文件名
                "savedName": unique_filename,   # 存储的唯一文件名 (uuid.ext)
                "fileKey": unique_filename,     # 文件唯一标识 (同savedName)
                "filePath": f"/api/uploads/{unique_filename}",  # 完整访问路径
                "downloadUrl": f"/api/uploads/{unique_filename}",  # 下载URL
                "size": file_size
            }
        }
        
    except Exception as e:
        print(f"文件上传错误: {str(e)}")  # 错误日志
        raise HTTPException(
            status_code=500,
            detail={
                "code": 500,
                "message": f"文件上传失败: {str(e)}"
            }
        )

# 添加任务状态查询接口
from typing import Optional, Dict, Any

@app.get("/api/task/status/{task_id}")
async def get_task_status(task_id: int) -> Dict[str, Any]:
    """查询后台任务状态"""
    try:
        import threading
        # 使用threading.enumerate()替代_threading._active
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
        raise HTTPException(
            status_code=500,
            detail={
                "code": 500,
                "message": f"查询任务状态失败: {str(e)}"
            }
        )

@app.delete("/api/delete/{filename}")
async def delete_file(filename: str):
    """删除上传的文件"""
    try:
        from urllib.parse import unquote
        upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads"))
        decoded_filename = unquote(filename)  # 解码URL编码的文件名
        file_path = os.path.join(upload_dir, decoded_filename)
        
        # 安全检查：防止目录遍历攻击
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
        raise HTTPException(
            status_code=500,
            detail={
                "code": 500,
                "message": f"文件删除失败: {str(e)}"
            }
        )

# 在此添加更多API路由...

if __name__ == "__main__":
    import uvicorn
    # 添加启动信息
    logger.info(f"启动目录: {os.getcwd()}")
    logger.info(f"脚本路径: {os.path.abspath(__file__)}")
    uvicorn.run(app, host="0.0.0.0", port=8000)