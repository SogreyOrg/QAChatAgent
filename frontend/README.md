# QAChatAgent 前端项目

这是一个基于Vue 3 + Vite构建的知识库问答聊天代理前端项目。该项目使用了现代前端技术栈，包括Vue 3、Vite、Pinia、Vue Router和Element Plus。

## 最近修复

### 2025/9/15 修复内容

1. **Element Plus组件解析错误修复**
   - 问题：全局预览组件中的Element Plus组件（如el-button）无法被正确解析
   - 原因：全局预览组件创建了单独的Vue应用实例，但没有为该实例注册Element Plus
   - 解决方案：在全局预览组件的应用实例中也注册Element Plus和Element Plus图标
   - 修改文件：`src/main.js`

2. **Vue Router警告修复**
   - 问题：路由配置中存在命名冲突，导致Vue Router警告
   - 原因：父路由和空路径子路由的名称配置不当
   - 解决方案：将路由名称从父路由移到子路由上
   - 修改文件：`src/router/index.js`

## 项目功能

- 知识库管理：创建、查看和删除知识库
- 文档管理：
  - 上传、查看和删除知识库中的文档
  - 文件预览：支持PDF/图片/Markdown/文本
  - 智能排序：按上传时间倒序排列
  - 优化显示：文件名截断、Tooltip提示
- 聊天界面：基于知识库内容进行问答交互

## 技术栈

- **Vue 3**：使用组合式API构建用户界面
- **Vite**：快速的前端构建工具
- **Pinia**：Vue的状态管理库
- **Vue Router**：Vue的官方路由管理器
- **Element Plus**：基于Vue 3的组件库
- **Sass**：CSS预处理器
- **Axios**：基于Promise的HTTP客户端

## 项目结构

```
frontend/
├── public/              # 静态资源
├── src/
│   ├── assets/          # 项目资源文件
│   │   └── icons/       # SVG图标
│   ├── components/      # 组件
│   │   ├── layout/      # 布局组件
│   │   ├── FilePreview.vue  # 文件预览组件
│   │   ├── GlobalPreview.vue  # 全局预览组件
│   │   └── KnowledgeManagement.vue  # 知识库管理组件
│   ├── router/          # 路由配置
│   ├── stores/          # Pinia状态管理
│   │   ├── chat.js      # 聊天状态
│   │   └── knowledge.js # 知识库状态
│   ├── views/           # 页面视图
│   │   ├── chat/        # 聊天相关视图
│   │   └── knowledge/   # 知识库相关视图
│   ├── App.vue          # 根组件
│   ├── main.js          # 入口文件
│   └── style.css        # 全局样式
├── index.html           # HTML模板
├── package.json         # 项目依赖
└── vite.config.js       # Vite配置
```

## 开发指南

### 安装依赖

```bash
npm install
# 或
yarn
# 或
pnpm install
```

### 启动开发服务器

```bash
npm run dev
# 或
yarn dev
# 或
pnpm dev
```

### 构建生产版本

```bash
npm run build
# 或
yarn build
# 或
pnpm build
```

### 预览生产构建

```bash
npm run preview
# 或
yarn preview
# 或
pnpm preview
```

## 主要功能说明

### 知识库管理

- 默认知识库：系统提供一个默认知识库，不可删除
- 创建知识库：用户可以创建自定义名称的知识库
- 删除知识库：非默认且为空的知识库可以被删除

### 文档管理

- 上传文档：支持拖拽上传文件到知识库
- 查看文档：显示知识库中的所有文档
- 删除文档：从知识库中移除文档

### 数据持久化

项目使用localStorage进行数据持久化，保存知识库和文档信息。