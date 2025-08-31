# 多模态RAG PDF处理系统

<div align="center">
  🇨🇳 中文版 | <a href="README.md">🇺🇸 English</a>
</div>

一个用于多模态RAG（检索增强生成）应用的综合PDF文档解析和元素提取系统。该项目提供强大的PDF处理功能，支持中英文OCR识别。

## 🚀 功能特性

- **高质量PDF处理**：从PDF文档中提取文本、表格和图像
- **多模态支持**：处理基于文本和图像密集型的PDF文档
- **OCR集成**：支持Tesseract和PaddleOCR引擎
- **语言支持**：针对中文（简体）和英文文本识别进行优化
- **表格结构检测**：自动表格解析和结构推断
- **LangChain集成**：与LangChain文档加载器兼容，用于RAG工作流

## 📋 系统要求

- Python 3.10 或更高版本
- Windows、macOS 或 Linux 操作系统
- Tesseract OCR（用于文本提取）

## 🛠️ 安装说明

### 方法一：使用pip（推荐）

```bash
# 克隆仓库
git clone <repository-url>
cd 多模态PDF文档解析流程

# 安装核心依赖
pip install -r requirements.txt

# 开发环境（包括测试和格式化工具）
pip install -r requirements-dev.txt
```

### 方法二：使用conda

```bash
# 创建conda环境
conda env create -f environment.yml

# 激活环境
conda activate multimodal-rag-pdf
```

### 方法三：现代Python安装方式

```bash
# 作为包安装
pip install -e .

# 或包含开发依赖
pip install -e ".[dev]"
```

## 🔧 Tesseract OCR配置

### Windows安装

1. **下载Tesseract**：
   - 访问：https://github.com/UB-Mannheim/tesseract/wiki
   - 下载最新的Windows安装程序（例如：`tesseract-ocr-w64-setup-5.3.3.exe`）

2. **安装Tesseract**：
   - 以管理员身份运行安装程序
   - 安装到默认位置：`C:\Program Files\Tesseract-OCR\`

3. **添加到PATH**：
   ```powershell
   # 永久添加Tesseract到PATH
   $env:PATH += ";C:\Program Files\Tesseract-OCR"
   [Environment]::SetEnvironmentVariable("PATH", $env:PATH, [EnvironmentVariableTarget]::User)
   ```

4. **验证安装**：
   ```powershell
   tesseract --version
   ```

### 其他安装方法

**使用Chocolatey**：
```powershell
choco install tesseract
```

**使用Conda**：
```bash
conda install -c conda-forge tesseract
```

详细的中文安装指南请参见：[`install_tesseract_windows.md`](install_tesseract_windows.md)

## 📖 使用方法

### 基础PDF处理

```python
from langchain_unstructured import UnstructuredLoader

# 使用快速策略初始化加载器（推荐）
loader = UnstructuredLoader(
    file_path="your_document.pdf",
    strategy="fast",  # 避免大模型下载
    infer_table_structure=True,
    languages=["chi_sim", "eng"],  # 中英文支持
    ocr_engine="paddleocr"  # 或 "tesseract"
)

# 加载和处理文档
documents = []
for doc in loader.lazy_load():
    documents.append(doc)

# 访问提取的内容
for doc in documents:
    print(f"内容: {doc.page_content}")
    print(f"元数据: {doc.metadata}")
```

### 高级配置

```python
import os
from langchain_unstructured import UnstructuredLoader

# 配置离线使用（避免网络依赖）
os.environ["HF_HUB_OFFLINE"] = "1"

# 高级加载器配置
loader = UnstructuredLoader(
    file_path="complex_document.pdf",
    strategy="fast",  # 推荐使用而非"hi_res"以提高稳定性
    infer_table_structure=True,
    languages=["chi_sim", "eng"],
    ocr_engine="paddleocr",
    include_page_breaks=True,
    extract_images_in_pdf=True
)

# 带错误处理的处理
try:
    documents = list(loader.lazy_load())
    print(f"成功处理了 {len(documents)} 个文档块")
except Exception as e:
    print(f"处理错误: {e}")
    # 如需要可回退到更简单的策略
