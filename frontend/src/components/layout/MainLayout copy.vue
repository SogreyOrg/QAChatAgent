<template>
  <div class="main-layout">
    <!-- 侧边栏 -->
    <div class="sidebar">
      <div class="sidebar-header">
        <h2>知识库</h2>
        <div>
          <el-button type="primary" size="small" @click="createNewKnowledgeBase">
            <el-icon><Plus /></el-icon>
            新建
          </el-button>
          <el-button 
            type="info" 
            size="small" 
            @click="manageKnowledge"
            style="margin-left: 8px"
          >
            <el-icon><Setting /></el-icon>
            管理
          </el-button>
        </div>
      </div>
      
      <div class="knowledge-list">
        <el-scrollbar>
          <el-menu
            :default-active="activeKnowledgeBaseId"
            @select="handleKnowledgeBaseSelect"
          >
            <el-menu-item
              v-for="kb in knowledgeBases"
              :key="kb.id"
              :index="kb.id"
            >
              <template #title>
                <div class="knowledge-item">
                  <span>{{ kb.name }}</span>
                  <span class="document-count">文档：<strong>{{ kb.documentCount }}</strong></span>
                </div>
              </template>
            </el-menu-item>
          </el-menu>
        </el-scrollbar>
      </div>
      
      <div class="document-list">
        <el-scrollbar>
          <el-table
            :data="documents"
            style="width: 100%"
            @row-click="handleDocumentClick"
            @cell-click="handleDocumentClick"
          >
            <el-table-column prop="name" label="文档名称" min-width="100">
              <template #default="{ row }">
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    <div>文件名: {{ row.name }}</div>
                    <div>大小: {{ formatFileSize(row.size) }}</div>
                    <div>上传时间: {{ formatTime(row.uploadedAt) }}</div>
                  </template>
                  <span 
                    class="document-name" 
                    @click.stop="previewDocument(row)"
                    style="display: inline-block; width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"
                  >
                    {{ formatFileName(row.name) }}
                  </span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="size" label="大小" width="80" align="center">
              <template #default="{ row }">
                {{ formatFileSize(row.size) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="70" align="center">
              <template #default="{ row }">
                <el-button
                  type="danger"
                  size="small"
                  @click.stop="deleteDocument(row.id)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-scrollbar>
      </div>
    </div>
    
    <!-- 主内容区 -->
    <div class="main-content">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, getCurrentInstance } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Setting } from '@element-plus/icons-vue'
import { useKnowledgeStore } from '@/stores/knowledge'
import axios from 'axios'
import { ElMessage, ElMessageBox, ElLoading, ElNotification } from 'element-plus'

const router = useRouter()
const knowledgeStore = useKnowledgeStore()

const activeKnowledgeBaseId = computed(() => knowledgeStore.activeKnowledgeBaseId)
const knowledgeBases = computed(() => knowledgeStore.knowledgeBases)
const documents = computed(() => {
  const docs = knowledgeStore.activeDocuments()
  return [...docs].sort((a, b) => new Date(b.uploadedAt) - new Date(a.uploadedAt))
})

const manageKnowledge = () => {
  router.push('/knowledge')
}

const deleteKnowledgeBase = async (knowledgeBaseId) => {
  try {
    await knowledgeStore.deleteKnowledgeBase(knowledgeBaseId)
  } catch (error) {
    console.log('删除知识库出错:', error)
  }
}

const createNewKnowledgeBase = async () => {
  try {
    const { value: name } = await ElMessageBox.prompt('请输入知识库名称', '新建知识库', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /\S+/,
      inputErrorMessage: '知识库名称不能为空'
    })
    
    if (name) {
      const newKnowledgeBase = await knowledgeStore.createKnowledgeBase(name)
      if (newKnowledgeBase) {
        // 创建成功后自动选中新创建的知识库
        knowledgeStore.activeKnowledgeBaseId = newKnowledgeBase.id
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('创建知识库出错:', error)
    }
  }
}

const handleKnowledgeBaseSelect = (knowledgeBaseId) => {
  knowledgeStore.activeKnowledgeBaseId = knowledgeBaseId
}

// 预览文档
const emit = defineEmits(['preview-document'])

