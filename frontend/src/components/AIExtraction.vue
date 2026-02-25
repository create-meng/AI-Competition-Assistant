<template>
  <div class="ai-extraction-container">
    <h2>AI 智能提取竞赛信息</h2>
    
    <!-- 选择AI提供商 -->
    <div class="provider-selector">
      <h3>1. 选择AI提供商</h3>
      <div v-if="providersLoading" class="loading">加载提供商列表中...</div>
      <div v-else class="provider-list">
        <div 
          v-for="provider in providers" 
          :key="provider.type"
          class="provider-card"
          :class="{ selected: selectedProvider === provider.type }"
          @click="selectProvider(provider)"
        >
          <div class="provider-header">
            <h4>{{ provider.name }}</h4>
            <span class="provider-brand" :class="getProviderBrandClass(provider.type)">
              {{ getProviderBrandText(provider.type) }}
            </span>
          </div>
          <div class="capabilities">
            <span 
              v-for="cap in provider.capabilities" 
              :key="cap"
              class="capability-tag"
            >
              {{ getCapabilityText(cap) }}
            </span>
          </div>
          <div class="model-info">
            <small>默认模型: {{ provider.default_model }}</small>
          </div>
        </div>
      </div>
    </div>

    <!-- 选择来源类型 -->
    <div class="source-type-selector" v-if="selectedProvider">
      <h3>2. 选择内容来源</h3>
      <div class="source-type-tabs">
        <button 
          class="tab-button"
          :class="{ active: sourceType === 'url' }"
          @click="sourceType = 'url'"
          :disabled="!supportsCapability('web_reading')"
        >
          <span class="icon">🌐</span>
          <span>网址</span>
          <span v-if="!supportsCapability('web_reading')" class="unsupported-hint">
            (需先抓取)
          </span>
        </button>
        <button 
          class="tab-button"
          :class="{ active: sourceType === 'file' }"
          @click="switchToFile()"
          :disabled="!supportsCapability('file_upload')"
        >
          <span class="icon">📄</span>
          <span>文件</span>
          <span v-if="!supportsCapability('file_upload')" class="unsupported-hint">
            (该提供商不支持文件直传)
          </span>
        </button>
        <button 
          class="tab-button"
          :class="{ active: sourceType === 'text' }"
          @click="sourceType = 'text'"
        >
          <span class="icon">📝</span>
          <span>文本</span>
        </button>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area" v-if="selectedProvider && sourceType">
      <h3>3. 输入内容</h3>
      
      <!-- URL输入 -->
      <div v-if="sourceType === 'url'" class="input-section">
        <input 
          v-model="urlInput"
          type="url"
          placeholder="请输入竞赛网页URL，例如: https://example.com/contest"
          class="url-input"
        />
        <div v-if="!supportsCapability('web_reading')" class="warning-message">
          ⚠️ {{ selectedProviderInfo?.name }} 不支持直接阅读网页，系统会先抓取网页内容后提交给AI分析
        </div>
      </div>

      <!-- 文件上传 -->
      <div v-if="sourceType === 'file'" class="input-section">
        <input 
          type="file"
          @change="handleFileChange"
          accept=".pdf,.txt,.html"
          class="file-input"
        />
        <div v-if="selectedFile" class="file-info">
          <p>已选择文件: {{ selectedFile.name }}</p>
          <p>大小: {{ formatFileSize(selectedFile.size) }}</p>
        </div>
        <div v-if="!supportsCapability('file_upload')" class="warning-message">
          ⚠️ {{ selectedProviderInfo?.name }} 不支持直接读取文件，系统会先解析文件内容后提交给AI分析
        </div>
      </div>

      <!-- 文本输入 -->
      <div v-if="sourceType === 'text'" class="input-section">
        <textarea 
          v-model="textInput"
          placeholder="请粘贴竞赛相关文本内容..."
          rows="10"
          class="text-input"
        ></textarea>
      </div>

      <!-- 提取按钮 -->
      <div class="action-buttons">
        <button 
          @click="startExtraction"
          :disabled="!canStartExtraction || extracting"
          class="btn-primary"
        >
          <span v-if="extracting">
            <span class="spinner"></span>
            AI 分析中...
          </span>
          <span v-else>🤖 开始AI提取</span>
        </button>
      </div>
    </div>

    <!-- 结果展示 -->
    <div class="result-area" v-if="extractionResult">
      <h3>提取结果</h3>
      
      <!-- 错误提示 -->
      <div v-if="extractionResult.status === 'error'" class="error-result">
        <div class="error-icon">❌</div>
        <h4>提取失败</h4>
        <p class="error-message">{{ extractionResult.message }}</p>
        <div v-if="extractionResult.data?.error" class="error-details">
          <p><strong>详细错误：</strong></p>
          <p>{{ extractionResult.data.error }}</p>
        </div>
        <div class="error-suggestions">
          <p><strong>建议：</strong></p>
          <ul>
            <li v-if="extractionResult.message.includes('不支持')">请尝试切换其他AI提供商</li>
            <li v-if="extractionResult.message.includes('API')">请检查API密钥配置是否正确</li>
            <li v-if="extractionResult.message.includes('网页')">请确认URL是否可访问</li>
            <li v-if="extractionResult.message.includes('文件')">请确认文件格式是否正确</li>
            <li>如果问题持续，请联系管理员</li>
          </ul>
        </div>
        <button @click="extractionResult = null" class="btn-secondary">重试</button>
      </div>

      <!-- 成功结果 -->
      <div v-else-if="extractionResult.status === 'success'" class="success-result">
        <div class="success-icon">✅</div>
        
        <!-- 置信度指示器 -->
        <div class="confidence-indicator">
          <label>AI 置信度：</label>
          <div class="confidence-bar-container">
            <div 
              class="confidence-bar"
              :class="getConfidenceClass(extractionResult.data.confidence)"
              :style="{ width: (extractionResult.data.confidence * 100) + '%' }"
            ></div>
          </div>
          <span class="confidence-value">
            {{ (extractionResult.data.confidence * 100).toFixed(0) }}%
          </span>
        </div>

        <!-- 提取的信息 -->
        <div class="extracted-info">
          <div class="info-item" v-if="extractionResult.data.extracted_json.name">
            <label>🏆 竞赛名称：</label>
            <span>{{ extractionResult.data.extracted_json.name }}</span>
          </div>

          <div class="info-item" v-if="extractionResult.data.extracted_json.organizer">
            <label>🏛️ 主办方：</label>
            <span>{{ extractionResult.data.extracted_json.organizer }}</span>
          </div>

          <div class="info-item" v-if="extractionResult.data.extracted_json.entrant_url">
            <label>🎯 参赛者入口：</label>
            <a 
              :href="extractionResult.data.extracted_json.entrant_url" 
              target="_blank"
              class="extracted-link"
            >
              {{ extractionResult.data.extracted_json.entrant_url }}
            </a>
          </div>

          <div class="info-item" v-if="extractionResult.data.extracted_json.teacher_url">
            <label>👨‍🏫 教师入口：</label>
            <a 
              :href="extractionResult.data.extracted_json.teacher_url" 
              target="_blank"
              class="extracted-link"
            >
              {{ extractionResult.data.extracted_json.teacher_url }}
            </a>
          </div>

          <div class="info-item" v-if="extractionResult.data.extracted_json.deadline">
            <label>⏰ 报名截止：</label>
            <span>{{ extractionResult.data.extracted_json.deadline }}</span>
          </div>

          <div class="info-item" v-if="extractionResult.data.extracted_json.requirements?.length">
            <label>📋 参赛要求：</label>
            <ul class="requirements-list">
              <li v-for="(req, index) in extractionResult.data.extracted_json.requirements" :key="index">
                {{ req }}
              </li>
            </ul>
          </div>

          <div class="info-item" v-if="extractionResult.data.extracted_json.contact_info">
            <label>📧 联系方式：</label>
            <span>{{ extractionResult.data.extracted_json.contact_info }}</span>
          </div>

          <div class="info-item" v-if="extractionResult.data.extracted_json.prize_info">
            <label>🏆 奖项信息：</label>
            <span>{{ extractionResult.data.extracted_json.prize_info }}</span>
          </div>

          <div class="info-item" v-if="extractionResult.data.extracted_json.notes">
            <label>💡 备注：</label>
            <span>{{ extractionResult.data.extracted_json.notes }}</span>
          </div>
        </div>

        <!-- 元数据 -->
        <div class="metadata">
          <h4>提取元数据</h4>
          <p><strong>AI提供商：</strong>{{ extractionResult.data.provider }}</p>
          <p><strong>使用模型：</strong>{{ extractionResult.data.model }}</p>
          <p><strong>提取时间：</strong>{{ formatDateTime(extractionResult.data.extraction_time) }}</p>
          <p v-if="extractionResult.data.source_url">
            <strong>来源网址：</strong>
            <a :href="extractionResult.data.source_url" target="_blank">{{ extractionResult.data.source_url }}</a>
          </p>
        </div>

        <!-- 免责声明 -->
        <div class="disclaimer">
          ⚠️ 以上信息由AI自动提取，仅供参考，请以竞赛官方网站发布的信息为准
        </div>

        <!-- 低置信度警告 -->
        <div v-if="extractionResult.data.confidence < 0.6" class="low-confidence-warning">
          ⚠️ AI对此次提取结果的置信度较低，建议人工核对信息准确性
        </div>

        <!-- 操作按钮 -->
        <div class="result-actions">
          <button @click="openSaveDialog" class="btn-primary">保存到竞赛</button>
          <button @click="viewRawResponse" class="btn-secondary">查看原始响应</button>
          <button @click="extractionResult = null" class="btn-secondary">重新提取</button>
        </div>
      </div>
    </div>

    <!-- 原始响应模态框 -->
    <div v-if="showRawResponse" class="modal-overlay" @click="showRawResponse = false">
      <div class="modal-content" @click.stop>
        <h3>AI 原始响应</h3>
        <pre class="raw-response">{{ extractionResult.data.raw_response }}</pre>
        <button @click="showRawResponse = false" class="btn-secondary">关闭</button>
      </div>
    </div>

    <!-- 保存到竞赛对话框 -->
    <SaveContestDialog
      v-model:visible="showSaveDialog"
      :initial-data="saveDialogInitialData"
      @success="onSaveSuccess"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import SaveContestDialog from '@/components/SaveContestDialog.vue'
