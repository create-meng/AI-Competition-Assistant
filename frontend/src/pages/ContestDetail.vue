<template>

  <AppLayout
    title="竞赛详情"
    :showBack="true"
    backText="返回列表"
    backTo="/contests"
  >
    <template #right>
      <HeaderUserInfo :showLogout="false" />
      <button @click="handleRedirect" class="ui-btn ui-btn-primary">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
          <polyline points="15 3 21 3 21 9"></polyline>
          <line x1="10" y1="14" x2="21" y2="3"></line>
        </svg>
        <span>{{ isLoggedIn ? (userRole === 'teacher' ? '前往教师入口' : '前往参赛入口') : '登录后跳转' }}</span>
      </button>
    </template>

    <!-- 主内容区 -->
    <main class="detail-main" v-loading="loading">

      <div v-if="contest" class="content-wrapper">

        

        <!-- 竞赛头部卡片 -->

        <div class="hero-card">

          <div class="hero-badge">

            <span class="badge-icon">🏆</span>

            <span class="badge-text">官方竞赛</span>

          </div>

          <h1 class="contest-title">{{ contest.name }}</h1>

          <div class="contest-meta">

            <div class="meta-item">

              <span class="meta-icon">🏢</span>

              <span class="meta-label">主办方</span>

              <span class="meta-value">{{ contest.organizer }}</span>

            </div>

            <div class="meta-item" v-if="contest.category">

              <span class="meta-icon">📂</span>

              <span class="meta-label">类别</span>

              <span class="meta-value">{{ contest.category }}</span>

            </div>

            <div class="meta-item" v-if="contest.deadline">

              <span class="meta-icon">⏰</span>

              <span class="meta-label">截止日期</span>

              <span class="meta-value">{{ formatDate(contest.deadline) }}</span>

            </div>

            <div class="meta-item">

              <span class="meta-icon">📊</span>

              <span class="meta-label">状态</span>

              <span :class="['status-tag', getStatusClass(contest.status)]">

                {{ getStatusText(contest.status) }}

              </span>

            </div>

          </div>

        </div>



        <!-- 信息网格 -->

        <div class="info-grid">

          

          <!-- 参赛要求 -->

          <div v-if="contest.requirements && contest.requirements.length > 0" class="info-card">

            <div class="card-header">

              <div class="card-icon requirements">

                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">

                  <path d="M9 11l3 3L22 4"></path>

                  <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>

                </svg>

              </div>

              <h3 class="card-title">参赛要求</h3>

            </div>

            <ul class="requirements-list">

              <li v-for="(req, index) in contest.requirements" :key="index" class="requirement-item">

                <span class="req-bullet"></span>

                <span class="req-text">{{ req }}</span>

              </li>

            </ul>

          </div>



          <!-- 奖项信息 -->

          <div v-if="contest.prize_info" class="info-card">

            <div class="card-header">

              <div class="card-icon prize">

                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">

                  <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path>

                  <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path>

                  <path d="M4 22h16"></path>

                  <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"></path>

                  <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"></path>

                  <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"></path>

                </svg>

              </div>

              <h3 class="card-title">奖项信息</h3>

            </div>

            <div class="card-content">

              <p class="prize-text">{{ contest.prize_info }}</p>

            </div>

          </div>



          <!-- 联系方式 -->

          <div v-if="contest.contact_info" class="info-card">

            <div class="card-header">

              <div class="card-icon contact">

                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">

                  <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>

                </svg>

              </div>

              <h3 class="card-title">联系方式</h3>

            </div>

            <ul class="contact-list">

              <li v-for="(item, index) in parseContactInfo(contest.contact_info)" :key="index" class="contact-item">

                <span class="contact-icon-small">{{ getContactIcon(item) }}</span>

                <span class="contact-text">{{ item }}</span>

              </li>

            </ul>

          </div>



          <!-- 竞赛阶段 -->

          <div v-if="contest.stages && contest.stages.length > 0" class="info-card stages-card">

            <div class="card-header">

              <div class="card-icon stages">

                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">

                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>

                </svg>

              </div>

              <h3 class="card-title">竞赛阶段</h3>

            </div>

            <div class="stages-timeline">

              <div 

                v-for="(stage, index) in contest.stages" 

                :key="index" 

                class="timeline-item"

              >

                <div class="timeline-marker">

                  <div class="marker-dot"></div>

                  <div v-if="index < contest.stages.length - 1" class="marker-line"></div>

                </div>

                <div class="timeline-content">

                  <div class="stage-header">

                    <h4 class="stage-name">{{ stage.name }}</h4>

                    <span v-if="stage.deadline" class="stage-date">

                      {{ formatDate(stage.deadline) }}

                    </span>

                  </div>

                  <p v-if="stage.description" class="stage-description">

                    {{ stage.description }}

                  </p>

                </div>

              </div>

            </div>

          </div>



        </div>



        <div v-if="isExpired" class="expired-tag">

          已截止

        </div>



        <!-- 底部操作栏 -->

        <div class="bottom-actions">

          <button @click="handleRedirect" class="ui-btn ui-btn-primary ui-btn-lg ui-btn-block">

            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">

              <path d="M5 12h14"></path>

              <path d="m12 5 7 7-7 7"></path>

            </svg>

            <span>{{ isLoggedIn ? (userRole === 'teacher' ? '前往教师入口' : '立即参赛') : '登录后跳转' }}</span>

          </button>

        </div>

      </div>



      <!-- 加载状态 -->

      <div v-if="loading" class="loading-state">

        <div class="loading-spinner"></div>

        <p>加载中...</p>

      </div>

    </main>

  </AppLayout>

