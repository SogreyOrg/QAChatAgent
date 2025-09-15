import { createApp } from 'vue'
import GlobalPreview from '@/components/GlobalPreview.vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
// 先导入自定义主题，再导入Element Plus样式
import './assets/element-theme.scss'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 注册全局预览组件
const preview = createApp(GlobalPreview)
const previewEl = document.createElement('div')
previewEl.id = 'global-preview'
document.body.appendChild(previewEl)
preview.mount('#global-preview')

app.mount('#app')

// 添加全局预览方法
app.config.globalProperties.$preview = (file) => {
  const previewInstance = document.getElementById('global-preview').__vue_app__
  previewInstance._instance.exposed.open(file)
}
