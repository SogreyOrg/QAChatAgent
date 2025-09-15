# QAChatAgent - PDF处理与知识库系统

## 功能特性
- PDF文件上传与处理
- 自动转换为Markdown格式
- 知识库管理接口
- 现代化Web界面

## 技术栈
- 后端：FastAPI + Python 3.11
- 前端：Vite + React
- OCR：PaddleOCR + Tesseract
- PDF处理：PyMuPDF + Unstructured

## 快速启动
```powershell
# 克隆项目
git clone https://github.com/yourname/QAChatAgent2.git
cd QAChatAgent2

# 安装后端依赖
conda env create -f backend/environment.yml
conda activate multimodal-rag-pdf

# 安装前端依赖
cd frontend
npm install
cd ..

# 启动服务
./start.ps1
```

## 开发指南
1. 后端开发：
```bash
cd backend
python main.py
```

2. 前端开发：
```bash
cd frontend
npm run dev
```

## 文件说明
- `backend/main.py`: 主API服务
- `backend/pdf_to_markdown.py`: PDF处理核心逻辑
- `start.ps1`: 一键启动脚本