import api from '@/api'

export default {
  name: 'AIExtraction',
  components: {
    SaveContestDialog
  },
  setup() {
    // 提供商相关
    const providers = ref([])
    const providersLoading = ref(true)
    const selectedProvider = ref(null)
    const selectedProviderInfo = ref(null)

    // 来源类型
    const sourceType = ref(null)

    // 输入内容
    const urlInput = ref('')
    const textInput = ref('')
    const selectedFile = ref(null)
    const uploadedFileId = ref(null)

    // 提取状态
    const extracting = ref(false)
    const extractionResult = ref(null)
    const showRawResponse = ref(false)
    
    // 保存竞赛对话框
    const showSaveDialog = ref(false)
    const saveDialogInitialData = ref({})

    // 加载提供商列表
    const loadProviders = async () => {
      try {
        const response = await api.get('/api/v1/ai/providers')
        if (response.data.status === 'success') {
          providers.value = response.data.data
        }
      } catch (error) {
        console.error('加载提供商列表失败:', error)
      } finally {
        providersLoading.value = false
      }
    }

    // 选择提供商
    const selectProvider = (provider) => {
      selectedProvider.value = provider.type
      selectedProviderInfo.value = provider
      sourceType.value = null
    }

    // 检查是否支持某个能力
    const supportsCapability = (capability) => {
      if (!selectedProviderInfo.value) return false
      return selectedProviderInfo.value.capabilities.includes(capability)
    }

    // 获取能力文本
    const getCapabilityText = (capability) => {
      const texts = {
        'text_only': '📝 文本',
        'file_upload': '📄 文件',
        'web_reading': '🌐 网页',
        'image_reading': '🖼️ 图片'
      }
      return texts[capability] || capability
    }

    // 获取提供商品牌文本
    const getProviderBrandText = (providerType) => {
      const brandTexts = {
        'cloudflare': 'CLOUDFLARE',
        'google': 'GOOGLE',
        'cerebras': 'CEREBRAS',
        'doubao': 'DOUBAO'
      }
      return brandTexts[providerType] || providerType.toUpperCase()
    }

    // 获取提供商品牌样式类
    const getProviderBrandClass = (providerType) => {
      return `brand-${providerType}`
    }

    // 文件选择处理
    const handleFileChange = async (event) => {
      const file = event.target.files[0]
      if (!file) return

      selectedFile.value = file

      // 上传文件
      const formData = new FormData()
      formData.append('file', file)

      try {
        const response = await api.post('/api/v1/documents/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        if (response.data.status === 'success') {
          uploadedFileId.value = response.data.data._id
        }
      } catch (error) {
        console.error('文件上传失败:', error)
        alert('文件上传失败: ' + (error.response?.data?.message || error.message))
      }
    }

    // 格式化文件大小
    const formatFileSize = (bytes) => {
      if (bytes < 1024) return bytes + ' B'
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
      return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
    }

    // 检查是否可以开始提取
    const canStartExtraction = computed(() => {
      if (sourceType.value === 'url') return urlInput.value.trim() !== ''
      if (sourceType.value === 'file') return uploadedFileId.value !== null
      if (sourceType.value === 'text') return textInput.value.trim() !== ''
      return false
    })

    // 开始提取
    // 取消控制
    let abortController = null

    const cancelOngoing = () => {
      if (abortController) {
        abortController.abort()
        abortController = null
      }
    }

    const switchToFile = () => {
      if (!supportsCapability('file_upload')) return
      sourceType.value = 'file'
    }

    const startExtraction = async () => {
      extracting.value = true
      extractionResult.value = null

      try {
        // 切换前先取消
        cancelOngoing()
        abortController = new AbortController()
        
        const requestData = {
          provider: selectedProvider.value,
          source_type: sourceType.value,
          prompt_template: 'unified_extraction_v4'
        }

        if (sourceType.value === 'url') {
          requestData.source_content = urlInput.value
        } else if (sourceType.value === 'file') {
          requestData.file_id = uploadedFileId.value
        } else if (sourceType.value === 'text') {
          requestData.source_content = textInput.value
        }

        const response = await api.post('/api/v1/ai/extract', requestData, { signal: abortController.signal })
        extractionResult.value = response.data

      } catch (error) {
        console.error('AI提取失败:', error)
        extractionResult.value = {
          status: 'error',
          message: error.response?.data?.message || error.message,
          data: error.response?.data?.data || null
        }
      } finally {
        extracting.value = false
      }
    }

    // 获取置信度样式类
    const getConfidenceClass = (confidence) => {
      if (confidence >= 0.8) return 'high'
      if (confidence >= 0.6) return 'medium'
      return 'low'
    }

    // 格式化日期时间
    const formatDateTime = (dateStr) => {
      if (!dateStr) return ''
      return new Date(dateStr).toLocaleString('zh-CN')
    }

    // 查看原始响应
    const viewRawResponse = () => {
      showRawResponse.value = true
    }

    // 打开保存对话框
    const openSaveDialog = () => {
      const ej = extractionResult.value?.data?.extracted_json || {}
      
      // 将AI提取的嵌套结构展平，方便SaveContestDialog处理
      // AI v3返回格式: { contest: {...}, dates: {...}, requirements: {...}, evaluation: {...}, contact: {...} }
      const flatData = {
        // 直接传递原始数据，让SaveContestDialog处理嵌套结构
        ...ej,
        // 同时提供展平的字段作为备用
        name: ej.contest?.name || ej.name || '',
        organizer: ej.contest?.organizer || ej.organizer || '',
        default_url: ej.contest?.default_url || ej.default_url || '',
        entrant_url: ej.contest?.entrant_url || ej.entrant_url || '',
        teacher_url: ej.contest?.teacher_url || ej.teacher_url || '',
        deadline: ej.dates?.deadline || ej.deadline || '',
        contact_info: ej.contact?.contact_info || ej.contact_info || '',
        prize_info: ej.evaluation?.prize_info || ej.prize_info || ''
      }
      
      saveDialogInitialData.value = flatData
      showSaveDialog.value = true
    }

    // 保存成功回调
    const onSaveSuccess = (contest) => {
      console.log('竞赛保存成功:', contest)
      alert('保存成功！')
    }

    onMounted(() => {
      loadProviders()
    })

    return {
      providers,
      providersLoading,
      selectedProvider,
      selectedProviderInfo,
      sourceType,
      urlInput,
      textInput,
      selectedFile,
      extracting,
      extractionResult,
      showRawResponse,
      showSaveDialog,
      saveDialogInitialData,
      canStartExtraction,
      selectProvider,
      supportsCapability,
      getCapabilityText,
      getProviderBrandText,
      getProviderBrandClass,
      handleFileChange,
      formatFileSize,
      startExtraction,
      getConfidenceClass,
      formatDateTime,
      viewRawResponse,
      switchToFile,
      cancelOngoing,
      openSaveDialog,
      onSaveSuccess
    }
  }
}
</script>

