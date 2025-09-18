# QAChatAgent 后端服务

## 项目简介

QAChatAgent 后端服务是一个基于 FastAPI 的 API 服务，提供 PDF 处理、知识库管理和智能对话功能。核心功能包括 PDF 文档解析、转换为 Markdown 格式，以及基于知识库的智能问答服务。

## 目录结构

```
backend/
├── .env                 # 环境变量配置
├── .venv/               # Python 虚拟环境
├── chat.db              # SQLite 数据库
├── environment.yml      # Conda 环境配置
├── main.py              # FastAPI 主程序
├── main.bck.py          # 主程序备份
├── pdf_to_markdown.py   # PDF 处理核心功能
├── requirements.txt     # pip 依赖列表
├── start.sh             # 启动脚本
├── uploads/             # 文件上传目录
└── README.md            # 后端文档
```

## 主要功能

### 1. PDF 处理
- **PDF 文档解析与结构化提取**：识别文本、标题、表格和图像
- **多语言 OCR 识别**：支持中英文混合识别
- **表格结构自动识别**：保留表格的结构化信息
- **图片提取与保存**：自动提取 PDF 中的图像并保存
- **PDF 转 Markdown**：将结构化内容转换为 Markdown 格式
- **批注版 PDF 生成**：生成带有内容区域标注的 PDF 文件

### 2. 文件管理
- **文件上传 API**：支持多种文件格式上传
- **文件删除 API**：安全删除文件
- **静态文件服务**：提供上传文件的访问服务
- **后台任务处理**：异步处理大型 PDF 文件

### 3. 智能对话
- **基于知识库的问答**：利用知识库内容进行智能问答
- **会话管理**：支持创建、存储和管理多个对话会话
- **流式响应**：使用 SSE 技术实现流式对话响应
- **上下文记忆**：保持对话上下文，提供连贯的交互体验
- **历史对话感知**：系统能够理解并参考历史对话内容，生成更连贯的回答
- **上下文感知检索**：基于历史对话优化知识库检索，提高回答相关性
- **智能问题重构**：根据对话历史自动重构用户问题，提高检索精度

## 技术栈

### 核心框架
- **Web 框架**：FastAPI
- **ASGI 服务器**：Uvicorn
- **数据库 ORM**：SQLAlchemy
- **环境变量管理**：python-dotenv

### PDF 处理
- **PDF 解析**：PyMuPDF (fitz)
- **文档结构化**：Unstructured
- **AI 框架**：LangChain
- **OCR 引擎**：
  - PaddleOCR (主要)
  - Tesseract (备选)

### 图像处理
- **图像库**：PIL (Pillow)
- **数据可视化**：Matplotlib
- **图像分析**：OpenCV (可选)

### AI 模型
- **大语言模型**：ChatZhipuAI (智谱 GLM-4)
- **提示工程**：LangChain 提示模板

## 系统要求

### 必要组件
- Python 3.11+
- Poppler (PDF 渲染引擎)
- Tesseract (OCR 引擎)
- SQLite (默认数据库，可配置其他)

### 依赖安装

1. **使用 Conda 环境**（推荐）：

```bash
conda env create -f environment.yml
conda activate multimodal-rag-pdf
```

2. **使用 pip**：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 环境配置

### 环境变量
创建 `.env` 文件，配置以下环境变量：
```
DATABASE_URL=sqlite:///./chat.db
ZHIPUAI_API_KEY=your_zhipuai_api_key
POPPLER_PATH=/path/to/poppler/bin
```

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

### 文件管理接口

- **POST /api/upload** - 上传文件
  - 请求：`multipart/form-data` 格式文件
  - 返回：文件信息，包含唯一标识和访问路径
  - 特性：PDF 文件会自动在后台进行处理

- **DELETE /api/delete/{filename}** - 删除文件
  - 参数：`filename` - 文件名
  - 返回：删除状态信息

- **GET /api/task/status/{task_id}** - 查询任务状态
  - 参数：`task_id` - 任务 ID
  - 返回：任务运行状态信息

### 聊天接口

- **GET /api/chat/stream** - 流式聊天响应
  - 参数：
    - `session_id` - 会话 ID
    - `message` - 用户消息
    - `collection_name` - 知识库名称（默认为"default"）
  - 返回：SSE 格式的流式响应
  - 特性：
    - 支持历史对话上下文感知
    - 基于历史对话优化知识库检索
    - 自动重构用户问题以提高检索精度
    - 实时流式返回AI回答

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
- Markdown 格式的文本文件 (`[文件名].md`)
- 带批注的 PDF 文件 (`[文件名]_annotated.pdf`)
- 提取的图片文件 (保存在 `[文件名]/` 目录)

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
```

3. **启动服务**：
```bash
# 使用启动脚本
./start.sh

# 或直接使用 uvicorn
python main.py

# 或指定主机和端口
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 性能优化

1. **PDF 处理优化**：
   - 大型 PDF 文件使用后台线程处理
   - 使用高分辨率模式提高 OCR 识别质量
   - 禁用第三方库的冗余日志，减少输出噪音

2. **数据库优化**：
   - 使用 SQLAlchemy ORM 进行数据库操作
   - 会话和消息分表存储，提高查询效率
   - 使用事务确保数据一致性

3. **API 响应优化**：
   - 使用 SSE 技术实现流式响应
   - 控制流式速度，提供平滑的用户体验
   - 异步处理大型请求，避免阻塞

## 注意事项

1. 确保 Poppler 和 Tesseract 正确安装并配置
2. 处理大型 PDF 文件可能需要较高的系统资源
3. OCR 识别质量取决于原始 PDF 的清晰度和格式
4. 对于复杂表格和特殊格式，可能需要手动调整生成的 Markdown