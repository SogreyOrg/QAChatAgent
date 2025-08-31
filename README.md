# Multimodal RAG PDF Processing System

<div align="center">
  <a href="README_CN.md">🇨🇳 中文版</a> | 🇺🇸 English
</div>

A comprehensive PDF document parsing and element extraction system for multimodal RAG (Retrieval-Augmented Generation) applications. This project provides robust PDF processing capabilities with OCR support for both Chinese and English text.

## 🚀 Features

- **High-Quality PDF Processing**: Extract text, tables, and images from PDF documents
- **Multimodal Support**: Handle both text-based and image-heavy PDFs
- **OCR Integration**: Support for both Tesseract and PaddleOCR engines
- **Language Support**: Optimized for Chinese (Simplified) and English text recognition
- **Table Structure Detection**: Automatic table parsing and structure inference
- **LangChain Integration**: Compatible with LangChain document loaders for RAG workflows

## 📋 Prerequisites

- Python 3.10 or higher
- Windows, macOS, or Linux operating system
- Tesseract OCR (for text extraction)

## 🛠️ Installation

### Method 1: Using pip (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd 多模态PDF文档解析流程

# Install core dependencies
pip install -r requirements.txt

# For development (includes testing and formatting tools)
pip install -r requirements-dev.txt
```

### Method 2: Using conda

```bash
# Create conda environment
conda env create -f environment.yml

# Activate environment
conda activate multimodal-rag-pdf
```

### Method 3: Modern Python installation

```bash
# Install as a package
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

## 🔧 Tesseract OCR Setup

### Windows Installation

1. **Download Tesseract**:
   - Visit: https://github.com/UB-Mannheim/tesseract/wiki
   - Download the latest Windows installer (e.g., `tesseract-ocr-w64-setup-5.3.3.exe`)

2. **Install Tesseract**:
   - Run installer as administrator
   - Install to default location: `C:\Program Files\Tesseract-OCR\`

3. **Add to PATH**:
   ```powershell
   # Add Tesseract to PATH permanently
   $env:PATH += ";C:\Program Files\Tesseract-OCR"
   [Environment]::SetEnvironmentVariable("PATH", $env:PATH, [EnvironmentVariableTarget]::User)
   ```

4. **Verify Installation**:
   ```powershell
   tesseract --version
   ```

### Alternative Installation Methods

**Using Chocolatey**:
```powershell
choco install tesseract
```

**Using Conda**:
```bash
conda install -c conda-forge tesseract
```

For detailed Chinese installation guide, see: [`install_tesseract_windows.md`](install_tesseract_windows.md)

## 📖 Usage

### Basic PDF Processing

```python
from langchain_unstructured import UnstructuredLoader

# Initialize loader with fast strategy (recommended)
loader = UnstructuredLoader(
    file_path="your_document.pdf",
    strategy="fast",  # Avoids large model downloads
    infer_table_structure=True,
    languages=["chi_sim", "eng"],  # Chinese and English support
    ocr_engine="paddleocr"  # or "tesseract"
)

# Load and process documents
documents = []
for doc in loader.lazy_load():
    documents.append(doc)

# Access extracted content
for doc in documents:
    print(f"Content: {doc.page_content}")
    print(f"Metadata: {doc.metadata}")
```

### Advanced Configuration

```python
import os
from langchain_unstructured import UnstructuredLoader

# Configure for offline usage (avoids network dependencies)
os.environ["HF_HUB_OFFLINE"] = "1"

# Advanced loader configuration
loader = UnstructuredLoader(
    file_path="complex_document.pdf",
    strategy="fast",  # Recommended over "hi_res" for stability
    infer_table_structure=True,
    languages=["chi_sim", "eng"],
    ocr_engine="paddleocr",
    include_page_breaks=True,
    extract_images_in_pdf=True
)

# Process with error handling
try:
    documents = list(loader.lazy_load())
    print(f"Successfully processed {len(documents)} document chunks")
except Exception as e:
    print(f"Processing error: {e}")
    # Fallback to simpler strategy if needed