</template>



<script setup>

import { ref, computed, onMounted } from 'vue'

import { useRoute } from 'vue-router'

import { useRouter } from 'vue-router'

import { useUserStore } from '@/store/user'

import { ElMessage } from 'element-plus'

import { contestAPI } from '@/api'

import AppLayout from '@/components/AppLayout.vue'

import HeaderUserInfo from '@/components/HeaderUserInfo.vue'



const route = useRoute()

const router = useRouter()

const userStore = useUserStore()

const userRole = userStore.userRole

const isLoggedIn = computed(() => userStore.isLoggedIn)



const loading = ref(false)

const contest = ref(null)



const isExpired = computed(() => {

  const d = contest.value?.deadline

  if (!d) return false

  const t = new Date(d).getTime()

  if (Number.isNaN(t)) return false

  return Date.now() > t

})



const loadContest = async () => {

  loading.value = true

  try {

    const res = await contestAPI.getContest(route.params.id)

    const payload = res.data || {}

    if (payload.status === 'success') {

      contest.value = payload.data

    } else {

      contest.value = null

      ElMessage.error(payload.message || '加载失败')

    }

  } catch (error) {

    console.error('加载竞赛详情失败:', error)

    ElMessage.error({

      message: '加载失败，请稍后重试',

      duration: 5000,

      showClose: true

    })

  } finally {

    loading.value = false

  }

}



const handleRedirect = async () => {

  if (!isLoggedIn.value) {

    router.push({

      path: '/login',

      query: {

        redirect: route.fullPath

      }

    })

    return

  }

  try {

    const res = await contestAPI.redirectToOfficial(route.params.id)

    const payload = res.data || {}

    if (payload.status === 'success' && payload.data?.url) {

      window.open(payload.data.url, '_blank')

      ElMessage.success(`正在跳转到${payload.data.role === 'teacher' ? '教师' : '参赛'}入口`)

    } else {

      ElMessage.error(payload.message || '未获取到跳转链接')

    }

  } catch (error) {

    console.error('获取跳转链接失败:', error)

    ElMessage.error('跳转失败，请稍后重试')

  }

}



