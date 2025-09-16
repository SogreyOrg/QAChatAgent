<template>
  <div class="knowledge-view">
    <div class="knowledge-header">
      <h2>{{ activeKnowledgeBase.name }}</h2>
      <p>{{ activeKnowledgeBase.description }}</p>
    </div>

    <div class="document-actions">
      <el-button type="primary" size="small" @click="openUploadDialog">
        <el-icon>
          <Upload />
        </el-icon>
        上传文档
      </el-button>
      <el-button v-if="activeKnowledgeBaseId !== '0'" type="danger" size="small" @click="deleteKnowledgeBase">
        <el-icon>
          <Delete />
        </el-icon>
        删除知识库
      </el-button>
    </div>

    <el-table :data="[{
      id: 'upload',
      name: '添加/上传文件',
      size: '',
      uploadedAt: '',
      isUpload: true
    }].concat(documents)" style="width: 100%" stripe @row-click="handleRowClick">
      <el-table-column prop="name" label="文档名称">
        <template #default="{ row }">
          <span v-if="row.isUpload" style="color: #409EFF; cursor: pointer">
            <el-icon>
              <Upload />
            </el-icon> {{ row.name }}
          </span>
          <span v-else>{{ row.name }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="size" label="大小" width="120">
        <template #default="{ row }">
          {{ row.size ? formatFileSize(row.size) : '' }}
        </template>
      </el-table-column>
      <el-table-column prop="uploadedAt" label="上传时间" width="180">
        <template #default="{ row }">
          {{ formatTime(row.uploadedAt) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <template v-if="!row.isUpload">
            <el-button type="primary" size="small" @click.stop="previewDocument(row)">
              预览
            </el-button>
            <el-button type="danger" size="small" @click.stop="deleteDocument(row.id)">
              删除
            </el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <!-- 上传文档对话框 -->
    <el-dialog v-model="uploadDialogVisible" title="上传文档" width="30%">
      <el-upload class="upload-demo" drag action="" :auto-upload="false" :on-change="handleFileChange"
        :show-file-list="false">
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处或<em>点击上传</em>
        </div>
      </el-upload>

      <div v-if="selectedFile" class="file-info">
        <p>文件名: {{ selectedFile.name }}</p>
        <p>大小: {{ formatFileSize(selectedFile.size) }}</p>
      </div>

      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!selectedFile" @click="uploadDocument">
          上传
        </el-button>
      </template>
    </el-dialog>

    <!-- 文档预览对话框 -->
    <el-dialog v-model="previewDialogVisible" width="80%" top="5vh" destroy-on-close fullscreen>
      <template #header>
        <div class="dialog-header">
          <span class="dialog-title">预览 - {{ previewDocumentName }}</span>
          <div v-if="isPdfPreview" class="pdf-controls">
            <el-radio-group v-model="viewMode" size="small">
              <el-radio-button label="original">原文</el-radio-button>
              <el-radio-button label="annotated">批注</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </template>
      <div class="document-preview">
        <file-preview v-if="displayPreviewDocument" :file="displayPreviewDocument" :key="displayPreviewDocument?.path"
          class="knowledge-preview" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, getCurrentInstance, watch } from 'vue'
import axios from 'axios'
import { ElLoading, ElMessage, ElMessageBox } from 'element-plus'
import { Upload, UploadFilled, Delete, Plus } from '@element-plus/icons-vue'
import { useKnowledgeStore } from '@/stores/knowledge'
import FilePreview from '@/components/FilePreview.vue'

const uploadProgress = ref(0)
const knowledgeStore = useKnowledgeStore()
const uploadDialogVisible = ref(false)
const previewDialogVisible = ref(false)
const selectedFile = ref(null)
const previewDocumentName = ref('')
const previewDocumentData = ref(null)
const viewMode = ref('original') // 默认显示原文

// 判断当前预览文件是否为PDF
const isPdfPreview = computed(() => {
  if (!previewDocumentData.value?.name) return false
  return previewDocumentData.value.name.toLowerCase().endsWith('.pdf')
})

// 根据当前模式决定显示的文件
const displayPreviewDocument = computed(() => {
  if (!previewDocumentData.value) return null

  // 如果不是PDF或者是原文模式，直接返回当前文件
  if (!isPdfPreview.value || viewMode.value === 'original') {
    return previewDocumentData.value
  }

  // 批注模式：构建批注文件路径
  const originalPath = previewDocumentData.value.path
  const originalName = previewDocumentData.value.name

  // 构建批注文件名和路径
  const nameWithoutExt = originalName.substring(0, originalName.lastIndexOf('.'))
  const annotatedName = `${nameWithoutExt}_annotated.pdf`

  // 构建批注文件的路径
  let annotatedPath = originalPath

  // 如果路径包含文件名（通常是这种情况），替换文件名部分
  if (originalPath.includes(previewDocumentData.value.fileKey)) {
    // 假设文件路径中包含fileKey，我们需要构建新的fileKey
    const fileKeyParts = previewDocumentData.value.fileKey.split('.')
    const newFileKey = `${fileKeyParts[0]}_annotated.${fileKeyParts[1]}`
    annotatedPath = originalPath.replace(previewDocumentData.value.fileKey, newFileKey)
  } else {
    // 如果没有fileKey，尝试直接替换文件名
    annotatedPath = originalPath.replace(
      originalName.replace(/\s/g, '%20'), // URL中空格可能被编码为%20
      annotatedName.replace(/\s/g, '%20')
    )
  }

  console.log('原始路径:', originalPath)
  console.log('批注路径:', annotatedPath)

  return {
    ...previewDocumentData.value,
    name: annotatedName,
    path: annotatedPath
  }
})

// 监听预览对话框状态，重置查看模式
watch(previewDialogVisible, (newVal) => {
  if (newVal) {
    viewMode.value = 'original' // 每次打开预览时默认显示原文
  }
})

const activeKnowledgeBase = computed(() => knowledgeStore.activeKnowledgeBase())
const activeKnowledgeBaseId = computed(() => knowledgeStore.activeKnowledgeBaseId)
const documents = computed(() => {
  // 过滤掉空文档列表的初始数据
  const docs = knowledgeStore.activeDocuments()
  return docs
    .filter(doc => doc.id !== '101' && doc.id !== '102' && doc.id !== '103' && doc.id !== '104' && doc.id !== '105')
    .sort((a, b) => new Date(b.uploadedAt) - new Date(a.uploadedAt))
})

const openUploadDialog = () => {
  uploadDialogVisible.value = true
  selectedFile.value = null
}

const deleteKnowledgeBase = () => {
  // 直接调用store中的方法，store内部已包含确认对话框和提示
  knowledgeStore.deleteKnowledgeBase(knowledgeStore.activeKnowledgeBaseId)
}

const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatTime = (timestamp) => {
  if (!timestamp || timestamp === '') return ''
  try {
    return new Date(timestamp).toLocaleString()
  } catch {
    return ''
  }
}

const uploadDocument = async () => {
  if (!selectedFile.value) return

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)

    const response = await axios.post(
      'http://localhost:8000/api/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          uploadProgress.value = Math.round(
            (progressEvent.loaded / progressEvent.total) * 100
          )
        }
      }
    )

    // 保存完整文件信息到知识库
    const documentData = {
      name: response.data.data.originalName,
      path: response.data.data.filePath,
      savedName: response.data.data.savedName,
      fileKey: response.data.data.fileKey,
      downloadUrl: response.data.data.downloadUrl,
      size: response.data.data.size
    }

    await knowledgeStore.uploadDocument(
      knowledgeStore.activeKnowledgeBaseId,
      documentData
    )

    ElMessage.success('文档上传成功')
    uploadDialogVisible.value = false
    uploadProgress.value = 0

  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error(`上传失败: ${error.response?.data?.message || error.message}`)
  }
}

