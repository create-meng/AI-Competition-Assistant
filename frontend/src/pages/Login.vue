<template>
  <div class="login-container">
    <div class="login-wrapper">
      <!-- 左侧品牌区域 -->
      <div class="brand-section">
        <div class="brand-content">
          <div class="brand-logo">
            <div class="logo-icon">🎯</div>
            <h1 class="brand-title">AI竞赛助手</h1>
          </div>
          <p class="brand-subtitle">智能竞赛信息提取与管理平台</p>
          <div class="brand-features">
            <div class="feature-item">
              <div class="feature-icon">🤖</div>
              <span>AI智能提取</span>
            </div>
            <div class="feature-item">
              <div class="feature-icon">🎯</div>
              <span>角色智能跳转</span>
            </div>
            <div class="feature-item">
              <div class="feature-icon">📊</div>
              <span>知识图谱可视化</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧登录表单 -->
      <div class="form-section">
        <div class="form-container">
          <div class="form-header">
            <h2 class="form-title">欢迎回来</h2>
            <p class="form-subtitle">登录您的账户以继续使用</p>
          </div>

          <!-- 错误提示 -->
          <div v-if="errorMessage" class="error-alert">
            <div class="error-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="15" y1="9" x2="9" y2="15"></line>
                <line x1="9" y1="9" x2="15" y2="15"></line>
              </svg>
            </div>
            <div class="error-content">
              <div class="error-title">登录失败</div>
              <div class="error-message">{{ errorMessage }}</div>
            </div>
            <button class="error-close" @click="clearError">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>

          <!-- 成功提示 -->
          <div v-if="successMessage" class="success-alert">
            <div class="success-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
              </svg>
            </div>
            <div class="success-message">{{ successMessage }}</div>
          </div>

          <!-- 登录表单 -->
          <form @submit.prevent="handleLogin" class="login-form">
            <div class="form-group">
              <label class="form-label">用户名</label>
              <div class="input-wrapper">
                <div class="input-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                  </svg>
                </div>
                <input
                  v-model="form.username"
                  type="text"
                  placeholder="请输入用户名"
                  required
                  class="form-input"
                  :class="{ 'input-error': fieldErrors.username }"
                  name="username"
                  autocomplete="username"
                />
              </div>
              <span v-if="fieldErrors.username" class="field-error">{{ fieldErrors.username }}</span>
            </div>

            <div class="form-group">
              <label class="form-label">密码</label>
              <div class="input-wrapper">
                <div class="input-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                    <circle cx="12" cy="16" r="1"></circle>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                  </svg>
                </div>
                <input
                  v-model="form.password"
                  type="password"
                  placeholder="请输入密码"
                  required
                  class="form-input"
                  :class="{ 'input-error': fieldErrors.password }"
                  name="password"
                  autocomplete="current-password"
                />
              </div>
              <span v-if="fieldErrors.password" class="field-error">{{ fieldErrors.password }}</span>
            </div>

            <button
              type="submit"
              :disabled="loading"
              class="login-btn"
            >
              <span v-if="!loading">登录</span>
              <span v-else class="loading-content">
                <div class="loading-spinner"></div>
                登录中...
              </span>
            </button>
          </form>

          <!-- 底部链接 -->
          <div class="form-footer">
            <span class="footer-text">还没有账号？</span>
            <router-link to="/register" class="footer-link">立即注册</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '@/api'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const fieldErrors = reactive({
  username: '',
  password: ''
})

const form = reactive({
  username: '',
  password: ''
})

const DRAFT_KEY = 'login_form_draft'

onMounted(() => {
  try {
    const draftRaw = sessionStorage.getItem(DRAFT_KEY)
    if (draftRaw) {
      const draft = JSON.parse(draftRaw)
      if (draft && typeof draft === 'object') {
        if (typeof draft.username === 'string') form.username = draft.username
        // 出于安全考虑，不从存储恢复密码
      }
    }
  } catch {}
})

watch(
  () => ({ username: form.username }),
  (val) => {
    try {
      sessionStorage.setItem(DRAFT_KEY, JSON.stringify(val))
    } catch {}
  },
  { deep: true }
)

const clearError = () => {
  errorMessage.value = ''
  fieldErrors.username = ''
  fieldErrors.password = ''
}

const clearSuccess = () => {
  successMessage.value = ''
}

const handleLogin = async () => {
  // 清除之前的错误
  clearError()
  clearSuccess()
  
  // 前端验证
  let hasError = false
  
  if (!form.username) {
    fieldErrors.username = '请输入用户名'
    hasError = true
  }
  
  if (!form.password) {
    fieldErrors.password = '请输入密码'
    hasError = true
  }
  
  if (hasError) {
    errorMessage.value = '请填写完整的登录信息'
    return
  }
  
  loading.value = true
  
  try {
    console.log('开始登录...', form)
    const response = await authAPI.login(form)
    console.log('登录响应:', response)
    
    const res = response.data
    
    if (res.status === 'success' && res.data) {
      // 保存token和用户信息
      userStore.setToken(res.data.access_token)
      userStore.setUser(res.data.user)
      
      // 显示成功消息
      successMessage.value = '登录成功！正在跳转...'
      
      // 延迟跳转
      setTimeout(() => {
        // 成功后清理草稿
        try { sessionStorage.removeItem(DRAFT_KEY) } catch {}
        router.push('/home')
      }, 1000)
    } else {
      errorMessage.value = res.message || '登录失败，请重试'
    }
  } catch (error) {
    console.error('登录失败:', error)
    console.error('错误详情:', error.response)
    
    // 提取错误消息
    let message = '登录失败，请检查网络连接'
    
    if (error.response) {
      const data = error.response.data
      
      // 处理不同的错误响应格式
      if (typeof data === 'string') {
        message = data
      } else if (data && data.detail) {
        message = data.detail
      } else if (data && data.message) {
        message = data.message
      }
      
      // 根据状态码和错误信息设置字段错误
      if (error.response.status === 401) {
        if (message.includes('用户名不存在')) {
          fieldErrors.username = '用户名不存在'
          message = '用户名不存在，请先注册'
        } else if (message.includes('密码错误')) {
          fieldErrors.password = '密码错误'
          message = '密码错误，请重新输入'
        }
      } else if (error.response.status === 500) {
        message = '服务器错误，请稍后再试'
      }
    } else if (error.message) {
      message = error.message
    }
    
    errorMessage.value = message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  background: var(--bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-6);
}

.login-wrapper {
  width: 100%;
  max-width: 1000px;
  background: var(--bg-primary);
  border-radius: var(--radius-3xl);
  box-shadow: var(--shadow-2xl);
  overflow: hidden;
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 600px;
}

/* 左侧品牌区域 */
.brand-section {
  background: var(--gradient-hero);
  padding: var(--spacing-12);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.brand-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 20%, rgba(14, 165, 233, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(6, 182, 212, 0.1) 0%, transparent 50%);
  pointer-events: none;
}

.brand-content {
  text-align: center;
  position: relative;
  z-index: 1;
}

.brand-logo {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-8);
}

