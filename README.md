# RAG-PDF2markdown

多模态RAG系统，用于PDF文档解析和元素提取，支持转换为结构化Markdown格式。

## 功能特性

- 📄 PDF文档解析与元素提取
- 🖼️ 图片自动提取与嵌入
- 🏷️ 结构化元素识别（标题、表格、列表等）
- 🔍 OCR支持（中英文混合识别）
- 📝 转换为标准Markdown格式

## 系统要求

### 必备组件
- Python 3.10+
- Poppler (Windows: 下载并添加到PATH)
- Tesseract OCR (用于文本识别)

### 推荐配置
- NVIDIA GPU (加速OCR处理)
- 至少8GB内存

## 安装指南

### Conda环境 (推荐)
```bash
conda env create -f environment.yml
conda activate multimodal-rag-pdf
```

### Pip安装
```bash
pip install -r requirements.txt
```

## 使用方法

### Jupyter Notebook
1. 打开 `载入_PDF_并进行元素提取_修复版.ipynb`
2. 按顺序执行单元格

### 命令行运行
```bash
python pdf_to_markdown.py
```

### 配置选项
- 修改 `pdf_to_markdown.py` 中的 `pdf_path` 变量指定输入PDF
- 输出目录默认为 `pdf_images/` 和 `output.md`

## 依赖管理

项目提供三种依赖配置方式：
1. `environment.yml` - Conda环境配置
2. `requirements.txt` - Pip依赖列表
3. `pyproject.toml` - 项目元数据

## 常见问题

### Q: 遇到poppler路径错误？
A: 确保已安装poppler并正确配置PATH环境变量：
```python
# 在代码中指定路径
poppler_path = r"E:\Programs\poppler-25.07.0\Library\bin"
os.environ["PATH"] = poppler_path + os.pathsep + os.environ["PATH"]
```

### Q: 如何提高OCR识别精度？
A: 
1. 使用更高分辨率的PDF
2. 确保安装最新版Tesseract
3. 指定语言参数：`languages=["chi_sim","eng"]`

## 项目结构
```
RAG-PDF2markdown/
├── pdf_to_markdown.py       # 主处理脚本
├── 载入_PDF_并进行元素提取_修复版.ipynb  # Jupyter Notebook
├── environment.yml         # Conda环境配置
├── requirements.txt        # Pip依赖
├── pyproject.toml          # 项目配置
└── pdf_images/             # 图片输出目录
```

## 许可证
MIT License - 详见 [LICENSE](LICENSE) 文件