const deleteDocument = async (documentId) => {
  try {
    await ElMessageBox.confirm('确定要删除此文档吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const doc = documents.value.find(d => d.id === documentId)
    if (!doc) throw new Error('文档不存在')

    // 使用fileKey或savedName删除文件
    const fileIdentifier = doc.fileKey || doc.savedName
    if (fileIdentifier) {
      try {
        const encodedName = encodeURIComponent(fileIdentifier)
        await axios.delete(`http://localhost:8000/api/delete/${encodedName}`)
      } catch (error) {
        console.error('文件删除失败:', error)
      }
    }

    // 从知识库删除记录
    await knowledgeStore.deleteDocument(
      knowledgeStore.activeKnowledgeBaseId,
      documentId
    )

    ElMessage.success(doc.fileKey ? '文档和文件删除成功' : '文档记录删除成功')

  } catch (error) {
    console.error('删除失败:', error)
    ElMessage.error(`删除失败: ${error.message}`)
  }
}

const handleRowClick = (row) => {
  if (row.isUpload) {
    openUploadDialog()
  } else {
    previewDocument(row)
  }
}

const previewDocument = (document) => {
  try {
    const instance = getCurrentInstance()
    if (instance && instance.appContext && instance.appContext.app) {
      const app = instance.appContext.app
      if (app.config.globalProperties.$preview) {
        app.config.globalProperties.$preview(document)
        return
      }
    }

    // 备选方案：使用本地预览对话框
    previewDocumentName.value = document.name
    previewDocumentData.value = document
    previewDialogVisible.value = true
  } catch (error) {
    console.error('预览出错:', error)
    // 使用本地预览对话框作为最后保障
    previewDocumentName.value = document.name
    previewDocumentData.value = document
    previewDialogVisible.value = true
  }
}
</script>

<style scoped>
.knowledge-view {
  padding: 20px;
  height: 90%;
  position: relative;
}

.knowledge-view::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    radial-gradient(circle at 25% 25%, rgba(106, 60, 181, 0.05) 0%, transparent 50%),
    radial-gradient(circle at 75% 75%, rgba(0, 184, 255, 0.05) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

.knowledge-header {
  margin-bottom: 20px;
  position: relative;
  z-index: 1;
  padding: 15px;
  background: linear-gradient(90deg, var(--bg-medium), transparent);
  border-left: 3px solid var(--accent-color);
  border-radius: 4px;
  box-shadow: var(--shadow-sm);
}

.knowledge-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: var(--accent-color);
  text-shadow: 0 0 5px rgba(0, 184, 255, 0.5);
  letter-spacing: 1px;
}

.knowledge-header p {
  margin: 0;
  color: var(--text-secondary);
}

.document-actions {
  margin-bottom: 20px;
  position: relative;
  z-index: 1;
  display: flex;
  gap: 10px;
}

.document-actions .el-button {
  position: relative;
  overflow: hidden;
}

.document-actions .el-button--primary::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(0, 184, 255, 0.2), transparent);
  transform: rotate(45deg);
  animation: shine 3s infinite;
}

