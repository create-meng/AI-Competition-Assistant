# AI提取功能 API端点文档

## 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: Bearer Token (JWT)
- **内容类型**: `application/json`

## 端点列表

### 1. 获取AI提供商列表

获取所有可用的AI提供商及其能力信息。

**端点**: `GET /ai/providers`

**请求头**:
```
Content-Type: application/json
```

**响应示例**:
```json
{
  "status": "success",
  "code": 200,
  "message": "获取成功",
  "data": [
    {
      "type": "cloudflare",
      "name": "Cloudflare Workers AI",
      "capabilities": ["text_only"],
      "requires": ["api_key", "account_id"],
      "default_model": "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
    },
    {
      "type": "google",
      "name": "Google Gemini",
      "capabilities": ["text_only", "file_upload", "image_reading", "web_reading"],
      "requires": ["api_key"],
      "default_model": "gemini-1.5-flash"
    },
    {
      "type": "doubao",
      "name": "豆包 AI",
      "capabilities": ["text_only", "web_reading"],
      "requires": ["api_key"],
      "default_model": "doubao-pro-32k"
    }
  ]
}
```

**能力说明**:
- `text_only`: 支持纯文本输入
- `file_upload`: 支持直接上传文件
- `web_reading`: 支持直接读取网页
- `image_reading`: 支持图片识别

---

### 2. AI智能提取

使用AI从URL、文件或文本中提取竞赛信息。

**端点**: `POST /ai/extract`

### 2.1 任务式提取（推荐）

通过后台任务分步执行（fetch → parse → ai → save），可在前端显示实时进度。

**端点**: `POST /ai/extract/job`

**请求头**:
```
Content-Type: application/json
Authorization: Bearer <token>
```

**请求参数**: 同“AI智能提取”

**成功响应**:
```json
{
  "status": "success",
  "code": 200,
  "message": "任务已启动",
  "data": { "job_id": "652e2..." }
}
```

---

### 2.2 查询任务进度

**端点**: `GET /ai/extract/jobs/{job_id}`

**成功响应**:
```json
{
  "status": "success",
  "code": 200,
  "message": "获取成功",
  "data": {
    "_id": "652e2...",
    "type": "ai_extraction",
    "status": "running|completed|failed|pending",
    "steps": [
      { "name": "fetch", "status": "completed", "detail": "抓取完成" },
      { "name": "parse", "status": "completed", "detail": "文本整理完成" },
      { "name": "ai", "status": "running", "detail": "AI 正在分析…" },
      { "name": "save", "status": "pending", "detail": "" }
    ],
    "result": {
      "extraction_id": "507f1f77bcf86cd799439011",
      "provider": "google",
      "model": "gemini-1.5-flash",
      "confidence": 0.82
    }
  }
}
```

