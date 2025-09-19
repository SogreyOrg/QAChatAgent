# QAChatAgent 前端

## 项目概述

QAChatAgent 前端是一个基于 Vue 3 的 Web 应用，提供用户界面与后端 API 交互，实现智能问答功能。最新版本增强了多会话管理和用户界面体验。

## 功能特性

- 多会话管理与切换
- 会话状态持久化存储
- 消息历史记录与自动滚动
- 文件上传与处理状态显示
- 流式对话响应
- 响应式设计
- 科技感UI界面
- 会话列表管理

## 技术栈

- Vue 3 (Composition API)
- Pinia (状态管理)
- Element Plus (UI 组件库)
- Axios (HTTP 客户端)
- Vue Router

## 项目结构

```
frontend/
├── public/            # 静态资源
├── src/
│   ├── assets/        # 静态资源
│   ├── components/    # 公共组件
│   ├── router/        # 路由配置
│   ├── services/      # API 服务
│   ├── stores/        # Pinia 状态管理
│   ├── views/         # 页面组件
│   ├── App.vue        # 根组件
│   └── main.js        # 应用入口
├── package.json       # 项目配置
└── README.md          # 前端文档
```

## 开发指南

1. 安装依赖：
```bash
npm install
```

2. 启动开发服务器：
```bash
npm run dev
```

3. 构建生产版本：
```bash
npm run build
```

## 环境变量

创建 `.env` 文件：
```
VITE_API_BASE_URL=http://localhost:8000
```

## 主要组件

- `ChatView.vue` - 主聊天界面，整合会话列表和消息显示
- `MainLayout.vue` - 应用主布局组件
- `FilePreview.vue` - 文件预览组件
- `KnowledgeManagement.vue` - 知识库管理组件
- `GlobalPreview.vue` - 全局预览组件

## 最近更新

- 优化会话切换逻辑
- 添加会话状态持久化
- 实现自动滚动到最新消息
- 增强用户界面交互体验
- 添加科技感UI设计元素