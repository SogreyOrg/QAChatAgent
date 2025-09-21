<template>
  <div class="chat-view">
    <!-- 聊天会话列表 -->
    <div class="chat-sessions">
      <div class="session-header">
        <h3>会话列表</h3>
        <el-button type="primary" size="small" @click="createNewChat">
          <el-icon>
            <Plus />
          </el-icon>
          新建
        </el-button>
      </div>

      <el-scrollbar>
        <el-menu :default-active="activeChatId" @select="handleChatSelect">
          <el-menu-item 
            v-for="chat in chatSessions" 
            :key="chat.session_id" 
            :index="String(chat.session_id)"
            @click="handleChatClick(chat)"
          >
            <template #title>
              <el-input
                v-if="editingSessionId === chat.session_id"
                v-model="editingTitle"
                size="small"
                @blur="saveTitle(chat)"
                @keyup.enter="saveTitle(chat)"
              />
              <span v-else @dblclick="startEditTitle(chat)">
                {{ chat.title }}
              </span>
              <el-button type="danger" size="small" @click.stop="deleteChat(chat.session_id)">
                删除
              </el-button>
            </template>
          </el-menu-item>
        </el-menu>
      </el-scrollbar>
    </div>

    <!-- 聊天内容区 -->
    <div class="chat-content">
      <div class="messages" ref="messagesRef">
        <div v-for="message in activeChat.messages" :key="message.id" class="message" :class="message.role">
          <div class="avatar">
            <el-avatar>
              {{ message.role === 'human' ? '我' : 'AI' }}
            </el-avatar>
          </div>
          <div class="content">
            <div class="time">{{ formatTime(message.timestamp) }}</div>
            <div class="text message-content" v-html="renderMarkdown(message.content)"></div>
          </div>
        </div>
      </div>

      <!-- 消息输入框 -->
      <div class="input-area">
        <el-input v-model="inputMessage" type="textarea" :rows="3" placeholder="输入消息..." @keyup.enter="sendMessage" />
        <div class="actions">
          <el-button type="primary" @click="sendMessage">发送</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useChatStore } from '@/stores/chat'
import { useKnowledgeStore } from '@/stores/knowledge'
import { ElMessage, ElMessageBox } from 'element-plus'

const chatStore = useChatStore()
const knowledgeStore = useKnowledgeStore()
const inputMessage = ref('')
const messagesRef = ref(null)
const editingSessionId = ref(null)
const editingTitle = ref('')

const chatSessions = computed(() => {
  console.log('Current chat sessions:', chatStore.chatSessions)
  return chatStore.chatSessions
})
const activeChatId = computed({
  get: () => {
    console.log('获取 activeChatId:', chatStore.activeChatId)
    return chatStore.activeChatId
  },
  set: (value) => {
    console.log('设置 activeChatId:', value)
    chatStore.activeChatId = value
  }
})
const activeChat = computed(() => chatStore.activeChat())
// const kb_id = computed(() => knowledgeStore.activeKnowledgeBaseId)

const createNewChat = () => {
  chatStore.createNewChat()
  console.log('新建会话后的 activeChatId:', activeChatId.value)
}

const handleChatSelect = (chatId) => {
  // 这个方法由 el-menu 的 @select 事件触发
  console.log('handleChatSelect 被调用，chatId:', chatId)
  if (chatId !== activeChatId.value) {
    activeChatId.value = chatId
    console.log('handleChatSelect 设置后的 activeChatId:', activeChatId.value)
    nextTick(() => {
      scrollToBottom()
    })
  }
}

const handleChatClick = (chat) => {  
  const chatId = chat.session_id  
  // 如果没有有效的ID，则不执行任何操作
  if (!chatId) {
    console.error('会话对象没有有效的ID属性')
    return
  }
  
  // 安全地比较，处理 activeChatId.value 可能为 undefined 的情况
  if (activeChatId.value === undefined || String(chatId) !== activeChatId.value) {
    // 这里可以添加会话切换前的业务逻辑
    console.log(`切换到会话:${chat.title}(${chatId})`)
    
    // 更新当前活动会话ID
    chatStore.activeChatId = chatId
    
    // 会话切换后的业务逻辑
    nextTick(() => {
      // 确保 activeChat 更新为当前选中的会话
      console.log('会话已切换，当前会话:', chatStore.activeChat())
      scrollToBottom()
    })
  } else {
    console.log(`当前会话:${chat.title}(${chatId})`)
    // 可以添加点击当前会话的业务逻辑
  }
}

const startEditTitle = (chat) => {
  editingSessionId.value = chat.session_id
  editingTitle.value = chat.title
}

