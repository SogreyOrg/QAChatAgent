<template>
  <div class="file-preview">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <p>正在加载文件预览...</p>
    </div>
    
    <!-- 错误状态 -->
    <div v-else-if="error" class="error-container">
      <el-icon class="error-icon"><WarningFilled /></el-icon>
      <p>{{ error }}</p>
    </div>
    
    <!-- 图片预览 -->
    <div v-else-if="isImage" class="image-preview">
      <img :src="fileUrl" :alt="fileName" @error="handleImageError" />
    </div>
    
    <!-- PDF预览 -->
    <div v-else-if="isPdf" class="pdf-preview">
      <iframe
        :src="pdfViewerUrl"
        width="100%"
        height="100%"
        style="border: none;"
        @load="pdfLoaded"
        @error="handlePdfError"
        allow="fullscreen"
      />
      <div v-if="!loading && error" class="pdf-fallback">
        <p>PDF预览加载失败，请<a :href="fileUrl" target="_blank">点击这里</a>直接查看</p>
      </div>
    </div>
    
    <!-- Markdown预览 -->
    <div v-else-if="isMarkdown" class="markdown-preview" v-html="renderedMarkdown"></div>
    
    <!-- 文本预览 -->
    <div v-else-if="isText" class="text-preview">
      <pre><code>{{ fileContent }}</code></pre>
    </div>
    
    <!-- 不支持的文件类型 -->
    <div v-else class="unsupported-container">
      <el-icon class="unsupported-icon"><DocumentDelete /></el-icon>
      <p>不支持预览此类型的文件</p>
      <el-button type="primary" size="small" @click="downloadFile">
        <el-icon><Download /></el-icon>
        下载文件
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { marked } from 'marked'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Loading, WarningFilled, DocumentDelete, Download } from '@element-plus/icons-vue'
import hljs from 'highlight.js'
import 'highlight.js/styles/atom-one-dark.css'

const props = defineProps({
  file: {
    type: Object,
    required: true
  }
})
console.log('预览组件props:', props)
// 加载状态
const loading = ref(true)
const error = ref(null)
const fileContent = ref('')
const renderedMarkdown = ref('')

// PDF查看器URL
const pdfViewerUrl = computed(() => {
  if (!props.file?.path) return ''
  
  // 处理路径（与fileUrl相同的逻辑）
  let path = props.file.path
  if (!path.startsWith('http://') && !path.startsWith('https://')) {
    if (path.startsWith('/api/uploads')) {
      path = `http://localhost:8000${path}`
    }
  }
  
  // 添加PDF查看器参数
  return `${path}#toolbar=0&navpanes=0&scrollbar=0&zoom=100`
})

// 文件URL
const fileUrl = computed(() => {
  if (!props.file) return ''
  console.log('预览文件信息:', props.file)
  
  // 如果path已经是完整URL，直接返回
  if (props.file.path?.startsWith('http://') || props.file.path?.startsWith('https://')) {
    return props.file.path
  }
  
  // 如果path是API上传路径，添加主机地址
  if (props.file.path?.startsWith('/api/uploads')) {
    return `http://localhost:8000${props.file.path}`
  }
  
  // 其他情况直接返回path（假设已经是完整URL）
  return props.file.path || ''
})

// 文件名
const fileName = computed(() => props.file?.name || '')

// 文件扩展名
const fileExtension = computed(() => {
  if (!fileName.value) return ''
  const parts = fileName.value.split('.')
  return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : ''
})

// 判断文件类型
const isImage = computed(() => {
  const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
  return imageExtensions.includes(fileExtension.value)
})

const isPdf = computed(() => fileExtension.value === 'pdf')

const isMarkdown = computed(() => {
  const mdExtensions = ['md', 'markdown']
  return mdExtensions.includes(fileExtension.value)
})

const isText = computed(() => {
  const textExtensions = ['txt', 'json', 'xml', 'csv', 'js', 'ts', 'html', 'css', 'py', 'java', 'c', 'cpp', 'h', 'sh', 'bat', 'ps1']
  return textExtensions.includes(fileExtension.value)
})

// PDF加载完成回调
const pdfLoaded = () => {
  console.log('PDF加载完成')
  loading.value = false
}

// PDF加载错误处理
const handlePdfError = (err) => {
  console.error('PDF加载错误:', err)
  error.value = `PDF加载失败: ${err.message}`
  loading.value = false
}

// 图片加载错误处理
const handleImageError = () => {
  error.value = '图片加载失败'
  loading.value = false
}

// 配置marked
marked.setOptions({
  highlight: function(code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
    return hljs.highlight(code, { language }).value;
  },
  langPrefix: 'hljs language-',
  gfm: true,
  breaks: true
})

