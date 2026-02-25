/**
 * API 接口封装
 * 包含请求去重、缓存和错误处理
 */
import axios from 'axios'
import router from '@/router'

// 请求去重 Map
const pendingRequests = new Map()

// 简单的内存缓存
const requestCache = new Map()
const CACHE_TTL = 60 * 1000 // 1分钟缓存

// 生成请求唯一键
function generateRequestKey(config) {
  const { method, url, params, data } = config
  return `${method}:${url}:${JSON.stringify(params || {})}:${JSON.stringify(data || {})}`
}

// 检查缓存
function getFromCache(key) {
  const cached = requestCache.get(key)
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data
  }
  requestCache.delete(key)
  return null
}

// 设置缓存
function setCache(key, data) {
  requestCache.set(key, { data, timestamp: Date.now() })
  // 限制缓存大小
  if (requestCache.size > 100) {
    const firstKey = requestCache.keys().next().value
    requestCache.delete(firstKey)
  }
}

// 创建axios实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 60000 // AI请求可能较慢，设置60秒超时
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 从localStorage获取token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // 如果是 FormData（文件上传），必须让浏览器自动设置 multipart 边界
    if (config.data instanceof FormData) {
      // 删除可能遗留的 Content-Type，避免 boundary 丢失
      delete config.headers['Content-Type']
    } else {
      // 其他请求默认为 JSON
      if (!config.headers['Content-Type']) {
        config.headers['Content-Type'] = 'application/json'
      }
    }

    // 请求去重（仅对 GET 请求）
    if (config.method === 'get' && !config.skipDedup) {
      const requestKey = generateRequestKey(config)
      
      // 检查是否有相同的请求正在进行
      if (pendingRequests.has(requestKey)) {
        const controller = new AbortController()
        config.signal = controller.signal
        controller.abort('Duplicate request cancelled')
        return Promise.reject({ isDuplicate: true, key: requestKey })
      }
      
      // 检查缓存
      if (config.useCache !== false) {
        const cached = getFromCache(requestKey)
        if (cached) {
          return Promise.reject({ isCached: true, data: cached })
        }
      }
      
      // 记录请求
      pendingRequests.set(requestKey, true)
      config._requestKey = requestKey
    }

    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    // 清除请求记录
    if (response.config._requestKey) {
      pendingRequests.delete(response.config._requestKey)
      // 缓存成功的 GET 请求
      if (response.config.method === 'get' && response.config.useCache !== false) {
        setCache(response.config._requestKey, response)
      }
    }
    return response
  },
  error => {
    // 处理缓存命中
    if (error.isCached) {
      return Promise.resolve(error.data)
    }
    
    // 处理重复请求
    if (error.isDuplicate) {
      return new Promise((resolve) => {
        // 等待原请求完成
        const checkInterval = setInterval(() => {
          if (!pendingRequests.has(error.key)) {
            clearInterval(checkInterval)
            const cached = getFromCache(error.key)
            if (cached) {
              resolve(cached)
            } else {
              resolve({ data: { status: 'error', message: '请求被取消' } })
            }
          }
        }, 100)
        // 最多等待5秒
        setTimeout(() => {
          clearInterval(checkInterval)
          resolve({ data: { status: 'error', message: '请求超时' } })
        }, 5000)
      })
    }

    // 清除请求记录
    if (error.config?._requestKey) {
      pendingRequests.delete(error.config._requestKey)
    }

    // 处理401未授权，但避免在登录/注册相关请求或已在登录页时触发整页刷新
    if (error.response?.status === 401) {
      const reqUrl = error?.config?.url || ''
      const isAuthRequest = reqUrl.includes('/api/v1/auth/login') ||
        reqUrl.includes('/api/v1/auth/register') ||
        reqUrl.includes('/api/v1/auth/refresh')
      const currentPath = window.location?.pathname || ''
      const isOnAuthPage = currentPath === '/login' || currentPath === '/register'

      if (!isAuthRequest && !isOnAuthPage) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        // 使用前端路由跳转，避免整页刷新导致表单输入丢失
        router.push('/login')
      }
    }
    
    // 处理429速率限制
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after'] || 60
      console.warn(`请求过于频繁，请 ${retryAfter} 秒后重试`)
    }
    
    return Promise.reject(error)
  }
)

