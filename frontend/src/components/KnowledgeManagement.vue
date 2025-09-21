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
  
  <!-- 添加知识库创建对话框 -->
  <el-dialog
    v-model="kbDialogVisible"
    title="新建知识库"
    width="500px"
  >
    <el-form :model="kbForm" label-width="100px">
      <el-form-item label="知识库名称" required>
        <el-input 
          v-model="kbForm.name" 
          placeholder="请输入知识库名称"
        />
      </el-form-item>
      <el-form-item label="知识库描述">
        <el-input
          v-model="kbForm.description"
          type="textarea"
          :rows="3"
          placeholder="请输入知识库描述（可选）"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="kbDialogVisible = false">取消</el-button>
      <el-button 
        type="primary" 
        @click="handleCreateKb"
      >
        创建
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ArrowLeft, Plus, Upload, Delete } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { useKnowledgeStore } from '@/stores/knowledge'
import { ElMessageBox, ElMessage } from 'element-plus'

const router = useRouter()
const knowledgeStore = useKnowledgeStore()

// 添加对话框相关的响应式数据
const kbDialogVisible = ref(false)
const kbForm = ref({
  name: '',
  description: ''
})

const createNewKnowledgeBase = async () => {
  try {
    console.log('开始创建新知识库流程');
    // 显示对话框而不是简单的prompt
    kbDialogVisible.value = true;
  } catch (error) {
    console.error('打开知识库创建对话框出错:', error);
  }
}

// 添加知识库创建处理方法
const handleCreateKb = async () => {
  try {
    if (!kbForm.value.name.trim()) {
      ElMessage.warning('请输入知识库名称');
      return;
    }
    
    console.log(`用户输入的知识库名称: ${kbForm.value.name}, 描述: ${kbForm.value.description}`);
    
    const newKnowledgeBase = await knowledgeStore.createKnowledgeBase(
      kbForm.value.name, 
      kbForm.value.description
    );
    
    console.log('知识库创建结果:', newKnowledgeBase);
    
    if (newKnowledgeBase) {
      kbDialogVisible.value = false;
      // 创建成功后自动选中新创建的知识库
      knowledgeStore.activeKnowledgeBaseId = newKnowledgeBase.id;
      // 重置表单
      ElMessage.success(`知识库 "${kbForm.value.name}" 创建成功`);
      kbForm.value = { name: '', description: '' };
    } else {
      ElMessage.error('创建知识库失败，请稍后重试');
    }
  } catch (error) {
    console.error('创建知识库失败:', error);
    ElMessage.error(`创建知识库失败: ${error.message || '未知错误'}`);
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