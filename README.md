# 🤖 AI 竞赛学习助手

基于 AI 的智能竞赛信息管理平台，帮助参赛者和指导教师快速获取竞赛信息、智能提取关键内容、一键跳转报名入口。

## ✨ 核心功能

- 🔐 **智能角色跳转** - 根据用户身份（参赛者/教师）自动跳转至对应的竞赛官网入口
- 📄 **多格式解析** - 支持 PDF、网页（HTML）、TXT 等多种格式的竞赛文档智能解析
- 🌐 **SPA 页面支持** - 智能识别 Vue/React 等单页应用，自动使用浏览器渲染提取完整内容
- 🧠 **AI 信息提取** - 自动抽取报名截止日期、参赛要求、联系方式等关键信息
- 👥 **双角色服务** - 参赛者快速报名，指导老师管理学生

### AI 提供商支持

| AI 提供商 | 文本 | 文件 | 网页 | 特点 |
|---------|------|------|------|------|
| Google Gemini | ✅ | ✅ | ✅ | 功能全面（推荐） |
| Cloudflare Workers AI | ✅ | ❌ | ❌ | 快速、经济 |
| 豆包 AI | ✅ | ❌ | ✅ | 国内访问快 |
| Free-QWQ | ✅ | ❌ | ❌ | 免费使用 |
| Cerebras | ✅ | ❌ | ❌ | 高性能 |

系统会自动检测 AI 能力，当 AI 不支持某项功能时自动降级处理（如先解析文件为文本再提交）。

## 🚀 快速开始

### 环境要求

- Python >= 3.10
- Node.js >= 18
- Conda 虚拟环境管理器

### 1. 后端配置

```bash
cd backend

# 创建并激活 conda 环境
conda create -n jishe python=3.10 -y
conda activate jishe

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
copy .env.example .env
# 编辑 .env 文件，至少配置一个 AI 提供商的 API 密钥

# 初始化数据库（SQLite，自动创建）
python scripts/init_db.py
```

### 2. 前端配置

```bash
cd frontend
npm install
```

### 3. 启动服务

**后端**:
```bash
cd backend
conda activate jishe
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**前端**:
```bash
cd frontend
npm run dev
```

### 4. 访问应用

- 前端界面: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 🔑 API 密钥配置

在 `backend/.env` 文件中配置（至少配置一个 AI 提供商）：

```ini
# SQLite 数据库（默认路径）
SQLITE_DB_PATH=data/app.db

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI 提供商（至少配置一个）
GOOGLE_API_KEY=your-google-api-key
CLOUDFLARE_API_KEY=your-cloudflare-api-key
CLOUDFLARE_ACCOUNT_ID=your-cloudflare-account-id
DOUBAO_API_KEY=your-doubao-api-key
FREE_QWQ_API_KEY=your-free-qwq-api-key
CEREBRAS_API_KEY=your-cerebras-api-key

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# 文件上传
MAX_FILE_SIZE=20971520
UPLOAD_DIR=./uploads
```

### 获取 API 密钥

- **Google Gemini（推荐）**: https://makersuite.google.com/app/apikey
- **Cloudflare**: https://dash.cloudflare.com/ → AI → Workers AI
- **豆包**: https://console.volcengine.com/ → AI服务 → 豆包
- **Free-QWQ**: https://api.suanli.cn/token
- **Cerebras**: https://cloud.cerebras.ai/

## 🛠 技术栈

**后端**: FastAPI + SQLite + 多 AI 提供商集成 + JWT 认证

**前端**: Vue 3 + Element Plus + Pinia + Axios

## 📁 项目结构

```
ai_competition_assistant/
├── backend/                    # FastAPI 后端
│   ├── main.py                # 应用入口
│   ├── database.py            # SQLite 数据库连接
│   ├── models/                # 数据模型
│   ├── routers/               # API 路由
│   ├── utils/                 # 工具模块
│   │   ├── ai_providers/     # AI 提供商
│   │   ├── cache.py          # 缓存模块
│   │   ├── rate_limiter.py   # 速率限制
│   │   └── logger.py         # 日志模块
│   ├── prompts/               # Prompt 模板
│   └── data/                  # SQLite 数据库文件
├── frontend/                  # Vue 3 前端
│   ├── src/
│   │   ├── api/              # API 封装
│   │   ├── components/       # 组件
│   │   ├── store/            # Pinia 状态管理
│   │   └── pages/            # 页面
│   └── package.json
└── README.md
```

## 🔧 故障排查

### 数据库问题
SQLite 数据库文件位于 `backend/data/app.db`，如需重置可删除该文件后重新运行 `python scripts/init_db.py`

### AI 提取失败
检查 API 密钥是否正确配置，查看错误提示选择合适的提供商

### 前端无法连接后端
检查 CORS 配置，确保后端已启动

### 依赖安装问题
```bash
cd backend
conda activate jishe
pip install -r requirements.txt
```

## ⚠️ 注意事项

- AI 提取结果仅供参考，请以官方信息为准
- 低于 60% 置信度的提取结果建议人工审核
- 本项目采用本地直接部署方式，不使用 Git 和 Docker

---

**版本**: v1.2.0  
**最后更新**: 2025-12-27
