<template>
  <div class="contests-page">
    <!-- 顶部导航 -->
    <header class="page-header">
      <div class="header-content">
        <div class="header-left">
          <button @click="$router.push('/home')" class="back-btn">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            返回首页
          </button>
          <h1 class="page-title">竞赛列表</h1>
        </div>
        <div class="header-right">
          <div class="user-info">
            <span class="user-role">{{ userRole === 'teacher' ? '👨‍🏫 指导老师' : '🎓 参赛者' }}</span>
            <span class="user-name">{{ user?.username }}</span>
          </div>
        </div>
      </div>
    </header>

    <!-- 搜索筛选区域 -->
    <section class="search-section">
      <div class="search-container">
        <div class="search-bar">
          <div class="search-input-wrapper">
            <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="M21 21l-4.35-4.35"></path>
            </svg>
            <input
              v-model="filters.search"
              type="text"
              placeholder="搜索竞赛名称..."
              class="search-input"
              @keyup.enter="loadContests"
            />
          </div>
          
          <div class="filter-group">
            <select v-model="filters.status" @change="loadContests" class="status-select">
              <option value="">全部状态</option>
              <option value="upcoming">即将开始</option>
              <option value="ongoing">进行中</option>
              <option value="ended">已结束</option>
            </select>
            
            <button @click="loadContests" class="search-btn">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="M21 21l-4.35-4.35"></path>
              </svg>
              搜索
            </button>
            
            <button @click="resetFilters" class="reset-btn">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
              </svg>
              重置
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 竞赛列表 -->
    <main class="contests-main">
      <div class="contests-container">
        <!-- 加载状态 -->
        <div v-if="loading" class="loading-container">
          <div class="loading-spinner"></div>
          <p>正在加载竞赛数据...</p>
        </div>

        <!-- 竞赛卡片列表 -->
        <div v-else-if="contests.length > 0" class="contests-grid">
          <div v-for="contest in contests" :key="contest.id" class="contest-card">
            <div class="card-header">
              <h3 class="contest-title">{{ contest.name }}</h3>
              <div class="status-badge" :class="contest.status">
                {{ getStatusText(contest.status) }}
              </div>
            </div>
            
            <div class="card-content">
              <div class="info-row">
                <div class="info-item">
                  <div class="info-label">主办方</div>
                  <div class="info-value">{{ contest.organizer }}</div>
                </div>
              </div>
              
              <div class="info-row" v-if="contest.category">
                <div class="info-item">
                  <div class="info-label">类别</div>
                  <div class="info-value">{{ contest.category }}</div>
                </div>
              </div>
              
              <div class="info-row" v-if="contest.deadline">
                <div class="info-item">
                  <div class="info-label">截止日期</div>
                  <div class="info-value deadline">{{ formatDate(contest.deadline) }}</div>
                </div>
              </div>
            </div>
            
            <div class="card-footer">
              <button @click="handleRedirect(contest.id)" class="action-btn primary">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                  <polyline points="15 3 21 3 21 9"/>
                  <line x1="10" y1="14" x2="21" y2="3"/>
                </svg>
                {{ userRole === 'teacher' ? '教师入口' : '参赛入口' }}
              </button>
              
              <button @click="viewDetail(contest.id)" class="action-btn secondary">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
                查看详情
              </button>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-else class="empty-state">
          <div class="empty-icon">📋</div>
          <h3>暂无竞赛数据</h3>
          <p>当前没有找到符合条件的竞赛，请尝试调整搜索条件</p>
          <button @click="resetFilters" class="empty-action-btn">重置筛选</button>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="total > 0" class="pagination-container">
        <div class="pagination-info">
          共 {{ total }} 条记录，第 {{ pagination.page }} / {{ Math.ceil(total / pagination.size) }} 页
        </div>
        <div class="pagination-controls">
          <button 
            @click="goToPage(pagination.page - 1)" 
            :disabled="pagination.page <= 1"
            class="page-btn"
          >
            上一页
          </button>
          
          <div class="page-numbers">
            <button 
              v-for="page in getPageNumbers()" 
              :key="page"
              @click="goToPage(page)"
              :class="['page-number', { active: page === pagination.page }]"
            >
              {{ page }}
            </button>
          </div>
          
          <button 
            @click="goToPage(pagination.page + 1)" 
            :disabled="pagination.page >= Math.ceil(total / pagination.size)"
            class="page-btn"
          >
            下一页
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage } from 'element-plus'
import { contestAPI } from '@/api'

