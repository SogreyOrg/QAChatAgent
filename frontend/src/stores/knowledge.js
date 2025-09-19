import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import axios from 'axios'

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
  const createKnowledgeBase = async (name, description = '') => {
    try {
      console.log(`开始创建知识库 - 名称: ${name}, 描述: ${description}`);
      const loading = ElLoading.service({
        lock: true,
        text: '正在创建知识库...',
        background: 'rgba(0, 0, 0, 0.7)'
      })
      
      // 确保description不是undefined
      const safeDescription = description || '';
      
      // 调用后端API创建知识库
      console.log(`发送API请求 - 参数:`, { name, description: safeDescription });
      const response = await axios.post('/api/knowledge_base/create', {
        name,
        description: safeDescription
      })
      
      if (response.data.code === 200) {
        const newKnowledgeBase = {
          id: response.data.data.id,
          name: response.data.data.name,
          description: response.data.data.description || '',
          documentCount: 0,
          createdAt: new Date().toISOString()
        }
        
        knowledgeBases.value.push(newKnowledgeBase)
        documents.value[newKnowledgeBase.id] = []
        
        ElMessage.success('知识库创建成功')
        loading.close()
        return newKnowledgeBase
      } else {
        throw new Error(response.data.message || '创建知识库失败')
      }
    } catch (error) {
      ElMessage.error(`创建知识库失败: ${error.response?.data?.detail || error.message}`)
      console.error('创建知识库出错:', error)
      return null
    }
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
    logger.info(`开始删除知识库 - ID: ${knowledgeBaseId}`);
    
    // 添加确认对话框
    await ElMessageBox.confirm(
      '确定要删除该知识库吗？所有相关文档也将被删除，此操作不可恢复！',
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    logger.info(`用户确认删除知识库 - ID: ${knowledgeBaseId}`);
    
    // 显示加载状态
    const loading = ElLoading.service({
      lock: true,
      text: '正在删除知识库...',
      background: 'rgba(0, 0, 0, 0.7)'
    });

    try {
      // 调用后端API删除知识库
      logger.info(`调用删除API - URL: /api/knowledge_base/delete/${knowledgeBaseId}`);
      const response = await axios.delete(`http://localhost:8000/api/knowledge_base/delete/${knowledgeBaseId}`);

      logger.info(`API响应状态: ${response.status}, 数据:`, response.data);

      if (response.data.code === 200) {
        // 从前端状态中移除知识库
        const index = knowledgeBases.value.findIndex(kb => kb.id === knowledgeBaseId);
        if (index !== -1) {
          knowledgeBases.value.splice(index, 1);
          delete documents.value[knowledgeBaseId];
          
          // 如果删除的是当前活跃知识库，则切换到第一个知识库
          if (knowledgeBaseId === activeKnowledgeBaseId.value) {
            if (knowledgeBases.value.length > 0) {
              activeKnowledgeBaseId.value = knowledgeBases.value[0].id;
            } else {
              activeKnowledgeBaseId.value = '0'; // 回退到默认知识库
            }
          }
          
          ElMessage.success('知识库删除成功');
          logger.info(`知识库删除成功 - ID: ${knowledgeBaseId}`);
          return true;
        }
      } else {
        const errorMsg = response.data.message || '删除知识库失败';
        logger.error(`API返回错误: ${errorMsg}`);
        throw new Error(errorMsg);
      }
    } catch (error) {
      const errorDetail = error.response?.data?.detail || error.message;
      logger.error(`删除知识库API调用失败: ${errorDetail}`, error);
      
      // 更详细的错误提示
      let userMessage = '删除知识库失败';
      if (error.response?.status === 404) {
        userMessage = '知识库不存在或已被删除';
      } else if (error.response?.status === 500) {
        userMessage = '服务器内部错误，请联系管理员';
      }
      
      ElMessage.error(`${userMessage}: ${errorDetail}`);
      return false;
    } finally {
      loading.close();
      logger.info(`删除知识库流程结束 - ID: ${knowledgeBaseId}`);
    }
  } catch (error) {
    // 仅处理用户取消操作的情况
    if (error !== 'cancel') {
      logger.error('删除知识库过程中出错:', error);
    }
    return false;
  }
};

  
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