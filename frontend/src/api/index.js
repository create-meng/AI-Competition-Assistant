/**
 * API 接口封装
 * 包含请求去重、缓存和错误处理
 */
import axios from 'axios'
import router from '@/router'
import { ElMessage } from 'element-plus'

// in-flight 去重 + 内存缓存（仅 GET）
const inflightGetRequests = new Map()
const requestCache = new Map()
const CACHE_TTL = 60 * 1000

function generateRequestKey(config) {
  const { method, url, params } = config
  return `${method}:${url}:${JSON.stringify(params || {})}`
}

function getFromCache(key) {
  const cached = requestCache.get(key)
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) return cached.data
  requestCache.delete(key)
  return null
}

function setCache(key, response) {
  requestCache.set(key, { data: response, timestamp: Date.now() })
  if (requestCache.size > 100) {
    const firstKey = requestCache.keys().next().value
    requestCache.delete(firstKey)
  }
}

function buildCachedAxiosResponse(config, cachedResponse) {
  // cachedResponse 是一个完整的 axios response
  return {
    ...cachedResponse,
    config,
    request: cachedResponse.request || null
  }
}

function resolveAdapter(adapterCandidate) {
  // Axios v1 可能将 adapter 设为数组/对象/undefined；这里统一解析为可调用函数
  if (typeof adapterCandidate === 'function') return adapterCandidate
  try {
    if (typeof axios.getAdapter === 'function') {
      return axios.getAdapter(adapterCandidate)
    }
  } catch (e) {
    // ignore and fallback below
  }
  if (Array.isArray(adapterCandidate)) {
    const fn = adapterCandidate.find(a => typeof a === 'function')
    if (fn) return fn
  }
  return null
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

    // GET 请求：缓存 & 同飞去重
    if (config.method === 'get') {
      const requestKey = generateRequestKey(config)
      config._requestKey = requestKey

      if (config.useCache !== false) {
        const cached = getFromCache(requestKey)
        if (cached) {
          config.adapter = async () => buildCachedAxiosResponse(config, cached)
          config.__fromCache = true
          return config
        }
      }

      const originalAdapter = resolveAdapter(config.adapter) || resolveAdapter(axios.defaults.adapter)
      if (!originalAdapter) {
        throw new Error('Axios adapter is not available')
      }
      if (!config.skipDedup) {
        config.adapter = async (cfg) => {
          if (inflightGetRequests.has(requestKey)) {
            return inflightGetRequests.get(requestKey)
          }
          const p = Promise.resolve(originalAdapter(cfg))
            .finally(() => {
              inflightGetRequests.delete(requestKey)
            })
          inflightGetRequests.set(requestKey, p)
          return p
        }
      }
    }

    return config
  },
  error => {
    return Promise.reject(error)
  }
)

export function normalizeApiError(err) {
  const status = err?.response?.status ?? null
  const data = err?.response?.data

  let message = ''
  let detail = null

  if (status === 422) {
    const d = data?.detail
    if (Array.isArray(d)) {
      message = '参数校验错误'
      detail = d.map(x => x?.msg).filter(Boolean).join('\n')
    }
  }

  if (!message) {
    message = data?.message || data?.detail || err?.message || '请求失败'
  }

  if (!status) {
    if (err?.code === 'ECONNABORTED' || /timeout/i.test(String(err?.message || ''))) {
      message = '请求超时，请稍后重试'
    } else {
      message = '网络连接失败，请检查网络'
    }
  }

  if (status === 503) {
    message = '服务暂不可用，请稍后重试'
  }

  return {
    status,
    message: String(message || '请求失败'),
    detail,
    url: err?.config?.url || '',
    method: err?.config?.method || '',
  }
}

export function normalizeApiFail(payload) {
  const message = payload?.message || '请求失败'
  return {
    status: null,
    message: String(message || '请求失败'),
    detail: null,
  }
}

export function showApiError(err, options = {}) {
  const norm = err?.normalized || normalizeApiError(err)
  const prefix = options?.prefix ? String(options.prefix) : ''
  const text = prefix ? `${prefix}: ${norm.message}` : norm.message

  if (norm.status === 401) {
    ElMessage.warning(text)
    return norm
  }
  if (norm.status === 403) {
    ElMessage.error(text)
    return norm
  }
  if (norm.status === 422 && norm.detail) {
    ElMessage.error(text + '\n' + norm.detail)
    return norm
  }

  ElMessage.error(text)
  return norm
}

export function showApiFail(payload, options = {}) {
  const norm = normalizeApiFail(payload)
  const prefix = options?.prefix ? String(options.prefix) : ''
  const text = prefix ? `${prefix}: ${norm.message}` : norm.message
  ElMessage.error(text)
  return norm
}

// 响应拦截器
api.interceptors.response.use(
  response => {
    const key = response.config?._requestKey
    if (key) {
      // 只缓存非 adapter（真正网络返回）的响应
      if (response.config.method === 'get' && response.config.useCache !== false && !response.config.__fromCache) {
        setCache(key, response)
      }
      inflightGetRequests.delete(key)
    }
    return response
  },
  error => {
    try {
      error.normalized = normalizeApiError(error)
    } catch (e) {
      // ignore
    }
    const key = error.config?._requestKey
    if (key) inflightGetRequests.delete(key)

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

// 认证相关API
export const authAPI = {
  // 用户注册
  register: (userData) => api.post('/api/v1/auth/register', userData),
  
  // 用户登录
  login: (credentials) => api.post('/api/v1/auth/login', credentials)
}

// AI提取相关API
export const aiAPI = {
  // 获取AI提供商列表
  getProviders: (config = {}) => api.get('/api/v1/ai/providers', config),
  
  // 启动任务式提取
  startJob: (data, config = {}) => api.post('/api/v1/ai/extract/job', data, config),
  // 查询任务进度（禁用缓存，每次都获取最新状态）
  getJob: (jobId, config = {}) => api.get(`/api/v1/ai/extract/jobs/${jobId}`, { ...config, useCache: false, skipDedup: true }),
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
