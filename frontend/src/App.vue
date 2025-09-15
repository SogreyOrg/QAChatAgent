<script setup>
import { ref, getCurrentInstance } from 'vue'
import MainLayout from '@/components/layout/MainLayout.vue'
import GlobalPreview from '@/components/GlobalPreview.vue'

const globalPreviewRef = ref(null)

// 设置全局预览方法
const instance = getCurrentInstance()
if (instance?.appContext?.app) {
  instance.appContext.app.config.globalProperties.$preview = (document) => {
    globalPreviewRef.value?.open(document)
  }
}

const handlePreview = (document) => {
  globalPreviewRef.value?.open(document)
}
</script>

<template>
  <MainLayout @preview-document="handlePreview">
    <router-view />
  </MainLayout>
  <GlobalPreview ref="globalPreviewRef" />
</template>

<style>
#app {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}
</style>
