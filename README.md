# QAChatAgent - PDF处理与知识库系统

## 项目概述
QAChatAgent 是一个集成了 PDF 处理、知识库管理和智能对话功能的 AI 辅助系统。该项目采用前后端分离架构，通过现代化的 Web 界面提供 PDF 文件处理、Markdown 转换、知识库管理和智能对话等功能。

## 核心功能

### PDF 处理与转换
- **PDF 文件上传与解析**：支持上传 PDF 文件并进行结构化解析
- **智能内容识别**：使用 OCR 技术识别 PDF 中的文本、表格和图像
- **Markdown 转换**：将 PDF 内容转换为 Markdown 格式，便于后续编辑和使用
- **批注版 PDF 生成**：自动生成带有内容区域标注的 PDF 文件

### 知识库管理
- **知识库创建与删除**：支持创建和管理多个知识库
- **文档上传与预览**：支持上传文档到知识库并提供预览功能
- **文档分类与管理**：对知识库中的文档进行分类和管理

### 智能对话
- **基于知识库的问答**：利用知识库内容进行智能问答
- **会话管理**：支持创建、切换和删除多个对话会话
- **流式响应**：采用 SSE 技术实现流式对话响应

## 技术栈
- **后端**：FastAPI + Python 3.11 + SQLAlchemy + LangChain
- **前端**：Vue 3 + Vite + Element Plus + Pinia
- **OCR**：PaddleOCR + Tesseract
- **PDF 处理**：PyMuPDF (fitz) + Unstructured
- **数据可视化**：Matplotlib

## 项目结构
```
QAChatAgent/
├── backend/            # 后端代码
│   ├── main.py         # 主 API 服务
│   ├── pdf_to_markdown.py  # PDF 处理核心
│   ├── uploads/        # 文件上传目录
│   └── environment.yml # 环境配置
├── frontend/           # 前端代码
│   ├── public/         # 静态资源
│   └── src/            # 源代码
│       ├── assets/     # 资源文件
│       ├── components/ # 组件
│       ├── router/     # 路由配置
│       ├── services/   # API 服务
│       ├── stores/     # 状态管理
│       └── views/      # 页面视图
├── start.ps1           # 一键启动脚本
└── README.md           # 项目文档
```

## 快速启动
```powershell
# 克隆项目
git clone https://github.com/SogreyOrg/QAChatAgent.git
cd QAChatAgent

# 启动服务 (需预先安装Python和Node.js)
./start.ps1
```

## 开发指南

### 环境准备
- Python 3.11+
- Node.js 16+
- Poppler (PDF 渲染引擎)
- Tesseract (OCR 引擎)

### 后端开发
```bash
cd backend
# 使用 Conda 环境（推荐）
conda env create -f environment.yml
conda activate multimodal-rag-pdf
# 或使用 pip
pip install -r requirements.txt

# 启动后端服务
python main.py
```

### 前端开发
```bash
cd frontend
npm install
npm run dev
```

## PDF 处理流程
1. **文件上传**：通过 FastAPI 接口上传 PDF 文件
2. **后台处理**：在后台线程中处理 PDF 文件
3. **内容提取**：使用 LangChain 和 Unstructured 提取 PDF 内容
4. **结构识别**：识别标题、表格、图像等结构化内容
5. **Markdown 转换**：将提取的内容转换为 Markdown 格式
6. **批注生成**：生成带有内容区域标注的 PDF 文件
7. **图像处理**：提取 PDF 中的图像并保存到指定目录

## 常见问题

### 1. PDF 处理失败？
- 确保 Poppler 和 Tesseract 正确安装并配置
- 检查 PDF 文件是否损坏或加密
- 对于大型 PDF，可能需要增加处理超时时间

### 2. 删除文件失败？
- 检查后端服务是否正常运行
- 确认文件权限设置正确
- 检查文件是否被其他程序占用

### 3. 前端无法连接后端？
- 确认后端服务已启动并监听正确端口
- 检查网络连接和防火墙设置
- 验证 API 路径配置是否正确

## 最近更新
- **PDF 原文/批注切换功能**：在预览界面添加原文和批注版本切换按钮
- **文件排序优化**：按上传时间倒序排列文件
- **UI 优化**：改进文件预览和知识库管理界面
- **性能优化**：提升 PDF 处理速度和稳定性