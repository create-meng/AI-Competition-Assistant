/**
 * 竞赛状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { contestAPI } from '@/api'

export const useContestStore = defineStore('contest', () => {
  // 状态
  const contests = ref([])
  const currentContest = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const pagination = ref({
    page: 1,
    pageSize: 10,
    total: 0
  })
  const filters = ref({
    status: '',
    category: '',
    search: ''
  })
  const lastFetch = ref(0)

  // 计算属性
  const hasContests = computed(() => contests.value.length > 0)
  const totalPages = computed(() => Math.ceil(pagination.value.total / pagination.value.pageSize))
  
  // 缓存是否有效（5分钟内）
  const isCacheValid = computed(() => {
    const cacheTime = 5 * 60 * 1000
    return Date.now() - lastFetch.value < cacheTime && hasContests.value
  })

  // 获取竞赛列表
  async function fetchContests(params = {}, forceRefresh = false) {
    // 如果缓存有效且不强制刷新，直接返回
    if (isCacheValid.value && !forceRefresh && !Object.keys(params).length) {
      return { success: true, data: contests.value }
    }

    loading.value = true
    error.value = null

    try {
      const queryParams = {
        page: pagination.value.page,
        page_size: pagination.value.pageSize,
        ...filters.value,
        ...params
      }

      // 移除空值
      Object.keys(queryParams).forEach(key => {
        if (!queryParams[key]) delete queryParams[key]
      })

      const response = await contestAPI.getContests(queryParams)
      
      if (response.data?.status === 'success') {
        contests.value = response.data.data?.items || response.data.data || []
        pagination.value.total = response.data.data?.total || contests.value.length
        lastFetch.value = Date.now()
        return { success: true, data: contests.value }
      } else {
        throw new Error(response.data?.message || '获取竞赛列表失败')
      }
    } catch (e) {
      error.value = e.message || '获取竞赛列表失败'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  // 获取单个竞赛详情
  async function fetchContest(contestId) {
    // 先从缓存中查找
    const cached = contests.value.find(c => c.id === contestId || c._id === contestId)
    if (cached) {
      currentContest.value = cached
    }

    loading.value = true
    error.value = null

    try {
      const response = await contestAPI.getContest(contestId)
      
      if (response.data?.status === 'success') {
        currentContest.value = response.data.data
        return { success: true, data: currentContest.value }
      } else {
        throw new Error(response.data?.message || '获取竞赛详情失败')
      }
    } catch (e) {
      error.value = e.message || '获取竞赛详情失败'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  // 更新筛选条件
  function setFilters(newFilters) {
    filters.value = { ...filters.value, ...newFilters }
    pagination.value.page = 1 // 重置页码
  }

  // 更新分页
  function setPage(page) {
    pagination.value.page = page
  }

  // 清空缓存
  function clearCache() {
    contests.value = []
    currentContest.value = null
    lastFetch.value = 0
  }

  return {
    // 状态
    contests,
    currentContest,
    loading,
    error,
    pagination,
    filters,
    // 计算属性
    hasContests,
    totalPages,
    isCacheValid,
    // 方法
    fetchContests,
    fetchContest,
    setFilters,
    setPage,
    clearCache
  }
})
