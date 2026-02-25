<template>
  <div class="extract-container">
    <div class="page-header">
        <div class="header-content">
          <h1>🤖 AI智能提取</h1>
        <p class="subtitle">使用AI自动提取竞赛信息，支持网址、文件和文本</p>
        <button class="btn-secondary" @click="$router.push('/home')">
          <span class="icon">←</span>
          返回首页
        </button>
        </div>
    </div>
    
    <div class="main-content">
      <!-- 单列布局 -->
      <div class="single-column">
          <!-- 选择AI提供商 -->
          <div class="section">
            <h2>1. 选择AI提供商</h2>
        <div v-if="providersLoading" class="loading-state">
          <div class="spinner"></div>
          <div class="progress-stats">
            <span class="stat-item">
              <span class="stat-label">已检查:</span>
              <span class="stat-value">{{ healthCheckProgress.current }}/{{ healthCheckProgress.total }}</span>
            </span>
            <span class="stat-item">
              <span class="stat-label">通过:</span>
              <span class="stat-value success">{{ healthCheckProgress.available }}/{{ healthCheckProgress.total }}</span>
            </span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: healthCheckProgress.total > 0 ? (healthCheckProgress.current / healthCheckProgress.total * 100) + '%' : '0%' }"></div>
          </div>
          <p class="loading-subtitle">正在测试AI提供商的连接状态，这可能需要30秒</p>
          <div class="health-check-info">
            <div class="info-item">
              <span class="icon">🔍</span>
              <span>检查API密钥配置</span>
            </div>
            <div class="info-item">
              <span class="icon">🌐</span>
              <span>测试网络连接</span>
            </div>
            <div class="info-item">
              <span class="icon">⚡</span>
              <span>验证AI服务响应</span>
            </div>
          </div>
        </div>
        <div v-else class="provider-grid">
          <div 
            v-for="provider in providers" 
            :key="provider.type"
            class="provider-card"
            :class="{ 
              selected: selectedProvider === provider.type,
              unavailable: provider.status === 'unavailable',
              available: provider.status === 'available'
            }"
            @click="selectProvider(provider)"
          >
            <div class="provider-header">
              <h3>{{ provider.name }}</h3>
              <div class="provider-badge" :class="provider.type">
                {{ provider.type.toUpperCase() }}
              </div>
            </div>
            
            <!-- 状态指示器 -->
            <div class="status-indicator">
              <div class="status-badge" :class="provider.status">
                <span class="status-icon">
                  {{ getStatusIcon(provider.status) }}
                </span>
                <span class="status-text">{{ getStatusText(provider.status) }}</span>
              </div>
              <div v-if="provider.reason" class="status-reason">
                {{ provider.reason }}
              </div>
            </div>
            
            <!-- 模型选择 -->
            <div v-if="provider.status === 'available'" class="model-selection">
              <label class="model-label">选择模型:</label>
              <select 
                v-model="selectedModels[provider.type]"
                class="model-select"
                @change="onModelChange(provider.type, $event)"
              >
                <option 
                  v-for="model in provider.available_models" 
                  :key="model"
                  :value="model"
                >
                  {{ model }} {{ getModelCapabilitiesText(provider.type, model) }}
                </option>
              </select>
            </div>
            
            <div v-else class="model-info">
              <small>暂不可用</small>
            </div>
            
            <!-- 性能信息 -->
            <div v-if="provider.status === 'available' && provider.response_time" class="performance-info">
              <small>响应时间: {{ provider.response_time.toFixed(2) }}s</small>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入合并（URL/文件/文本同时提供，系统自动合并） -->
      <div class="section" v-if="selectedProvider">
        <div class="section-header">
          <h2>2. 输入内容（可多选，自动合并）</h2>
          <button 
            @click="clearAllInputs"
            class="btn-clear"
            :disabled="!hasAnyInput"
            title="清空所有输入内容"
          >
            <span class="icon">🗑️</span>
            一键清空
          </button>
        </div>
        <div class="input-section">
          <div class="input-group">
            <label for="url-input">竞赛网页URL（可选）</label>
            <input 
              id="url-input"
              v-model="urlInput"
              type="url"
              placeholder="https://example.com/contest"
              class="url-input"
            />
            <div v-if="!supportsCapability('web_reading')" class="warning-message">
              ⚠️ {{ selectedProviderInfo?.name }} 不支持直接阅读网页，系统会先抓取网页内容后提交给AI分析
            </div>
          </div>

          <div class="file-upload-area">
            <input 
              type="file"
              @change="handleFileChange"
              accept=".pdf,.txt,.html"
              class="file-input"
              id="file-input"
            />
            <label for="file-input" class="file-upload-label">
              <div class="upload-icon">📁</div>
              <div class="upload-text">
                <strong>点击选择文件</strong>
                <span>或拖拽文件到这里</span>
              </div>
              <div class="upload-tip">支持 PDF、TXT、HTML 文件，最大 20MB</div>
            </label>
          </div>
          <div v-if="selectedFile" class="file-info">
            <div class="file-details">
              <span class="file-name">{{ selectedFile.name }}</span>
              <span class="file-size">{{ formatFileSize(selectedFile.size) }}</span>
            </div>
          </div>

          <div class="input-group">
            <label for="text-input">补充文本（可选）</label>
            <textarea 
              id="text-input"
              v-model="textInput"
              placeholder="可粘贴补充说明、通知片段等..."
              rows="10"
              class="text-input"
            ></textarea>
          </div>
        </div>
      </div>

          <!-- 提交按钮 -->
          <div class="section" v-if="selectedProvider">
            <h2>3. 提交</h2>
            <div class="action-section">
              <button 
                @click="startExtraction"
                :disabled="!canStartExtraction || extracting"
                class="btn-primary btn-extract"
              >
                <span v-if="extracting">
                  <span class="spinner"></span>
                  AI 分析中...
                </span>
                <span v-else>
                  <span class="icon">🤖</span>
                  开始AI提取
                </span>
              </button>
              <button 
                v-if="extracting"
                @click="cancelExtraction"
                class="btn-danger btn-cancel"
              >
                <span class="icon">⏹</span>
                终止任务
              </button>
            </div>
          </div>

          <!-- 任务进度（始终显示直到用户清空） -->
          <div class="section" v-if="jobData">
            <h2>4. 任务进度</h2>
            <div class="job-progress">
              <div class="job-meta">
                <div class="meta-item"><label>任务ID：</label><span>{{ jobId || '-' }}</span></div>
                <div class="meta-item"><label>状态：</label><span>{{ jobData?.status || (extracting ? 'running' : '-') }}</span></div>
                <div class="meta-item" v-if="jobError"><label>错误：</label><span class="error-text">{{ jobError }}</span></div>
              </div>
              <div class="steps" v-if="jobData?.steps?.length">
                <div class="step" v-for="(s, idx) in jobData.steps" :key="idx" :class="s.status">
                  <div class="step-head">
                    <span class="step-index">{{ idx + 1 }}</span>
                    <span class="step-name">{{ s.name.toUpperCase() }}</span>
                    <span class="step-status">{{ stepStatusText(s.status) }}</span>
                  </div>
                  <!-- 失败时显示详细错误信息 -->
                  <div v-if="s.status === 'failed' && s.detail" class="step-error-detail">
                    <pre class="error-message">{{ s.detail }}</pre>
                  </div>
                  <!-- 非失败状态显示普通详情 -->
                  <div v-else-if="s.detail" class="step-detail">{{ s.detail }}</div>
                  <!-- 查看解析内容按钮 -->
                  <div v-if="s.name === 'fetch' && s.status === 'completed'" class="step-actions">
                    <button 
                      v-if="extractedContent.url"
                      @click="showExtractedContent('url')"
                      class="btn-view-detail"
                    >
                      📄 查看URL解析内容 ({{ Math.round(extractedContent.url.length / 1000) }}k字符)
                    </button>
                    <button 
                      v-if="extractedContent.file"
                      @click="showExtractedContent('file')"
                      class="btn-view-detail"
                    >
                      📄 查看文件解析内容 ({{ Math.round(extractedContent.file.length / 1000) }}k字符)
                    </button>
                    <div v-if="!extractedContent.url && !extractedContent.file" class="no-content-tip">
                      ℹ️ 本次提取未获取到可查看的原始内容
                    </div>
                  </div>
                </div>
              </div>
              <div class="steps" v-else>
                <div class="step running">
                  <div class="step-head">
                    <span class="spinner"></span>
                    <span>任务正在启动…</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        <!-- 结果展示区（完成或失败后显示） -->
        <div class="section" v-if="extractionResult">
          <!-- 提取结果 -->
          <div>
            <h2>5. 提取结果</h2>
            
            <!-- 错误提示 -->
            <div v-if="extractionResult.status === 'error'" class="result-card error-result">
              <div class="result-header">
                <div class="result-icon error">❌</div>
                <h3>提取失败</h3>
              </div>
              <div class="error-content">
                <p class="error-message">{{ extractionResult.message }}</p>
                <div v-if="extractionResult.data?.error" class="error-details">
                  <h4>详细错误：</h4>
                  <p>{{ extractionResult.data.error }}</p>
                </div>
                <div v-if="extractionResult.data?.raw_response" class="raw-response-section">
                  <h4>原始响应：</h4>
                  <div class="raw-response-container">
                    <pre class="raw-response-content">{{ extractionResult.data.raw_response }}</pre>
                    <button @click="copyRawResponse" class="btn-copy">复制</button>
                  </div>
                </div>
                <div class="error-suggestions">
                  <h4>建议：</h4>
                  <ul>
                    <li v-if="extractionResult.message.includes('不支持')">请尝试切换其他AI提供商</li>
                    <li v-if="extractionResult.message.includes('API')">请检查API密钥配置是否正确</li>
                    <li v-if="extractionResult.message.includes('网页')">请确认URL是否可访问</li>
                    <li v-if="extractionResult.message.includes('文件')">请确认文件格式是否正确</li>
                    <li v-if="extractionResult.message.includes('JSON格式')">AI返回格式异常，请尝试重新提取或切换提供商</li>
                    <li>如果问题持续，请联系管理员</li>
                  </ul>
                </div>
                <div class="error-actions">
                  <button @click="viewRawResponse" class="btn-debug" v-if="extractionResult.data?.raw_response">
                    <span class="icon">🔍</span> 查看完整原始响应
                  </button>
                  <button @click="extractionResult = null" class="btn-secondary">重试</button>
                </div>
              </div>
            </div>

            <!-- 成功结果 -->
            <div v-else-if="extractionResult.status === 'success'" class="result-card success-result">
              <div class="result-header">
                <div class="result-icon success">✅</div>
                <h3>提取成功</h3>
                <div class="confidence-badge" :class="getConfidenceClass(extractionResult.data.confidence)">
                  {{ (extractionResult.data.confidence * 100).toFixed(0) }}% 置信度
                </div>
              </div>
              
              <!-- 主要信息卡片 -->
              <div class="main-info-grid">
                <!-- 竞赛基本信息 -->
                <div class="info-card" v-if="extractionResult.data.extracted_json.name || extractionResult.data.extracted_json.organizer">
                  <h4>🏆 竞赛信息</h4>
                  <div class="info-content">
                    <div v-if="extractionResult.data.extracted_json.name">
                      <strong>竞赛名称：</strong>{{ extractionResult.data.extracted_json.name }}
                    </div>
                    <div v-if="extractionResult.data.extracted_json.organizer">
                      <strong>主办方：</strong>{{ extractionResult.data.extracted_json.organizer }}
                    </div>
                    <div v-if="extractionResult.data.extracted_json.category">
                      <strong>竞赛类别：</strong>{{ extractionResult.data.extracted_json.category }}
                    </div>
                    <div v-if="extractionResult.data.extracted_json.default_url">
                      <strong>官网：</strong>
                      <a :href="extractionResult.data.extracted_json.default_url" target="_blank" class="extracted-link">
                        {{ extractionResult.data.extracted_json.default_url }}
                      </a>
                    </div>
                  </div>
                </div>

                <!-- 入口链接 -->
                <div class="info-card" v-if="extractionResult.data.extracted_json.entrant_url || extractionResult.data.extracted_json.teacher_url">
                  <h4>🔗 参赛入口</h4>
                  <div class="info-content">
                    <div v-if="extractionResult.data.extracted_json.entrant_url">
                      <strong>🎯 参赛者入口：</strong>
                      <a :href="extractionResult.data.extracted_json.entrant_url" target="_blank" class="extracted-link">
                        {{ extractionResult.data.extracted_json.entrant_url }}
                      </a>
                    </div>
                    <div v-if="extractionResult.data.extracted_json.teacher_url">
                      <strong>👨‍🏫 教师入口：</strong>
                      <a :href="extractionResult.data.extracted_json.teacher_url" target="_blank" class="extracted-link">
                        {{ extractionResult.data.extracted_json.teacher_url }}
                      </a>
                    </div>
                  </div>
                </div>

                <!-- 时间安排 -->
                <div class="info-card" v-if="extractionResult.data.extracted_json.deadline || extractionResult.data.extracted_json.start_date || extractionResult.data.extracted_json.publish_time">
                  <h4>📅 时间安排</h4>
                  <div class="info-content">
                    <div v-if="extractionResult.data.extracted_json.deadline">
                      <strong>报名截止：</strong>{{ extractionResult.data.extracted_json.deadline }}
                    </div>
                    <div v-if="extractionResult.data.extracted_json.start_date">
                      <strong>开始时间：</strong>{{ extractionResult.data.extracted_json.start_date }}
                    </div>
                    <div v-if="extractionResult.data.extracted_json.publish_time">
                      <strong>发布时间：</strong>{{ extractionResult.data.extracted_json.publish_time }}
                    </div>
                  </div>
                </div>

                <!-- 参赛要求 -->
                <div class="info-card" v-if="extractionResult.data.extracted_json.requirements?.length || extractionResult.data.extracted_json.team_min || extractionResult.data.extracted_json.team_max">
                  <h4>📋 参赛要求</h4>
                  <div class="info-content">
                    <div v-if="extractionResult.data.extracted_json.team_min || extractionResult.data.extracted_json.team_max">
                      <strong>团队规模：</strong>
                      {{ extractionResult.data.extracted_json.team_min || 1 }}-{{ extractionResult.data.extracted_json.team_max || 5 }}人
                    </div>
                    <div v-if="extractionResult.data.extracted_json.requirements?.length">
                      <strong>参赛资格：</strong>
                      <ul class="requirements-list">
                        <li v-for="(req, index) in extractionResult.data.extracted_json.requirements" :key="index">
                          {{ req }}
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>

                <!-- 奖项信息 -->
                <div class="info-card" v-if="extractionResult.data.extracted_json.prize_info">
                  <h4>🏆 奖项设置</h4>
                  <div class="info-content">
                    <div>
                      <p class="prize-text">{{ extractionResult.data.extracted_json.prize_info }}</p>
                    </div>
                  </div>
                </div>

                <!-- 联系方式 -->
                <div class="info-card" v-if="extractionResult.data.extracted_json.contact_info">
                  <h4>📞 联系方式</h4>
                  <div class="info-content contact-list">
                    <div 
                      v-for="(item, index) in formatContactInfo(extractionResult.data.extracted_json.contact_info)" 
                      :key="index"
                      class="contact-item"
                    >
                      {{ item }}
                    </div>
                  </div>
                </div>

                <!-- 备注信息 -->
                <div class="info-card" v-if="extractionResult.data.extracted_json.notes">
                  <h4>💡 备注信息</h4>
                  <div class="info-content">
                    <p class="requirement-text">{{ extractionResult.data.extracted_json.notes }}</p>
                  </div>
                </div>
              </div>

              <!-- 元数据 -->
              <div class="metadata">
                <h4>提取元数据</h4>
                <div class="metadata-grid">
                  <div class="metadata-item">
                    <label>AI提供商：</label>
                    <span>{{ extractionResult.data.provider }}</span>
                  </div>
                  <div class="metadata-item">
                    <label>使用模型：</label>
                    <span>{{ extractionResult.data.model }}</span>
                  </div>
                  <div class="metadata-item">
                    <label>提取时间：</label>
                    <span>{{ formatDateTime(extractionResult.data.extraction_time) }}</span>
                  </div>
                  <div class="metadata-item" v-if="extractionResult.data.source_url">
                    <label>来源网址：</label>
                    <a :href="extractionResult.data.source_url" target="_blank">{{ extractionResult.data.source_url }}</a>
                  </div>
                </div>
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
                <button @click="viewRawResponse" class="btn-debug" title="查看AI返回的原始数据，便于调试">
                  <span class="icon">🔍</span> 查看原始响应
                </button>
                <button @click="extractionResult = null" class="btn-secondary">重新提取</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 原始响应模态框 -->
    <div v-if="showRawResponse" class="modal-overlay" @click="showRawResponse = false">
      <div class="modal-content modal-large" @click.stop>
        <div class="modal-header">
          <div>
            <h3>🔍 AI 原始响应调试</h3>
            <p class="modal-subtitle">查看AI返回的原始数据，便于调试和问题排查</p>
          </div>
          <button @click="showRawResponse = false" class="modal-close">×</button>
        </div>
        <div class="modal-body">
          <div class="raw-response-info" v-if="rawResponseMetadata">
            <div class="metadata-item">
              <strong>提供商：</strong>{{ rawResponseMetadata.provider }}
            </div>
            <div class="metadata-item">
              <strong>模型：</strong>{{ rawResponseMetadata.model }}
            </div>
            <div class="metadata-item">
              <strong>置信度：</strong>{{ rawResponseMetadata.confidence ? (rawResponseMetadata.confidence * 100).toFixed(0) + '%' : 'N/A' }}
            </div>
          </div>
          <div class="raw-response-tabs">
            <button 
              class="tab-button" 
              :class="{ active: rawResponseTab === 'formatted' }"
              @click="rawResponseTab = 'formatted'"
            >
              格式化显示
            </button>
            <button 
              class="tab-button" 
              :class="{ active: rawResponseTab === 'raw' }"
              @click="rawResponseTab = 'raw'"
            >
              原始文本
            </button>
          </div>
          <div class="raw-response-content">
            <pre v-if="rawResponseTab === 'formatted'" class="raw-response formatted">{{ formatRawResponse(currentRawResponse) }}</pre>
            <pre v-else class="raw-response">{{ currentRawResponse }}</pre>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="copyRawResponse" class="btn-primary">
            <span class="icon">📋</span> 复制到剪贴板
          </button>
          <button @click="downloadRawResponse" class="btn-secondary">
            <span class="icon">💾</span> 下载为文件
          </button>
          <button @click="showRawResponse = false" class="btn-secondary">关闭</button>
        </div>
      </div>
    </div>

    <!-- 查看解析内容模态框 -->
    <div v-if="showExtractedContentModal" class="modal-overlay" @click="showExtractedContentModal = false">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ currentViewContent.type }}</h3>
          <button @click="showExtractedContentModal = false" class="modal-close">×</button>
        </div>
        <div class="modal-body">
          <pre class="extracted-content-view">{{ currentViewContent.content }}</pre>
        </div>
        <div class="modal-footer">
          <button @click="showExtractedContentModal = false" class="btn-secondary">关闭</button>
        </div>
      </div>
    </div>

    <!-- 登录提示模态框 -->
    <div v-if="showLoginPrompt" class="modal-overlay" @click="showLoginPrompt = false">
      <div class="modal-content login-prompt-modal" @click.stop>
        <div class="modal-header">
          <h3>🔐 需要登录</h3>
          <button @click="showLoginPrompt = false" class="modal-close">×</button>
        </div>
        <div class="modal-body">
          <div class="login-prompt-content">
            <div class="login-icon">👤</div>
            <h4>请先登录后再使用AI提取功能</h4>
            <p>登录后您可以：</p>
            <ul class="feature-list">
              <li>✅ 使用AI智能提取竞赛信息</li>
              <li>✅ 保存提取结果到竞赛库</li>
              <li>✅ 管理您的竞赛项目</li>
              <li>✅ 享受完整的个性化服务</li>
            </ul>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="goToLogin" class="btn-primary">立即登录</button>
          <button @click="showLoginPrompt = false" class="btn-secondary">稍后再说</button>
        </div>
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

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { aiAPI } from '@/api'
import SaveContestDialog from '@/components/SaveContestDialog.vue'

