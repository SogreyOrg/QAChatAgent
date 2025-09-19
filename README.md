# QAChatAgent - 智能问答聊天代理

## 项目概述

QAChatAgent 是一个基于 AI 的智能问答系统，提供 PDF 文档处理和基于知识库的智能对话功能。系统分为前端和后端两部分，支持多会话管理和上下文感知的智能问答。最新版本增强了多会话管理功能和知识库检索能力。

## 主要功能

### 后端功能
- PDF 文档解析与结构化提取
- 多语言 OCR 识别
- 表格结构自动识别
- 图片提取与保存
- 基于知识库的智能问答
- 多会话管理
- 上下文感知检索
- 智能问题重构
- 历史对话感知

### 前端功能
- 响应式聊天界面
- 多会话切换与管理
- 消息历史记录
- 文件上传与处理状态显示
- 流式对话响应
- 自动滚动到最新消息
- 科技感UI设计
- 会话状态持久化

## 技术栈

### 后端
- Python 3.11+
- FastAPI
- SQLAlchemy
- PyMuPDF
- PaddleOCR
- ChatZhipuAI (GLM-4)

### 前端
- Vue 3
- Pinia
- Element Plus
- Axios

## 快速开始

1. 克隆仓库：
```bash
git clone https://github.com/赋范AI/QAChatAgent.git
cd QAChatAgent
```

2. 启动后端服务：
```bash
cd backend
pip install -r requirements.txt
python main.py
```

3. 启动前端开发服务器：
```bash
cd frontend
npm install
npm run dev
```

## 项目结构

```
QAChatAgent/
├── backend/          # 后端服务
├── frontend/         # 前端应用
├── docs/             # 项目文档
├── CHANGELOG.md      # 版本变更记录
└── README.md         # 项目主文档
```

## 贡献指南

欢迎提交 Pull Request。对于重大变更，请先开 Issue 讨论。

## 许可证

MIT License