const previewDocument = (document) => {
  console.log('=== 文档预览调试 ===')
  const fullPath = document?.path ? `http://localhost:8000${document.path}` : null
  console.log('地址:', fullPath)
  try {
    // 统一通过事件触发预览
    console.log('触发preview-document事件')
    emit('preview-document', {
      ...document,
      path: fullPath,
      downloadUrl: fullPath,
      type: document.name.split('.').pop().toLowerCase()
    })
  } catch (error) {
    console.error('预览出错:', error)
    ElMessage.error(`预览失败: ${error.message}`)
    // 作为最后手段，直接打开URL
    if (fullPath) {
      console.log('尝试直接打开文件URL:', fullPath)
      window.open(fullPath, '_blank')
    } else {
      console.error('文档缺少path属性，无法预览')
    }
  } finally {
    console.groupEnd()
  }
}

// const deleteDocument = async (documentId) => {
//   try {
//     await ElMessageBox.confirm('确定要删除此文档吗？', '提示', {
//       confirmButtonText: '确定',
//       cancelButtonText: '取消',
//       type: 'warning'
//     })
    
//     knowledgeStore.deleteDocument(knowledgeStore.activeKnowledgeBaseId, documentId)
//     ElMessage.success('文档删除成功')
//   } catch (error) {
//     console.log('取消删除文档', error)
//   }
// }

const deleteDocument = async (documentId) => {
  try {
    await ElMessageBox.confirm('确定要删除此文档吗？', '警告', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger'
    })

    const doc = documents.value.find(d => d.id === documentId)
    if (!doc) throw new Error('文档不存在')

    const loading = ElLoading.service({
      lock: true,
      text: '正在删除文档...',
      background: 'rgba(0, 0, 0, 0.7)'
    })

    try {
      // 并行删除文件和相关记录
      const [fileDeleteResult] = await Promise.allSettled([
        axios.delete(`http://localhost:8000/api/delete/${encodeURIComponent(doc.fileKey || doc.savedName)}`),
        knowledgeStore.deleteDocument(
          knowledgeStore.activeKnowledgeBaseId,
          documentId
        )
      ])

      if (fileDeleteResult.status === 'rejected') {
        console.error('文件删除失败:', fileDeleteResult.reason)
        throw new Error('文件删除失败: ' + (fileDeleteResult.reason.response?.data?.message || fileDeleteResult.reason.message))
      }

      // 更新本地数据
      documents.value = documents.value.filter(d => d.id !== documentId)
      
      ElNotification.success({
        title: '删除成功',
        message: `文档 "${doc.name}" 已删除`,
        duration: 3000,
        position: 'bottom-right'
      })
    } finally {
      loading.close()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElNotification.error({
        title: '删除失败',
        message: error.response?.data?.message || error.message,
        duration: 5000,
        position: 'bottom-right'
      })
    }
  }
}

const formatFileSize = (bytes) => {
  if (!bytes) return ''
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleString()
}

const formatFileName = (name) => {
  if (!name) return ''
  const maxLength = 15 // 最大显示长度
  const extensionIndex = name.lastIndexOf('.')
  
  if (extensionIndex <= 0 || name.length <= maxLength) {
    return name
  }
  
  const prefix = name.substring(0, 5)
  const suffix = name.substring(extensionIndex - 3, extensionIndex)
  const extension = name.substring(extensionIndex)
  
  return `${prefix}...${suffix}${extension}`
}

const handleDocumentClick = (document, column, event) => {
  console.group('文档点击事件')
  console.log('文档对象:', document)
  console.log('点击列:', column)
  console.log('事件目标:', event.target)
  
  try {
    // 只处理行点击，避免与列内按钮冲突
    if (column?.property) {
      console.log('忽略列点击:', column.property)
      return
    }
    
    console.log('触发预览...')
    previewDocument(document)
  } catch (error) {
    console.error('文档点击处理出错:', error)
    // 作为最后手段，直接打开文件URL
    if (document?.path) {
      window.open(`http://localhost:8000${document.path}`, '_blank')
    }
  } finally {
    console.groupEnd()
  }
}
</script>

