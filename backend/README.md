# QAChatAgent 后端服务

## 项目简介

QAChatAgent 后端服务是一个基于 FastAPI 的 API 服务，提供 PDF 处理和知识库管理功能。核心功能包括 PDF 文档解析、转换为 Markdown 格式，以及文件上传和管理服务。

## 主要功能

1. **PDF 处理**：
   - PDF 文档解析与结构化提取
   - 支持中英文 OCR 识别
   - 表格结构自动识别
   - 图片提取与保存
   - PDF 转 Markdown 格式转换

2. **文件管理**：
   - 文件上传 API
   - 文件删除 API
   - 静态文件服务

## 技术栈

- **Web 框架**：FastAPI
- **服务器**：Uvicorn
- **PDF 处理**：
  - PyMuPDF (fitz)
  - Unstructured
  - LangChain Unstructured
- **OCR 引擎**：
  - PaddleOCR (主要)
  - Tesseract (备选)
- **图像处理**：
  - PIL (Pillow)
  - OpenCV
  - Matplotlib

## 系统要求

### 必要组件

- Python 3.11+
- Poppler (PDF 渲染引擎)
- Tesseract (OCR 引擎)

### 依赖安装

1. **使用 Conda 环境**（推荐）：

```bash
conda env create -f environment.yml
conda activate multimodal-rag-pdf
```

2. **使用 pip**：

```bash
pip install -r requirements.txt
```

## 环境配置

### Poppler 配置

PDF 处理依赖 Poppler，可通过以下方式配置：

1. **环境变量设置**：
   设置 `POPPLER_PATH` 环境变量指向 Poppler 的 bin 目录

2. **默认路径**：
   程序会自动检测以下常见安装路径：
   - `C:\Program Files\poppler\Library\bin`
   - `C:\Program Files (x86)\poppler\Library\bin`
   - `E:\Programs\poppler-25.07.0\Library\bin`

## API 接口

### 文件排序说明
- 所有文件列表按上传时间倒序排列
- 最新上传的文件显示在最上方

### 基础接口

- **GET /** - 服务状态检查
  - 返回：`{"message": "QAChatAgent API服务运行中"}`

### 文件管理接口

- **POST /api/upload** - 上传文件
  - 请求：`multipart/form-data` 格式文件
  - 返回：文件信息，包含唯一标识和访问路径

- **DELETE /api/delete/{filename}** - 删除文件
  - 参数：`filename` - 文件名
  - 返回：删除状态信息

- **GET /api/uploads/{filename}** - 访问上传的文件
  - 参数：`filename` - 文件名
  - 返回：请求的文件

## PDF 处理功能

`pdf_to_markdown.py` 提供了两种 PDF 处理方法：

1. **使用 LangChain Unstructured 加载**：
   - 高分辨率模式，支持复杂文档
   - 自动解析表格结构
   - 支持中英文 OCR

2. **使用 Unstructured 直接处理**：
   - 提取文本和结构化内容
   - 表格结构检测
   - 中英文混合识别

处理后会生成：
- Markdown 格式的文本文件
- 提取的图片文件

## 启动服务

1. **切换到后端目录**：
```bash
cd backend
```

2. **激活虚拟环境**：
```bash
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Windows (CMD)
.\.venv\Scripts\activate.bat

# Linux/MacOS
source .venv/bin/activate

# 验证虚拟环境是否激活成功
# 激活后，命令行提示符前应显示虚拟环境名称，如：
# (.venv) PS D:\github\赋范AI\QAChatAgent\backend>
```

3. **安装依赖**：
```bash
# 确保在虚拟环境中安装所有依赖
pip install -r requirements.txt

# 如果遇到权限问题，可以尝试：
pip install --user -r requirements.txt
```

4. **检查安装的包**：
```bash
pip list
# 应能看到 requirements.txt 中列出的所有包
```

3. **启动服务**：
```bash
# 使用启动脚本
./start.sh

# 或直接使用 uvicorn
PYTHONPATH=. uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. **调试提示**：
- 确保在虚拟环境中安装了所有依赖：`pip install -r requirements.txt`
- 如果遇到导入错误，检查虚拟环境是否正确激活
- 确保工作目录是`backend/`目录

## 目录结构

```
backend/
├── .venv/                # Python 虚拟环境
├── environment.yml       # Conda 环境配置
├── main.py               # FastAPI 主程序
├── pdf_to_markdown.py    # PDF 处理核心功能
├── requirements.txt      # pip 依赖列表
├── start.sh              # 启动脚本
├── uploads/              # 文件上传目录
└── __pycache__/          # Python 缓存文件
```

## 注意事项

1. 确保 Poppler 和 Tesseract 正确安装并配置
2. 处理大型 PDF 文件可能需要较高的系统资源
3. OCR 识别质量取决于原始 PDF 的清晰度和格式