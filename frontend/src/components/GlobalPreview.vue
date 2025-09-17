<template>
  <el-dialog
    v-model="visible"
    width="90%"
    top="5vh"
    :style="{ 'max-height': '85vh' }"
    destroy-on-close
    @closed="handleClose"
  >
    <template #header>
      <div class="dialog-header">
        <span class="dialog-title">预览 - {{ currentFile?.name }}</span>
        <div v-if="isPdf" class="pdf-controls">
          <el-radio-group v-model="viewMode" size="small">
            <el-radio-button label="original">原文</el-radio-button>
            <el-radio-button label="annotated">批注</el-radio-button>
          </el-radio-group>
        </div>
      </div>
    </template>
    <FilePreview :file="displayFile" :key="displayFile?.path" class="sidebar-preview" />
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import FilePreview from './FilePreview.vue'

const visible = ref(false)
const currentFile = ref(null)
const viewMode = ref('original') // 默认显示原文

// 判断当前文件是否为PDF
const isPdf = computed(() => {
  if (!currentFile.value?.name) return false
  return currentFile.value.name.toLowerCase().endsWith('.pdf')
})

// 根据当前模式决定显示的文件
const displayFile = computed(() => {
  if (!currentFile.value) return null
  
  // 如果不是PDF或者是原文模式，直接返回当前文件
  if (!isPdf.value || viewMode.value === 'original') {
    return currentFile.value
  }
  
  // 批注模式：使用savedName构建批注路径
  const originalPath = currentFile.value.path
  const savedName = currentFile.value.savedName || currentFile.value.name
  const nameWithoutExt = savedName.substring(0, savedName.lastIndexOf('.'))
  const annotatedName = `${nameWithoutExt}_annotated.pdf`
  
  // 构建批注文件的API路径
  let annotatedPath = originalPath.replace(
    savedName.replace(/\s/g, '%20'),
    annotatedName.replace(/\s/g, '%20')
  )
  
  // 确保路径以/api/uploads开头
  if (!annotatedPath.startsWith('/api/uploads/')) {
    annotatedPath = `/api/uploads/${annotatedName}`
  }
  
  return {
    ...currentFile.value,
    name: annotatedName,
    path: annotatedPath
  }
})

const open = (file) => {
  currentFile.value = file
  viewMode.value = 'original' // 每次打开默认显示原文
  visible.value = true
}

const handleClose = () => {
  currentFile.value = null
}

defineExpose({
  open
})
</script>

<style scoped>
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
</style>