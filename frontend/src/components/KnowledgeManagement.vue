<template>
  <div class="knowledge-management">
    <div class="management-header">
      <el-button type="text" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h3>知识库管理</h3>
      <el-button 
        type="primary" 
        size="small" 
        @click="createNewKnowledgeBase"
        style="margin-left: auto"
      >
        <el-icon><Plus /></el-icon>
        新建知识库
      </el-button>
    </div>
    
    <router-view />
 
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ArrowLeft, Plus, Upload, Delete } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { useKnowledgeStore } from '@/stores/knowledge'
import { ElMessageBox } from 'element-plus'

const router = useRouter()
const knowledgeStore = useKnowledgeStore()

const createNewKnowledgeBase = async () => {
  try {
    const { value: name } = await ElMessageBox.prompt('请输入知识库名称', '新建知识库', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /\S+/,
      inputErrorMessage: '知识库名称不能为空'
    })
    
    if (name) {
      knowledgeStore.createKnowledgeBase(name)
    }
  } catch (error) {
    console.log('取消创建知识库', error)
  }
}

const activeKnowledgeBaseId = computed(() => knowledgeStore.activeKnowledgeBaseId)

const openUploadDialog = () => {
  // 实现上传文档对话框逻辑
  console.log('打开上传文档对话框')
}

const deleteKnowledgeBase = () => {
  // 直接调用store中的方法，store内部已包含确认对话框和提示
  knowledgeStore.deleteKnowledgeBase(knowledgeStore.activeKnowledgeBaseId)
}

const goBack = () => {
  router.push('/chat')
}
</script>

<style scoped>
.knowledge-management {
  padding: 20px;
  height: 100%;
  position: relative;
}

/* 添加科技感背景 */
.knowledge-management::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    radial-gradient(circle at 25% 25%, rgba(106, 60, 181, 0.05) 0%, transparent 50%),
    radial-gradient(circle at 75% 75%, rgba(0, 184, 255, 0.05) 0%, transparent 50%),
    linear-gradient(rgba(0, 184, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 184, 255, 0.03) 1px, transparent 1px);
  background-size: 100% 100%, 100% 100%, 20px 20px, 20px 20px;
  pointer-events: none;
  z-index: 0;
}

.management-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  gap: 10px;
  position: relative;
  z-index: 1;
  padding: 15px;
  background: linear-gradient(90deg, var(--bg-medium), transparent);
  border-left: 3px solid var(--accent-color);
  border-radius: 4px;
  box-shadow: var(--shadow-sm);
}

.management-header h3 {
  margin: 0 0 0 10px;
  flex-grow: 1;
  color: var(--accent-color);
  text-shadow: 0 0 5px rgba(0, 184, 255, 0.5);
  letter-spacing: 1px;
  font-size: 20px;
}

.management-header .el-button--text {
  color: var(--text-primary);
}

.management-header .el-button--text:hover {
  color: var(--accent-color);
}

/* 添加按钮发光效果 */
.management-header .el-button--primary {
  position: relative;
  overflow: hidden;
}

.management-header .el-button--primary::before {
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

.document-actions {
  margin-bottom: 20px;
  position: relative;
  z-index: 1;
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
</style>