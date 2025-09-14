# QAChatAgent 项目

<div align="center">
  <a href="README_CN.md">🇨🇳 中文版</a> | 🇺🇸 English
</div>

一个结合知识库管理和PDF处理的问答聊天代理系统，包含前后端完整实现。

## 🎯 当前版本功能 (v0.3.0)

✅ 知识库管理功能  
✅ PDF文件上传与处理  
✅ 前端Vue3 + Element Plus界面  
✅ FastAPI后端服务  
✅ 文件上传进度显示  
✅ 文件元数据管理 (fileKey, savedName等)  
✅ 文件删除功能  
✅ 前后端文件状态同步  

## 🏗️ 项目结构

```
QAChatAgent/
├── backend/                  # 后端服务
│   ├── main.py               # FastAPI主应用
│   ├── pdf_to_markdown.py    # PDF处理核心逻辑
│   ├── requirements.txt      # Python依赖
│   └── environment.yml       # Conda环境配置
├── frontend/                 # 前端项目
│   ├── src/                  # Vue3源代码
│   │   ├── stores/           # Pinia状态管理
│   │   └── views/knowledge/  # 知识库管理界面
│   └── ...                   # 前端配置和依赖
├── tmp/                      # 原始Python程序备份
└── README.md                 # 项目说明
```

## 🚀 快速开始

### 后端开发

```bash
cd backend
# 使用conda创建环境
conda env create -f environment.yml
conda activate qachatagent

# 启动后端服务
uvicorn main:app --reload
```

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

## 🌐 部署说明

1. 确保已安装Python 3.8+和Node.js 16+
2. 后端默认运行在: http://localhost:8000
3. 前端默认运行在: http://localhost:5173
4. 文件上传API端点: /api/upload
5. 文件删除API端点: /api/delete/{filename}
6. 文件元数据结构:
   ```json
   {
     "fileKey": "唯一文件标识",
     "savedName": "存储文件名",
     "path": "文件访问路径",
     "downloadUrl": "文件下载URL"
   }
   ```

## 📌 版本更新

### v0.3.0 (2025-09-14)
- 新增文件元数据管理功能
- 实现前后端文件状态同步
- 完善文件删除流程
- 修复文件上传后元数据丢失问题

### v0.2.0 (2025-09-10)
- 初始版本发布
- 实现基础文件上传功能
- 搭建知识库管理界面

## 📄 License

MIT License