const userStore = useUserStore()
const router = useRouter()

// 提供商相关
const providers = ref([])
const providersLoading = ref(true)
const selectedProvider = ref(null)
const selectedProviderInfo = ref(null)
const selectedModels = ref({})  // 存储每个提供商选择的模型

// 来源类型
// 源输入改为合并，不再区分类型
const sourceType = ref('auto')

// 输入内容
const urlInput = ref('')
const textInput = ref('')
const selectedFile = ref(null)
const uploadedFileId = ref(null)

// 提取状态
const extracting = ref(false)
const extractionResult = ref(null)
const showRawResponse = ref(false)
const rawResponseTab = ref('formatted')  // 'formatted' or 'raw'
const currentRawResponse = ref('')
const rawResponseMetadata = ref(null)

// 保存竞赛对话框
const showSaveDialog = ref(false)
const saveDialogInitialData = ref({})

// 任务式提取状态
const jobId = ref(null)
const jobData = ref(null)
const jobPolling = ref(false)
const jobError = ref(null)

// 解析内容存储
const extractedContent = ref({
  url: null,
  file: null
})

// 查看解析内容模态框
const showExtractedContentModal = ref(false)
const currentViewContent = ref({ type: '', content: '' })

// 登录提示模态框
const showLoginPrompt = ref(false)

