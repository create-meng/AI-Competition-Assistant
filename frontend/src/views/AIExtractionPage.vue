<template>
  <div class="ai-extraction-page">
    <div class="page-header">
      <h1>🤖 AI 智能提取</h1>
      <p class="subtitle">使用AI自动提取竞赛信息，支持网址、文件和文本</p>
    </div>

    <AIExtraction />

    <div class="help-section">
      <h3>💡 使用帮助</h3>
      <div class="help-cards">
        <div class="help-card">
          <h4>1️⃣ 选择AI提供商</h4>
          <p>根据需要选择合适的AI提供商：</p>
          <ul>
            <li><strong>Cloudflare Workers AI</strong>: 快速响应，仅支持文本</li>
            <li><strong>Google Gemini</strong>: 功能全面，支持文件、网页和图片</li>
            <li><strong>豆包 AI</strong>: 支持文本和网页阅读</li>
          </ul>
        </div>

        <div class="help-card">
          <h4>2️⃣ 准备内容来源</h4>
          <p>选择您的信息来源方式：</p>
          <ul>
            <li><strong>网址</strong>: 输入竞赛官网URL</li>
            <li><strong>文件</strong>: 上传PDF、HTML或TXT文件</li>
            <li><strong>文本</strong>: 直接粘贴文本内容</li>
          </ul>
        </div>

        <div class="help-card">
          <h4>3️⃣ 查看提取结果</h4>
          <p>AI会自动提取以下信息：</p>
          <ul>
            <li>参赛者入口和教师入口URL</li>
            <li>报名截止日期</li>
            <li>参赛要求</li>
            <li>联系方式和奖项信息</li>
          </ul>
        </div>
      </div>

      <div class="notes">
        <h4>⚠️ 注意事项</h4>
        <ul>
          <li>不同AI提供商支持的功能不同，请根据实际需求选择</li>
          <li>如果AI不支持某项功能（如直接读取网页），系统会自动先提取内容再提交</li>
          <li>AI提取结果仅供参考，请务必核对官方信息</li>
          <li>置信度低于60%的结果建议人工审核</li>
          <li>首次使用需要在后端配置相应的API密钥</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import AIExtraction from '@/components/AIExtraction.vue'

export default {
  name: 'AIExtractionPage',
  components: {
    AIExtraction
  }
}
</script>

<style scoped>
.ai-extraction-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-header h1 {
  font-size: 36px;
  color: #333;
  margin-bottom: 10px;
}

.subtitle {
  font-size: 16px;
  color: #777;
}

.help-section {
  margin-top: 60px;
  padding: 30px;
  background: #f9f9f9;
  border-radius: 12px;
}

.help-section h3 {
  font-size: 24px;
  color: #333;
  margin-bottom: 20px;
}

.help-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.help-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.help-card h4 {
  color: #4CAF50;
  margin-bottom: 10px;
}

.help-card ul {
  margin: 10px 0 0 20px;
  color: #555;
}

.help-card li {
  margin-bottom: 5px;
}

.notes {
  background: white;
  padding: 20px;
  border-radius: 8px;
  border-left: 4px solid #ff9800;
}

.notes h4 {
  color: #e65100;
  margin-bottom: 10px;
}

.notes ul {
  margin: 10px 0 0 20px;
  color: #555;
}

.notes li {
  margin-bottom: 8px;
}
</style>

