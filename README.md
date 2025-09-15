# QAChatAgent - PDF处理与知识库系统

## 功能特性
- PDF文件上传与处理
- 自动转换为Markdown格式
- 知识库管理接口
- 现代化Web界面

## 技术栈
- 后端：FastAPI + Python 3.11
- 前端：Vite + Vue 3 + Element Plus
- OCR：PaddleOCR + Tesseract
- PDF处理：PyMuPDF + Unstructured

## 项目结构
```
QAChatAgent2/
├── backend/            # 后端代码
│   ├── main.py        # 主API服务
│   ├── pdf_to_markdown.py  # PDF处理核心
│   ├── uploads/       # 文件上传目录
│   └── environment.yml # 环境配置
├── frontend/           # 前端代码
│   ├── public/
│   └── src/
├── start.ps1           # 一键启动脚本
└── README.md           # 项目文档
```

## 快速启动
```powershell
# 克隆项目
git clone https://github.com/yourname/QAChatAgent2.git
cd QAChatAgent2

# 启动服务 (需预先安装Python和Node.js)
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
npm install
npm run dev
```

## 常见问题
1. 删除文件失败？
   - 检查后端服务是否运行
   - 确认文件权限设置正确