const stepStatusText = (status) => {
  const map = { pending: '待执行', running: '进行中', completed: '已完成', failed: '失败' }
  return map[status] || status
}

const startJobPolling = (id) => {
  jobPolling.value = true
  let pollCount = 0
  const maxPolls = 120 // 最多轮询2分钟（120 * 1秒）
  
  const tick = async () => {
    if (!jobPolling.value) return
    
    pollCount++
    console.log(`🔄 轮询任务状态 #${pollCount}, jobId: ${id}`)
    
    // 防止无限轮询
    if (pollCount > maxPolls) {
      console.warn('⚠️ 轮询超时，停止轮询')
      jobPolling.value = false
      extracting.value = false
      extractionResult.value = { 
        status: 'error', 
        message: '任务处理超时，请检查网络连接或稍后重试', 
        data: null 
      }
      return
    }
    
    try {
      const resp = await aiAPI.getExtractionJobStatus(id)
      console.log(`📦 轮询响应 #${pollCount}:`, JSON.stringify(resp.data, null, 2))
      
      if (resp.data?.status === 'success') {
        const newJobData = resp.data.data
        console.log(`📊 任务数据:`, {
          status: newJobData?.status,
          steps: newJobData?.steps?.map(s => `${s.name}:${s.status}`)
        })
        
        // 只在数据真正变化时更新
        if (JSON.stringify(newJobData) !== JSON.stringify(jobData.value)) {
          console.log('🔄 数据有变化，更新 jobData')
          jobData.value = newJobData
          
          // 保存解析内容（如果有）- 只在内容变化时记录日志
          if (jobData.value?.context) {
            let contentChanged = false
            if (jobData.value.context.url_content && jobData.value.context.url_content !== extractedContent.value.url) {
              extractedContent.value.url = jobData.value.context.url_content
              console.log('✅ 保存URL解析内容，长度:', extractedContent.value.url.length)
              contentChanged = true
            }
            if (jobData.value.context.file_content && jobData.value.context.file_content !== extractedContent.value.file) {
              extractedContent.value.file = jobData.value.context.file_content
              console.log('✅ 保存文件解析内容，长度:', extractedContent.value.file.length)
              contentChanged = true
            }
            
            // 只在内容变化时记录状态
            if (contentChanged) {
              console.log('📊 当前 extractedContent 状态:', {
                hasUrl: !!extractedContent.value.url,
                hasFile: !!extractedContent.value.file
              })
            }
          }
        }
        
        const st = jobData.value?.status
        if (st === 'completed') {
          jobPolling.value = false
          extracting.value = false
          const exId = jobData.value?.result?.extraction_id
          if (exId) {
            const exResp = await aiAPI.getExtraction(exId)
            extractionResult.value = exResp.data
          } else {
            extractionResult.value = { status: 'error', message: '任务完成但未返回结果ID', data: null }
          }
          // 成功后不隐藏进度，保持显示以便查看解析内容
          return
        }
        if (st === 'failed') {
          jobPolling.value = false
          extracting.value = false
          extractionResult.value = { status: 'error', message: jobData.value?.error || '任务失败', data: null }
          // 失败时保留进度信息
          return
        }
      }
    } catch (e) {
      console.error('轮询任务状态失败:', e)
      jobError.value = e?.message || '任务查询失败'
      jobPolling.value = false
      extracting.value = false
      return
    }
    
    // 根据轮询次数调整间隔：前20次每500ms，之后每1秒
    const interval = pollCount <= 20 ? 500 : 1000
    setTimeout(tick, interval)
  }
  // 立即执行第一次轮询
  tick()
}

