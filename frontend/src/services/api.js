import axios from 'axios'

// 创建axios实例
const api = axios.create({
  // 根据实际部署情况设置baseURL
  // 开发环境下，通常使用相对路径，由Vite的代理功能转发请求
  baseURL: '',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 可以在这里添加认证信息等
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    // 只返回响应的数据部分
    return response.data
  },
  error => {
    // 处理错误响应
    console.error('API请求错误:', error)
    return Promise.reject(error)
  }
)

export default api