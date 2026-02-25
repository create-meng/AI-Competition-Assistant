/**
 * Pinia Store 配置
 * 包含持久化插件和状态管理
 */
import { createPinia } from 'pinia'

// 持久化插件
function persistPlugin({ store }) {
  const key = `pinia_${store.$id}`
  
  // 从 localStorage 恢复状态
  const savedState = localStorage.getItem(key)
  if (savedState) {
    try {
      const parsed = JSON.parse(savedState)
      store.$patch(parsed)
    } catch (e) {
      console.warn(`Failed to restore state for ${store.$id}:`, e)
    }
  }
  
  // 监听状态变化并保存
  store.$subscribe((mutation, state) => {
    // 排除敏感数据
    const stateToSave = { ...state }
    
    // 不持久化某些字段
    if (store.$id === 'user') {
      // token 单独存储，不在这里重复
      delete stateToSave.token
    }
    
    try {
      localStorage.setItem(key, JSON.stringify(stateToSave))
    } catch (e) {
      console.warn(`Failed to save state for ${store.$id}:`, e)
    }
  })
}

// 创建 Pinia 实例
const pinia = createPinia()
pinia.use(persistPlugin)

export default pinia