// 加载提供商列表
const loadProviders = async () => {
  try {
    console.log('开始加载提供商列表...')
    console.log('正在进行健康检查，这可能需要30秒...')
    
    // 使用流式API获取实时进度
    const response = await fetch('/api/v1/ai/providers/stream', {
      method: 'GET',
      headers: {
        'Accept': 'text/event-stream',
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
            console.log('收到进度更新:', data)
            
            // 更新进度
            updateHealthCheckProgress(data.current, data.total, data.available)
            
            // 如果检查完成，更新提供商列表
            if (data.completed && data.providers) {
              providers.value = data.providers
              console.log('提供商列表加载成功:', providers.value)
              providersLoading.value = false
              console.log('所有提供商健康检查完成')
              return
            }
          } catch (e) {
            console.error('解析进度数据失败:', e)
          }
        }
      }
    }
    
  } catch (error) {
    console.error('加载提供商列表时出错:', error)
    // 如果流式API失败，回退到普通API
    try {
      const response = await aiAPI.getProviders()
      if (response.data.status === 'success') {
        providers.value = response.data.data
        providersLoading.value = false
      }
    } catch (fallbackError) {
      console.error('回退API也失败:', fallbackError)
      providersLoading.value = false
    }
  }
}

// 健康检查进度更新
const healthCheckProgress = ref({ current: 0, total: 0, available: 0, message: '正在检查AI提供商...' })

const updateHealthCheckProgress = (current, total, available = 0) => {
  console.log('更新进度:', { current, total, available })
  healthCheckProgress.value = {
    current,
    total,
    available,
    message: '正在检查AI提供商...'
  }
  console.log('进度更新后:', healthCheckProgress.value)
}

// 轮询提供商健康检查状态直到稳定或超时
const startProvidersPolling = async (totalCount, attempt = 0) => {
  if (attempt > 20) {
    providersLoading.value = false
    return
  }
  try {
    const resp = await aiAPI.getProviders()
    if (resp.data?.status === 'success') {
      providers.value = resp.data.data
      const knownCount = providers.value.filter(p => ['available','unavailable'].includes(p.status)).length
      updateHealthCheckProgress(knownCount, totalCount)
      if (knownCount >= totalCount) {
        providersLoading.value = false
        return
      }
    }
  } catch (e) {
    // 忽略并继续
  }
  setTimeout(() => startProvidersPolling(totalCount, attempt + 1), 1500)
}

// 选择提供商
const selectProvider = (provider) => {
  // 只允许选择可用的提供商
  if (provider.status !== 'available') {
    return
  }
  
  selectedProvider.value = provider.type
  selectedProviderInfo.value = provider
  sourceType.value = null
  extractionResult.value = null  // 清空提取结果
  
  // 初始化模型选择
  if (!selectedModels.value[provider.type]) {
    selectedModels.value[provider.type] = provider.default_model
  }
  
  console.log('🔄 提供商已切换，清空提取结果')
}

// 模型选择变化
const onModelChange = (providerType, event) => {
  selectedModels.value[providerType] = event.target.value
  
  // 切换模型时清空提取结果
  extractionResult.value = null
  console.log('🔄 模型已切换，清空提取结果')
}

// 切换内容来源类型
// 取消控制
let abortController = null
const cancelOngoing = () => {
  if (abortController) {
    abortController.abort()
    abortController = null
  }
}

// 终止提取任务
const cancelExtraction = async () => {
  console.log('⏹ 用户终止任务')
  
  // 停止轮询
  jobPolling.value = false
  
  // 取消正在进行的请求
  cancelOngoing()
  
  // 如果有任务ID，调用后端取消接口
  if (jobId.value) {
    try {
      await aiAPI.cancelExtractionJob(jobId.value)
    } catch (e) {
      console.warn('取消任务请求失败:', e)
    }
  }
  
  // 重置状态
  extracting.value = false
  extractionResult.value = {
    status: 'error',
    message: '任务已被用户终止',
    data: null
  }
}

const switchSourceType = (type) => {
  if (sourceType.value !== type) {
    cancelOngoing()
    sourceType.value = type
    extractionResult.value = null  // 清空提取结果
    
    // 清空相关输入
    if (type === 'url') {
      urlInput.value = ''
    } else if (type === 'file') {
      selectedFile.value = null
      uploadedFileId.value = null
    } else if (type === 'text') {
      textInput.value = ''
    }
    
    console.log('🔄 内容来源已切换，清空提取结果和输入')
  }
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
    'web_reading': '🌐 网页'
  }
  return texts[capability] || capability
}

// 根据提供商和模型获取能力列表
const getModelCapabilities = (providerType, model) => {
  // 能力说明：
  // - file_reading: 可以直接处理PDF文件（不需要本地解析）
  // - web_reading: 可以直接读取URL内容（如Gemini的URL Context功能）
  // 注意：所有AI都支持文本输入，这是基础能力不需要标注
  
  // 支持URL Context的Google模型列表（根据官方文档2025年12月确认）
  // 注意：gemini-2.0系列不支持URL Context
  const urlContextModels = [
    'gemini-3-pro-preview',
    'gemini-3-flash-preview',
    'gemini-2.5-pro',
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite',
  ]
  
  // Google所有模型都支持文件直传
  const googleModels = [
    'gemini-3-pro-preview',
    'gemini-3-flash-preview',
    'gemini-2.5-pro',
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite',
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
  ]
  
  // 根据模型判断能力
  if (providerType === 'google' && model) {
    const caps = []
    if (googleModels.includes(model)) {
      caps.push('file_reading')
    }
    if (urlContextModels.includes(model)) {
      caps.push('web_reading')
    }
    return caps
  }
  
  // 提供商默认能力
  const providerDefaults = {
    'google': ['file_reading', 'web_reading'],
    // Cloudflare 和 Cerebras 不支持文件直传和网页直读
    'cloudflare': [],
    'cerebras': [],
    'doubao': []
  }
  
  return providerDefaults[providerType] || []
}

