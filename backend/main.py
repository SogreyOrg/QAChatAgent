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
        
        # 安全处理文件名
        import uuid
        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
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
                "originalName": file.filename,
                "savedName": unique_filename,
                "filePath": f"/api/uploads/{unique_filename}",
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

# 在此添加更多API路由...

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)