// 加载文件内容
const loadFileContent = async () => {
  if (!props.file) return
  
  loading.value = true
  error.value = null
  
  try {
    console.log('开始加载文件:', props.file.name)
    console.log('文件URL:', fileUrl.value)
    
    if (isImage.value) {
      loading.value = false
      return
    }
    
    if (isPdf.value) {
      loading.value = false
      return
    }
    
    if (isMarkdown.value || isText.value) {
      const response = await axios.get(fileUrl.value)
      fileContent.value = response.data
      
      if (isMarkdown.value) {
        renderedMarkdown.value = marked(fileContent.value)
      }
    }
    
    loading.value = false
  } catch (err) {
    console.error('加载文件内容失败:', err)
    error.value = `加载文件内容失败: ${err.message}`
    loading.value = false
  }
}

// 下载文件
const downloadFile = () => {
  if (!fileUrl.value) {
    ElMessage.error('文件URL不可用')
    return
  }
  
  const link = document.createElement('a')
  link.href = fileUrl.value
  link.download = fileName.value
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// 监听文件变化
watch(() => props.file, () => {
  loadFileContent()
}, { deep: true })

// 组件挂载时加载文件
onMounted(() => {
  loadFileContent()
})
</script>

<style scoped>
.file-preview {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden; /* 隐藏外层滚动条 */
}

.loading-container,
.error-container,
.unsupported-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  width: 100%;
  color: var(--text-secondary);
}

.loading-icon {
  font-size: 48px;
  animation: rotate 2s linear infinite;
  margin-bottom: 16px;
  color: var(--accent-color);
}

.error-icon,
.unsupported-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: #f56c6c;
}

/* 通用预览样式 */
.image-preview {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
}

.image-preview img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.pdf-preview {
  width: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.pdf-preview iframe {
  flex: 1;
  width: 100%;
  height: 100%;
  border: none;
}

.markdown-preview,
.text-preview {
  width: 100%;
  overflow: auto;
  padding: 20px;
  background-color: var(--bg-light);
  color: var(--text-primary);
  line-height: 1.6;
  text-align: left;
}

/* 左侧区域预览特殊样式 */
.sidebar-preview .image-preview,
.sidebar-preview .pdf-preview,
.sidebar-preview .markdown-preview,
.sidebar-preview .text-preview {
  height: calc(85vh - 100px); /* 适配85%高度的浮窗 */
}

/* 知识库管理预览样式 */
.knowledge-preview .image-preview,
.knowledge-preview .pdf-preview,
.knowledge-preview .markdown-preview,
.knowledge-preview .text-preview {
  height: calc(100vh - 120px); /* 原始高度 */
}

.text-preview pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.text-preview code {
  font-family: 'Courier New', Courier, monospace;
  color: var(--text-primary);
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Markdown样式 */
:deep(.markdown-preview h1) {
  font-size: 2em;
  margin-top: 0.67em;
  margin-bottom: 0.67em;
  color: var(--accent-color);
}

:deep(.markdown-preview h2) {
  font-size: 1.5em;
  margin-top: 0.83em;
  margin-bottom: 0.83em;
  color: var(--accent-color);
}

:deep(.markdown-preview h3) {
  font-size: 1.17em;
  margin-top: 1em;
  margin-bottom: 1em;
}

:deep(.markdown-preview h4) {
  font-size: 1em;
  margin-top: 1.33em;
  margin-bottom: 1.33em;
}

:deep(.markdown-preview p) {
  margin-top: 1em;
  margin-bottom: 1em;
  text-align: left; /* 段落左对齐 */
}

:deep(.markdown-preview a) {
  color: var(--accent-color);
  text-decoration: none;
}

:deep(.markdown-preview a:hover) {
  text-decoration: underline;
}

:deep(.markdown-preview code) {
  font-family: 'Courier New', Courier, monospace;
  background-color: var(--bg-medium);
  padding: 2px 4px;
  border-radius: 4px;
}

:deep(.markdown-preview pre) {
  background-color: var(--bg-medium);
  padding: 16px;
  border-radius: 4px;
  overflow: auto;
  text-align: start; /* 代码块左对齐 */
}

:deep(.markdown-preview table) {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
}

:deep(.markdown-preview th),
:deep(.markdown-preview td) {
  border: 1px solid var(--border-color);
  padding: 8px;
  text-align: left;
}

:deep(.markdown-preview th) {
  background-color: var(--bg-medium);
}

:deep(.markdown-preview tr:nth-child(even)) {
  background-color: var(--bg-light);
}

:deep(.markdown-preview blockquote) {
  border-left: 4px solid var(--accent-color);
  margin: 16px 0;
  padding: 8px 16px;
  background-color: var(--bg-medium);
}

:deep(.markdown-preview img) {
  max-width: 100%;
}

:deep(.markdown-preview ul),
:deep(.markdown-preview ol) {
  padding-left: 20px;
  text-align: start; /* 列表左对齐 */
}
</style>