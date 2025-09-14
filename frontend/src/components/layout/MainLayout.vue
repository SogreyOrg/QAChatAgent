【知识库管理】<template>
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
          >
            <el-table-column prop="name" label="文档名称" />
            <el-table-column prop="size" label="大小" width="100" />
            <el-table-column label="操作" width="80">
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
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Setting } from '@element-plus/icons-vue'
import { useKnowledgeStore } from '@/stores/knowledge'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const knowledgeStore = useKnowledgeStore()

const activeKnowledgeBaseId = computed(() => knowledgeStore.activeKnowledgeBaseId)
const knowledgeBases = computed(() => knowledgeStore.knowledgeBases)
const documents = computed(() => knowledgeStore.activeDocuments())

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
      knowledgeStore.createKnowledgeBase(name)
    }
  } catch (error) {
    console.log('取消创建知识库', error)
  }
}

const handleKnowledgeBaseSelect = (knowledgeBaseId) => {
  knowledgeStore.activeKnowledgeBaseId = knowledgeBaseId
}

const deleteDocument = async (documentId) => {
  try {
    await ElMessageBox.confirm('确定要删除此文档吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    knowledgeStore.deleteDocument(knowledgeStore.activeKnowledgeBaseId, documentId)
    ElMessage.success('文档删除成功')
  } catch (error) {
    console.log('取消删除文档', error)
  }
}



const handleDocumentClick = (document) => {
  // 在这里处理文档点击事件，可以打开文档预览或编辑
  console.log('点击文档:', document)
}
</script>

<style scoped>
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

.el-menu-item.is-active {
  background: linear-gradient(90deg, var(--primary-dark), transparent);
  border-left: 3px solid var(--accent-color);
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.2);
}

.el-menu-item:hover {
  background-color: var(--bg-light);
}

/* 添加按钮发光效果 */
.el-button--primary {
  position: relative;
  overflow: hidden;
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
</style>