const router = useRouter()
const userStore = useUserStore()
const userRole = computed(() => userStore.userRole)
const user = computed(() => userStore.user)

const loading = ref(false)
const contests = ref([])
const total = ref(0)

const filters = reactive({
  search: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  size: 10
})

const loadContests = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.page - 1) * pagination.size,
      limit: pagination.size,
      search: filters.search || undefined,
      status: filters.status || undefined
    }
    
    const res = await contestAPI.getContests(params)
    const payload = res.data || {}
    if (payload.status === 'success' && payload.data) {
      contests.value = payload.data.items || []
      total.value = payload.data.total || 0
    } else {
      contests.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('加载竞赛列表失败:', error)
    ElMessage.error('加载竞赛列表失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.search = ''
  filters.status = ''
  pagination.page = 1
  loadContests()
}

const handleRedirect = async (contestId) => {
  try {
    const res = await contestAPI.redirectToOfficial(contestId)
    const payload = res.data || {}
    if (payload.status === 'success' && payload.data?.url) {
      window.open(payload.data.url, '_blank')
      ElMessage.success(`正在跳转到${payload.data.role === 'teacher' ? '教师' : '参赛'}入口`)
    } else {
      ElMessage.error(payload.message || '未获取到跳转链接')
    }
  } catch (error) {
    console.error('获取跳转链接失败:', error)
    ElMessage.error('获取跳转链接失败')
  }
}

const viewDetail = (contestId) => {
  router.push(`/contests/${contestId}`)
}

const getStatusText = (status) => {
  const map = {
    upcoming: '即将开始',
    ongoing: '进行中',
    ended: '已结束'
  }
  return map[status] || status
}

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('zh-CN')
}

const goToPage = (page) => {
  if (page >= 1 && page <= Math.ceil(total.value / pagination.size)) {
    pagination.page = page
    loadContests()
  }
}

const getPageNumbers = () => {
  const totalPages = Math.ceil(total.value / pagination.size)
  const current = pagination.page
  const pages = []
  
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i++) {
      pages.push(i)
    }
  } else {
    if (current <= 4) {
      for (let i = 1; i <= 5; i++) pages.push(i)
      pages.push('...')
      pages.push(totalPages)
    } else if (current >= totalPages - 3) {
      pages.push(1)
      pages.push('...')
      for (let i = totalPages - 4; i <= totalPages; i++) pages.push(i)
    } else {
      pages.push(1)
      pages.push('...')
      for (let i = current - 1; i <= current + 1; i++) pages.push(i)
      pages.push('...')
      pages.push(totalPages)
    }
  }
  
  return pages
}

onMounted(() => {
  loadContests()
})
</script>

<style scoped>
.contests-page {
  min-height: 100vh;
  background: var(--bg-secondary);
}

/* 顶部导航 */
.page-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--bg-glass);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-4) var(--spacing-6);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-4);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: all 0.2s ease;
}

.back-btn:hover {
  background: var(--bg-tertiary);
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.page-title {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  background: var(--gradient-text);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.user-role {
  padding: var(--spacing-1) var(--spacing-3);
  background: var(--bg-accent);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--primary-color);
}

.user-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
}

/* 搜索区域 */
.search-section {
  padding: var(--spacing-6) 0;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-light);
}

.search-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-6);
}

.search-bar {
  display: flex;
  gap: var(--spacing-4);
  align-items: center;
  flex-wrap: wrap;
}

.search-input-wrapper {
  position: relative;
  flex: 1;
  min-width: 300px;
}

.search-icon {
  position: absolute;
  left: var(--spacing-3);
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-quaternary);
  z-index: 1;
}

.search-input {
  width: 100%;
  padding: var(--spacing-3) var(--spacing-3) var(--spacing-3) var(--spacing-10);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  color: var(--text-primary);
  transition: all 0.2s ease;
}

.search-input:focus {
  outline: none;
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
}

.search-input::placeholder {
  color: var(--text-quaternary);
}

.filter-group {
  display: flex;
  gap: var(--spacing-3);
  align-items: center;
}

.status-select {
  padding: var(--spacing-3) var(--spacing-4);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 120px;
}

.status-select:focus {
  outline: none;
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
}

.search-btn,
.reset-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-4);
  border: none;
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  cursor: pointer;
  transition: all 0.2s ease;
}

.search-btn {
  background: var(--gradient-primary);
  color: white;
}

