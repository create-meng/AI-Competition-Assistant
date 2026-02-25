<template>
  <div class="register-container geometric-bg">
    <div class="register-box card-modern">
      <h1 class="title text-gradient">创建账号</h1>
      <p class="subtitle">加入AI竞赛助手平台</p>
      
      <form @submit.prevent="handleRegister" class="register-form" autocomplete="on">
        <div class="form-row">
          <div class="form-group">
            <label>用户名 <span class="required">*</span></label>
            <input
              v-model="form.username"
              type="text"
              placeholder="请输入用户名"
              required
              class="form-input"
              name="username"
              autocomplete="username"
            />
          </div>
          
          <div class="form-group">
            <label>邮箱</label>
            <input
              v-model="form.email"
              type="email"
              placeholder="请输入邮箱（选填）"
              class="form-input"
              name="email"
              autocomplete="email"
            />
          </div>
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label>密码 <span class="required">*</span></label>
            <input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              required
              class="form-input"
              name="new-password"
              autocomplete="new-password"
            />
          </div>
          
          <div class="form-group">
            <label>确认密码 <span class="required">*</span></label>
            <input
              v-model="form.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              required
              class="form-input"
              name="confirm-password"
              autocomplete="new-password"
            />
          </div>
        </div>
        
        <div class="form-group">
          <label>角色 <span class="required">*</span></label>
          <div class="role-options">
            <div 
              class="role-option" 
              :class="{ active: form.role === 'entrant' }"
              @click="form.role = 'entrant'"
            >
              <div class="role-icon">🎓</div>
              <div class="role-text">参赛者</div>
              <div class="role-desc">参与竞赛项目</div>
            </div>
            <div 
              class="role-option" 
              :class="{ active: form.role === 'teacher' }"
              @click="form.role = 'teacher'"
            >
              <div class="role-icon">👨‍🏫</div>
              <div class="role-text">指导老师</div>
              <div class="role-desc">指导学生参赛</div>
            </div>
          </div>
        </div>
        
        <div class="form-row">
          <div class="form-group">
            <label>学校</label>
            <input
              v-model="form.school"
              type="text"
              placeholder="请输入学校名称（选填）"
              class="form-input"
            />
          </div>
          
          <div class="form-group">
            <label>真实姓名</label>
            <input
              v-model="form.real_name"
              type="text"
              placeholder="请输入真实姓名（选填）"
              class="form-input"
            />
          </div>
        </div>
        
        <button
          type="submit"
          :disabled="loading"
          class="register-btn"
        >
          {{ loading ? '注册中...' : '🚀 开始注册' }}
        </button>
      </form>
      
      <div class="footer">
        <span>已有账号？</span>
        <router-link to="/login" class="modern-link">立即登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authAPI } from '@/api'

const router = useRouter()
const loading = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  role: 'entrant',
  school: '',
  real_name: ''
})

const DRAFT_KEY = 'register_form_draft'

onMounted(() => {
  try {
    const raw = sessionStorage.getItem(DRAFT_KEY)
    if (raw) {
      const draft = JSON.parse(raw)
      if (draft && typeof draft === 'object') {
        if (typeof draft.username === 'string') form.username = draft.username
        if (typeof draft.email === 'string') form.email = draft.email
        if (draft.role === 'teacher' || draft.role === 'entrant') form.role = draft.role
        if (typeof draft.school === 'string') form.school = draft.school
        if (typeof draft.real_name === 'string') form.real_name = draft.real_name
      }
    }
  } catch {}
})

watch(
  () => ({
    username: form.username,
    email: form.email,
    role: form.role,
    school: form.school,
    real_name: form.real_name
  }),
  (val) => {
    try { sessionStorage.setItem(DRAFT_KEY, JSON.stringify(val)) } catch {}
  },
  { deep: true }
)

const handleRegister = async () => {
  // 基本验证
  if (!form.username || !form.password || !form.confirmPassword) {
    ElMessage.error({
      message: '请填写必填项',
      duration: 3000,
      showClose: true
    })
    return
  }
  
  if (form.password !== form.confirmPassword) {
    ElMessage.error({
      message: '两次输入的密码不一致',
      duration: 3000,
      showClose: true
    })
    return
  }
  
  if (form.password.length < 6) {
    ElMessage.error({
      message: '密码长度不能少于6位',
      duration: 3000,
      showClose: true
    })
    return
  }
  
  loading.value = true
  
  try {
    const data = {
      username: form.username,
      password: form.password,
      email: form.email || null,
      role: form.role,
      school: form.school || null,
      real_name: form.real_name || null
    }
    
    console.log('开始注册...', data)
    const response = await authAPI.register(data)
    console.log('注册响应:', response)
    
    const res = response.data
    
    if (res.status === 'success') {
      ElMessage.success({
        message: '注册成功！请登录',
        duration: 2000,
        showClose: true
      })
      
      // 延迟跳转
      setTimeout(() => {
        // 成功后清理草稿
        try { sessionStorage.removeItem(DRAFT_KEY) } catch {}
        router.push('/login')
      }, 500)
    } else {
      ElMessage.error({
        message: res.message || '注册失败，请重试',
        duration: 6000,
        showClose: true
      })
    }
  } catch (error) {
    console.error('注册失败:', error)
    console.error('错误详情:', error.response)
    
    // 提取错误消息
    let errorMessage = '注册失败，请检查网络连接'
    
    if (error.response) {
      const data = error.response.data
      
      if (typeof data === 'string') {
        errorMessage = data
      } else if (data && data.detail) {
        errorMessage = data.detail
      } else if (data && data.message) {
        errorMessage = data.message
      }
    } else if (error.message) {
      errorMessage = error.message
    }
    
    ElMessage.error({
      message: errorMessage,
      duration: 6000,
      showClose: true
    })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: var(--gradient-hero);
  padding: 40px 20px;
}

.register-box {
  background: white;
  padding: 48px;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  width: 700px;
  max-width: 100%;
}

.title {
  font-size: 32px;
  font-weight: 800;
  text-align: center;
  margin-bottom: 12px;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  text-align: center;
  color: #666;
  margin-bottom: 40px;
  font-size: 16px;
  font-weight: 500;
}

.register-form {
  margin-top: 40px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #333;
  font-weight: 600;
  font-size: 14px;
}

.required {
  color: #f56c6c;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.role-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.role-option {
  padding: 20px;
  border: 2px solid #ddd;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.role-option:hover {
  border-color: #667eea;
  transform: translateY(-2px);
}

.role-option.active {
  border-color: #667eea;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
}

.role-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.role-text {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.role-desc {
  font-size: 14px;
  color: #666;
}

.register-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  background: var(--gradient-primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 8px;
}

.register-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-colored-lg);
}

.register-btn:active:not(:disabled) {
  transform: translateY(0);
}

.register-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.footer {
  text-align: center;
  margin-top: 24px;
  color: #666;
  font-size: 15px;
}

.footer a {
  color: var(--primary-color);
  text-decoration: none;
  margin-left: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.footer a:hover {
  color: var(--primary-dark);
  text-decoration: underline;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .register-box {
    width: 100%;
    padding: 32px 24px;
  }
  
  .form-row {
    grid-template-columns: 1fr;
    gap: 0;
  }
  
  .role-options {
    grid-template-columns: 1fr;
  }
  
  .title {
    font-size: 28px;
  }
  
  .subtitle {
    font-size: 14px;
  }
}
</style>
