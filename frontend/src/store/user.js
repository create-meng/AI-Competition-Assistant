import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || '')
  const lastActivity = ref(Date.now())

  const isLoggedIn = computed(() => !!token.value)
  const userRole = computed(() => user.value?.role || '')
  const username = computed(() => user.value?.username || '')

  function setUser(userData) {
    user.value = userData
    // 同时保存到 localStorage 以便刷新后恢复
    if (userData) {
      localStorage.setItem('user', JSON.stringify(userData))
    }
  }

  function setToken(tokenValue) {
    token.value = tokenValue
    localStorage.setItem('token', tokenValue)
    updateActivity()
  }

  function logout() {
    user.value = null
    token.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  function updateActivity() {
    lastActivity.value = Date.now()
  }

  // 初始化时从 localStorage 恢复用户信息
  function initFromStorage() {
    const savedUser = localStorage.getItem('user')
    if (savedUser && token.value) {
      try {
        user.value = JSON.parse(savedUser)
      } catch (e) {
        console.warn('Failed to parse saved user:', e)
      }
    }
  }

  // 检查 token 是否可能过期（简单检查）
  function isTokenExpired() {
    // 如果超过 25 分钟没有活动，认为可能过期
    const expireTime = 25 * 60 * 1000
    return Date.now() - lastActivity.value > expireTime
  }

  return {
    user,
    token,
    lastActivity,
    isLoggedIn,
    userRole,
    username,
    setUser,
    setToken,
    logout,
    updateActivity,
    initFromStorage,
    isTokenExpired
  }
})