// 获取模型能力的简短文本（用于下拉框选项）
const getModelCapabilitiesText = (providerType, model) => {
  const caps = getModelCapabilities(providerType, model)
  const tags = []
  
  if (caps.includes('file_reading')) tags.push('📄文件')
  if (caps.includes('web_reading')) tags.push('🌐网页')
  
  return tags.length > 0 ? `[${tags.join(' ')}]` : ''
}

// 获取状态图标
const getStatusIcon = (status) => {
  const icons = {
    'available': '✅',
    'unavailable': '❌',
    'unknown': '❓'
  }
  return icons[status] || '❓'
}

// 获取状态文本
const getStatusText = (status) => {
  const texts = {
    'available': '可用',
    'unavailable': '不可用',
    'unknown': '未知'
  }
  return texts[status] || '未知'
}

// 文件选择处理
const handleFileChange = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  // 检查文件大小
  const maxSize = 20 * 1024 * 1024 // 20MB
  if (file.size > maxSize) {
    alert('文件大小不能超过 20MB')
    return
  }

  selectedFile.value = file

  // 检查用户是否已登录
  if (!userStore.isLoggedIn) {
    showLoginPrompt.value = true
    return
  }

  // 上传文件
  const formData = new FormData()
  formData.append('file', file)

  try {
    console.log('开始上传文件...')
    const response = await aiAPI.uploadFile(formData)
    console.log('文件上传响应:', response.data)
    
    if (response.data.status === 'success') {
      uploadedFileId.value = response.data.data._id
      console.log('文件上传成功，文件ID:', uploadedFileId.value)
    } else {
      uploadedFileId.value = null  // 重置文件ID
      alert('文件上传失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('文件上传失败:', error)
    uploadedFileId.value = null  // 重置文件ID
    
    // 检查是否是认证错误
    if (error.response?.status === 401) {
      alert('登录已过期，请重新登录')
      userStore.logout()
      // 可以在这里跳转到登录页面
    } else if (error.response?.status === 403) {
      alert('没有权限上传文件，请检查登录状态')
    } else {
      alert('文件上传失败: ' + (error.response?.data?.message || error.message))
    }
  }
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

// 清空所有输入内容
const clearAllInputs = () => {
  // 清空URL输入
  urlInput.value = ''
  
  // 清空文本输入
  textInput.value = ''
  
  // 清空文件选择
  selectedFile.value = null
  uploadedFileId.value = null
  
  // 清空文件输入框
  const fileInput = document.getElementById('file-input')
  if (fileInput) {
    fileInput.value = ''
  }
  
  // 清空提取结果
  extractionResult.value = null
  extractedContent.value = { url: null, file: null }
  
  // 清空任务相关状态
  jobId.value = null
  jobData.value = null
  jobError.value = null
  
  console.log('已清空所有输入内容')
}

// 跳转到登录页面
const goToLogin = () => {
  showLoginPrompt.value = false
  router.push('/login')
}

// 检查是否可以开始提取
const canStartExtraction = computed(() => {
  return urlInput.value.trim() !== '' || uploadedFileId.value !== null || textInput.value.trim() !== ''
})

// 检查是否有任何输入内容
const hasAnyInput = computed(() => {
  return urlInput.value.trim() !== '' || selectedFile.value !== null || textInput.value.trim() !== ''
})

// 开始提取
const startExtraction = async () => {
  extracting.value = true
  extractionResult.value = null
  jobId.value = null
  jobData.value = null
  jobError.value = null
  jobPolling.value = false  // 确保停止之前的轮询
  extractedContent.value = { url: null, file: null }  // 清空解析内容

  try {
    cancelOngoing()
    abortController = new AbortController()
    const requestData = {
      provider: selectedProvider.value,
      prompt_template: 'unified_extraction_v4',
      model: selectedModels.value[selectedProvider.value] || selectedProviderInfo.value?.default_model
    }

    if (urlInput.value.trim()) requestData.source_url = urlInput.value.trim()
    if (uploadedFileId.value) requestData.file_id = uploadedFileId.value
    if (textInput.value.trim()) requestData.source_text = textInput.value.trim()
    
    console.log('🔍 前端调试 - 请求数据:', requestData)

    const response = await aiAPI.startExtractionJob(requestData, { signal: abortController.signal })
    if (response.data?.status === 'success') {
      jobId.value = response.data.data?.job_id || null
      if (jobId.value) {
        startJobPolling(jobId.value)
      } else {
        extracting.value = false
        extractionResult.value = { status: 'error', message: '任务创建失败：缺少job_id', data: null }
      }
    } else {
      extracting.value = false
      extractionResult.value = response.data
      // 启动失败时重置状态
      jobId.value = null
      jobData.value = null
      jobError.value = null
    }

  } catch (error) {
    console.error('AI提取失败:', error)
    extractionResult.value = {
      status: 'error',
      message: error.response?.data?.message || error.message,
      data: error.response?.data?.data || null
    }
    // 异常时重置状态
    extracting.value = false
    jobId.value = null
    jobData.value = null
    jobError.value = null
    jobPolling.value = false
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

// 格式化联系方式（按分号或换行分割）
const formatContactInfo = (contactStr) => {
  if (!contactStr) return []
  // 按分号、换行符分割，过滤空项
  return contactStr
    .split(/[;；\n]/)
    .map(s => s.trim())
    .filter(Boolean)
}

// 查看原始响应
const viewRawResponse = () => {
  if (extractionResult.value?.data) {
    currentRawResponse.value = extractionResult.value.data.raw_response || '无原始响应'
    rawResponseMetadata.value = {
      provider: extractionResult.value.data.provider || 'Unknown',
      model: extractionResult.value.data.model || 'Unknown',
      confidence: extractionResult.value.data.confidence
    }
  }
  rawResponseTab.value = 'formatted'
  showRawResponse.value = true
}

// 查看当前任务状态（调试功能）
const viewCurrentJobStatus = async () => {
  if (!jobId.value) return
  
  try {
    const resp = await aiAPI.getExtractionJobStatus(jobId.value)
    if (resp.data?.status === 'success') {
      const jobInfo = resp.data.data
      currentRawResponse.value = JSON.stringify(jobInfo, null, 2)
      rawResponseMetadata.value = {
        provider: jobInfo.provider || 'Unknown',
        model: jobInfo.model || 'Unknown',
        confidence: null
      }
      rawResponseTab.value = 'formatted'
      showRawResponse.value = true
    }
  } catch (err) {
    console.error('获取任务状态失败:', err)
    alert('获取任务状态失败: ' + err.message)
  }
}

// 格式化原始响应
const formatRawResponse = (text) => {
  try {
    // 尝试解析JSON并格式化
    const parsed = JSON.parse(text)
    return JSON.stringify(parsed, null, 2)
  } catch {
    // 如果不是JSON，直接返回原文本
    return text
  }
}

// 复制原始响应
const copyRawResponse = async () => {
  try {
    const textToCopy = currentRawResponse.value
    await navigator.clipboard.writeText(textToCopy)
    alert('✅ 原始响应已复制到剪贴板')
  } catch (err) {
    console.error('复制失败:', err)
    alert('❌ 复制失败: ' + err.message)
  }
}

// 下载原始响应为文件
const downloadRawResponse = () => {
  try {
    const text = currentRawResponse.value
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const filename = `ai_raw_response_${timestamp}.txt`
    
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.click()
    URL.revokeObjectURL(url)
    
    console.log('✅ 原始响应已下载为文件:', filename)
  } catch (err) {
    console.error('下载失败:', err)
    alert('❌ 下载失败: ' + err.message)
  }
}

// 查看解析内容
const showExtractedContent = (type) => {
  if (type === 'url' && extractedContent.value.url) {
    currentViewContent.value = {
      type: 'URL解析内容',
      content: extractedContent.value.url
    }
    showExtractedContentModal.value = true
  } else if (type === 'file' && extractedContent.value.file) {
    currentViewContent.value = {
      type: '文件解析内容',
      content: extractedContent.value.file
    }
    showExtractedContentModal.value = true
  }
}

// 保存到竞赛
const openSaveDialog = () => {
  // 检查登录状态
  if (!userStore.isLoggedIn) {
    showLoginPrompt.value = true
    return
  }
  
  // 从提取结果中获取数据（后端已返回扁平化结构）
  const ej = extractionResult.value?.data?.extracted_json || {}
  
  console.log('📋 openSaveDialog - extracted_json:', ej)
  console.log('📋 requirements:', ej.requirements)
  
  // 直接传递扁平化数据
  saveDialogInitialData.value = {
    name: ej.name || '',
    organizer: ej.organizer || '',
    category: ej.category || '',
    default_url: ej.default_url || '',
    entrant_url: ej.entrant_url || '',
    teacher_url: ej.teacher_url || '',
    deadline: ej.deadline || '',
    start_date: ej.start_date || '',
    publish_time: ej.publish_time || '',
    contact_info: ej.contact_info || '',
    prize_info: ej.prize_info || '',
    requirements: ej.requirements || [],
    team_min: ej.team_min || null,
    team_max: ej.team_max || null,
    notes: ej.notes || ''
  }
  
  console.log('📋 saveDialogInitialData:', saveDialogInitialData.value)
  showSaveDialog.value = true
}

// 保存成功回调
const onSaveSuccess = (contest) => {
  console.log('竞赛保存成功:', contest)
  alert('保存成功！')
}

onMounted(() => {
  // 检查用户登录状态
  if (!userStore.isLoggedIn) {
    console.log('用户未登录，显示登录提示')
    showLoginPrompt.value = true
    return
  }
  
  console.log('用户已登录，开始加载提供商列表')
  loadProviders()
})
</script>

<style scoped>
.extract-container {
  min-height: 100vh;
  background: var(--bg-secondary);
}

.page-header {
  background: var(--bg-primary);
  padding: 40px 20px;
  text-align: center;
  box-shadow: var(--shadow-md);
  border-bottom: 1px solid var(--border-color);
}

.header-content h1 {
  margin: 0 0 10px 0;
  font-size: 36px;
  font-weight: 700;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 16px;
  margin-bottom: 20px;
}

.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 20px;
}

/* 左右分栏布局 */
.single-column {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

/* 进度条样式 */
.progress-bar {
  width: 100%;
  height: 8px;
  background: var(--border-color);
  border-radius: 4px;
  overflow: hidden;
  margin: 15px 0;
}

.progress-fill {
  height: 100%;
  background: var(--gradient-primary);
  transition: width 0.3s ease;
}

/* 任务进度样式 */
.job-progress {
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  padding: 20px;
  border: 1px solid var(--border-color);
}

.job-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 20px;
  font-size: 14px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-item label {
  font-weight: 600;
  color: var(--text-secondary);
}

.meta-item span {
  color: var(--text-primary);
  word-break: break-all;
}

.error-text {
  color: var(--danger-color) !important;
}

.steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step {
  padding: 12px 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  transition: all 0.3s ease;
}

.step.pending {
  opacity: 0.6;
  background: var(--bg-tertiary);
}

.step.running {
  border-color: var(--primary-color);
  background: rgba(37, 99, 235, 0.05);
}

.step.completed {
  border-color: var(--success-color);
  background: rgba(34, 197, 94, 0.05);
}

.step.failed {
  border-color: var(--danger-color);
  background: rgba(239, 68, 68, 0.05);
}

.step-head {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
}

.step-index {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--primary-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.step.pending .step-index {
  background: var(--text-tertiary);
}

.step.running .step-index {
  background: var(--primary-color);
}

.step.completed .step-index {
  background: var(--success-color);
}

.step.failed .step-index {
  background: var(--danger-color);
}

.step-name {
  color: var(--text-primary);
  font-size: 14px;
  letter-spacing: 0.5px;
}

.step-status {
  margin-left: auto;
  font-size: 12px;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.step.running .step-status {
  background: rgba(37, 99, 235, 0.1);
  color: var(--primary-color);
}

.step.completed .step-status {
  background: rgba(34, 197, 94, 0.1);
  color: var(--success-color);
}

.step.failed .step-status {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger-color);
}

.step-detail {
  margin-top: 8px;
  font-size: 13px;
  color: var(--text-secondary);
  font-style: italic;
}

/* 失败步骤的错误详情 */
.step-error-detail {
  margin-top: 12px;
  padding: 16px;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border: 1px solid #fecaca;
  border-radius: 8px;
  border-left: 4px solid #ef4444;
}

.step-error-detail .error-message {
  margin: 0;
  font-size: 13px;
  color: #991b1b;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  line-height: 1.6;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .single-column { gap: 20px; }
}

.section {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: 30px;
  margin-bottom: 30px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

.section h2 {
  color: var(--text-primary);
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 20px 0;
  padding-bottom: 10px;
  border-bottom: 2px solid var(--border-color);
}

/* 加载状态 */
.loading-state {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

.loading-subtitle {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-top: 8px;
  opacity: 0.8;
}

.health-check-info {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
}

.health-check-info .info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  font-size: 14px;
  color: var(--text-secondary);
  opacity: 0.8;
  animation: pulse 2s infinite;
}

.health-check-info .info-item .icon {
  font-size: 16px;
}

.progress-stats {
  display: flex;
  gap: 20px;
  justify-content: center;
  margin-top: 15px;
  padding: 10px;
  background: var(--bg-tertiary);
  border-radius: 8px;
}

.progress-stats .stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.progress-stats .stat-label {
  font-size: 12px;
  color: var(--text-tertiary);
  font-weight: 500;
}

.progress-stats .stat-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.progress-stats .stat-value.success {
  color: var(--success-color, #52c41a);
}

@keyframes pulse {
  0%, 100% { opacity: 0.8; }
  50% { opacity: 1; }
}

.spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 10px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 提供商网格 */
.provider-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.provider-card {
  background: var(--bg-primary);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.provider-card:hover {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.provider-card.selected {
  border-color: var(--primary-color);
  background: rgba(37, 99, 235, 0.05);
  box-shadow: var(--shadow-md);
}

.provider-card.unavailable {
  opacity: 0.6;
  cursor: not-allowed;
  background: var(--bg-tertiary);
}

.provider-card.unavailable:hover {
  transform: none;
  box-shadow: var(--shadow-sm);
}

.provider-card.available {
  border-color: var(--success-color);
}

.provider-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.provider-header h3 {
  color: var(--text-primary);
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.provider-badge {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.provider-badge.cloudflare {
  background: linear-gradient(135deg, #f38020 0%, #faad3f 100%);
}

.provider-badge.google {
  background: linear-gradient(135deg, #4285f4 0%, #34a853 100%);
}

.provider-badge.cerebras {
  background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%);
}

.provider-badge.doubao {
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
}

.capabilities {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 15px;
}

.capability-tag {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
}

.model-info {
  color: var(--text-tertiary);
  font-size: 12px;
}

/* 状态指示器 */
.status-indicator {
  margin-bottom: 15px;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
}

.status-badge.available {
  background: rgba(34, 197, 94, 0.1);
  color: var(--success-color);
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.status-badge.unavailable {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger-color);
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.status-badge.unknown {
  background: rgba(156, 163, 175, 0.1);
  color: var(--text-secondary);
  border: 1px solid rgba(156, 163, 175, 0.2);
}

.status-icon {
  font-size: 16px;
}

.status-text {
  font-weight: 600;
}

.status-reason {
  color: var(--text-secondary);
  font-size: 12px;
  margin-top: 4px;
  padding-left: 20px;
}

/* 模型选择 */
.model-selection {
  margin-bottom: 15px;
}

.model-label {
  display: block;
  color: var(--text-primary);
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 8px;
}

.model-select {
  width: 100%;
  padding: 8px 12px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.model-select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.model-select:hover {
  border-color: var(--primary-color);
}

/* 性能信息 */
.performance-info {
  color: var(--text-tertiary);
  font-size: 12px;
  text-align: center;
  margin-top: 8px;
  padding: 4px 8px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
}

/* 来源类型选择 */
.source-tabs {
  display: flex;
  gap: 15px;
  margin-top: 20px;
}

.tab-button {
  flex: 1;
  padding: 20px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-lg);
  background: var(--bg-primary);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  font-size: 16px;
  font-weight: 500;
}

.tab-button:hover:not(:disabled) {
  border-color: var(--primary-color);
  background: rgba(37, 99, 235, 0.05);
}

.tab-button.active {
  border-color: var(--primary-color);
  background: rgba(37, 99, 235, 0.1);
  color: var(--primary-color);
}

.tab-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tab-button .icon {
  font-size: 24px;
}

.unsupported-hint {
  font-size: 12px;
  color: var(--warning-color);
}

/* 输入区域 */
.input-section {
  margin-top: 20px;
}

.input-group {
  margin-bottom: 15px;
}

.input-group label {
  display: block;
  color: var(--text-primary);
  font-weight: 600;
  font-size: 15px;
  margin-bottom: 8px;
}

.url-input,
.text-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 15px;
  font-family: inherit;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: all 0.3s ease;
}

.url-input:focus,
.text-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.url-input::placeholder,
.text-input::placeholder {
  color: var(--text-tertiary);
}

.text-input {
  resize: vertical;
  min-height: 120px;
}

/* 文件上传 */
.file-upload-area {
  position: relative;
  margin-bottom: 15px;
}

.file-input {
  position: absolute;
  opacity: 0;
  width: 100%;
  height: 100%;
  cursor: pointer;
}

.file-upload-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  border: 2px dashed var(--border-color);
  border-radius: var(--radius-lg);
  background: var(--bg-primary);
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 200px;
}

.file-upload-label:hover {
  border-color: var(--primary-color);
  background: rgba(37, 99, 235, 0.02);
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.6;
}

.upload-text {
  text-align: center;
  margin-bottom: 8px;
}

.upload-text strong {
  display: block;
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.upload-text span {
  color: var(--text-secondary);
  font-size: 14px;
}

.upload-tip {
  color: var(--text-tertiary);
  font-size: 12px;
  text-align: center;
}

.file-info {
  margin-top: 15px;
  padding: 15px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.file-details {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-name {
  color: var(--text-primary);
  font-weight: 500;
  flex: 1;
  margin-right: 10px;
  word-break: break-all;
}

.file-size {
  color: var(--text-secondary);
  font-size: 14px;
  white-space: nowrap;
}

.warning-message {
  margin-top: 15px;
  padding: 12px 16px;
  background: rgba(245, 158, 11, 0.1);
  border-left: 4px solid var(--warning-color);
  color: var(--warning-color);
  border-radius: var(--radius-sm);
  font-size: 14px;
}

/* 按钮样式 */
.btn-primary,
.btn-secondary {
  padding: 12px 24px;
  border: none;
  border-radius: var(--radius-md);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn-primary {
  background: var(--gradient-primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.btn-primary:disabled {
  background: var(--bg-tertiary);
  color: var(--text-tertiary);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-secondary {
  background: var(--bg-primary);
  color: var(--text-primary);
  border: 2px solid var(--border-color);
}

.btn-secondary:hover {
  background: var(--bg-tertiary);
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.btn-extract {
  padding: 16px 32px;
  font-size: 18px;
}

.btn-cancel {
  padding: 16px 24px;
  font-size: 16px;
}

.btn-danger {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn-danger:hover {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
}

.action-section {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 30px;
}

/* 清空按钮样式 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h2 {
  margin: 0;
}

.btn-clear {
  padding: 8px 16px;
  background: var(--bg-primary);
  color: var(--text-secondary);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-clear:hover:not(:disabled) {
  background: var(--danger-color);
  color: white;
  border-color: var(--danger-color);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.btn-clear:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-clear .icon {
  font-size: 16px;
}

/* 结果展示 */
.result-card {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  padding: 30px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

.result-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
}

.result-icon {
  font-size: 32px;
}

.result-icon.success {
  color: var(--success-color);
}

.result-icon.error {
  color: var(--danger-color);
}

.result-header h3 {
  color: var(--text-primary);
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

/* 错误结果 */
.error-result {
  border-left: 4px solid var(--danger-color);
}

.error-content {
  color: var(--text-primary);
}

.error-message {
  color: var(--danger-color);
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 20px;
}

.error-details,
.error-suggestions {
  margin-top: 20px;
  padding: 15px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.error-details h4,
.error-suggestions h4 {
  color: var(--text-primary);
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 10px 0;
}

.error-suggestions ul {
  margin: 10px 0 0 20px;
  color: var(--text-secondary);
}

.error-suggestions li {
  margin-bottom: 5px;
}

/* 成功结果 */
.success-result {
  border-left: 4px solid var(--success-color);
}

/* 置信度指示器 */
.confidence-indicator {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 30px;
  padding: 20px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
}

.confidence-indicator label {
  color: var(--text-primary);
  font-weight: 600;
  font-size: 16px;
  white-space: nowrap;
}

.confidence-bar-container {
  flex: 1;
  height: 24px;
  background: var(--border-color);
  border-radius: 12px;
  overflow: hidden;
}

.confidence-bar {
  height: 100%;
  transition: width 0.5s ease;
  border-radius: 12px;
}

.confidence-bar.high {
  background: linear-gradient(90deg, var(--success-color), #66BB6A);
}

.confidence-bar.medium {
  background: linear-gradient(90deg, var(--warning-color), #FFD54F);
}

.confidence-bar.low {
  background: linear-gradient(90deg, var(--danger-color), #EF5350);
}

.confidence-value {
  font-weight: 600;
  font-size: 16px;
  min-width: 50px;
  text-align: right;
  color: var(--text-primary);
}

/* 提取信息 */
.extracted-info {
  margin: 30px 0;
}

.info-item {
  margin-bottom: 20px;
  padding: 20px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.info-item label {
  display: block;
  color: var(--text-primary);
  font-weight: 600;
  font-size: 16px;
  margin-bottom: 10px;
}

.extracted-link {
  color: var(--primary-color);
  text-decoration: none;
  word-break: break-all;
  font-weight: 500;
}

.extracted-link:hover {
  text-decoration: underline;
}

.requirements-list {
  margin: 10px 0 0 20px;
  color: var(--text-secondary);
}

.requirements-list li {
  margin-bottom: 8px;
}

/* 元数据 */
.metadata {
  margin-top: 30px;
  padding: 20px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.metadata h4 {
  color: var(--text-primary);
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 15px 0;
}

.metadata-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.metadata-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.metadata-item label {
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
}

.metadata-item span,
.metadata-item a {
  color: var(--text-primary);
  font-size: 15px;
}

.metadata-item a {
  color: var(--primary-color);
  text-decoration: none;
}

.metadata-item a:hover {
  text-decoration: underline;
}

/* 免责声明和警告 */
.disclaimer,
.low-confidence-warning {
  margin-top: 20px;
  padding: 15px 20px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
}

.disclaimer {
  background: rgba(245, 158, 11, 0.1);
  border-left: 4px solid var(--warning-color);
  color: var(--warning-color);
}

.low-confidence-warning {
  background: rgba(239, 68, 68, 0.1);
  border-left: 4px solid var(--danger-color);
  color: var(--danger-color);
}

/* 结果操作按钮 */
.result-actions {
  margin-top: 30px;
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.error-actions {
  margin-top: 20px;
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  justify-content: center;
}

/* 模态框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  border: 1px solid var(--border-color);
  max-width: 800px;
  max-height: 80vh;
  width: 100%;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-tertiary);
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
}

.modal-header h3 {
  color: var(--text-primary);
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  transition: all 0.3s ease;
}

.modal-close:hover {
  background: var(--bg-quaternary);
  color: var(--text-primary);
}

.modal-body {
  padding: 30px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  padding: 20px 30px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-tertiary);
  border-radius: 0 0 var(--radius-xl) var(--radius-xl);
  text-align: right;
}

/* 调试按钮样式 */
.btn-debug {
  padding: 12px 24px;
  border: 2px solid var(--primary-color);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--primary-color);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.btn-debug:hover {
  background: var(--primary-color);
  color: white;
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.btn-debug .icon {
  font-size: 18px;
}

.btn-sm {
  padding: 8px 16px;
  font-size: 14px;
}

/* 大型模态框 */
.modal-large {
  max-width: 1200px;
  max-height: 90vh;
}

.modal-subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  margin: 5px 0 0 0;
}

/* 原始响应信息 */
.raw-response-info {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  padding: 15px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.raw-response-info .metadata-item {
  display: flex;
  gap: 8px;
  align-items: center;
  color: var(--text-secondary);
  font-size: 14px;
}

.raw-response-info .metadata-item strong {
  color: var(--text-primary);
}

/* 标签页样式 */
.raw-response-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
  border-bottom: 2px solid var(--border-color);
}

.tab-button {
  padding: 10px 20px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-secondary);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: -2px;
}

.tab-button:hover {
  color: var(--text-primary);
  background: var(--bg-tertiary);
}

.tab-button.active {
  color: var(--primary-color);
  border-bottom-color: var(--primary-color);
}

/* 原始响应内容 */
.raw-response-content {
  max-height: 60vh;
  overflow-y: auto;
}

.raw-response {
  background: var(--bg-tertiary);
  padding: 20px;
  border-radius: var(--radius-md);
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.raw-response-section {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #ff4d4f;
}

.raw-response-container {
  position: relative;
  margin-top: 10px;
}

.raw-response-content {
  background: var(--bg-tertiary);
  padding: 15px;
  border-radius: var(--radius-md);
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  margin-bottom: 10px;
}

.btn-copy {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 4px 8px;
  font-size: 11px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
}

.btn-copy:hover {
  background: #40a9ff;
}

/* 解析内容查看 */
.extracted-content-view {
  background: var(--bg-quaternary);
  padding: 20px;
  border-radius: var(--radius-md);
  overflow-x: auto;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 60vh;
  overflow-y: auto;
}

.large-modal {
  max-width: 1000px;
}

/* 登录提示模态框样式 */
.login-prompt-modal {
  max-width: 500px;
  text-align: center;
}

.login-prompt-content {
  padding: 20px 0;
}

.login-icon {
  font-size: 64px;
  margin-bottom: 20px;
  opacity: 0.8;
}

.login-prompt-content h4 {
  color: var(--text-primary);
  font-size: 20px;
  margin-bottom: 16px;
  font-weight: 600;
}

.login-prompt-content p {
  color: var(--text-secondary);
  font-size: 16px;
  margin-bottom: 20px;
}

.feature-list {
  text-align: left;
  list-style: none;
  padding: 0;
  margin: 0;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  padding: 20px;
}

.feature-list li {
  color: var(--text-primary);
  font-size: 14px;
  padding: 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.feature-list li:not(:last-child) {
  border-bottom: 1px solid var(--border-color);
}

.login-prompt-modal .modal-footer {
  justify-content: center;
  gap: 12px;
}

/* 步骤操作按钮 */
.step-actions {
  margin-top: 12px;
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  border: 1px dashed var(--border-color);
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn-view-detail {
  padding: 8px 16px;
  background: linear-gradient(135deg, var(--primary-color) 0%, #4facfe 100%);
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(79, 172, 254, 0.3);
}

.btn-view-detail:hover {
  background: linear-gradient(135deg, #4facfe 0%, var(--primary-color) 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(79, 172, 254, 0.5);
}

.no-content-tip {
  color: var(--text-secondary);
  font-size: 13px;
  font-style: italic;
  padding: 8px 12px;
  background: var(--bg-quaternary);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
}

/* 重新设计的提取结果页面 */
.main-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.info-card {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 20px;
  transition: all 0.3s ease;
}

.info-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  border-color: var(--primary-color);
}

.info-card h4 {
  color: var(--text-primary);
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 15px 0;
  padding-bottom: 10px;
  border-bottom: 2px solid var(--primary-color);
}

.info-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-content > div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-content strong {
  color: var(--text-primary);
  font-weight: 600;
  font-size: 14px;
}

.info-content p, .info-content span {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.5;
}

/* 联系方式列表样式 */
.info-content.contact-list {
  gap: 8px;
}

.contact-item {
  padding: 8px 12px;
  background: var(--bg-quaternary);
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--text-secondary);
  border-left: 3px solid var(--primary-color);
}

.requirement-text, .prize-text {
  background: var(--bg-quaternary);
  padding: 12px;
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--primary-color);
  margin-top: 8px;
}

.timeline-list {
  margin: 8px 0 0 0;
  padding: 0;
  list-style: none;
}

.timeline-list li {
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
}

.timeline-list li:last-child {
  border-bottom: none;
}

.stage-desc {
  color: var(--text-secondary);
  font-size: 13px;
  margin-top: 4px;
  font-style: italic;
}

.confidence-badge {
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
  margin-left: 10px;
}

.confidence-badge.high {
  background: #52c41a;
  color: white;
}

.confidence-badge.medium {
  background: #faad14;
  color: white;
}

.confidence-badge.low {
  background: #f5222d;
  color: white;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .main-content {
    padding: 20px 10px;
  }
  
  .section {
    padding: 20px;
  }
  
  .provider-grid {
    grid-template-columns: 1fr;
  }
  
  .source-tabs {
    flex-direction: column;
  }
  
  .tab-button {
    padding: 15px;
  }
  
  .metadata-grid {
    grid-template-columns: 1fr;
  }
  
  .result-actions {
    flex-direction: column;
  }
  
  .modal-content {
    margin: 10px;
    max-height: 90vh;
  }
  
  .modal-header,
  .modal-body,
  .modal-footer {
    padding: 15px 20px;
  }
}

@media (max-width: 480px) {
  .page-header {
    padding: 20px 10px;
  }
  
  .header-content h1 {
    font-size: 28px;
  }
  
  .section h2 {
    font-size: 20px;
  }
  
  .provider-card {
    padding: 15px;
  }
  
  .file-upload-label {
    padding: 30px 15px;
    min-height: 150px;
  }
  
  .upload-icon {
    font-size: 36px;
  }
}
</style>

