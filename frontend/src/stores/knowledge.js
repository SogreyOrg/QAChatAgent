import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

export const useKnowledgeStore = defineStore('knowledge', () => {
  // 本地存储键名
  const STORAGE_KEY = 'knowledge_data'
  
  // 加载本地数据
  const loadFromLocal = () => {
    try {
      const data = localStorage.getItem(STORAGE_KEY)
      if (data) {
        const parsed = JSON.parse(data)
        return {
          knowledgeBases: parsed.knowledgeBases || [],
          documents: parsed.documents || {}
        }
      }
    } catch (e) {
      console.error('Failed to load knowledge data', e)
    }
    return null
  }
  
  // 保存到本地
  const saveToLocal = () => {
    const data = {
      knowledgeBases: knowledgeBases.value,
      documents: documents.value
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  }
  
  // 尝试加载本地数据
  const localData = loadFromLocal()
  // 知识库列表
  const knowledgeBases = ref(
    localData?.knowledgeBases || [
      {
        id: '0',
        name: '默认知识库',
        description: '系统默认知识库',
        documentCount: 0,
        createdAt: new Date().toISOString()
      }
    ]
  )
  
  // 当前选中的知识库ID
  const activeKnowledgeBaseId = ref('0')
  
  // 知识库中的文档列表
  const documents = ref(localData?.documents || {
    '0': [] // 默认知识库初始为空
  })
  
  // 监听数据变化并自动保存
  watch(
    [knowledgeBases, documents],
    () => {
      saveToLocal()
    },
    { deep: true }
  )
  
  // 获取当前活跃的知识库
  const activeKnowledgeBase = () => {
    return knowledgeBases.value.find(kb => kb.id === activeKnowledgeBaseId.value) || knowledgeBases.value[0]
  }
  
  // 获取当前知识库的文档
  const activeDocuments = () => {
    return documents.value[activeKnowledgeBaseId.value] || []
  }
  
  // 创建新的知识库
  const createKnowledgeBase = (name, description = '') => {
    const newKnowledgeBase = {
      id: Date.now().toString(),
      name,
      description,
      documentCount: 0,
      createdAt: new Date().toISOString()
    }
    knowledgeBases.value.push(newKnowledgeBase)
    documents.value[newKnowledgeBase.id] = []
    return newKnowledgeBase
  }
  
  // 上传文档到知识库
  const uploadDocument = (knowledgeBaseId, document) => {
    if (!documents.value[knowledgeBaseId]) {
      documents.value[knowledgeBaseId] = []
    }
    
    const newDocument = {
      id: document.docId,
      name: document.name,
      size: document.size,
      uploadedAt: new Date().toISOString(),
      fileKey: document.fileKey,
      savedName: document.savedName,
      path: document.path,
      downloadUrl: document.downloadUrl
    }

    console.log('uploadDocument', newDocument)
    
    documents.value[knowledgeBaseId].push(newDocument)
    
    // 更新知识库文档计数
    const kb = knowledgeBases.value.find(kb => kb.id === knowledgeBaseId)
    if (kb) {
      kb.documentCount = documents.value[knowledgeBaseId].length
    }
    
    return newDocument
  }
  
  // 删除文档
  const deleteDocument = (knowledgeBaseId, documentId) => {
    if (!documents.value[knowledgeBaseId]) return false
    
    const index = documents.value[knowledgeBaseId].findIndex(doc => doc.id === documentId)
    if (index !== -1) {
      documents.value[knowledgeBaseId].splice(index, 1)
      
      // 更新知识库文档计数
      const kb = knowledgeBases.value.find(kb => kb.id === knowledgeBaseId)
      if (kb) {
        kb.documentCount = documents.value[knowledgeBaseId].length
      }
      
      return true
    }
    
    return false
  }
  
  // 删除知识库
  const deleteKnowledgeBase = async (knowledgeBaseId) => {
    try {
      // 禁止删除默认知识库
      if (knowledgeBaseId === '0') {
        ElMessage.warning('默认知识库不可删除')
        return false
      }
      
      // 检查知识库是否为空
      const docCount = documents.value[knowledgeBaseId]?.length || 0
      if (docCount > 0) {
        ElMessage.warning('请先删除该知识库中的所有文档')
        return false
      }
      
      await ElMessageBox.confirm('确定要删除此知识库吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      
      const index = knowledgeBases.value.findIndex(kb => kb.id === knowledgeBaseId)
      if (index !== -1) {
        knowledgeBases.value.splice(index, 1)
        delete documents.value[knowledgeBaseId]
        
        // 如果删除的是当前活跃知识库，则切换到第一个知识库
        if (knowledgeBaseId === activeKnowledgeBaseId.value) {
          if (knowledgeBases.value.length > 0) {
            activeKnowledgeBaseId.value = knowledgeBases.value[0].id
          }
        }
        
        ElMessage.success('知识库删除成功')
        return true
      }
      
      return false
    } catch (error) {
      // 仅处理用户取消操作的情况
      if (error !== 'cancel') {
        console.log('删除知识库出错:', error)
      }
      return false
    }
  }
  
  return {
    knowledgeBases,
    activeKnowledgeBaseId,
    documents,
    activeKnowledgeBase,
    activeDocuments,
    createKnowledgeBase,
    uploadDocument,
    deleteDocument,
    deleteKnowledgeBase
  }
})