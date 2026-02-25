<template>
  <Teleport to="body">
    <!-- 主对话框 -->
    <Transition name="modal">
      <div v-if="visible && currentStep === 'form'" class="save-dialog-overlay" @click.self="handleClose">
        <div class="save-dialog">
          <!-- 头部 -->
          <div class="dialog-header">
            <div class="header-title">
              <span class="header-icon">💾</span>
              <h3>{{ isEdit ? '编辑竞赛' : '保存到竞赛库' }}</h3>
            </div>
            <button class="close-btn" @click="handleClose" :disabled="saving">×</button>
          </div>

          <!-- 表单内容 -->
          <div class="dialog-body">
            <!-- 基本信息区 -->
            <div class="form-section">
              <div class="section-header">
                <span class="section-icon">📋</span>
                <span class="section-title">基本信息</span>
              </div>
              
              <div class="form-grid">
                <div class="form-item full">
                  <label class="required">竞赛名称</label>
                  <input v-model="form.name" type="text" placeholder="请输入竞赛名称" 
                    :class="{ error: errors.name }" @blur="validateField('name')" />
                  <span v-if="errors.name" class="error-msg">{{ errors.name }}</span>
                </div>
                
                <div class="form-item">
                  <label class="required">主办方</label>
                  <input v-model="form.organizer" type="text" placeholder="主办单位名称"
                    :class="{ error: errors.organizer }" @blur="validateField('organizer')" />
                  <span v-if="errors.organizer" class="error-msg">{{ errors.organizer }}</span>
                </div>
                
                <div class="form-item">
                  <label>报名截止</label>
                  <input v-model="form.deadline" type="date" />
                </div>
              </div>
            </div>

            <!-- 链接信息区 -->
            <div class="form-section">
              <div class="section-header">
                <span class="section-icon">🔗</span>
                <span class="section-title">入口链接</span>
              </div>
              
              <div class="form-grid">
                <div class="form-item full">
                  <label>官网地址</label>
                  <input v-model="form.default_url" type="url" placeholder="https://..." />
                </div>
                
                <div class="form-item">
                  <label>参赛者入口</label>
                  <input v-model="form.entrant_url" type="url" placeholder="学生报名入口" />
                </div>
                
                <div class="form-item">
                  <label>教师入口</label>
                  <input v-model="form.teacher_url" type="url" placeholder="教师管理入口" />
                </div>
              </div>
            </div>

            <!-- 详细信息区 -->
            <div class="form-section">
              <div class="section-header">
                <span class="section-icon">📝</span>
                <span class="section-title">详细信息</span>
              </div>
              
              <div class="form-grid">
                <div class="form-item full">
                  <label>参赛要求</label>
                  <div class="tags-box">
                    <div class="tags-list">
                      <span v-for="(req, idx) in requirements" :key="idx" class="tag">
                        {{ req }}
                        <button type="button" @click="removeRequirement(idx)">×</button>
                      </span>
                    </div>
                    <input v-model="newRequirement" type="text" placeholder="输入要求后按回车添加"
                      @keydown.enter.prevent="addRequirement" />
                  </div>
                </div>
                
                <div class="form-item full">
                  <label>联系方式</label>
                  <div class="tags-box contact-tags">
                    <div class="tags-list">
                      <span v-for="(c, idx) in contacts" :key="idx" class="tag contact-tag">
                        <span class="contact-icon">{{ getContactIcon(c) }}</span>
                        {{ c }}
                        <button type="button" @click="removeContact(idx)">×</button>
                      </span>
                    </div>
                    <input v-model="newContact" type="text" placeholder="输入联系方式后按回车添加"
                      @keydown.enter.prevent="addContact" />
                  </div>
                </div>
                
                <div class="form-item full">
                  <label>奖项设置</label>
                  <textarea v-model="form.prize_info" rows="3" placeholder="奖项设置、奖金等信息"></textarea>
                </div>
              </div>
            </div>
          </div>

          <!-- 底部按钮 -->
          <div class="dialog-footer">
            <button class="btn-cancel" @click="handleClose" :disabled="saving">取消</button>
            <button class="btn-save" @click="handleSubmit" :disabled="saving || !isFormValid">
              <span v-if="saving" class="loading-spinner"></span>
              {{ saving ? '检查中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 重名检测对话框 -->
    <Transition name="modal">
      <div v-if="visible && currentStep === 'duplicate'" class="save-dialog-overlay" @click.self="goBackToForm">
        <div class="duplicate-dialog">
          <div class="dialog-header warning-header">
            <div class="header-title">
              <span class="header-icon">⚠️</span>
              <h3>发现相似竞赛</h3>
            </div>
            <button class="close-btn" @click="goBackToForm">×</button>
          </div>

          <div class="dialog-body">
            <p class="duplicate-hint">
              系统检测到已存在 <strong>{{ duplicateMatches.length }}</strong> 个相似的竞赛，请选择处理方式：
            </p>

            <!-- 匹配列表 - 简洁列表设计 -->
            <div class="duplicate-list">
              <div 
                v-for="match in duplicateMatches" 
                :key="match.id" 
                class="duplicate-item"
                :class="{ selected: selectedDuplicate?.id === match.id }"
                @click="selectedDuplicate = match"
              >
                <input 
                  type="radio" 
                  :id="'dup-' + match.id" 
                  :value="match" 
                  v-model="selectedDuplicate"
                  class="item-radio"
                />
                <span class="match-badge" :class="match._match_type === 'similar' ? 'similar' : 'exact'">
                  {{ match._match_type === 'similar' ? '相似' : '同名' }}
                </span>
                <span class="item-name">{{ match.name }}</span>
                <a 
                  class="item-link" 
                  :href="'/contests/' + match.id" 
                  target="_blank" 
                  @click.stop
                  title="在新标签页中查看详情"
                >
                  <span class="link-icon">↗</span>
                </a>
              </div>
            </div>

            <!-- 操作选项 -->
            <div class="action-options">
              <h4 class="options-title">请选择操作：</h4>
              <div class="options-grid">
                <label class="option-card" :class="{ active: duplicateAction === 'merge', disabled: !selectedDuplicate }">
                  <input type="radio" value="merge" v-model="duplicateAction" :disabled="!selectedDuplicate" />
                  <span class="option-icon">🔄</span>
                  <span class="option-name">智能合并</span>
                  <span class="option-desc">AI合并新旧信息</span>
                </label>
                
                <label class="option-card" :class="{ active: duplicateAction === 'overwrite', disabled: !selectedDuplicate }">
                  <input type="radio" value="overwrite" v-model="duplicateAction" :disabled="!selectedDuplicate" />
                  <span class="option-icon">📝</span>
                  <span class="option-name">覆盖更新</span>
                  <span class="option-desc">用新数据替换</span>
                </label>
                
                <label class="option-card" :class="{ active: duplicateAction === 'create' }">
                  <input type="radio" value="create" v-model="duplicateAction" />
                  <span class="option-icon">➕</span>
                  <span class="option-name">另建新条目</span>
                  <span class="option-desc">忽略重复创建</span>
                </label>
              </div>
            </div>
          </div>

          <div class="dialog-footer">
            <button class="btn-cancel" @click="goBackToForm" :disabled="merging">返回编辑</button>
            <button 
              class="btn-save" 
              @click="handleDuplicateAction"
              :disabled="merging || (!selectedDuplicate && duplicateAction !== 'create')"
            >
              <span v-if="merging" class="loading-spinner"></span>
              {{ merging ? '处理中...' : '下一步' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 合并预览对话框 -->
    <Transition name="modal">
      <div v-if="visible && currentStep === 'preview'" class="save-dialog-overlay" @click.self="goBackToDuplicate">
        <div class="preview-dialog">
          <div class="dialog-header preview-header">
            <div class="header-title">
              <span class="header-icon">👁️</span>
              <h3>合并结果预览</h3>
            </div>
            <button class="close-btn" @click="goBackToDuplicate">×</button>
          </div>

          <div class="dialog-body">
            <p class="preview-hint">
              以下是AI合并后的竞赛信息，请确认无误后保存：
            </p>

            <!-- 预览卡片 -->
            <div class="preview-card">
              <div class="preview-header-section">
                <span class="preview-badge">🤖 AI合并结果</span>
                <h3 class="preview-title">{{ mergedData.name }}</h3>
                <div class="preview-meta">
                  <span v-if="mergedData.organizer">
                    <span class="meta-icon">🏢</span> 主办方 <strong>{{ mergedData.organizer }}</strong>
                  </span>
                  <span v-if="mergedData.deadline">
                    <span class="meta-icon">📅</span> 截止日期 <strong>{{ formatDate(mergedData.deadline) }}</strong>
                  </span>
                </div>
              </div>

              <div class="preview-content">
                <!-- 参赛要求 -->
                <div class="preview-block" v-if="mergedData.requirements?.length">
                  <div class="block-header">
                    <span class="block-icon">📋</span>
                    <span class="block-title">参赛要求</span>
                  </div>
                  <ul class="block-list">
                    <li v-for="(req, idx) in mergedData.requirements" :key="idx">{{ req }}</li>
                  </ul>
                </div>

                <!-- 奖项信息 -->
                <div class="preview-block" v-if="mergedData.prize_info">
                  <div class="block-header">
                    <span class="block-icon">🏆</span>
                    <span class="block-title">奖项信息</span>
                  </div>
                  <p class="block-text">{{ mergedData.prize_info }}</p>
                </div>

                <!-- 联系方式 -->
                <div class="preview-block" v-if="mergedData.contact_info">
                  <div class="block-header">
                    <span class="block-icon">📞</span>
                    <span class="block-title">联系方式</span>
                  </div>
                  <div class="contact-items">
                    <span v-for="(c, idx) in parseContacts(mergedData.contact_info)" :key="idx" class="contact-chip">
                      {{ c }}
                    </span>
                  </div>
                </div>

                <!-- 链接 -->
                <div class="preview-block" v-if="mergedData.default_url || mergedData.entrant_url || mergedData.teacher_url">
                  <div class="block-header">
                    <span class="block-icon">🔗</span>
                    <span class="block-title">相关链接</span>
                  </div>
                  <div class="link-items">
                    <a v-if="mergedData.default_url" :href="mergedData.default_url" target="_blank" class="link-chip">
                      🌐 官网
                    </a>
                    <a v-if="mergedData.entrant_url" :href="mergedData.entrant_url" target="_blank" class="link-chip">
                      🎯 参赛入口
                    </a>
                    <a v-if="mergedData.teacher_url" :href="mergedData.teacher_url" target="_blank" class="link-chip">
                      👨‍🏫 教师入口
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="dialog-footer">
            <button class="btn-cancel" @click="goBackToDuplicate" :disabled="confirming">返回修改</button>
            <button class="btn-save" @click="confirmMerge" :disabled="confirming">
              <span v-if="confirming" class="loading-spinner"></span>
              {{ confirming ? '保存中...' : '确认保存' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { contestAPI } from '@/api'

const props = defineProps({
  visible: { type: Boolean, default: false },
  initialData: { type: Object, default: () => ({}) },
  contestId: { type: [String, Number], default: null }
})

const emit = defineEmits(['update:visible', 'success', 'close'])

// 步骤控制: form -> duplicate -> preview
const currentStep = ref('form')

// 表单数据
const form = reactive({
  name: '', organizer: '', default_url: '', entrant_url: '',
  teacher_url: '', deadline: '', prize_info: ''
})

// 参赛要求和联系方式
const requirements = ref([])
const newRequirement = ref('')
const contacts = ref([])
const newContact = ref('')

// 错误和状态
const errors = reactive({ name: '', organizer: '' })
const saving = ref(false)
const merging = ref(false)
const confirming = ref(false)

// 重名检测
const duplicateMatches = ref([])
const selectedDuplicate = ref(null)
const duplicateAction = ref('merge')

// 合并预览
const mergedData = ref({})
const mergeTargetId = ref(null)

// 计算属性
const isEdit = computed(() => !!props.contestId)
const isFormValid = computed(() => form.name.trim() && form.organizer.trim())

// 工具函数
const validateField = (field) => {
  if (field === 'name') errors.name = form.name.trim() ? '' : '请输入竞赛名称'
  else if (field === 'organizer') errors.organizer = form.organizer.trim() ? '' : '请输入主办方'
}

const addRequirement = () => {
  const val = newRequirement.value.trim()
  if (val && !requirements.value.includes(val)) requirements.value.push(val)
  newRequirement.value = ''
}

const removeRequirement = (idx) => requirements.value.splice(idx, 1)

const addContact = () => {
  const val = newContact.value.trim()
  if (val && !contacts.value.includes(val)) contacts.value.push(val)
  newContact.value = ''
}

const removeContact = (idx) => contacts.value.splice(idx, 1)

const getContactIcon = (text) => {
  const t = text.toLowerCase()
  if (t.includes('邮箱') || t.includes('email') || t.includes('@')) return '📧'
  if (t.includes('电话') || t.includes('phone') || /\d{3,}/.test(t)) return '📞'
  if (t.includes('微信') || t.includes('wechat') || t.includes('qq')) return '💬'
  if (t.includes('联系人')) return '👤'
  return '📋'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
  } catch { return dateStr }
}

const getStatusText = (status) => {
  const map = { upcoming: '即将开始', ongoing: '进行中', ended: '已结束' }
  return map[status] || status
}

const truncateText = (text, len) => {
  if (!text) return ''
  return text.length > len ? text.slice(0, len) + '...' : text
}

const parseContacts = (contactStr) => {
  if (!contactStr) return []
  return contactStr.split(/[;；\n]/).map(s => s.trim()).filter(Boolean)
}

// 重置
const resetForm = () => {
  Object.assign(form, { name: '', organizer: '', default_url: '', entrant_url: '', teacher_url: '', deadline: '', prize_info: '' })
  requirements.value = []
  newRequirement.value = ''
  contacts.value = []
  newContact.value = ''
  errors.name = ''
  errors.organizer = ''
  currentStep.value = 'form'
  duplicateMatches.value = []
  selectedDuplicate.value = null
  duplicateAction.value = 'merge'
  mergedData.value = {}
  mergeTargetId.value = null
}

// 填充数据
const fillFromInitialData = (data) => {
  if (!data) return
  form.name = data.name || ''
  form.organizer = data.organizer || ''
  form.default_url = data.default_url || ''
  form.entrant_url = data.entrant_url || ''
  form.teacher_url = data.teacher_url || ''
  form.prize_info = data.prize_info || ''
  
  const contact = data.contact_info || ''
  contacts.value = contact ? contact.split(/[;；\n]/).map(s => s.trim()).filter(Boolean) : []
  
  form.deadline = ''
  if (data.deadline) {
    const dl = String(data.deadline).trim()
    if (/^\d{4}-\d{2}-\d{2}$/.test(dl)) form.deadline = dl
    else if (/^\d{4}-\d{2}$/.test(dl)) {
      const [year, month] = dl.split('-').map(Number)
      const lastDay = new Date(year, month, 0).getDate()
      form.deadline = `${year}-${String(month).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`
    } else {
      try {
        const d = new Date(dl)
        if (!isNaN(d.getTime())) form.deadline = d.toISOString().split('T')[0]
      } catch {}
    }
  }
  
  requirements.value = Array.isArray(data.requirements) 
    ? data.requirements.filter(r => typeof r === 'string' && r.trim()) 
    : []
}

// 构建payload
const buildPayload = () => ({
  name: form.name.trim(),
  organizer: form.organizer.trim(),
  default_url: form.default_url?.trim() || null,
  entrant_url: form.entrant_url?.trim() || null,
  teacher_url: form.teacher_url?.trim() || null,
  deadline: form.deadline ? new Date(form.deadline).toISOString() : null,
  requirements: requirements.value,
  contact_info: contacts.value.length > 0 ? contacts.value.join('; ') : null,
  prize_info: form.prize_info?.trim() || null
})

// 监听
watch(() => props.visible, (val) => {
  if (val) {
    resetForm()
    if (props.initialData && Object.keys(props.initialData).length > 0) {
      fillFromInitialData(props.initialData)
    }
  }
})

watch(() => props.initialData, (val) => {
  if (props.visible && val && Object.keys(val).length > 0) fillFromInitialData(val)
}, { deep: true })

// 导航
const handleClose = () => {
  if (saving.value || merging.value || confirming.value) return
  emit('update:visible', false)
  emit('close')
}

const goBackToForm = () => {
  if (merging.value) return
  currentStep.value = 'form'
}

const goBackToDuplicate = () => {
  if (confirming.value) return
  currentStep.value = 'duplicate'
}

// 提交表单
const handleSubmit = async () => {
  validateField('name')
  validateField('organizer')
  if (errors.name || errors.organizer) return
  
  if (isEdit.value) {
    await doSave()
    return
  }
  
  saving.value = true
  try {
    const res = await contestAPI.checkDuplicate(form.name.trim())
    if (res.data?.status === 'success' && res.data.data?.has_duplicate) {
      duplicateMatches.value = res.data.data.matches
      selectedDuplicate.value = duplicateMatches.value[0] || null
      duplicateAction.value = 'merge'
      currentStep.value = 'duplicate'
    } else {
      await doSave()
    }
  } catch (e) {
    console.error('检查重名失败:', e)
    await doSave()
  } finally {
    saving.value = false
  }
}

// 处理重名操作
const handleDuplicateAction = async () => {
  if (duplicateAction.value === 'create') {
    merging.value = true
    try {
      const res = await contestAPI.createContest(buildPayload())
      if (res.data?.status === 'success') {
        merging.value = false  // 先重置状态
        emit('success', res.data.data)
        emit('update:visible', false)
        emit('close')
      } else throw new Error(res.data?.message || '保存失败')
    } catch (e) {
      alert('保存失败: ' + (e.response?.data?.message || e.message))
      merging.value = false
    }
    return
  }
  
  if (duplicateAction.value === 'overwrite' && selectedDuplicate.value) {
    merging.value = true
    try {
      const res = await contestAPI.updateContest(selectedDuplicate.value.id, buildPayload())
      if (res.data?.status === 'success') {
        merging.value = false  // 先重置状态
        emit('success', res.data.data)
        emit('update:visible', false)
        emit('close')
      } else throw new Error(res.data?.message || '更新失败')
    } catch (e) {
      if (e.response?.status === 401) {
        alert('登录已过期，请重新登录后再试')
      } else {
        alert('更新失败: ' + (e.response?.data?.message || e.message))
      }
      merging.value = false
    }
    return
  }
  
  if (duplicateAction.value === 'merge' && selectedDuplicate.value) {
    merging.value = true
    try {
      const res = await contestAPI.mergeContest(selectedDuplicate.value.id, buildPayload())
      if (res.data?.status === 'success') {
        mergedData.value = res.data.data.merged_data
        mergeTargetId.value = selectedDuplicate.value.id
        currentStep.value = 'preview'
      } else throw new Error(res.data?.message || '合并失败')
    } catch (e) {
      if (e.response?.status === 401) {
        alert('登录已过期，请重新登录后再试')
      } else {
        alert('合并失败: ' + (e.response?.data?.message || e.message))
      }
    } finally {
      merging.value = false
    }
  }
}

// 确认合并
const confirmMerge = async () => {
  confirming.value = true
  try {
    const res = await contestAPI.confirmMerge(mergeTargetId.value, mergedData.value)
    if (res.data?.status === 'success') {
      confirming.value = false  // 先重置状态
      emit('success', res.data.data)
      emit('update:visible', false)  // 直接关闭弹窗
      emit('close')
    } else throw new Error(res.data?.message || '保存失败')
  } catch (e) {
    if (e.response?.status === 401) {
      alert('登录已过期，请重新登录后再试')
    } else {
      alert('保存失败: ' + (e.response?.data?.message || e.message))
    }
    confirming.value = false
  }
}

// 直接保存
const doSave = async () => {
  saving.value = true
  try {
    const payload = buildPayload()
    const res = isEdit.value 
      ? await contestAPI.updateContest(props.contestId, payload)
      : await contestAPI.createContest(payload)
    
    if (res.data?.status === 'success') {
      saving.value = false  // 先重置状态
      emit('success', res.data.data)
      emit('update:visible', false)
      emit('close')
    } else throw new Error(res.data?.message || '保存失败')
  } catch (e) {
    if (e.response?.status === 422) {
      const detail = e.response?.data?.detail
      if (Array.isArray(detail)) {
        alert('参数校验错误:\n' + detail.map(d => d.msg).join('\n'))
        saving.value = false
        return
      }
    }
    alert('保存失败: ' + (e.response?.data?.message || e.message))
    saving.value = false
  }
}
</script>

<style scoped>
.save-dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  backdrop-filter: blur(4px);
}

.save-dialog, .duplicate-dialog, .preview-dialog {
  background: var(--bg-primary, #fff);
  border-radius: 16px;
  width: 100%;
  max-width: 640px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  animation: dialogIn 0.2s ease-out;
}

.duplicate-dialog, .preview-dialog { max-width: 800px; }

@keyframes dialogIn {
  from { opacity: 0; transform: scale(0.95) translateY(-10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

/* 头部 */
.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
}

.warning-header {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-radius: 16px 16px 0 0;
}

.preview-header {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border-radius: 16px 16px 0 0;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon { font-size: 24px; }

.header-title h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary, #1f2937);
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(255,255,255,0.8);
  font-size: 20px;
  color: var(--text-secondary, #6b7280);
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s;
}

.close-btn:hover { background: rgba(255,255,255,1); color: var(--text-primary, #1f2937); }

/* 内容区 */
.dialog-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* 提示文字 */
.duplicate-hint, .preview-hint {
  margin: 0 0 20px;
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 14px;
}

.duplicate-hint { background: #fef3c7; color: #92400e; }
.preview-hint { background: #dbeafe; color: #1e40af; }

/* 竞赛卡片列表 */
.duplicate-cards {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
  max-height: 400px;
  overflow-y: auto;
}

.contest-card {
  border: 2px solid var(--border-color, #e5e7eb);
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
}

.contest-card:hover { border-color: #93c5fd; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1); }
.contest-card.selected { border-color: #3b82f6; box-shadow: 0 4px 16px rgba(59, 130, 246, 0.2); }

/* 卡片头部 */
.card-header {
  padding: 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid var(--border-color, #e5e7eb);
}

.card-badge-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.match-badge {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 20px;
  font-weight: 500;
}

.match-badge.exact { background: #fee2e2; color: #dc2626; }
.match-badge.similar { background: #fef3c7; color: #d97706; }

.card-radio {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.card-title {
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary, #1f2937);
  line-height: 1.4;
}

.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.meta-icon { font-size: 14px; }
.meta-label { color: var(--text-secondary, #6b7280); }
.meta-value { color: var(--text-primary, #374151); font-weight: 500; }

.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.upcoming { background: #dbeafe; color: #1d4ed8; }
.status-badge.ongoing { background: #dcfce7; color: #16a34a; }
.status-badge.ended { background: #f3f4f6; color: #6b7280; }

/* 卡片内容 - 三栏 */
.card-content {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1px;
  background: var(--border-color, #e5e7eb);
}

.info-block {
  padding: 16px;
  background: #fff;
}

.block-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 2px solid #3b82f6;
}

.block-icon { font-size: 16px; }
.block-title { font-size: 13px; font-weight: 600; color: var(--text-primary, #374151); }

.block-list {
  margin: 0;
  padding-left: 16px;
  font-size: 12px;
  color: var(--text-secondary, #6b7280);
  line-height: 1.6;
}

.block-list li { margin-bottom: 4px; }
.more-hint { color: #3b82f6; font-style: italic; }

.block-text {
  margin: 0;
  font-size: 12px;
  color: var(--text-secondary, #6b7280);
  line-height: 1.6;
}

.contact-items {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.contact-chip {
  font-size: 11px;
  padding: 4px 8px;
  background: #f0fdf4;
  color: #16a34a;
  border-radius: 4px;
  border: 1px solid #bbf7d0;
}

/* 卡片底部 */
.card-footer {
  display: flex;
  gap: 12px;
  padding: 12px 20px;
  background: #f8fafc;
  border-top: 1px solid var(--border-color, #e5e7eb);
}

.card-link {
  font-size: 12px;
  color: #3b82f6;
  text-decoration: none;
}

.card-link:hover { text-decoration: underline; }

/* 操作选项 */
.action-options {
  background: var(--bg-secondary, #f9fafb);
  border-radius: 12px;
  padding: 16px;
}

/* 简洁的重名列表样式 */
.duplicate-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
  max-height: 240px;
  overflow-y: auto;
}

.duplicate-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #fff;
  border: 2px solid var(--border-color, #e5e7eb);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.duplicate-item:hover {
  border-color: #93c5fd;
  background: #f8fafc;
}

.duplicate-item.selected {
  border-color: #3b82f6;
  background: #eff6ff;
}

.duplicate-item .item-radio {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #3b82f6;
}

.duplicate-item .match-badge {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 500;
  flex-shrink: 0;
}

.duplicate-item .match-badge.exact {
  background: #dcfce7;
  color: #16a34a;
}

.duplicate-item .match-badge.similar {
  background: #fef3c7;
  color: #d97706;
}

.duplicate-item .item-name {
  flex: 1;
  font-size: 14px;
  color: var(--text-primary, #1f2937);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.duplicate-item .item-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: #f1f5f9;
  border-radius: 6px;
  color: #64748b;
  text-decoration: none;
  transition: all 0.2s;
  flex-shrink: 0;
}

.duplicate-item .item-link:hover {
  background: #3b82f6;
  color: #fff;
}

.duplicate-item .item-link .link-icon {
  font-size: 14px;
  font-weight: bold;
}

.options-title {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #374151);
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.option-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: #fff;
  border: 2px solid var(--border-color, #e5e7eb);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.option-card:hover:not(.disabled) { border-color: #93c5fd; }
.option-card.active { border-color: #3b82f6; background: #eff6ff; }
.option-card.disabled { opacity: 0.5; cursor: not-allowed; }
.option-card input { display: none; }

.option-icon { font-size: 28px; }
.option-name { font-size: 14px; font-weight: 600; color: var(--text-primary, #1f2937); }
.option-desc { font-size: 11px; color: var(--text-secondary, #6b7280); }

/* 预览卡片 */
.preview-card {
  border: 2px solid #3b82f6;
  border-radius: 16px;
  overflow: hidden;
  background: #fff;
}

.preview-header-section {
  padding: 24px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-bottom: 1px solid #bfdbfe;
}

.preview-badge {
  display: inline-block;
  font-size: 12px;
  padding: 4px 12px;
  background: #3b82f6;
  color: #fff;
  border-radius: 20px;
  margin-bottom: 12px;
}

.preview-title {
  margin: 0 0 12px;
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary, #1f2937);
}

.preview-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  font-size: 14px;
  color: var(--text-secondary, #6b7280);
}

.preview-meta strong { color: var(--text-primary, #374151); }

.preview-content {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1px;
  background: var(--border-color, #e5e7eb);
}

.preview-block {
  padding: 20px;
  background: #fff;
}

.preview-block:last-child:nth-child(odd) {
  grid-column: 1 / -1;
}

.link-items {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.link-chip {
  font-size: 13px;
  padding: 6px 12px;
  background: #eff6ff;
  color: #3b82f6;
  border-radius: 6px;
  text-decoration: none;
  border: 1px solid #bfdbfe;
}

.link-chip:hover { background: #dbeafe; }

/* 表单样式 */
.form-section { margin-bottom: 24px; }
.form-section:last-child { margin-bottom: 0; }

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--primary-color, #3b82f6);
}

.section-icon { font-size: 18px; }
.section-title { font-size: 15px; font-weight: 600; color: var(--text-primary, #374151); }

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-item { display: flex; flex-direction: column; gap: 6px; }
.form-item.full { grid-column: 1 / -1; }

.form-item label { font-size: 13px; font-weight: 500; color: var(--text-secondary, #6b7280); }
.form-item label.required::after { content: '*'; color: #ef4444; margin-left: 4px; }

.form-item input, .form-item textarea {
  padding: 10px 12px;
  border: 1px solid var(--border-color, #d1d5db);
  border-radius: 8px;
  font-size: 14px;
  color: var(--text-primary, #1f2937);
  background: var(--bg-primary, #fff);
  transition: all 0.2s;
}

.form-item input:focus, .form-item textarea:focus {
  outline: none;
  border-color: var(--primary-color, #3b82f6);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-item input.error { border-color: #ef4444; }
.form-item textarea { resize: vertical; min-height: 80px; font-family: inherit; }
.error-msg { font-size: 12px; color: #ef4444; }

/* 标签输入框 */
.tags-box {
  border: 1px solid var(--border-color, #d1d5db);
  border-radius: 8px;
  padding: 8px;
  background: var(--bg-primary, #fff);
  transition: all 0.2s;
}

.tags-box:focus-within {
  border-color: var(--primary-color, #3b82f6);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.tags-list { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.tags-list:empty { margin-bottom: 0; }

.tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  color: var(--primary-color, #3b82f6);
  border-radius: 6px;
  font-size: 13px;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.tag button {
  width: 16px; height: 16px;
  border: none; background: transparent;
  color: inherit; cursor: pointer;
  padding: 0; font-size: 14px;
  opacity: 0.6; transition: opacity 0.2s;
}

.tag button:hover { opacity: 1; }

.contact-tag {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  color: #16a34a;
  border-color: rgba(22, 163, 74, 0.2);
}

.contact-icon { font-size: 14px; margin-right: 2px; }

.tags-box input {
  width: 100%; border: none;
  padding: 6px 4px; font-size: 14px;
  background: transparent;
}

.tags-box input:focus { outline: none; box-shadow: none; }

/* 底部 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--border-color, #e5e7eb);
  background: var(--bg-secondary, #f9fafb);
  border-radius: 0 0 16px 16px;
}

.btn-cancel, .btn-save {
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-cancel {
  background: var(--bg-primary, #fff);
  color: var(--text-primary, #374151);
  border: 1px solid var(--border-color, #d1d5db);
}

.btn-cancel:hover:not(:disabled) { background: var(--bg-secondary, #f3f4f6); }

.btn-save {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #fff;
  border: none;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
}

.btn-save:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.4);
}

.btn-save:disabled, .btn-cancel:disabled { opacity: 0.6; cursor: not-allowed; }

.loading-spinner {
  width: 16px; height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* 过渡动画 */
.modal-enter-active, .modal-leave-active { transition: opacity 0.2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }

/* 响应式 */
@media (max-width: 768px) {
  .save-dialog-overlay { padding: 10px; }
  .save-dialog, .duplicate-dialog, .preview-dialog { max-height: 95vh; }
  .form-grid { grid-template-columns: 1fr; }
  .form-item { grid-column: 1; }
  .card-content { grid-template-columns: 1fr; }
  .preview-content { grid-template-columns: 1fr; }
  .options-grid { grid-template-columns: 1fr; }
  .card-meta { flex-direction: column; gap: 8px; }
}
</style>