<style scoped>
:root {
  /* 基础色 */
  --bg-dark: #0a0e17;
  --bg-medium: #141a2a;
  --bg-light: #1e2638;
  --border-color: #2a3a50;
  
  /* 文字色 */
  --text-primary: #e0e5ec;
  --text-secondary: #8a9bb9;
  
  /* 强调色 */
  --accent-color: #00b8ff;
  --accent-glow: rgba(0, 184, 255, 0.3);
  --primary-dark: rgba(0, 184, 255, 0.2);
  
  /* 表格专用变量 - 增强科技感 */
  --el-table-header-bg-color: var(--bg-medium);
  --el-table-tr-bg-color: var(--bg-dark);
  --el-table-text-color: var(--text-primary);
  --el-table-border-color: var(--border-color);
  --el-table-row-hover-bg-color: color-mix(in srgb, var(--bg-light), var(--accent-glow) 10%);
  --el-table-header-text-color: var(--accent-color);
  --el-table-current-row-bg-color: color-mix(in srgb, var(--bg-light), var(--accent-color) 5%);
  --el-table-fixed-box-shadow: 0 0 10px var(--accent-glow);
}

.document-name {
  color: var(--el-color-primary);
  cursor: pointer;
}

.document-name:hover {
  text-decoration: underline;
}
.main-layout {
  display: flex;
  height: 100vh;
  background-color: var(--bg-dark);
  position: relative;
  overflow: hidden;
}

/* 添加科技感背景 */
.main-layout::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    radial-gradient(circle at 25% 25%, rgba(106, 60, 181, 0.05) 0%, transparent 50%),
    radial-gradient(circle at 75% 75%, rgba(0, 184, 255, 0.05) 0%, transparent 50%),
    linear-gradient(rgba(106, 60, 181, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(106, 60, 181, 0.03) 1px, transparent 1px);
  background-size: 100% 100%, 100% 100%, 20px 20px, 20px 20px;
  pointer-events: none;
  z-index: 0;
}

.sidebar {
  width: 280px;
  background-color: var(--bg-medium);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  z-index: 1;
  box-shadow: var(--shadow-md);
}

.sidebar-header {
  padding: 19px 16px 19px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
  background: linear-gradient(90deg, var(--bg-medium), var(--bg-light));
}

.sidebar-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--accent-color);
  text-shadow: 0 0 5px rgba(0, 184, 255, 0.5);
  letter-spacing: 1px;
}

.knowledge-list {
  flex: 1;
  border-bottom: 1px solid var(--border-color);
}

.document-list {
  flex: 2;
  position: relative;
}

/* 文档列表暗色风格 */
/* 强制所有Element表格使用暗黑科技风格 */
.el-table,
.el-table__header-wrapper,
.el-table__body-wrapper,
.el-table__empty-block {
  background-color: var(--bg-dark) !important;
}

.el-table {
  --el-table-border-color: var(--border-color);
  --el-table-header-bg-color: var(--bg-medium);
  --el-table-row-hover-bg-color: color-mix(in srgb, var(--bg-light), var(--accent-color) 5%);
  --el-table-current-row-bg-color: color-mix(in srgb, var(--bg-light), var(--accent-color) 10%);
  
  border: 1px solid var(--border-color);
  box-shadow: 
    0 0 10px rgba(0, 184, 255, 0.1),
    inset 0 0 15px rgba(0, 184, 255, 0.05);
}

