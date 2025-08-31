# 在Windows上安装Tesseract OCR

## 方法1：使用官方安装程序（推荐）

1. **下载Tesseract**：
   - 访问：https://github.com/UB-Mannheim/tesseract/wiki
   - 下载最新的Windows安装程序（例如：`tesseract-ocr-w64-setup-5.3.3.exe`）

2. **安装Tesseract**：
   - 以管理员身份运行安装程序
   - 安装到默认位置：`C:\Program Files\Tesseract-OCR\`
   - 确保包含语言包（英语是默认的）

3. **添加到PATH环境变量**：
   ```powershell
   # 永久添加Tesseract到PATH
   $env:PATH += ";C:\Program Files\Tesseract-OCR"
   [Environment]::SetEnvironmentVariable("PATH", $env:PATH, [EnvironmentVariableTarget]::User)
   ```

4. **验证安装**：
   ```powershell
   tesseract --version
   ```

## 方法2：使用Chocolatey

```powershell
# 如果没有安装Chocolatey，先安装
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 安装Tesseract
choco install tesseract
```

## 方法3：使用Conda

```powershell
conda install -c conda-forge tesseract
```

## Python配置

安装Tesseract后，配置Python路径：

```python
import pytesseract

# 设置Tesseract路径（如果安装在其他位置请调整）
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```