const getStatusClass = (status) => {

  const map = {

    upcoming: 'status-info',

    ongoing: 'status-success',

    ended: 'status-ended'

  }

  return map[status] || 'status-info'

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

  return new Date(date).toLocaleDateString('zh-CN', {

    year: 'numeric',

    month: 'long',

    day: 'numeric'

  })

}



// 解析联系方式字符串为数组

const parseContactInfo = (contactStr) => {

  if (!contactStr) return []

  // 按分号、换行分割

  return contactStr.split(/[;；\n]/).map(s => s.trim()).filter(Boolean)

}



// 根据联系方式内容返回对应图标

const getContactIcon = (text) => {

  const t = text.toLowerCase()

  if (t.includes('邮箱') || t.includes('email') || t.includes('@')) return '📧'

  if (t.includes('电话') || t.includes('phone') || /\d{11}/.test(t) || /\d{3,4}[-\s]?\d{7,8}/.test(t)) return '📞'

  if (t.includes('qq')) return '💬'

  if (t.includes('微信') || t.includes('wechat')) return '💬'

  if (t.includes('联系人')) return '👤'

  return '📋'

}



onMounted(() => {

  loadContest()

})

</script>



<style scoped>

.detail-container {

  min-height: 100vh;

  background: var(--bg-secondary);

}



.action-btn {

  display: flex;

  align-items: center;

  gap: 8px;

  padding: 10px 20px;

  border: none;

  border-radius: var(--radius-md);

  font-size: 15px;

  font-weight: 600;

  cursor: pointer;

  transition: all 0.3s ease;

}



.action-btn.primary {

  background: var(--gradient-primary);

  color: white;

  box-shadow: var(--shadow-md);

}



.action-btn.primary:hover {

  transform: translateY(-2px);

  box-shadow: var(--shadow-colored-lg);

}



/* 主内容区 */

.detail-main {
  padding: 0;
}



.content-wrapper {

  display: flex;

  flex-direction: column;

  gap: 24px;

}



/* 英雄卡片 */

.hero-card {

  background: var(--bg-primary);

  border: 1px solid var(--border-color);

  border-radius: var(--radius-xl);

  padding: 48px;

  box-shadow: var(--shadow-lg);

  position: relative;

  overflow: hidden;

}



.hero-card::before {

  content: '';

  position: absolute;

  top: 0;

  left: 0;

  right: 0;

  height: 4px;

  background: var(--gradient-primary);

}



.hero-badge {

  display: inline-flex;

  align-items: center;

  gap: 6px;

  padding: 6px 14px;

  background: var(--bg-accent-light);

  border: 1px solid var(--primary-lighter);

  border-radius: var(--radius-lg);

  margin-bottom: 20px;

}



.badge-icon {

  font-size: 16px;

}



.badge-text {

  font-size: 13px;

  font-weight: 600;

  color: var(--primary-dark);

}



.contest-title {

  font-size: 36px;

  font-weight: 800;

  color: var(--text-primary);

  margin: 0 0 32px;

  line-height: 1.3;

}



.contest-meta {

  display: grid;

  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));

  gap: 24px;

}



.meta-item {

  display: flex;

  align-items: center;

  gap: 10px;

}



.meta-icon {

  font-size: 20px;

  flex-shrink: 0;

}



.meta-label {

  font-size: 14px;

  color: var(--text-tertiary);

  font-weight: 500;

}



.meta-value {

  font-size: 15px;

  color: var(--text-primary);

  font-weight: 600;

}



.status-tag {

  padding: 6px 12px;

  border-radius: var(--radius-sm);

  font-size: 13px;

  font-weight: 700;

  text-transform: uppercase;

  letter-spacing: 0.5px;

}



.status-tag.status-success {

  background: rgba(16, 185, 129, 0.1);

  color: var(--success-dark);

  border: 1px solid var(--success-light);

}



.status-tag.status-info {

  background: rgba(6, 182, 212, 0.1);

  color: var(--info-dark);

  border: 1px solid var(--info-light);

}