---
**请求头**:
```
Content-Type: application/json
Authorization: Bearer <token>
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| provider | string | 是 | AI提供商类型: `cloudflare`/`google`/`doubao` |
| source_type | string | 是 | 来源类型: `url`/`file`/`text` |
| source_content | string | 条件 | URL或文本内容（source_type为url或text时必填） |
| file_id | string | 条件 | 文件ID（source_type为file时必填） |
| model | string | 否 | 模型名称（可选，使用默认模型） |
| prompt_template | string | 否 | Prompt模板名称，默认为`html_extraction_v1` |

**请求示例1 - 从URL提取**:
```json
{
  "provider": "google",
  "source_type": "url",
  "source_content": "https://example.com/contest",
  "prompt_template": "html_extraction_v1"
}
```

**请求示例2 - 从文件提取**:
```json
{
  "provider": "cloudflare",
  "source_type": "file",
  "file_id": "507f1f77bcf86cd799439011"
}
```

**请求示例3 - 从文本提取**:
```json
{
  "provider": "doubao",
  "source_type": "text",
  "source_content": "2025年全国大学生计算机设计大赛\n报名入口：https://..."
}
```

**成功响应**:
```json
{
  "status": "success",
  "code": 200,
  "message": "提取成功",
  "data": {
    "extraction_id": "507f1f77bcf86cd799439011",
    "extracted_json": {
      "entrant_url": "https://example.com/student/register",
      "teacher_url": "https://example.com/teacher/login",
      "deadline": "2025-11-30",
      "requirements": [
        "全日制在校本科生或研究生",
        "团队2-5人"
      ],
      "contact_info": "contact@example.com",
      "prize_info": "一等奖10000元，二等奖5000元",
      "confidence": 0.85,
      "notes": ""
    },
    "raw_response": "AI的原始返回内容...",
    "provider": "Google Gemini",
    "model": "gemini-1.5-flash",
    "confidence": 0.85,
    "source_url": "https://example.com/contest",
    "source_doc_id": null,
    "source_type": "url",
    "extraction_time": "2025-10-06T12:00:00.000Z",
    "status": "success"
  }
}
```

**错误响应1 - 未配置API密钥**:
```json
{
  "status": "error",
  "code": 400,
  "message": "未配置google的API密钥",
  "data": null
}
```

**错误响应2 - AI不支持功能**:
```json
{
  "status": "error",
  "code": 400,
    "message": "Cloudflare Workers AI 不支持文件上传功能，请先解析文件为文本后重试",
    "data": {
      "provider": "Cloudflare Workers AI",
      "model": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
      "error": "不支持的功能"
    }
}
```

**错误响应3 - 网页抓取失败**:
```json
{
  "status": "error",
  "code": 400,
  "message": "网页抓取失败: HTTP错误: 404",
  "data": null
}
```

**错误响应4 - AI返回格式错误**:
```json
{
  "status": "error",
  "code": 400,
  "message": "AI返回的内容不是有效的JSON格式",
  "data": {
    "provider": "Google Gemini",
    "model": "gemini-1.5-flash",
    "raw_response": "AI的原始返回...",
    "error": "JSON解析失败"
  }
}
```

---

### 3. 获取提取结果详情

根据提取记录ID获取详细信息。

**端点**: `GET /ai/extractions/{extraction_id}`

**请求头**:
```
Authorization: Bearer <token>
```

**路径参数**:
- `extraction_id`: 提取记录的MongoDB ObjectId

**成功响应**:
```json
{
  "status": "success",
  "code": 200,
  "message": "获取成功",
  "data": {
    "_id": "507f1f77bcf86cd799439011",
    "source_url": "https://example.com/contest",
    "source_doc_id": null,
    "source_type": "url",
    "extracted_json": {
      "entrant_url": "https://example.com/student",
      "teacher_url": "https://example.com/teacher",
      "deadline": "2025-12-31",
      "confidence": 0.85
    },
    "model": "gemini-1.5-flash",
    "provider": "Google Gemini",
    "prompt_id": "html_extraction_v1",
    "extraction_time": "2025-10-06T12:00:00.000Z",
    "raw_response": "...",
    "confidence": 0.85,
    "status": "success"
  }
}
```

**错误响应**:
```json
{
  "status": "error",
  "code": 404,
  "message": "提取记录不存在",
  "data": null
}
```

---

## 错误代码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误或业务逻辑错误 |
| 401 | 未授权（需要登录） |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 通用错误响应格式

```json
{
  "status": "error",
  "code": 400,
  "message": "错误描述信息",
  "data": {
    "error": "详细错误信息",
    "suggestion": "解决建议"
  }
}
```

## 使用示例

### cURL示例

```bash
# 1. 获取提供商列表
curl -X GET http://localhost:8000/api/v1/ai/providers

# 2. 从URL提取信息
curl -X POST http://localhost:8000/api/v1/ai/extract \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "provider": "google",
    "source_type": "url",
    "source_content": "https://example.com/contest"
  }'

# 3. 查看提取结果
curl -X GET http://localhost:8000/api/v1/ai/extractions/507f1f77bcf86cd799439011 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### JavaScript示例

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
})

// 获取提供商列表
const providers = await api.get('/ai/providers')

// AI提取
const result = await api.post('/ai/extract', {
  provider: 'google',
  source_type: 'url',
  source_content: 'https://example.com/contest'
})

// 获取提取详情
const detail = await api.get(`/ai/extractions/${result.data.data.extraction_id}`)
```

### Python示例

```python
import httpx
import asyncio

async def extract_info():
    async with httpx.AsyncClient() as client:
        # 获取提供商
        resp = await client.get('http://localhost:8000/api/v1/ai/providers')
        providers = resp.json()
        
        # AI提取
        resp = await client.post(
            'http://localhost:8000/api/v1/ai/extract',
            json={
                'provider': 'google',
                'source_type': 'text',
                'source_content': '竞赛内容...'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        result = resp.json()
        print(result)

asyncio.run(extract_info())
```

## 注意事项

1. **API密钥配置**: 使用前必须在后端`.env`文件中配置对应的API密钥
2. **超时设置**: AI请求可能较慢，建议设置60秒超时
3. **速率限制**: 建议添加请求频率限制，避免超出API配额
4. **结果验证**: 低置信度(<0.6)的结果建议人工审核
5. **错误处理**: 实现完整的错误处理和重试机制
6. **安全性**: 不要在前端暴露API密钥，所有调用通过后端中转

## 更新日志

### v1.0.0 (2025-10-06)
- ✅ 实现多AI提供商支持
- ✅ 智能能力检测和降级处理
- ✅ 完整的错误提示机制
- ✅ 置信度评估功能

