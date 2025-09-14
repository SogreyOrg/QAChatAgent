# Multimodal RAG PDF Processing System

<div align="center">
  <a href="README_CN.md">🇨🇳 中文版</a> | 🇺🇸 English
</div>

A comprehensive PDF document parsing and element extraction system for multimodal RAG (Retrieval-Augmented Generation) applications. This project provides powerful PDF processing capabilities with support for Chinese and English OCR recognition.

## 🚀 Features

- **High-quality PDF Processing**: Extract text, tables, and images from PDF documents
- **Multimodal Support**: Handle both text-based and image-intensive PDFs
- **OCR Integration**: Support for Tesseract and PaddleOCR engines
- **Language Support**: Optimized for Chinese (Simplified) and English text recognition
- **Table Structure Detection**: Automatic table parsing and structure inference
- **LangChain Integration**: Compatible with LangChain document loaders for RAG workflows

## 📋 System Requirements

- Python 3.10 or higher
- Windows, macOS, or Linux OS
- Tesseract OCR (for text extraction)

## 🛠️ Installation

### Method 1: Using pip (Recommended)

```bash
# Clone repository
git clone https://github.com/Sogrey/RAG-PDF2markdown.git
cd RAG-PDF2markdown

# Install core dependencies
pip install -r requirements.txt
```

### Method 2: Using conda

```bash
# Create conda environment
conda env create -f environment.yml

# Activate environment
conda activate multimodal-rag-pdf
```

### Method 3: Modern Python Installation

```bash
# Install as package
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

### Method 4: Using Python 3.11.9 with venv (Tested)

```powershell
# Create virtual environment with Python 3.11.9
python -m venv venv-py311

# Activate environment
.\venv-py311\Scripts\activate  # Windows
# source venv-py311/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

## 🔧 Tesseract OCR Configuration

### Windows Installation

1. **Download Tesseract**:
   - Visit: https://github.com/UB-Mannheim/tesseract/wiki
   - Download latest Windows installer (e.g. `tesseract-ocr-w64-setup-5.3.3.exe`)

2. **Install Tesseract**:
   - Run installer as administrator
   - Install to default location: `C:\Program Files\Tesseract-OCR\`

3. **Add to PATH**:
   ```powershell
   # Permanently add Tesseract to PATH
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

For detailed Chinese installation guide see: [`install_tesseract_windows.md`](install_tesseract_windows.md)

## 📖 Usage

### Basic PDF Processing

```python
from langchain_unstructured import UnstructuredLoader

# Initialize loader with fast strategy (recommended)
loader = UnstructuredLoader(
    file_path="your_document.pdf",
    strategy="fast",  # Avoid large model downloads
    infer_table_structure=True,
    languages=["chi_sim", "eng"],  # Chinese/English support
    ocr_engine="paddleocr"  # or "tesseract"
)

# Load and process document
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

# Configure for offline use (avoid network dependencies)
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

See main notebook [`Load PDF and Extract Elements.ipynb`](载入%20PDF%20并进行元素提取.ipynb) for complete examples and interactive demos.

## 🏗️ Project Structure

```
Multimodal-PDF-Document-Parser/
├── README.md                           # English documentation
├── README_CN.md                        # Chinese documentation (this file)
├── requirements.txt                    # Core dependencies
├── requirements-dev.txt               # Development dependencies
├── environment.yml                    # Conda environment spec
├── pyproject.toml                     # Modern Python project config
├── setup.py                          # Backup installation script
├── install_tesseract_windows.md      # Tesseract installation guide (Chinese)
├── Load PDF and Extract Elements.ipynb # Main demo notebook
├── 0.pdf                             # Sample test PDF
└── pdf_images/                       # Extracted images directory
```

## 🔍 Troubleshooting

### Common Issues

#### 1. TesseractNotFoundError
```
TesseractNotFoundError: tesseract is not installed or it's not in your PATH
```

**Solution**: Follow installation guide above to install Tesseract OCR and ensure it's in system PATH.

#### 2. LocalEntryNotFoundError (Network Issues)
```
LocalEntryNotFoundError: Connection error, and we cannot find the requested files in the disk cache
```

**Solution**:
- Use `strategy="fast"` instead of `strategy="hi_res"`
- Set offline mode: `os.environ["HF_HUB_OFFLINE"] = "1"`
- Check network connection for initial model downloads

#### 3. OCR Engine Issues

**PaddleOCR Issues**:
```python
# Fallback to Tesseract
loader = UnstructuredLoader(
    file_path="document.pdf",
    strategy="fast",
    ocr_engine="tesseract"  # Switch from paddleocr
)
```

**Tesseract Path Issues**:
```python
import pytesseract
# Set explicit path (Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

#### 4. Memory Issues with Large PDFs

```python
# Process large PDFs page by page
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

# Run coverage tests
pytest --cov=src

# Run specific test file
pytest tests/test_pdf_processing.py
```

## 🎯 Performance Optimization Tips

1. **Use Fast Strategy**: Prefer `strategy="fast"` over `strategy="hi_res"` for better performance and fewer dependencies
2. **Batch Processing**: Process multiple PDFs in batches to optimize resource usage
3. **OCR Engine Selection**:
   - Use PaddleOCR for better Chinese text recognition
   - Use Tesseract for faster processing of English-dominant documents
4. **Memory Management**: For large PDFs, consider processing page by page

## 📚 Dependencies

### Core Dependencies
- `langchain-core>=0.1.0` - Core LangChain functionality
- `langchain-community>=0.0.1` - Community extensions
- `langchain-unstructured>=0.1.0` - Unstructured document loading
- `unstructured>=0.10.0` - PDF processing engine
- `pypdf>=3.0.0` - PDF operations
- `pytesseract>=0.3.10` - Tesseract OCR Python interface
- `paddlepaddle>=2.5.0` and `paddleocr>=2.7.0` - PaddleOCR support
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
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Format code: `black . && isort .`
5. Run tests: `pytest`
6. Commit changes: `git commit -am 'Add feature'`
7. Push to branch: `git push origin feature-name`
8. Submit Pull Request

## 📄 License

This project is licensed under MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Refer to [Tesseract Installation Guide](install_tesseract_windows.md)
3. Examine working code patterns in the example notebook
4. Submit an issue with detailed error information and system details

## 🎖️ Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) for document processing framework
- [Unstructured](https://github.com/Unstructured-IO/unstructured) for PDF parsing capabilities
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for text recognition
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) for Chinese text recognition