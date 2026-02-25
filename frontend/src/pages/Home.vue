<template>
  <div class="home-container">
    <!-- 顶部导航栏 -->
    <header class="header">
        <div class="header-content">
        <div class="logo">
          <div class="logo-icon">🎯</div>
          <h1 class="logo-text">AI竞赛助手</h1>
        </div>
          <div class="user-info">
          <div class="user-badge" :class="userRole">
            <span class="badge-icon">{{ userRole === 'teacher' ? '👨‍🏫' : '🎓' }}</span>
            <span class="badge-text">{{ userRole === 'teacher' ? '指导老师' : '参赛者' }}</span>
          </div>
          <div class="user-name">{{ user?.username }}</div>
          <button @click="handleLogout" class="logout-btn">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
            退出
          </button>
        </div>
        </div>
    </header>

    <!-- 主内容区 -->
    <main class="main-content">
      <!-- 欢迎横幅 -->
      <section class="hero-section">
        <div class="hero-content">
          <h2 class="hero-title">欢迎使用 AI 竞赛助手</h2>
          <p class="hero-subtitle">智能竞赛信息提取与管理平台，让参赛更简单</p>
          <div class="hero-stats">
              <div class="stat-item">
                <div class="stat-number">{{ stats.contests }}</div>
                <div class="stat-label">竞赛总数</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ stats.ongoing }}</div>
                <div class="stat-label">进行中</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ stats.extractions }}</div>
              <div class="stat-label">AI提取</div>
            </div>
          </div>
        </div>
      </section>

      <!-- 功能卡片网格 -->
      <section class="features-section">
        <div class="features-grid">
          <!-- 竞赛列表卡片 -->
          <div class="feature-card" @click="$router.push('/contests')">
            <div class="card-header">
              <div class="card-icon contests">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                  <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
              </div>
              <div class="card-badge">热门</div>
            </div>
            <div class="card-content">
              <h3 class="card-title">竞赛列表</h3>
              <p class="card-description">浏览所有竞赛信息，智能角色跳转，一键直达参赛入口</p>
            </div>
            <div class="card-footer">
              <span class="card-action">查看竞赛 →</span>
            </div>
          </div>

          <!-- AI智能提取卡片 -->
          <div class="feature-card" @click="$router.push('/ai-extract')">
            <div class="card-header">
              <div class="card-icon ai">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                  <path d="M2 17l10 5 10-5"></path>
                  <path d="M2 12l10 5 10-5"></path>
                </svg>
              </div>
              <div class="card-badge new">新功能</div>
            </div>
            <div class="card-content">
              <h3 class="card-title">AI智能提取</h3>
              <p class="card-description">上传文档或输入URL，AI自动提取竞赛关键信息</p>
            </div>
            <div class="card-footer">
              <span class="card-action">开始提取 →</span>
            </div>
          </div>

          <!-- 知识图谱卡片 -->
          <div class="feature-card coming-soon">
            <div class="card-header">
              <div class="card-icon graph">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="3"></circle>
                  <path d="M12 1v6m0 6v6m11-7h-6m-6 0H1"></path>
                </svg>
              </div>
              <div class="card-badge coming">即将推出</div>
            </div>
            <div class="card-content">
              <h3 class="card-title">知识图谱</h3>
              <p class="card-description">可视化展示竞赛知识结构，智能关联分析</p>
            </div>
            <div class="card-footer">
              <span class="card-action disabled">敬请期待</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 快速操作 -->
      <section class="quick-actions">
        <h3 class="section-title">快速操作</h3>
        <div class="actions-grid">
          <button @click="$router.push('/contests')" class="action-btn primary">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 11l3 3L22 4"></path>
              <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
            </svg>
            浏览竞赛
          </button>
          <button @click="$router.push('/ai-extract')" class="action-btn secondary">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            上传文档
          </button>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage } from 'element-plus'
import { contestAPI, aiAPI } from '@/api'

const router = useRouter()
const userStore = useUserStore()

const user = computed(() => userStore.user)
const userRole = computed(() => userStore.userRole)

const stats = ref({
  contests: 0,
  ongoing: 0,
  extractions: 0
})