.status-tag.status-ended {

  background: rgba(100, 116, 139, 0.1);

  color: var(--secondary-dark);

  border: 1px solid var(--secondary-light);

}



/* 信息网格 */

.info-grid {

  display: grid;

  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));

  gap: 24px;

}



.info-card {

  background: var(--bg-primary);

  border: 1px solid var(--border-color);

  border-radius: var(--radius-lg);

  padding: 28px;

  box-shadow: var(--shadow-md);

  transition: all 0.3s ease;

}



.info-card:hover {

  border-color: var(--primary-light);

  box-shadow: var(--shadow-colored);

  transform: translateY(-4px);

}



.info-card.stages-card {

  grid-column: 1 / -1;

}



.card-header {

  display: flex;

  align-items: center;

  gap: 12px;

  margin-bottom: 20px;

}



.card-icon {

  width: 40px;

  height: 40px;

  border-radius: var(--radius-md);

  display: flex;

  align-items: center;

  justify-content: center;

  flex-shrink: 0;

}



.card-icon.requirements {

  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(52, 211, 153, 0.1) 100%);

  color: var(--success-color);

}



.card-icon.prize {

  background: linear-gradient(135deg, rgba(251, 113, 133, 0.1) 0%, rgba(251, 191, 36, 0.1) 100%);

  color: var(--accent-coral);

}



.card-icon.contact {

  background: linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(34, 211, 238, 0.1) 100%);

  color: var(--info-color);

}



.card-icon.stages {

  background: linear-gradient(135deg, rgba(20, 184, 166, 0.1) 0%, rgba(56, 189, 248, 0.1) 100%);

  color: var(--primary-color);

}



.card-title {

  font-size: 18px;

  font-weight: 700;

  color: var(--text-primary);

  margin: 0;

}



.card-content {

  color: var(--text-secondary);

  line-height: 1.7;

}



/* 要求列表 */

.requirements-list {

  list-style: none;

  padding: 0;

  margin: 0;

  display: flex;

  flex-direction: column;

  gap: 14px;

}



.requirement-item {

  display: flex;

  align-items: flex-start;

  gap: 12px;

  padding: 14px;

  background: var(--bg-secondary);

  border-radius: var(--radius-md);

  border: 1px solid var(--border-light);

  transition: all 0.2s ease;

}



.requirement-item:hover {

  background: var(--bg-accent-light);

  border-color: var(--primary-lighter);

}



.req-bullet {

  width: 6px;

  height: 6px;

  border-radius: 50%;

  background: var(--primary-color);

  flex-shrink: 0;

  margin-top: 7px;

}



.req-text {

  font-size: 15px;

  color: var(--text-primary);

  line-height: 1.6;

}



/* 奖项与联系信息 */

.prize-text {

  font-size: 15px;

  line-height: 1.7;

  color: var(--text-secondary);

  white-space: pre-wrap;

}



/* 联系方式列表 */

.contact-list {

  list-style: none;

  padding: 0;

  margin: 0;

  display: flex;

  flex-direction: column;

  gap: 12px;

}



.contact-item {

  display: flex;

  align-items: center;

  gap: 12px;

  padding: 12px 14px;

  background: var(--bg-secondary);

  border-radius: var(--radius-md);

  border: 1px solid var(--border-light);

  transition: all 0.2s ease;

}



.contact-item:hover {

  background: rgba(6, 182, 212, 0.05);

  border-color: var(--info-light);

}



.contact-icon-small {

  font-size: 18px;

  flex-shrink: 0;

}



.contact-text {

  font-size: 14px;

  color: var(--text-primary);

  line-height: 1.5;

  word-break: break-all;

}



/* 竞赛阶段时间轴 */

.stages-timeline {

  display: flex;

  flex-direction: column;

  gap: 0;

}



.timeline-item {

  display: flex;

  gap: 20px;

  position: relative;

}



