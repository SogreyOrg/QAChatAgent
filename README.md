# QAChatAgent 知识库问答系统

<div align="center">
  <a href="README_CN.md">🇨🇳 中文版</a> | 🇺🇸 English
</div>

基于多模态文档的智能问答系统，支持PDF/图片/Markdown/文本的解析与预览，包含完整的前后端实现。

## 🎯 当前版本功能 (v0.3.0)

✅ 知识库管理功能  
✅ 多格式文件上传与处理（PDF/图片/Markdown/文本）  
✅ 文件预览系统（支持多种格式实时预览）  
✅ 智能文件名显示（长文件名自动截断）  
✅ 按上传时间倒序排序  
✅ 响应式前端界面（Vue3 + Element Plus）  
✅ RESTful API服务（FastAPI）  
✅ 文件元数据管理（fileKey/savedName/path等）  
✅ 前后端状态实时同步  
✅ 完善的错误处理与日志  

## 🏗️ 项目结构

```
QAChatAgent/
├── backend/                  # 后端服务
│   ├── main.py               # FastAPI主应用
│   ├── pdf_to_markdown.py    # 文档处理核心
│   ├── uploads/              # 文件存储目录
│   ├── requirements.txt      # Python依赖
│   └── environment.yml       # Conda环境配置
├── frontend/                 # 前端项目
│   ├── src/                  # Vue3源代码
│   │   ├── components/       # 公共组件
│   │   │   ├── FilePreview.vue  # 文件预览组件
│   │   │   └── GlobalPreview.vue # 全局预览控制
│   │   ├── stores/           # Pinia状态管理
│   │   ├── views/knowledge/  # 知识库管理界面
│   │   └── App.vue           # 根组件
│   └── vite.config.js        # 前端构建配置
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

### v0.4.0 (2025-09-15)
- 新增多格式文件预览系统
- 实现智能文件名显示（截断长文件名）
- 统一按上传时间倒序排序
- 优化响应式布局

### v0.3.0 (2025-09-14)
- 文件元数据管理功能
- 前后端状态同步优化
- 完善错误处理机制

### v0.2.0 (2025-09-10)
- 基础文件上传功能
- 知识库管理界面搭建

## 📄 License

MIT License