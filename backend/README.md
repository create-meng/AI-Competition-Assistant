# 后端 API 说明

## 项目结构

```
backend/
├── main.py                 # FastAPI 应用入口
├── database.py             # MongoDB 连接管理
├── models/                 # 数据模型
├── routers/                # API 路由
├── utils/                  # 工具函数
├── prompts/                # AI Prompt 模板
└── scripts/                # 工具脚本
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 环境配置

复制 `.env.example` 为 `.env` 并填入配置：

```ini
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=ai_competition_assistant
SECRET_KEY=your-secret-key
 
# Cloudflare Workers AI
# 必填：
CLOUDFLARE_API_KEY=your-cloudflare-token
CLOUDFLARE_ACCOUNT_ID=your-account-id
# 可选：默认模型（未设置则使用 @cf/meta/llama-3.3-70b-instruct-fp8-fast）
CLOUDFLARE_MODEL=@cf/meta/llama-3.3-70b-instruct-fp8-fast
```

## 运行服务

```bash
uvicorn main:app --reload
```

访问 http://localhost:8000/docs 查看 API 文档

## 初始化数据库

```bash
python scripts/init_db.py
```

## API 路由

### 认证 (`/api/v1/auth`)
- POST `/register` - 注册
- POST `/login` - 登录
- GET `/me` - 获取当前用户

### 竞赛 (`/api/v1/contests`)
- GET `/` - 竞赛列表
- GET `/{id}` - 竞赛详情
- POST `/` - 创建竞赛
- PUT `/{id}` - 更新竞赛
- DELETE `/{id}` - 删除竞赛
- GET `/{id}/redirect` - 角色跳转（核心功能）

### AI 提取 (`/api/v1/ai`)
- POST `/extract/url` - 从URL提取
- POST `/extract/file` - 从文件提取
- GET `/extractions` - 提取记录列表
- GET `/extractions/{id}` - 提取详情