.timeline-marker {

  display: flex;

  flex-direction: column;

  align-items: center;

  position: relative;

  z-index: 1;

}



.marker-dot {

  width: 14px;

  height: 14px;

  border-radius: 50%;

  background: var(--primary-color);

  border: 3px solid var(--bg-primary);

  box-shadow: 0 0 0 2px var(--primary-color);

  flex-shrink: 0;

}



.marker-line {

  width: 2px;

  flex: 1;

  background: var(--border-color);

  min-height: 40px;

  margin: 4px 0;

}



.timeline-content {

  flex: 1;

  padding-bottom: 28px;

}



.stage-header {

  display: flex;

  justify-content: space-between;

  align-items: center;

  margin-bottom: 8px;

  gap: 16px;

}



.stage-name {

  font-size: 17px;

  font-weight: 700;

  color: var(--text-primary);

  margin: 0;

}



.stage-date {

  font-size: 14px;

  color: var(--text-tertiary);

  font-weight: 500;

  white-space: nowrap;

  padding: 4px 10px;

  background: var(--bg-tertiary);

  border-radius: var(--radius-sm);

}



.stage-description {

  font-size: 14px;

  color: var(--text-secondary);

  line-height: 1.6;

  margin: 0;

}



/* 底部操作栏 */

.bottom-actions {

  position: fixed;

  bottom: 0;

  left: 0;

  right: 0;

  background: var(--bg-glass);

  backdrop-filter: blur(20px);

  border-top: 1px solid var(--border-color);

  padding: 20px 24px;

  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.05);

  z-index: 100;

}



.expired-tag {

  position: fixed;

  left: 50%;

  transform: translateX(-50%);

  bottom: 92px;

  padding: 10px 18px;

  background: rgba(239, 68, 68, 0.1);

  border: 1px solid rgba(239, 68, 68, 0.25);

  color: #b91c1c;

  border-radius: var(--radius-full);

  font-weight: 800;

  letter-spacing: 1px;

  z-index: 101;

}



.main-action-btn {

  display: flex;

  align-items: center;

  justify-content: center;

  gap: 10px;

  width: 100%;

  max-width: 600px;

  margin: 0 auto;

  padding: 16px 32px;

  background: var(--gradient-primary);

  color: white;

  border: none;

  border-radius: var(--radius-lg);

  font-size: 16px;

  font-weight: 700;

  cursor: pointer;

  box-shadow: var(--shadow-colored);

  transition: all 0.3s ease;

}



.main-action-btn:hover {

  transform: translateY(-2px);

  box-shadow: var(--shadow-colored-lg);

}



.main-action-btn:active {

  transform: translateY(0);

}



/* 加载状态 */

.loading-state {

  display: flex;

  flex-direction: column;

  align-items: center;

  justify-content: center;

  padding: 80px 20px;

}



.loading-spinner {

  width: 48px;

  height: 48px;

  border: 4px solid var(--border-color);

  border-top-color: var(--primary-color);

  border-radius: 50%;

  animation: spin 0.8s linear infinite;

}



@keyframes spin {

  to {

    transform: rotate(360deg);

  }

}



.loading-state p {

  margin-top: 20px;

  color: var(--text-tertiary);

  font-size: 15px;

}



/* 响应式设计 */

@media (max-width: 768px) {

  .detail-main {

    padding: 20px 16px 100px;

  }



  .hero-card {

    padding: 28px 20px;

  }



  .contest-title {

    font-size: 28px;

  }



  .contest-meta {

    grid-template-columns: 1fr;

    gap: 16px;

  }



  .info-grid {

    grid-template-columns: 1fr;

    gap: 16px;

  }



  .header-wrapper {

    padding: 12px 16px;

  }



  .action-btn span {

    display: none;

  }



  .stage-header {

    flex-direction: column;

    align-items: flex-start;

    gap: 8px;

  }

}

</style>

