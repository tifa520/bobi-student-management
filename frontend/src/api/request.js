import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    const sessionId = localStorage.getItem('enroll-session')
    if (sessionId) {
      config.headers['enroll-session'] = sessionId
    }
    const accessToken = localStorage.getItem('access_token')
    if (accessToken) {
      config.headers['Authorization'] = `Bearer ${accessToken}`
    }
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now()
      }
    }
    return config
  },
  error => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    const data = response.data
    if (data.code && data.code !== 0) {
      if (data.code === 401) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login'
        }
        return Promise.reject(new Error(data.message || '未授权，请重新登录'))
      }
      ElMessage.error(data.message || '操作失败')
      return Promise.reject(new Error(data.message || '操作失败'))
    }
    return data
  },
  async error => {
    const { response, config } = error
    if (!response) {
      ElMessage.error('网络连接失败，请检查网络后重试')
      return Promise.reject(error)
    }
    // 统一使用 refreshTokenQueue 处理 401，避免与下方队列逻辑冲突
    if (response.status === 401 && !config._retry) {
      config._retry = true
      return refreshTokenRequest(config)
    }
    if (response.status === 403) {
      ElMessage.error('权限不足，无法执行此操作')
      return Promise.reject(error)
    }
    if (response.status === 404) {
      const msg = response.data?.detail || '请求的资源不存在'
      ElMessage.error(msg)
      return Promise.reject(error)
    }
    if (response.status === 500) {
      ElMessage.error('服务器错误，请稍后重试')
      return Promise.reject(error)
    }
    const detail = response.data?.detail
    if (detail) {
      const msg = typeof detail === 'string' ? detail : JSON.stringify(detail)
      ElMessage.error('请求错误：' + msg)
    } else {
      ElMessage.error('请求失败，请稍后重试')
    }
    return Promise.reject(error)
  }
)

// 全局未捕获的 Promise 拒绝处理
window.addEventListener('unhandledrejection', (event) => {
  console.error('未处理的 Promise 拒绝:', event.reason)
  ElMessage.error('发生未知错误，请刷新页面重试')
})

// Token 刷新队列（保持原逻辑）
let isRefreshing = false
let pendingRequests = []

function refreshTokenRequest(failedConfig) {
  if (!isRefreshing) {
    isRefreshing = true
    const refreshToken = localStorage.getItem('refresh_token')
    return axios.post('/api/auth/refresh', { refresh_token: refreshToken })
      .then(res => {
        if (res.data.code === 0) {
          const newAccessToken = res.data.data.access_token
          localStorage.setItem('access_token', newAccessToken)
          pendingRequests.forEach(cb => cb(newAccessToken))
          pendingRequests = []
          failedConfig.headers['Authorization'] = `Bearer ${newAccessToken}`
          return request(failedConfig)
        } else {
          throw new Error('Refresh failed')
        }
      })
      .catch(() => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
        return Promise.reject(new Error('登录已过期'))
      })
      .finally(() => {
        isRefreshing = false
      })
  } else {
    return new Promise(resolve => {
      pendingRequests.push(token => {
        failedConfig.headers['Authorization'] = `Bearer ${token}`
        resolve(request(failedConfig))
      })
    })
  }
}

export default request