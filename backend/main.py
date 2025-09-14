from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import uuid

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
app.mount("/api/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """标准化文件上传接口"""
    try:
        # 使用正确的上传目录路径
        upload_dir = os.path.abspath("uploads")
        os.makedirs(upload_dir, exist_ok=True)
        if not os.path.isdir(upload_dir):
            raise Exception(f"上传目录创建失败: {upload_dir}")
        
        # 安全处理文件名：uuidv4.原文件后缀名
        import uuid
        original_name = file.filename or "file"
        file_ext = os.path.splitext(original_name)[1] or ".bin"  # 获取文件后缀，默认.bin
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        print(f"准备保存文件到: {file_path}")  # 调试日志
        
        # 分块写入文件
        with open(file_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):  # 1MB/块
                f.write(chunk)
        
        # 验证文件是否保存成功
        if not os.path.exists(file_path):
            raise Exception("文件保存后验证失败")
            
        file_size = os.path.getsize(file_path)
        print(f"文件保存成功，大小: {file_size}字节")
        
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

@app.delete("/api/delete/{filename}")
async def delete_file(filename: str):
    """删除上传的文件"""
    try:
        from urllib.parse import unquote
        upload_dir = os.path.abspath("uploads")
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
    uvicorn.run(app, host="0.0.0.0", port=8000)