```

### Jupyter Notebook Usage

See the main notebook [`载入 PDF 并进行元素提取.ipynb`](载入%20PDF%20并进行元素提取.ipynb) for complete examples and interactive demonstrations.

## 🏗️ Project Structure

```
多模态PDF文档解析流程/
├── README.md                           # This file
├── requirements.txt                    # Core dependencies
├── requirements-dev.txt               # Development dependencies
├── environment.yml                    # Conda environment specification
├── pyproject.toml                     # Modern Python project configuration
├── setup.py                          # Fallback setup script
├── install_tesseract_windows.md      # Tesseract installation guide (Chinese)
├── 载入 PDF 并进行元素提取.ipynb        # Main demonstration notebook
├── 0.pdf                             # Sample PDF for testing
└── pdf_images/                       # Extracted images directory
```

## 🔍 Troubleshooting

### Common Issues

#### 1. TesseractNotFoundError
```
TesseractNotFoundError: tesseract is not installed or it's not in your PATH
```

**Solution**: Install Tesseract OCR following the installation guide above and ensure it's added to your system PATH.

#### 2. LocalEntryNotFoundError (Network Issues)
```
LocalEntryNotFoundError: Connection error, and we cannot find the requested files in the disk cache
```

**Solutions**:
- Use `strategy="fast"` instead of `strategy="hi_res"`
- Set offline mode: `os.environ["HF_HUB_OFFLINE"] = "1"`
- Check internet connection for first-time model downloads

#### 3. OCR Engine Issues

**For PaddleOCR problems**:
```python
# Fallback to Tesseract
loader = UnstructuredLoader(
    file_path="document.pdf",
    strategy="fast",
    ocr_engine="tesseract"  # Switch from paddleocr
)
```

**For Tesseract path issues**:
```python
import pytesseract
# Set explicit path (Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

#### 4. Memory Issues with Large PDFs

```python
# Process PDFs page by page for large files
loader = UnstructuredLoader(
    file_path="large_document.pdf",
    strategy="fast",
    chunking_strategy="by_page"
)
```

## 🧪 Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_pdf_processing.py
```

## 🎯 Performance Tips

1. **Use Fast Strategy**: Prefer `strategy="fast"` over `strategy="hi_res"` for better performance and fewer dependencies
2. **Batch Processing**: Process multiple PDFs in batches to optimize resource usage
3. **OCR Engine Selection**: 
   - Use PaddleOCR for better Chinese text recognition
   - Use Tesseract for faster processing of English-heavy documents
4. **Memory Management**: For large PDFs, consider processing page by page

## 📚 Dependencies

### Core Dependencies
- `langchain-core>=0.1.0` - Core LangChain functionality
- `langchain-community>=0.0.1` - Community extensions
- `langchain-unstructured>=0.1.0` - Unstructured document loading
- `unstructured>=0.10.0` - PDF processing engine
- `pypdf>=3.0.0` - PDF manipulation
- `pytesseract>=0.3.10` - Tesseract OCR Python interface
- `paddlepaddle>=2.5.0` & `paddleocr>=2.7.0` - PaddleOCR support
- `pillow>=9.0.0` - Image processing
- `opencv-python>=4.8.0` - Computer vision operations

### Development Dependencies
- `jupyter>=1.0.0` - Notebook environment
- `pytest>=7.0.0` - Testing framework
- `black>=23.0.0` - Code formatting
- `isort>=5.12.0` - Import sorting
- `flake8>=6.0.0` - Code linting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run code formatting: `black . && isort .`
5. Run tests: `pytest`
6. Commit your changes: `git commit -am 'Add feature'`
7. Push to the branch: `git push origin feature-name`
8. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review the [Tesseract installation guide](install_tesseract_windows.md)
3. Examine the example notebook for working code patterns
4. Open an issue with detailed error messages and system information

## 🎖️ Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) for document processing framework
- [Unstructured](https://github.com/Unstructured-IO/unstructured) for PDF parsing capabilities
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for text recognition
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) for Chinese text recognition