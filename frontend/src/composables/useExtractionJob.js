import { ref } from 'vue'
import { aiAPI } from '@/api'

export function useExtractionJob() {
  const jobId = ref(null)
  const jobData = ref(null)
  const jobPolling = ref(false)
  const jobError = ref(null)

  const extractedContent = ref({ url: null, file: null })

  let _timer = null

  const stopPolling = () => {
    jobPolling.value = false
    if (_timer) {
      clearTimeout(_timer)
      _timer = null
    }
  }

  const startPolling = (id, { onCompleted, onFailed } = {}) => {
    stopPolling()
    jobId.value = id
    jobPolling.value = true
    jobError.value = null

    let pollCount = 0
    const maxPolls = 120

    const tick = async () => {
      if (!jobPolling.value) return
      pollCount += 1

      if (pollCount > maxPolls) {
        stopPolling()
        jobError.value = '任务处理超时，请稍后重试'
        if (onFailed) onFailed(jobError.value)
        return
      }

      try {
        const resp = await aiAPI.getJob(id)
        if (resp.data?.status === 'success') {
          const newJobData = resp.data.data
          jobData.value = newJobData

          if (newJobData?.context) {
            if (newJobData.context.url_content) extractedContent.value.url = newJobData.context.url_content
            if (newJobData.context.file_content) extractedContent.value.file = newJobData.context.file_content
          }

          const st = newJobData?.status
          if (st === 'completed') {
            stopPolling()
            if (onCompleted) onCompleted(newJobData)
            return
          }
          if (st === 'failed') {
            stopPolling()
            const msg = newJobData?.error || '任务失败'
            jobError.value = msg
            if (onFailed) onFailed(msg)
            return
          }
        }
      } catch (e) {
        stopPolling()
        jobError.value = e?.message || '任务查询失败'
        if (onFailed) onFailed(jobError.value)
        return
      }

      const interval = pollCount <= 20 ? 500 : 1000
      _timer = setTimeout(tick, interval)
    }

    tick()
  }

  const cancelJob = async () => {
    if (!jobId.value) return
    try {
      await aiAPI.cancelExtractionJob(jobId.value)
    } finally {
      stopPolling()
    }
  }

  return {
    jobId,
    jobData,
    jobPolling,
    jobError,
    extractedContent,
    startPolling,
    stopPolling,
    cancelJob
  }
}