.search-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-colored);
}

.reset-btn {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.reset-btn:hover {
  background: var(--bg-tertiary);
  border-color: var(--primary-color);
  color: var(--primary-color);
}

/* 主内容区 */
.contests-main {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-6);
}

.contests-container {
  min-height: 400px;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-16);
  gap: var(--spacing-4);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.loading-container p {
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

/* 竞赛网格 */
.contests-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: var(--spacing-6);
}

.contest-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: var(--spacing-6);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.contest-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--gradient-primary);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.contest-card:hover {
  border-color: var(--border-focus);
  box-shadow: var(--shadow-lg);
  transform: translateY(-4px);
}

.contest-card:hover::before {
  opacity: 1;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-4);
  padding-bottom: var(--spacing-4);
  border-bottom: 1px solid var(--border-light);
}

.contest-title {
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  margin: 0;
  line-height: var(--leading-tight);
  flex: 1;
  margin-right: var(--spacing-3);
}

.status-badge {
  padding: var(--spacing-1) var(--spacing-3);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  flex-shrink: 0;
}

.status-badge.upcoming {
  background: rgba(6, 182, 212, 0.1);
  color: var(--info-dark);
  border: 1px solid var(--info-light);
}

.status-badge.ongoing {
  background: rgba(16, 185, 129, 0.1);
  color: var(--success-dark);
  border: 1px solid var(--success-light);
}

.status-badge.ended {
  background: rgba(100, 116, 139, 0.1);
  color: var(--secondary-dark);
  border: 1px solid var(--secondary-light);
}

.card-content {
  margin-bottom: var(--spacing-4);
}

.info-row {
  margin-bottom: var(--spacing-3);
}

.info-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.info-label {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--text-secondary);
  min-width: 80px;
}

.info-value {
  font-size: var(--text-sm);
  color: var(--text-primary);
  flex: 1;
}

.info-value.deadline {
  color: var(--warning-dark);
  font-weight: var(--font-semibold);
}

.card-footer {
  display: flex;
  gap: var(--spacing-3);
  padding-top: var(--spacing-4);
  border-top: 1px solid var(--border-light);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-4);
  border: none;
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  cursor: pointer;
  transition: all 0.2s ease;
  flex: 1;
  justify-content: center;
}

.action-btn.primary {
  background: var(--gradient-primary);
  color: white;
}

.action-btn.primary:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-colored);
}

.action-btn.secondary {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.action-btn.secondary:hover {
  background: var(--bg-tertiary);
  border-color: var(--primary-color);
  color: var(--primary-color);
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-16);
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: var(--spacing-4);
}

.empty-state h3 {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-2);
}

.empty-state p {
  color: var(--text-secondary);
  margin-bottom: var(--spacing-6);
  max-width: 400px;
}

.empty-action-btn {
  padding: var(--spacing-3) var(--spacing-6);
  background: var(--gradient-primary);
  color: white;
  border: none;
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  cursor: pointer;
  transition: all 0.2s ease;
}

.empty-action-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-colored);
}

/* 分页 */
.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--spacing-8);
  padding: var(--spacing-4) var(--spacing-6);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
}

.pagination-info {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.page-btn {
  padding: var(--spacing-2) var(--spacing-4);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  background: var(--bg-tertiary);
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  gap: var(--spacing-1);
}

.page-number {
  width: 32px;
  height: 32px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-number:hover {
  background: var(--bg-tertiary);
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.page-number.active {
  background: var(--gradient-primary);
  border-color: var(--primary-color);
  color: white;
  font-weight: var(--font-semibold);
}

/* 动画 */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    padding: var(--spacing-3) var(--spacing-4);
  }

  .search-container {
    padding: 0 var(--spacing-4);
  }

  .search-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input-wrapper {
    min-width: auto;
  }

  .filter-group {
    justify-content: space-between;
  }

  .contests-main {
    padding: var(--spacing-4);
  }

  .contests-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-4);
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-2);
  }

  .card-footer {
    flex-direction: column;
  }

  .pagination-container {
    flex-direction: column;
    gap: var(--spacing-4);
    text-align: center;
  }

  .user-name {
    display: none;
  }
}

@media (max-width: 480px) {
  .page-title {
    font-size: var(--text-xl);
  }

  .contest-card {
    padding: var(--spacing-4);
  }

  .contest-title {
    font-size: var(--text-base);
  }
}
</style>