## [0.3.1] - 2025-09-22
### Fixed
- 修复了 `chroma_store.py` 中的值解包错误，解决了 `ValueError: too many values to unpack (expected 2)` 问题
- 修改了 `start.ps1` 脚本，使用 uvicorn 直接启动服务，提高启动稳定性
- 修复了 `main.py` 中的 uvicorn 启动配置，解决了 `WARNING: You must pass the application as an import string` 错误

### Enhanced
- 增强了 `document_loader.py` 中的文档加载函数，添加元数据返回功能
- 改进了文档处理流程，使向量数据库能够存储更丰富的文档元数据信息

## [0.3.0] - 2025-09-21
### Added
- 流式Markdown消息渲染功能
- marked和DOMPurify依赖

### Changed
- 改进消息内容解析和显示方式

## [0.2.0] - 2025-09-20
### Added
- 新增会话标题编辑功能
- 添加数据库表结构迁移脚本
- 实现前后端标题同步更新机制
- 新增知识库管理功能（创建、删除）
- 添加知识库描述字段
- 增强API日志记录

### Fixed
- 修复会话标题更新失败问题
- 优化数据库操作错误处理
- 解决前端状态不一致问题
- 修复知识库删除异常问题
- 解决表单验证边界条件问题

### Changed
- 改进会话列表的响应式更新
- 增强API错误提示信息
- 优化知识库管理UI交互
- 改进前端错误处理机制



## [0.1.0] - 2025-09-19 数据库和聊天历史记录修复

### 修复
- 修复了 `database.py` 中的 SQLAlchemy 类型错误，使用 `onupdate` 自动更新时间戳
- 重构了 `get_session_history` 和 `load_session_history` 函数，将 ORM 对象返回改为字典返回，解决会话分离问题
- 更新了 `rag_chat.py` 中的 `convert_db_messages_to_langchain_messages` 函数，适配新的数据结构
- 解决了 `'dict' object has no attribute 'role'` 错误
- 解决了 `Instance <Message> is not bound to a Session` 错误
- 解决了 `Error binding parameter 1: type 'Session' is not supported` 错误

### 优化
- 改进了数据库查询性能，使用直接字段查询代替完整 ORM 对象查询
- 增强了缓存机制，确保缓存内容类型一致性
- 提高了系统整体稳定性


## [0.0.1] - 初始版本

### 新增
- 项目初始化
- 基础数据库模型和操作函数
- 聊天历史记录功能
- 缓存机制实现