.logo-icon {
  font-size: 48px;
}

.brand-title {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  background: var(--gradient-text);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

.brand-subtitle {
  font-size: var(--text-lg);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-8);
  font-weight: var(--font-medium);
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.feature-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3) var(--spacing-4);
  background: var(--bg-glass);
  border-radius: var(--radius-lg);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-light);
}

.feature-icon {
  font-size: 20px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}

.feature-item span {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-primary);
}

/* 右侧表单区域 */
.form-section {
  padding: var(--spacing-12);
  display: flex;
  align-items: center;
  justify-content: center;
}

.form-container {
  width: 100%;
  max-width: 400px;
}

.form-header {
  text-align: center;
  margin-bottom: var(--spacing-8);
}

.form-title {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-2);
}

.form-subtitle {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

/* 错误和成功提示 */
.error-alert,
.success-alert {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  padding: var(--spacing-4);
  border-radius: var(--radius-lg);
  margin-bottom: var(--spacing-6);
  animation: slideUp 0.3s ease;
}

.error-alert {
  background: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.success-alert {
  background: rgba(16, 185, 129, 0.05);
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.error-icon {
  color: var(--danger-color);
  flex-shrink: 0;
}

.success-icon {
  color: var(--success-color);
  flex-shrink: 0;
}

.error-content {
  flex: 1;
}

.error-title {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--danger-color);
  margin-bottom: var(--spacing-1);
}

.error-message {
  font-size: var(--text-sm);
  color: var(--danger-dark);
  line-height: var(--leading-normal);
}

.success-message {
  font-size: var(--text-sm);
  color: var(--success-dark);
  font-weight: var(--font-medium);
}

.error-close {
  background: none;
  border: none;
  color: var(--danger-color);
  cursor: pointer;
  padding: var(--spacing-1);
  border-radius: var(--radius-sm);
  transition: background-color 0.2s ease;
}

.error-close:hover {
  background: rgba(239, 68, 68, 0.1);
}

/* 表单样式 */
.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-6);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.form-label {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.input-wrapper {
  position: relative;
}

.input-icon {
  position: absolute;
  left: var(--spacing-3);
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-quaternary);
  z-index: 1;
}

.form-input {
  width: 100%;
  padding: var(--spacing-3) var(--spacing-3) var(--spacing-3) var(--spacing-10);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  color: var(--text-primary);
  transition: all 0.2s ease;
}

.form-input:focus {
  outline: none;
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
}

.form-input::placeholder {
  color: var(--text-quaternary);
}

.form-input.input-error {
  border-color: var(--danger-color);
  background: rgba(239, 68, 68, 0.02);
}

.form-input.input-error:focus {
  border-color: var(--danger-color);
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

.field-error {
  font-size: var(--text-xs);
  color: var(--danger-color);
  font-weight: var(--font-medium);
}

/* 登录按钮 */
.login-btn {
  width: 100%;
  padding: var(--spacing-4);
  background: var(--gradient-primary);
  color: white;
  border: none;
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.login-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.login-btn:hover::before {
  left: 100%;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-colored);
}

.login-btn:active:not(:disabled) {
  transform: translateY(0);
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.loading-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-2);
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* 底部链接 */
.form-footer {
  text-align: center;
  margin-top: var(--spacing-6);
  padding-top: var(--spacing-6);
  border-top: 1px solid var(--border-light);
}

.footer-text {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.footer-link {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--primary-color);
  text-decoration: none;
  margin-left: var(--spacing-2);
  transition: color 0.2s ease;
}

.footer-link:hover {
  color: var(--primary-dark);
  text-decoration: underline;
}

/* 动画 */
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-wrapper {
    grid-template-columns: 1fr;
    max-width: 500px;
  }

  .brand-section {
    padding: var(--spacing-8);
    min-height: 300px;
  }

  .form-section {
    padding: var(--spacing-8);
  }

  .brand-features {
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: center;
  }

  .feature-item {
    flex: 1;
    min-width: 120px;
  }
}

@media (max-width: 480px) {
  .login-container {
    padding: var(--spacing-4);
  }

  .brand-section,
  .form-section {
    padding: var(--spacing-6);
  }

  .brand-title {
    font-size: var(--text-2xl);
  }

  .form-title {
    font-size: var(--text-xl);
  }

  .brand-features {
    flex-direction: column;
  }
}
</style>