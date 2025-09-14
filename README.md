# QAChatAgent 项目

<div align="center">
  <a href="README_CN.md">🇨🇳 中文版</a> | 🇺🇸 English
</div>

一个结合知识库管理和PDF处理的问答聊天代理系统，包含前后端完整实现。

## 🏗️ 项目结构

```
QAChatAgent/
├── backend/                  # 后端服务
│   ├── pdf_to_markdown.py    # PDF处理核心逻辑
│   ├── requirements.txt      # Python依赖
│   └── environment.yml       # Conda环境配置
├── frontend/                # 前端项目
│   ├── src/                 # Vue3源代码
│   └── ...                  # 前端配置和依赖
├── tmp/                     # 原始Python程序备份
└── README.md                # 项目说明
```

## 🚀 快速开始

### 后端开发

```bash
cd backend
# 使用conda创建环境
conda env create -f environment.yml
conda activate qachatagent

# 或使用pip安装依赖
pip install -r requirements.txt
```

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

## 📄 License

MIT License