.document-actions .el-button--danger::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(255, 51, 102, 0.2), transparent);
  transform: rotate(45deg);
  animation: shine 3s infinite;
}

.file-info {
  margin-top: 20px;
  padding: 15px;
  background-color: var(--bg-medium);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
}

.document-preview {
  height: 100%;
  overflow: auto;
  background-color: var(--bg-medium);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 0;
  color: var(--text-primary);
  box-shadow: var(--shadow-md);
  position: relative;
}

.el-table {
  background-color: var(--bg-medium) !important;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  overflow: hidden;
  box-shadow: var(--shadow-md);
  position: relative;
  z-index: 1;
}

.el-table::before {
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
  z-index: -1;
}

.el-table th {
  background-color: var(--bg-light) !important;
  color: var(--accent-color) !important;
  border-bottom: 1px solid var(--border-color) !important;
}

.el-table td {
  border-bottom: 1px solid var(--border-color) !important;
  color: var(--text-primary) !important;
}

.el-table--striped .el-table__body tr.el-table__row--striped td {
  background-color: var(--bg-light) !important;
}

.el-upload {
  border: 1px dashed var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;
}

.el-upload:hover {
  border-color: var(--accent-color);
  box-shadow: 0 0 10px rgba(0, 184, 255, 0.3);
}

.el-upload__text {
  color: var(--text-secondary);
}

.el-upload__text em {
  color: var(--accent-color);
  font-style: normal;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.dialog-title {
  font-size: 18px;
  font-weight: bold;
}

.pdf-controls {
  margin-left: 20px;
}

@keyframes shine {
  0% {
    left: -100%;
  }

  20% {
    left: 100%;
  }

  100% {
    left: 100%;
  }
}
</style>