<style scoped>
.ai-extraction-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

h2 {
  color: #333;
  margin-bottom: 30px;
}

h3 {
  color: #555;
  margin: 20px 0 15px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e0e0e0;
}

/* 提供商选择 */
.provider-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 15px;
  margin-top: 15px;
}

.provider-card {
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s;
}

.provider-card:hover {
  border-color: #4CAF50;
  box-shadow: 0 2px 8px rgba(76, 175, 80, 0.2);
}

.provider-card.selected {
  border-color: #4CAF50;
  background: #f1f8f4;
}

.provider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.provider-card h4 {
  margin: 0;
  color: #333;
  flex: 1;
}

.provider-brand {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: bold;
  color: white;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 各提供商品牌样式 */
.brand-cloudflare {
  background: linear-gradient(135deg, #f38020, #ff6b35);
}

.brand-google {
  background: linear-gradient(135deg, #4285f4, #34a853);
}

.brand-cerebras {
  background: linear-gradient(135deg, #ff6b35, #f7931e);
}

.brand-doubao {
  background: linear-gradient(135deg, #1976d2, #42a5f5);
}

.capabilities {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 10px;
}

.capability-tag {
  background: #e3f2fd;
  color: #1976d2;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 12px;
}

.model-info {
  color: #777;
  font-size: 12px;
}

/* 来源类型选择 */
.source-type-tabs {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.tab-button {
  flex: 1;
  padding: 15px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  transition: all 0.3s;
}

.tab-button:hover:not(:disabled) {
  border-color: #4CAF50;
}

.tab-button.active {
  border-color: #4CAF50;
  background: #f1f8f4;
}

.tab-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tab-button .icon {
  font-size: 24px;
}

.unsupported-hint {
  font-size: 11px;
  color: #ff9800;
}

/* 输入区域 */
.input-section {
  margin-top: 15px;
}

.url-input,
.text-input {
  width: 100%;
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
}

.url-input:focus,
.text-input:focus {
  outline: none;
  border-color: #4CAF50;
}

.file-input {
  width: 100%;
  padding: 10px;
}

.file-info {
  margin-top: 10px;
  padding: 10px;
  background: #f5f5f5;
  border-radius: 6px;
}

.warning-message {
  margin-top: 10px;
  padding: 12px;
  background: #fff3e0;
  border-left: 4px solid #ff9800;
  color: #e65100;
  border-radius: 4px;
}

/* 按钮 */
.action-buttons {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}

.btn-primary,
.btn-secondary {
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background: #4CAF50;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #45a049;
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
}

.btn-secondary:hover {
  background: #e0e0e0;
}

.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: 8px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 结果区域 */
.result-area {
  margin-top: 30px;
  padding: 20px;
  background: #fafafa;
  border-radius: 8px;
}

.error-result,
.success-result {
  padding: 20px;
  background: white;
  border-radius: 8px;
}

.error-result {
  border-left: 4px solid #f44336;
}

.success-result {
  border-left: 4px solid #4CAF50;
}

.error-icon,
.success-icon {
  font-size: 48px;
  text-align: center;
  margin-bottom: 15px;
}

.error-message {
  color: #f44336;
  font-size: 16px;
  margin: 10px 0;
}

.error-details {
  margin-top: 15px;
  padding: 10px;
  background: #ffebee;
  border-radius: 4px;
}

.error-suggestions {
  margin-top: 15px;
  padding: 10px;
  background: #fff3e0;
  border-radius: 4px;
}

.error-suggestions ul {
  margin: 5px 0 0 20px;
}

/* 置信度指示器 */
.confidence-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 6px;
}

.confidence-bar-container {
  flex: 1;
  height: 24px;
  background: #e0e0e0;
  border-radius: 12px;
  overflow: hidden;
}

.confidence-bar {
  height: 100%;
  transition: width 0.5s;
}

.confidence-bar.high {
  background: linear-gradient(90deg, #4CAF50, #66BB6A);
}

.confidence-bar.medium {
  background: linear-gradient(90deg, #FFC107, #FFD54F);
}

.confidence-bar.low {
  background: linear-gradient(90deg, #F44336, #EF5350);
}

.confidence-value {
  font-weight: bold;
  min-width: 50px;
  text-align: right;
}

/* 提取信息 */
.extracted-info {
  margin: 20px 0;
}

.info-item {
  margin-bottom: 15px;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 6px;
}

.info-item label {
  display: block;
  font-weight: bold;
  color: #555;
  margin-bottom: 5px;
}

.extracted-link {
  color: #1976d2;
  text-decoration: none;
  word-break: break-all;
}

.extracted-link:hover {
  text-decoration: underline;
}

.requirements-list {
  margin: 5px 0 0 20px;
}

/* 元数据 */
.metadata {
  margin-top: 20px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 6px;
  font-size: 14px;
}

.metadata h4 {
  margin-top: 0;
}

.metadata p {
  margin: 8px 0;
}

/* 免责声明 */
.disclaimer,
.low-confidence-warning {
  margin-top: 15px;
  padding: 12px;
  border-radius: 6px;
  font-size: 14px;
}

.disclaimer {
  background: #fff3e0;
  border-left: 4px solid #ff9800;
  color: #e65100;
}

.low-confidence-warning {
  background: #ffebee;
  border-left: 4px solid #f44336;
  color: #c62828;
}

/* 结果操作按钮 */
.result-actions {
  margin-top: 20px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

/* 模态框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 8px;
  max-width: 800px;
  max-height: 80vh;
  overflow: auto;
}

.raw-response {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.loading {
  text-align: center;
  padding: 20px;
  color: #777;
}
</style>