/* 上传弹框表格正文优化 */
.el-dialog .el-table__body-wrapper,
.el-dialog .el-table td {
  background: linear-gradient(135deg, #0a0e17, #0f1524) !important;
  border-bottom: 1px solid var(--border-color) !important;
}

.el-dialog .el-table tr:hover td {
  background: linear-gradient(135deg, #141a2a, #1a2238) !important;
}

.el-dialog .el-table {
  box-shadow: 
    inset 0 0 15px rgba(0, 184, 255, 0.1),
    0 0 10px rgba(0, 184, 255, 0.2);
}

/* 知识库管理表格正文优化 */
.knowledge-management .el-table__body-wrapper,
.knowledge-management .el-table td {
  background: linear-gradient(135deg, #0a0e17, #141a2a) !important;
  border-bottom: 1px solid var(--border-color) !important;
}

.knowledge-management .el-table tr:hover td {
  background: linear-gradient(135deg, #1e2638, #242e4a) !important;
}

/* 左侧文件列表表格正文优化 */
.sidebar .el-table__body-wrapper,
.sidebar .el-table td {
  background: linear-gradient(to right, #0a0e17, #141a2a) !important;
  border-bottom: 1px solid var(--border-color) !important;
}

.sidebar .el-table tr:hover td {
  background: linear-gradient(to right, #1e2638, #283250) !important;
}

/* 左侧文件列表特殊样式 */
.knowledge-list .el-table {
  background: linear-gradient(to bottom, var(--bg-medium), var(--bg-dark)) !important;
}

/* 增强表头科技感 */
.el-table th {
  font-weight: 600;
  letter-spacing: 0.5px;
  text-shadow: 0 0 5px var(--accent-glow);
}

/* 增强行悬停效果 */
.el-table tr:hover td {
  transition: all 0.2s ease-out;
}

/* 强化所有表头样式 */
.el-table th {
  background: linear-gradient(to bottom, var(--bg-medium), var(--bg-dark)) !important;
  color: var(--accent-color) !important;
  font-weight: 600;
  text-shadow: 0 0 5px var(--accent-glow);
  border-bottom: 1px solid var(--accent-color) !important;
}

/* 增强所有单元格效果 */
.el-table td {
  background-color: var(--bg-dark) !important;
  transition: all 0.3s;
  position: relative;
  border-bottom: 1px solid var(--border-color) !important;
}

/* 弹框表格特殊样式 */
.el-dialog .el-table th,
.el-dialog .el-table td {
  background-color: var(--bg-dark) !important;
}

/* 添加单元格底部光效 */
.el-table td::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent-color), transparent);
  opacity: 0.1;
}

/* 当前行高亮效果 */
.el-table__body tr.current-row td {
  background-color: var(--el-table-current-row-bg-color) !important;
}

/* 添加科技感滚动条 */
.document-list .el-scrollbar__thumb {
  background-color: var(--accent-color);
  opacity: 0.5;
}

.document-list .el-scrollbar__thumb:hover {
  opacity: 0.8;
  box-shadow: 0 0 10px var(--accent-color);
}

.main-content {
  flex: 1;
  overflow: auto;
  position: relative;
  z-index: 1;
}

.document-count {
  margin-left: 8px;
  font-size: 13px;
  color: var(--text-secondary);
  padding-right: 8px;
}
.document-count::after {
  content: attr(data-count);
  font-weight: bold;
  font-size: 14px;
}

.knowledge-item {
  display: flex;
  align-items: center;
  width: 100%;
}

.document-count {
  margin-left: auto;
  padding-right: 8px;
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

.el-menu-item * {
  color: var(--text-primary);
}

.el-menu-item.is-active {
  background: linear-gradient(90deg, var(--primary-dark), transparent);
  border-left: 3px solid var(--accent-color);
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.2);
}

.el-menu-item:hover {
  background-color: var(--bg-light);
}

/* 知识库列表暗色风格 */
.knowledge-list .el-menu {
  --el-menu-bg-color: transparent;
  --el-menu-text-color: var(--text-primary);
  --el-menu-hover-bg-color: var(--bg-light);
  --el-menu-active-color: var(--accent-color);
}

.knowledge-list .el-menu-item.is-active {
  background: linear-gradient(90deg, var(--primary-dark), transparent) !important;
}

/* 添加按钮发光效果 */
.el-button--primary {
  position: relative;
  overflow: hidden;
}

.el-button--danger {
  background: linear-gradient(145deg, #ff4d4d, #cc0000);
  border: none;
  color: white !important;
}

.el-button--danger:hover {
  background: linear-gradient(145deg, #ff6666, #e60000);
  box-shadow: 0 0 10px rgba(255, 0, 0, 0.3);
}

.el-button--primary::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(0, 184, 255, 0.1), transparent);
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
@media (max-width: 768px) {
  .document-list .el-table {
    font-size: 14px;
  }
}

</style>