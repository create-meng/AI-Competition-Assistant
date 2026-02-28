import { ref } from 'vue'
import { aiAPI } from '@/api'

export function useProvidersHealth() {
  const providers = ref([])
  const providersLoading = ref(true)
  const healthCheckProgress = ref({ current: 0, total: 0, available: 0, message: '正在检查AI提供商...' })

  const updateHealthCheckProgress = (current, total, available = 0) => {
    healthCheckProgress.value = {
      current,
      total,
      available,
      message: '正在检查AI提供商...'
    }
  }

  const startProvidersPolling = async (totalCount, attempt = 0) => {
    if (attempt > 20) {
      providersLoading.value = false
      return
    }
    try {
      const resp = await aiAPI.getProviders()
      if (resp.data?.status === 'success') {
        providers.value = resp.data.data
        const knownCount = providers.value.filter(p => ['available', 'unavailable'].includes(p.status)).length
        updateHealthCheckProgress(knownCount, totalCount)
        if (knownCount >= totalCount) {
          providersLoading.value = false
          return
        }
      }
    } catch (e) {
      // ignore
    }
    setTimeout(() => startProvidersPolling(totalCount, attempt + 1), 1500)
  }

  const loadProviders = async () => {
    providersLoading.value = true

    try {
      const response = await fetch('/api/v1/ai/providers/stream', {
        method: 'GET',
        headers: {
          Accept: 'text/event-stream',
          'Cache-Control': 'no-cache'
        }
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              updateHealthCheckProgress(data.current, data.total, data.available)

              if (data.completed && data.providers) {
                providers.value = data.providers
                providersLoading.value = false
                return
              }
            } catch (e) {
              // ignore
            }
          }
        }
      }
    } catch (e) {
      try {
        const resp = await aiAPI.getProviders()
        if (resp.data?.status === 'success') {
          providers.value = resp.data.data
        }
      } finally {
        providersLoading.value = false
      }
    }
  }

  return {
    providers,
    providersLoading,
    healthCheckProgress,
    loadProviders,
    startProvidersPolling
  }
}