const handleLogout = () => {
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

const loadStats = async () => {
  try {
    const contestRes = await contestAPI.getContests({ limit: 1 })
    if (contestRes.data?.status === 'success') {
      stats.value.contests = contestRes.data.data?.total || 0
    }
    
    const ongoingRes = await contestAPI.getContests({ status: 'ongoing', limit: 1 })
    if (ongoingRes.data?.status === 'success') {
      stats.value.ongoing = ongoingRes.data.data?.total || 0
    }
    
    // AI提取统计
    const extractCountRes = await aiAPI.getExtractionsCount()
    if (extractCountRes.data?.status === 'success') {
      stats.value.extractions = extractCountRes.data?.data?.total || 0
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: var(--bg-secondary);
}

/* 顶部导航栏 */
.header {
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

.logo {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.logo-icon {
  font-size: 28px;
}

.logo-text {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  background: var(--gradient-text);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.user-badge {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-4);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
}

.user-badge.teacher {
  background: rgba(245, 158, 11, 0.1);
  color: var(--warning-dark);
  border: 1px solid var(--warning-light);
}

.user-badge.entrant {
  background: rgba(16, 185, 129, 0.1);
  color: var(--success-dark);
  border: 1px solid var(--success-light);
}

.badge-icon {
  font-size: 16px;
}

.user-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
}

.logout-btn {
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

.logout-btn:hover {
  background: var(--bg-tertiary);
  border-color: var(--danger-color);
  color: var(--danger-color);
}

/* 主内容区 */
.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-8) var(--spacing-6);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-12);
}

/* 欢迎横幅 */
.hero-section {
  text-align: center;
  padding: var(--spacing-16) var(--spacing-8);
  background: var(--gradient-hero);
  border-radius: var(--radius-3xl);
  border: 1px solid var(--border-light);
  position: relative;
  overflow: hidden;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 20%, rgba(14, 165, 233, 0.05) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(6, 182, 212, 0.05) 0%, transparent 50%);
  pointer-events: none;
}

.hero-content {
  position: relative;
  z-index: 1;
}

.hero-title {
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-4);
  line-height: var(--leading-tight);
}

.hero-subtitle {
  font-size: var(--text-lg);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-8);
  font-weight: var(--font-medium);
}

.hero-stats {
  display: flex;
  justify-content: center;
  gap: var(--spacing-8);
  flex-wrap: wrap;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: var(--text-3xl);
  font-weight: var(--font-extrabold);
  background: var(--gradient-text);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  display: block;
  margin-bottom: var(--spacing-1);
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  font-weight: var(--font-medium);
}

/* 功能卡片网格 */
.features-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-6);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: var(--spacing-6);
}

.feature-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-2xl);
  padding: var(--spacing-6);
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.feature-card::before {
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

.feature-card:hover {
  border-color: var(--border-focus);
  box-shadow: var(--shadow-lg);
  transform: translateY(-4px);
}

.feature-card:hover::before {
  opacity: 1;
}

.feature-card.coming-soon {
  opacity: 0.7;
  cursor: not-allowed;
}

.feature-card.coming-soon:hover {
  transform: none;
  box-shadow: var(--shadow-sm);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-4);
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.card-icon.contests {
  background: var(--gradient-primary);
}

.card-icon.ai {
  background: var(--gradient-info);
}

.card-icon.graph {
  background: var(--gradient-success);
}

.card-badge {
  padding: var(--spacing-1) var(--spacing-3);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.card-badge {
  background: rgba(14, 165, 233, 0.1);
  color: var(--primary-dark);
  border: 1px solid var(--primary-light);
}

.card-badge.new {
  background: rgba(16, 185, 129, 0.1);
  color: var(--success-dark);
  border: 1px solid var(--success-light);
}

.card-badge.coming {
  background: rgba(100, 116, 139, 0.1);
  color: var(--secondary-dark);
  border: 1px solid var(--secondary-light);
}

.card-content {
  margin-bottom: var(--spacing-4);
}

.card-title {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-2);
}

.card-description {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: var(--leading-relaxed);
}

.card-footer {
  display: flex;
  justify-content: flex-end;
}

.card-action {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--primary-color);
  transition: color 0.2s ease;
}

.feature-card:hover .card-action {
  color: var(--primary-dark);
}

.card-action.disabled {
  color: var(--text-quaternary);
}

/* 快速操作 */
.quick-actions {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.section-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-2);
}

.actions-grid {
  display: flex;
  gap: var(--spacing-4);
  flex-wrap: wrap;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-6);
  border: none;
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn.primary {
  background: var(--gradient-primary);
  color: white;
  box-shadow: var(--shadow-sm);
}

.action-btn.primary:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-colored);
}

.action-btn.secondary {
  background: var(--bg-primary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.action-btn.secondary:hover {
  background: var(--bg-tertiary);
  border-color: var(--border-focus);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    padding: var(--spacing-3) var(--spacing-4);
  }

  .main-content {
    padding: var(--spacing-6) var(--spacing-4);
    gap: var(--spacing-8);
  }

  .hero-section {
    padding: var(--spacing-12) var(--spacing-6);
  }

  .hero-title {
    font-size: var(--text-3xl);
  }

  .hero-stats {
    gap: var(--spacing-6);
  }

  .features-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-4);
  }

  .user-info {
    gap: var(--spacing-2);
  }

  .user-name {
    display: none;
  }

  .actions-grid {
    flex-direction: column;
  }
}

@media (max-width: 480px) {
  .hero-title {
    font-size: var(--text-2xl);
  }

  .hero-subtitle {
    font-size: var(--text-base);
  }

  .hero-stats {
    flex-direction: column;
    gap: var(--spacing-4);
  }
}
</style>