const saveTitle = async (chat) => {
  if (!editingTitle.value.trim()) {
    editingSessionId.value = null
    return
  }

  // 如果标题没有变化，直接退出编辑模式
  if (chat.title === editingTitle.value) {
    editingSessionId.value = null
    return
  }

  // 保存原始标题以便回滚
  const originalTitle = chat.title
  const sessionId = chat.session_id

  try {
    // 先检查会话是否存在
    const sessionExists = chatStore.chatSessions.some(s => s.session_id === sessionId)
    if (!sessionExists) {
      throw new Error('会话不存在')
    }

    // 调用后端API更新标题
    const response = await fetch(`/api/session/update/${sessionId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        title: editingTitle.value
      })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      const errorMsg = errorData.detail || '更新标题失败'
      
      // 如果会话不存在，从列表中移除
      if (response.status === 404) {
        chatStore.deleteChat(sessionId)
      } else {
        // 恢复原始标题
        const index = chatStore.chatSessions.findIndex(s => s.session_id === sessionId)
        if (index !== -1) {
          chatStore.chatSessions[index].title = originalTitle
        }
      }
      
      throw new Error(errorMsg)
    }

    const result = await response.json()
    
    // 更新前端存储
    const index = chatStore.chatSessions.findIndex(s => s.session_id === sessionId)
    if (index !== -1) {
      chatStore.chatSessions[index].title = editingTitle.value
    }
    editingSessionId.value = null
    ElMessage.success(result.message || '标题更新成功')
  } catch (error) {
    console.error('更新标题失败:', {
      sessionId,
      error: error.message,
      stack: error.stack
    })
    editingSessionId.value = null
    ElMessage.error(`更新标题失败: ${error.message}`)
  }
}

const deleteChat = async (chatId) => {
  try {
    await ElMessageBox.confirm('确定要删除此会话吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    chatStore.deleteChat(chatId)
    ElMessage.success('会话删除成功')
  } catch (error) {
    console.log('取消删除会话', error)
  }
}

const sendMessage = () => {
  if (!inputMessage.value.trim()) return

  console.log('发送消息:', inputMessage.value, knowledgeStore.activeKnowledgeBaseId)
  chatStore.sendMessage(inputMessage.value, knowledgeStore.activeKnowledgeBaseId )
  inputMessage.value = ''

  nextTick(() => {
    scrollToBottom()
  })
}

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString()
}

const renderMarkdown = (content) => {
  return DOMPurify.sanitize(marked.parse(content))
}

const scrollToBottom = () => {
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
.chat-view {
  display: flex;
  height: 100%;
  position: relative;
}

/* 添加科技感背景 */
.chat-view::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    radial-gradient(circle at 75% 25%, rgba(0, 184, 255, 0.05) 0%, transparent 50%),
    radial-gradient(circle at 25% 75%, rgba(106, 60, 181, 0.05) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

.chat-sessions {
  width: 240px;
  background-color: var(--bg-medium);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  z-index: 1;
}

.session-header {
  padding: 20px 17px 21px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
  background: linear-gradient(90deg, var(--bg-medium), var(--bg-light));
}

.session-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--accent-color);
  text-shadow: 0 0 5px rgba(0, 184, 255, 0.5);
  letter-spacing: 1px;
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-dark);
  position: relative;
}

/* 添加科技感网格背景 */
.chat-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    linear-gradient(rgba(0, 184, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 184, 255, 0.03) 1px, transparent 1px);
  background-size: 20px 20px;
  pointer-events: none;
  z-index: 0;
}

.messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  position: relative;
  z-index: 1;
}

.message {
  display: flex;
  margin-bottom: 20px;
  position: relative;
}

.message.human {
  flex-direction: row-reverse;
}

.avatar {
  margin: 25px 10px 0;
}

.avatar .el-avatar {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
  border: 2px solid var(--border-color);
  box-shadow: var(--shadow-sm);
}

.content {
  max-width: 70%;
}

.message.human .content {
  align-items: flex-end;
}

.text {
  /* min-height: 32px; */
  padding: 12px 16px;
  border-radius: 8px;
  background-color: var(--bg-medium);
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
  position: relative;
}

.message-content {
  /* white-space: pre-wrap; */
  word-break: break-word;
}

/* 添加AI消息的科技感装饰 */
.message:not(.human) .text::before {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  border-radius: 10px;
  background: linear-gradient(45deg, var(--primary-color), transparent, var(--primary-light));
  background-size: 400% 400%;
  opacity: 0.3;
  z-index: -1;
  animation: gradient-shift 3s ease infinite;
}

.message.human .text {
  background: linear-gradient(135deg, var(--accent-dark), var(--accent-color));
  color: var(--text-primary);
  border: none;
}

.message .content .time {
  text-align: start;
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary);
}

.message.user .content .time {
  text-align: end;
}

.input-area {
  padding: 16px;
  border-top: 1px solid var(--border-color);
  background-color: var(--bg-medium);
  position: relative;
  z-index: 1;
}

/* 添加输入区域的发光边框 */
.input-area::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent-color), transparent);
  opacity: 0.5;
}

.actions {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}

.el-menu {
  border-right: none;
  background-color: transparent;
}

.el-menu-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.3s ease;
  border-left: 3px solid transparent;
}

.el-menu-item:hover {
  background-color: var(--bg-light);
}

.el-menu-item.is-active {
  background: linear-gradient(90deg, var(--primary-dark), transparent);
  border-left: 3px solid var(--accent-color);
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.2);
}

/* 输入框样式 */
.el-textarea__inner {
  background-color: var(--bg-dark);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  transition: all 0.3s ease;
}

.el-textarea__inner:focus {
  border-color: var(--accent-color);
  box-shadow: 0 0 10px rgba(0, 184, 255, 0.3);
}

/* 发送按钮动画效果 */
.actions .el-button {
  position: relative;
  overflow: hidden;
}

.actions .el-button::after {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  transform: rotate(45deg);
  animation: shine 3s infinite;
}

@keyframes shine {
  0% {
    left: -50%;
    top: -50%;
  }

  100% {
    left: 150%;
    top: 150%;
  }
}
</style>