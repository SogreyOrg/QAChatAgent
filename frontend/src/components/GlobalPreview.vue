<template>
  <el-dialog
    v-model="visible"
    :title="`预览 - ${currentFile?.name}`"
    width="90%"
    top="5vh"
    :style="{ 'max-height': '85vh' }"
    destroy-on-close
    @closed="handleClose"
  >
    <FilePreview :file="currentFile" class="sidebar-preview" />
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import FilePreview from './FilePreview.vue'

const visible = ref(false)
const currentFile = ref(null)

const open = (file) => {
  currentFile.value = file
  visible.value = true
}

const handleClose = () => {
  currentFile.value = null
}

defineExpose({
  open
})
</script>