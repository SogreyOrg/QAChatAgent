import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useChatStore = defineStore('chat', () => {
  // 聊天会话列表
  const chatSessions = ref([
    {
      id: '1',
      title: '新的会话',
      messages: [],
      createdAt: new Date().toISOString()
    }
  ])
  
  // 当前活跃的会话ID
  const activeChatId = ref('1')
  
  // 获取当前活跃的会话
  const activeChat = () => {
    return chatSessions.value.find(chat => chat.id === activeChatId.value) || chatSessions.value[0]
  }
  
  // 创建新的会话
  const createNewChat = () => {
    const newChat = {
      id: Date.now().toString(),
      title: '新的会话',
      messages: [],
      createdAt: new Date().toISOString()
    }
    chatSessions.value.unshift(newChat)
    activeChatId.value = newChat.id
    return newChat
  }
  
  // 发送消息
  const sendMessage = (content) => {
    const chat = activeChat()
    if (!chat) return
    
    // 用户消息
    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    }
    
    chat.messages.push(userMessage)
    
    // 模拟AI响应
    setTimeout(() => {
      const aiMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `这是对"${content}"的回复`,
        timestamp: new Date().toISOString()
      }
      chat.messages.push(aiMessage)
    }, 1000)
    
    // 如果是第一条消息，更新会话标题
    if (chat.messages.length === 1) {
      chat.title = content.substring(0, 20) + (content.length > 20 ? '...' : '')
    }
  }
  
  // 删除会话
  const deleteChat = (chatId) => {
    const index = chatSessions.value.findIndex(chat => chat.id === chatId)
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