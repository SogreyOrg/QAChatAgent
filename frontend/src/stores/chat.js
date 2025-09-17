import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { chatApi } from '@/services/api'

// 生成会话ID的函数 - 使用时间戳毫秒
function generateSessionId() {
  return Date.now().toString();
}

export const useChatStore = defineStore('chat', () => {
  // 从本地存储加载聊天会话
  const loadChatSessions = () => {
    try {
      const savedSessions = localStorage.getItem('chatSessions')
      const savedActiveId = localStorage.getItem('activeChatId')
      
      if (savedSessions) {
        return {
          sessions: JSON.parse(savedSessions),
          activeId: savedActiveId
        }
      }
    } catch (error) {
      console.error('加载聊天会话失败:', error)
    }
    
    // 如果没有保存的会话或加载失败，创建一个新的会话
    const defaultSession = {
      session_id: generateSessionId(),
      title: '新的会话',
      messages: [],
      createdAt: new Date().toISOString()
    }
    
    return {
      sessions: [defaultSession],
      activeId: defaultSession.session_id
    }
  }
  
  // 初始化数据
  const { sessions, activeId } = loadChatSessions()
  
  // 聊天会话列表
  const chatSessions = ref(sessions)
  
  // 当前活跃的会话ID
  const activeChatId = ref(activeId)
  
  // 监听变化并保存到本地存储
  watch(chatSessions, (newSessions) => {
    localStorage.setItem('chatSessions', JSON.stringify(newSessions))
  }, { deep: true })
  
  watch(activeChatId, (newActiveId) => {
    localStorage.setItem('activeChatId', newActiveId)
  })
  
  // 获取当前活跃的会话
  const activeChat = () => {
    return chatSessions.value.find(chat => chat.session_id === activeChatId.value) || chatSessions.value[0]
  }
  
  // 创建新的会话
  const createNewChat = () => {
    const newChat = {
      session_id: generateSessionId(), // 使用时间戳毫秒作为会话ID
      title: '新的会话',
      messages: [],
      createdAt: new Date().toISOString()
    }
    chatSessions.value.unshift(newChat)
    activeChatId.value = newChat.session_id
    return newChat
  }
  
  // 发送消息
  const sendMessage = async (content) => {
    const chat = activeChat()
    if (!chat) return
    
    const timestamp = new Date().toISOString()
    
    // 用户消息
    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp
    }
    
    chat.messages.push(userMessage)
    
    try {
      // 调试：打印会话ID
      console.log('发送消息的会话ID:', chat.id, '类型:', typeof chat.id)
      
      // 确保会话ID是字符串类型
      // 注意：我们保留现有的会话ID，不再尝试转换为UUID格式
      
      // 创建AI消息占位
      const aiMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString()
      }
      chat.messages.push(aiMessage)
      
      // 建立SSE连接获取流式响应
      const eventSource = new EventSource(
        `/api/chat/stream?session_id=${chat.session_id}&message=${encodeURIComponent(content)}`
      )
      
      console.log('SSE连接已建立')
      
      eventSource.onmessage = (event) => {
        console.log('收到SSE消息:', event.data)
        
        if (event.data === '[DONE]') {
          console.log('SSE流结束')
          eventSource.close()
          return
        }
        
        // 更新AI消息内容
        aiMessage.content += event.data
        chat.messages = [...chat.messages] // 触发响应式更新
      }
      
      eventSource.onerror = (err) => {
        console.error('SSE错误:', err)
        eventSource.close()
      }
    } catch (error) {
      console.error('发送消息失败:', error)
      // 可以在这里添加错误处理逻辑，比如显示错误提示
    }
    
    // 如果是第一条消息，更新会话标题
    if (chat.messages.length === 1) {
      chat.title = content.substring(0, 20) + (content.length > 20 ? '...' : '')
    }
  }
  
  // 删除会话
  const deleteChat = (chatId) => {
    const index = chatSessions.value.findIndex(chat => chat.session_id === chatId)
    if (index !== -1) {
      chatSessions.value.splice(index, 1)
      
      // 如果删除的是当前活跃会话，则切换到第一个会话
      if (chatId === activeChatId.value) {
        if (chatSessions.value.length > 0) {
          activeChatId.value = chatSessions.value[0].id
        } else {
          // 如果没有会话了，创建一个新的
          createNewChat()
        }
      }
    }
  }
  
  return {
    chatSessions,
    activeChatId,
    activeChat,
    createNewChat,
    sendMessage,
    deleteChat
  }
})