```

### Jupyter Notebook使用

参见主要notebook [`载入 PDF 并进行元素提取.ipynb`](载入%20PDF%20并进行元素提取.ipynb) 获取完整示例和交互式演示。

## 🏗️ 项目结构

```
多模态PDF文档解析流程/
├── README.md                           # 英文说明文档
├── README_CN.md                        # 中文说明文档（本文件）
├── requirements.txt                    # 核心依赖
├── requirements-dev.txt               # 开发依赖
├── environment.yml                    # Conda环境规范
├── pyproject.toml                     # 现代Python项目配置
├── setup.py                          # 备用安装脚本
├── install_tesseract_windows.md      # Tesseract安装指南（中文）
├── 载入 PDF 并进行元素提取.ipynb        # 主演示notebook
├── 0.pdf                             # 测试用样本PDF
└── pdf_images/                       # 提取的图像目录
```

## 🔍 故障排除

### 常见问题

#### 1. TesseractNotFoundError（Tesseract未找到错误）
```
TesseractNotFoundError: tesseract is not installed or it's not in your PATH
```

**解决方案**：按照上述安装指南安装Tesseract OCR，并确保将其添加到系统PATH中。

#### 2. LocalEntryNotFoundError（网络问题）
```
LocalEntryNotFoundError: Connection error, and we cannot find the requested files in the disk cache
```

**解决方案**：
- 使用 `strategy="fast"` 而非 `strategy="hi_res"`
- 设置离线模式：`os.environ["HF_HUB_OFFLINE"] = "1"`
- 检查首次模型下载的网络连接

#### 3. OCR引擎问题

**PaddleOCR问题**：
```python
# 回退到Tesseract
loader = UnstructuredLoader(
    file_path="document.pdf",
    strategy="fast",
    ocr_engine="tesseract"  # 从paddleocr切换
)
```

**Tesseract路径问题**：
```python
import pytesseract
# 设置明确路径（Windows）
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

#### 4. 大PDF文件内存问题

```python
# 对大文件逐页处理PDF
loader = UnstructuredLoader(
    file_path="large_document.pdf",
    strategy="fast",
    chunking_strategy="by_page"
)
```

## 🧪 测试

```bash
# 运行测试
pytest

# 运行覆盖率测试
pytest --cov=src

# 运行特定测试文件
pytest tests/test_pdf_processing.py
```

## 🎯 性能优化建议

1. **使用快速策略**：优先使用 `strategy="fast"` 而非 `strategy="hi_res"` 以获得更好的性能和更少的依赖
2. **批处理**：批量处理多个PDF以优化资源使用
3. **OCR引擎选择**：
   - 使用PaddleOCR获得更好的中文文本识别效果
   - 使用Tesseract更快地处理英文为主的文档
4. **内存管理**：对于大PDF，考虑逐页处理

## 📚 依赖关系

### 核心依赖
- `langchain-core>=0.1.0` - 核心LangChain功能
- `langchain-community>=0.0.1` - 社区扩展
- `langchain-unstructured>=0.1.0` - 非结构化文档加载
- `unstructured>=0.10.0` - PDF处理引擎
- `pypdf>=3.0.0` - PDF操作
- `pytesseract>=0.3.10` - Tesseract OCR Python接口
- `paddlepaddle>=2.5.0` 和 `paddleocr>=2.7.0` - PaddleOCR支持
- `pillow>=9.0.0` - 图像处理
- `opencv-python>=4.8.0` - 计算机视觉操作

### 开发依赖
- `jupyter>=1.0.0` - Notebook环境
- `pytest>=7.0.0` - 测试框架
- `black>=23.0.0` - 代码格式化
- `isort>=5.12.0` - 导入排序
- `flake8>=6.0.0` - 代码检查

## 🤝 贡献指南

1. Fork仓库
2. 创建功能分支：`git checkout -b feature-name`
3. 进行更改并添加测试
4. 运行代码格式化：`black . && isort .`
5. 运行测试：`pytest`
6. 提交更改：`git commit -am 'Add feature'`
7. 推送到分支：`git push origin feature-name`
8. 提交Pull Request

## 📄 许可证

本项目使用MIT许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🆘 技术支持

如果遇到问题：

1. 查看[故障排除](#故障排除)部分
2. 查阅[Tesseract安装指南](install_tesseract_windows.md)
3. 检查示例notebook中的工作代码模式
4. 使用详细的错误信息和系统信息提交issue

## 🎖️ 致谢

- [LangChain](https://github.com/langchain-ai/langchain) 提供文档处理框架
- [Unstructured](https://github.com/Unstructured-IO/unstructured) 提供PDF解析功能
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) 提供文本识别
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) 提供中文文本识别