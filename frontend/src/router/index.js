import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/chat/ChatView.vue'
import KnowledgeManagement from '../components/KnowledgeManagement.vue'
import KnowledgeView from '../views/knowledge/KnowledgeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/chat'
    },
    {
      path: '/chat',
      name: 'chat',
      component: ChatView
    },
    {
      path: '/knowledge',
      component: KnowledgeManagement,
      children: [
        {
          path: '',
          name: 'knowledge',
          component: KnowledgeView
        }
      ]
    }
  ]
})

export default router