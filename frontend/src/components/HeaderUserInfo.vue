<template>
  <div class="header-user">
    <template v-if="isLoggedIn">
      <div v-if="showRoleBadge" class="header-user-badge" :class="userRole">
        <span class="header-user-badge-icon">{{ userRole === 'teacher' ? '👨‍🏫' : '🎓' }}</span>
        <span class="header-user-badge-text">{{ userRole === 'teacher' ? '指导老师' : '参赛者' }}</span>
      </div>
      <div class="header-user-name">{{ username }}</div>
      <button v-if="showLogout" class="ui-btn ui-btn-secondary ui-btn-sm" type="button" @click="handleLogout">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
          <polyline points="16 17 21 12 16 7"></polyline>
          <line x1="21" y1="12" x2="9" y2="12"></line>
        </svg>
        退出
      </button>
    </template>

    <template v-else>
      <div class="header-user-badge guest">
        <span class="header-user-badge-text">游客</span>
      </div>
      <button class="ui-btn ui-btn-primary ui-btn-sm" type="button" @click="goToLogin">登录</button>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'

const props = defineProps({
  showRoleBadge: { type: Boolean, default: true },
  showLogout: { type: Boolean, default: true }
})

const router = useRouter()
const userStore = useUserStore()

const isLoggedIn = computed(() => userStore.isLoggedIn)
const userRole = computed(() => userStore.userRole)
const username = computed(() => userStore.username)

const handleLogout = () => {
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.header-user {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-3);
  min-width: 0;
}

.header-user-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-4);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  white-space: nowrap;
}

.header-user-badge.teacher {
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary-color);
  border: 1px solid rgba(59, 130, 246, 0.25);
}

.header-user-badge.entrant {
  background: rgba(16, 185, 129, 0.1);
  color: var(--success-dark);
  border: 1px solid var(--success-light);
}

.header-user-badge.guest {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.header-user-badge-icon {
  font-size: 16px;
}

.header-user-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 160px;
}
</style>