// 清除缓存的方法
export function clearApiCache() {
  requestCache.clear()
}

// 清除特定缓存
export function clearCacheByPattern(pattern) {
  for (const key of requestCache.keys()) {
    if (key.includes(pattern)) {
      requestCache.delete(key)
    }
  }
}

// 认证相关API
export const authAPI = {
  // 用户注册
  register: (userData) => api.post('/api/v1/auth/register', userData),
  
  // 用户登录
  login: (credentials) => api.post('/api/v1/auth/login', credentials),
  
  // 获取当前用户信息
  getCurrentUser: () => api.get('/api/v1/auth/me'),
  
  // 刷新token
  refreshToken: (refreshToken) => api.post('/api/v1/auth/refresh', { refresh_token: refreshToken })
}

// AI提取相关API
export const aiAPI = {
  // 获取AI提供商列表
  getProviders: (config = {}) => api.get('/api/v1/ai/providers', config),
  
  // AI智能提取
  extract: (data, config = {}) => api.post('/api/v1/ai/extract', data, config),
  // 启动任务式提取
  startJob: (data, config = {}) => api.post('/api/v1/ai/extract/job', data, config),
  startExtractionJob: (data, config = {}) => api.post('/api/v1/ai/extract/job', data, config),
  // 查询任务进度（禁用缓存，每次都获取最新状态）
  getJob: (jobId, config = {}) => api.get(`/api/v1/ai/extract/jobs/${jobId}`, { ...config, useCache: false, skipDedup: true }),
  getExtractionJobStatus: (jobId, config = {}) => api.get(`/api/v1/ai/extract/jobs/${jobId}`, { ...config, useCache: false, skipDedup: true }),
  // 取消任务
  cancelExtractionJob: (jobId, config = {}) => api.post(`/api/v1/ai/extract/jobs/${jobId}/cancel`, {}, config),
  // 健康检查重试（单个提供商）
  retryProviderHealth: (providerType, config = {}) => api.post(`/api/v1/ai/providers/${providerType}/retry`, {}, config),
  
  // 获取提取结果
  getExtraction: (extractionId, config = {}) => api.get(`/api/v1/ai/extractions/${extractionId}`, config),
  
  // 文件上传
  uploadFile: (formData, config = {}) => api.post('/api/v1/documents/upload', formData, config),

  // 统计提取总数
  getExtractionsCount: (config = {}) => api.get('/api/v1/ai/extractions/count', config)
}

// 竞赛相关API
export const contestAPI = {
  // 获取竞赛列表
  getContests: (params = {}) => api.get('/api/v1/contests/', { params }),
  
  // 获取竞赛详情
  getContest: (contestId) => api.get(`/api/v1/contests/${contestId}`),
  
  // 新增竞赛
  createContest: (payload) => api.post('/api/v1/contests/', payload),

  // 更新竞赛
  updateContest: (contestId, payload) => api.put(`/api/v1/contests/${contestId}`, payload),

  // 角色跳转
  redirectToOfficial: (contestId) => api.get(`/api/v1/contests/${contestId}/redirect`),
  
  // 检查重名竞赛
  checkDuplicate: (name) => api.post('/api/v1/contests/check-duplicate', null, { params: { name } }),
  
  // AI合并竞赛信息（预览）
  mergeContest: (existingId, newData) => api.post('/api/v1/contests/merge', newData, { params: { existing_id: existingId } }),
  
  // 确认合并保存
  confirmMerge: (existingId, mergedData) => api.post('/api/v1/contests/merge/confirm', mergedData, { params: { existing_id: existingId } })
}

export default api
