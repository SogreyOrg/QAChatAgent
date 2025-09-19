# 更新日志

## [2025-09-19] - 数据库和聊天历史记录修复

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

## [2025-09-18] - 初始版本

### 新增
- 项目初始化
- 基础数据库模型和操作函数
- 聊天历史记录功能
- 缓存机制实现