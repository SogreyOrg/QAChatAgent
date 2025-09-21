import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

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
  const sendMessage = async (content, kb_id) => {
    const chat = activeChat()
    if (!chat) return
    
    const timestamp = new Date().toISOString()
    
    // 用户消息
    const userMessage = {
      id: Date.now().toString(),
      role: 'human',
      content,
      timestamp
    }
    
    chat.messages.push(userMessage)
    
    try {
      // 调试：打印会话ID
      console.log(chat)
      console.log('发送消息的会话ID:', chat.session_id)
      
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
        `/api/chat/stream?session_id=${chat.session_id}&message=${encodeURIComponent(content)}&kb_id=${kb_id}`
      )

      // 添加连接状态检查
      eventSource.onopen = () => {
        console.log('SSE连接已成功建立')
        console.log('SSE readyState:', eventSource.readyState) // 应该为1 (OPEN)
      }
      
      eventSource.onmessage = (event) => {
        // console.log('收到原始SSE消息:', event.data)
        
        if (event.data === '[DONE]') {
          console.log('SSE流结束')
          eventSource.close()

          // 接收完成，打印完整的AI消息内容
          console.log('AI消息内容:', aiMessage.content)
          return
        }
        
        // 解析JSON格式的消息
        try {
          // console.log('解析前的内容:', event.data)
          const data = JSON.parse(event.data)          
          // console.log('解析后的内容0:', data.content)
          if (data && data.content) {
            // console.log('解析后的内容:', data.content)
            aiMessage.content += data.content
          }
        } catch (e) {
          // 如果解析失败，尝试检查是否是多个JSON对象连接在一起
          console.warn('初次解析失败，尝试处理可能的多JSON对象:', e)
          
          try {
            // 尝试将字符串分割成多个JSON对象
            const jsonPattern = /{[^}]+}/g
            const jsonMatches = event.data.match(jsonPattern)
            
            if (jsonMatches && jsonMatches.length > 0) {
              console.log('检测到多个JSON对象:', jsonMatches.length)
              
              // 解析每个JSON对象并提取content
              jsonMatches.forEach(jsonStr => {
                try {
                  const jsonObj = JSON.parse(jsonStr)
                  if (jsonObj && jsonObj.content) {
                    aiMessage.content += jsonObj.content
                  }
                } catch (innerError) {
                  console.error('解析子JSON对象失败:', innerError)
                }
              })
            } else {
              // 如果没有匹配到JSON对象，则作为普通文本处理
              console.error('未检测到有效的JSON对象，作为普通文本处理')
              aiMessage.content += event.data
            }
          } catch (outerError) {
            // 如果所有尝试都失败，则作为普通文本处理
            console.error('所有解析尝试均失败:', outerError)
            aiMessage.content += event.data
          }
        }
        
        chat.messages = [...chat.messages] // 触发响应式更新
      }
      
      eventSource.onerror = (err) => {
        console.error('SSE错误:', err)
        // 添加重试逻辑或用户提示
        aiMessage.content += "\n[连接中断，请刷新页面重试]"
        chat.messages = [...chat.messages] // 触发响应式更新
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