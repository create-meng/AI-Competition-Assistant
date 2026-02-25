---
trigger: manual
---

---
description: |
  AI 竞赛学习助手项目开发规范
  核心功能：
  - 竞赛官网自动跳转与角色识别（参赛者/教师）
  - PDF与网页智能解析，提取关键信息
  - 竞赛知识图谱自动生成与可视化
  - 为学生和老师提供一站式竞赛辅助服务
globs:
  - "**/*.py"
  - "**/*.js"
  - "**/*.vue"
  - "**/*.ts"
  - "**/*.tsx"
  - "**/prompts/**"
  - "**/backend/**"
  - "**/frontend/**"
alwaysApply: true
---

# AI 竞赛学习助手项目规则（Project Rules）

## 📋 目录

1. [总体原则](#1-总体原则)
2. [项目架构](#2-项目架构)
3. [开发环境与依赖](#3-开发环境与依赖)
4. [代码风格与质量控制](#4-代码风格与质量控制)
5. [后端/API 规范](#5-后端api-规范fastapi)
6. [数据库设计](#6-数据库设计mongodb)
7. [网页与文档解析规则](#7-网页与文档解析规则)
8. [AI/LLM 使用规则](#8-aillm-使用规则)
9. [文件上传与存储](#9-文件上传与存储)
10. [知识图谱生成规范](#10-知识图谱生成规范)
11. [安全与防护](#11-安全与防护)
12. [测试与质量保证](#12-测试与质量保证)
13. [本地部署与运行](#13-本地部署与运行)
14. [前端与 UX 规范](#14-前端与-ux-规范)
15. [数据评估与验收标准](#15-数据评估与验收标准)
16. [合规与伦理](#16-合规与伦理)
17. [Prompt 管理与模板](#17-prompt-管理与模板)
18. [开发阶段与里程碑](#18-开发阶段与里程碑)
19. [AI IDE 使用规范](#19-ai-ide-使用规范)
20. [文件管理与文档更新规范](#20-文件管理与文档更新规范)

---

## 1. 总体原则

### 1.1 核心设计理念

- **模块化 & 单一职责**: 每个模块（auth、contests、ai_extract、crawler、pdf_parser、frontend）只做一件事，便于测试和替换
- **可重复 & 可复现**: 所有环境、依赖、初始化脚本必须可复现（`requirements.txt`、`package.json`）
- **安全与隐私优先**: 默认不收集个人敏感信息（PII），需要收集时必须提示并记录用户同意
- **可解释性与可审计**: AI 抽取结果需记录"来源 + 原始片段 + 模型版本 + prompt"，便于追溯与纠错
- **渐进交付**: MVP → 增量迭代，先做可展示、能跑通的最小可行产品

### 1.2 禁用工具与技术

**本项目明确禁止使用以下工具**：

#### ❌ 禁止使用 Git
- 不要在文档、代码或说明中提及任何Git命令
- 不要创建 `.gitignore` 文件
- 不要使用 `git clone`、`git commit`、`git push` 等命令
- 不要在贡献指南中包含Git相关流程
- 不要创建 `.git` 目录或配置

**原因**: 项目使用其他版本控制方式

#### ❌ 禁止使用 Docker
- 不要创建 `Dockerfile`
- 不要创建 `docker-compose.yml`
- 不要在部署文档中使用Docker相关命令
- 不要在说明中提及容器化部署
- 不要使用 `docker build`、`docker run` 等命令

**原因**: 项目采用本地直接部署方式

#### ✅ 允许的部署方式
- 本地直接安装部署
- Conda虚拟环境管理
- 系统服务方式运行
- 手动启动脚本（.bat/.sh）

### 1.3 项目目标

构建 **AI 驱动的竞赛一站式助手平台**，核心功能：

- 🔐 **智能角色跳转**: 识别用户身份（参赛者/教师），自动跳转至对应的竞赛官网入口
- 📄 **多格式解析**: 支持 PDF、网页（HTML）等多种格式的竞赛文档智能解析
- 🧠 **AI 信息提取**: 自动抽取报名截止日期、参赛要求、联系方式等关键信息
- 🕸️ **知识图谱可视化**: 为每个竞赛项目生成知识图谱，展示竞赛阶段、关联资源、技能要求等
- 👥 **双角色服务**: 
  - **参赛者**: 查找竞赛、快速报名、获取学习资源
  - **指导老师**: 查看赛事信息、管理学生报名、指导项目进度

系统特点：

- 💡 智能化：AI 自动解析文档，减少人工整理工作
- 🎯 精准性：角色识别跳转，一键直达目标页面
- 📊 可视化：知识图谱展示竞赛全景信息
- 🔒 可追溯：保留原始文档与 AI 抽取记录，便于核对

---

## 2. 项目架构

### 2.1 目录结构规范

```
ai_competition_assistant/
│
├── backend/                      # FastAPI 后端
│   ├── main.py                   # 入口文件
│   ├── database.py               # MongoDB连接
│   ├── models/                   # Pydantic数据模型
│   │   ├── user.py
│   │   ├── contest.py
│   │   └── extraction.py
│   ├── routers/                  # 各模块路由
│   │   ├── auth.py               # 登录注册API
│   │   ├── contests.py           # 比赛相关API
│   │   ├── projects.py           # 项目信息API
│   │   └── ai_extract.py         # AI智能提取模块
│   ├── utils/
│   │   ├── crawler.py            # 爬虫
│   │   ├── pdf_parser.py         # PDF解析
│   │   └── ai_model.py           # LLM封装
│   ├── prompts/                  # Prompt模板管理
│   │   ├── html_extraction_v1.txt
│   │   └── pdf_extraction_v1.txt
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                     # Vue/React 前端
│   ├── src/
│   │   ├── pages/                # 登录页、主页、比赛页
│   │   ├── components/           # 通用组件
│   │   ├── router/               # 前端路由控制
│   │   ├── api/                  # 与后端通信接口
│   │   └── store/                # 用户信息与状态
│   └── package.json
│
├── docs/
│   ├── system_architecture.md    # 系统架构图
│   ├── api_spec.md               # 接口文档
│   └── data_model.md             # 数据结构说明
│
├── tests/                        # 测试目录
│   ├── unit/
│   └── integration/
│
└── README.md
```

### 2.2 技术栈

**后端**:
- FastAPI (Python 3.10+)
- MongoDB (pymongo/motor)
- JWT 认证 (python-jose)
- AI: LangChain / OpenAI / 本地模型
- 文档处理: PyMuPDF, BeautifulSoup4

**前端**:
- Vue 3 / React 18
- Element Plus / Ant Design
- Axios
- Vue Router / React Router

---

## 3. 开发环境与依赖

### 3.1 版本要求

- Python >= 3.10 (推荐 3.10/3.11)
- Node >= 18
- MongoDB >= 5.0

### 3.2 后端依赖（示例）

```txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
motor>=3.3.0  # 异步MongoDB
python-jose[cryptography]
bcrypt
python-multipart
langchain
openai  # 或其他LLM SDK
PyMuPDF
beautifulsoup4
requests
python-dotenv
email-validator>=2.0.0  # Pydantic邮箱验证
```

### 3.3 环境管理

- **强制使用 conda 虚拟环境 `jishe`**: 所有 Python 开发必须在 `jishe` 环境中进行
- 配置文件使用 `.env`（不提交到仓库）
- 提供 `.env.example` 作为模板
- **环境激活命令**: `conda activate jishe`
- **依赖安装**: 必须在 `jishe` 环境中执行 `pip install -r requirements.txt`

**`.env.example` 示例**:
```ini
# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=ai_competition_assistant

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Model
OPENAI_API_KEY=your-openai-api-key
MODEL_NAME=gpt-3.5-turbo

# 文件上传
MAX_FILE_SIZE=20971520  # 20MB
UPLOAD_DIR=./uploads

# 爬虫设置
CRAWLER_DELAY=1.0
USER_AGENT=AICompetitionAssistantBot/1.0
```

---

## 4. 代码风格与质量控制

### 4.1 格式化工具

- **Python**: `black` + `isort`
- **JavaScript/TypeScript**: `prettier` + `eslint`

### 4.2 静态类型

- 后端关键模块使用类型注解
- 可选使用 `mypy` 进行类型检查

### 4.3 注释与文档

- 模块顶层加功能说明（中文）
- 函数添加 docstring（简述参数、返回、异常）

示例：
```python
def extract_urls_from_html(html_content: str) -> dict:
    """从HTML内容中提取参赛者和教师入口URL
    
    Args:
        html_content: HTML页面内容
        
    Returns:
        包含 entrant_url 和 teacher_url 的字典
        
    Raises:
        ValueError: 当HTML内容为空时
    """
    pass
```

### 4.4 测试覆盖

- 核心业务（auth、contest 跳转、ai_extract）至少有单元/集成测试
- MVP 阶段覆盖率目标 ≥ 60%
- 发布演示前尽量提高覆盖率

### 4.5 代码审查

- 关键功能开发完成后，进行代码自审
- 检查点：
  - 是否符合项目架构
  - 是否遵守代码规范
  - 是否包含必要的错误处理
  - 是否有安全隐患
  - 是否添加了必要的注释

---

## 5. 后端/API 规范（FastAPI）

### 5.1 API 版本化

所有路由前缀: `/api/v1/...`

### 5.2 统一返回格式（强制）

**成功响应**:
```json
{
  "status": "success",
  "code": 200,
  "message": "操作成功",
  "data": {
    // 实际数据
  }
}
```

**错误响应**:
```json
{
  "status": "error",
  "code": 400,
  "message": "错误描述",
  "data": null
}
```

**实现示例**:
```python
from fastapi import HTTPException

def success(data=None, message="OK", code=200):
    return {"status": "success", "code": code, "message": message, "data": data}

def error(message="Error", code=400):
    raise HTTPException(
        status_code=code, 
        detail={"status": "error", "message": message}
    )
```

### 5.3 错误处理

- 使用 `HTTPException` 定义明确的 status_code 与 message
- 不要泄露内部堆栈信息
- 生产环境隐藏详细错误

### 5.4 认证与授权

- **认证方式**: JWT (access token + refresh token)
- **密码存储**: 使用 `bcrypt` 存储哈希
- **Token 管理**: refresh token 可在 DB 保存黑名单/白名单
- **权限控制**: 基于 `role` 字段（`entrant`、`teacher`、`admin`）

### 5.5 角色跳转接口（核心功能）

**核心接口**: `GET /api/v1/contests/{contest_id}/redirect`

功能：根据当前用户角色返回对应的竞赛官网入口

```python
@router.get("/contests/{contest_id}/redirect")
async def redirect_to_official(
    contest_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    根据用户角色返回对应的竞赛入口URL
    
    Returns:
        {
            "url": "跳转地址",
            "role": "用户角色",
            "contest_name": "竞赛名称"
        }
    """
    contest = await db.contests.find_one({"_id": ObjectId(contest_id)})
    
    if not contest:
        raise HTTPException(status_code=404, detail="竞赛不存在")
    
    if current_user["role"] == "entrant":
        url = contest.get("entrant_url") or contest.get("default_url")
    elif current_user["role"] == "teacher":
        url = contest.get("teacher_url") or contest.get("default_url")
    else:
        url = contest.get("default_url")
    
    return success({
        "url": url,
        "role": current_user["role"],
        "contest_name": contest["name"]
    })
```

### 5.6 分页与过滤

列表接口必须支持：
- 分页参数: `limit`, `offset` 或 `page`, `size`
- 筛选参数: 如 `status`, `category` 等

示例：
```python
@router.get("/contests")
async def get_contests(
    skip: int = 0,
    limit: int = 10,
    status: Optional[str] = None,
    search: Optional[str] = None
):
    """获取竞赛列表，支持分页和搜索"""
    query = {}
    if status:
        query["status"] = status
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    
    contests = await db.contests.find(query).skip(skip).limit(limit).to_list(length=limit)
    total = await db.contests.count_documents(query)
    
    return success({
        "items": contests,
        "total": total,
        "page": skip // limit + 1,
        "size": limit
    })
```

### 5.7 速率限制

- 对外暴露 API 适当限制（如 60 req/min/user）
- AI 推理接口更严格限制（如 10 req/min/user）
- 文件上传接口限制（如 5 次/min/user）

推荐使用 `slowapi` 库：
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/ai/extract")
@limiter.limit("10/minute")
async def extract_info(request: Request):
    pass
```

---

## 6. 数据库设计（MongoDB）

### 6.1 集合命名

小写复数形式: `users`, `contests`, `projects`, `documents`, `ai_extractions`, `knowledge_graphs`

### 6.2 核心集合 Schema

#### Users 集合
```json
{
  "_id": "ObjectId",
  "username": "string (unique)",
  "email": "string (optional)",
  "password_hash": "string",
  "role": "entrant|teacher|admin",
  "school": "string",
  "real_name": "string (optional)",
  "created_at": "ISODate",
  "last_login": "ISODate",
  "profile": {
    "bio": "string",
    "avatar_url": "string"
  }
}
```

#### Contests 集合
```json
{
  "_id": "ObjectId",
  "name": "string",
  "organizer": "string",
  "category": "string",
  "entrant_url": "string|null",
  "teacher_url": "string|null",
  "default_url": "string|null",
  "deadline": "ISODate|null",
  "status": "upcoming|ongoing|ended",
  "requirements": ["string"],
  "prize_info": "string",
  "contact_info": "string",
  "documents": ["ObjectId"],
  "stages": [
    {
      "name": "string",
      "deadline": "ISODate",
      "description": "string"
    }
  ],
  "knowledge_graph_id": "ObjectId|null",
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

#### AI Extractions 集合
```json
{
  "_id": "ObjectId",
  "contest_id": "ObjectId|null",
  "source_url": "string|null",
  "source_doc_id": "ObjectId|null",
  "source_type": "pdf|html|docx",
  "extracted_json": {
    "entrant_url": "string|null",
    "teacher_url": "string|null",
    "deadline": "string|null",
    "requirements": ["string"],
    "contact_info": "string|null",
    "prize_info": "string|null",
    "stages": [{"name": "string", "deadline": "string"}]
  },
  "model": "model-name#version",
  "prompt_id": "string",
  "prompt_version": "string",
  "extraction_time": "ISODate",
  "raw_snippet": "string",
  "confidence": "float (0.0-1.0)",
  "status": "pending|success|failed|needs_review",
  "reviewed_by": "ObjectId|null",
  "reviewed_at": "ISODate|null"
}
```

#### Documents 集合
```json
{
  "_id": "ObjectId",
  "contest_id": "ObjectId",
  "filename": "string",
  "file_type": "pdf|docx|html",
  "file_size": "int",
  "file_path": "string",
  "file_hash": "string (SHA256)",
  "uploaded_by": "ObjectId",
  "uploaded_at": "ISODate",
  "parsed_text": "string|null",
  "parse_status": "pending|success|failed",
  "parse_error": "string|null"
}
```

#### Knowledge Graphs 集合
```json
{
  "_id": "ObjectId",
  "contest_id": "ObjectId",
  "graph_data": {
    "nodes": [
      {
        "id": "string",
        "label": "string",
        "type": "stage|requirement|skill|resource|deadline",
        "properties": {}
      }
    ],
    "edges": [
      {
        "source": "node_id",
        "target": "node_id",
        "relation": "requires|leads_to|related_to|depends_on"
      }
    ]
  },
  "generated_by": "ai|manual",
  "generator_model": "string|null",
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

### 6.3 索引策略

对查询频繁字段建索引：

```python
# Users
db.users.create_index([("username", 1)], unique=True)
db.users.create_index([("email", 1)], unique=True, sparse=True)

# Contests
db.contests.create_index([("name", 1)])
db.contests.create_index([("deadline", 1)])
db.contests.create_index([("status", 1)])
db.contests.create_index([("category", 1)])

# AI Extractions
db.ai_extractions.create_index([("source_url", 1)])
db.ai_extractions.create_index([("source_doc_id", 1)])
db.ai_extractions.create_index([("status", 1)])
db.ai_extractions.create_index([("contest_id", 1)])

# Documents
db.documents.create_index([("contest_id", 1)])
db.documents.create_index([("file_hash", 1)])
db.documents.create_index([("uploaded_at", -1)])

# Knowledge Graphs
db.knowledge_graphs.create_index([("contest_id", 1)], unique=True)
```

### 6.4 数据保留策略

- 保存原始文档（PDF/HTML）和处理后的结构化数据
- 保留原始片段以便审核
- AI 推理日志保留 90-365 天
- 过期竞赛数据归档（可选）

### 6.5 PII 处理

- 默认不保留明文邮箱/电话
- 如需保存，必须加密或哈希并记录用户同意
- 使用环境变量配置加密密钥

### 6.6 数据库管理规范

**禁止创建数据库重置脚本**:
- ❌ 不要创建 `reset_db.py`、`clear_db.py` 等数据库清理脚本
- ❌ 不要在代码中包含删除数据库集合的逻辑
- ❌ 不要自动清理用户数据

**数据库重置方式**:
- ✅ 使用 MongoDB UI 工具（如 MongoDB Compass、Studio 3T）手动删除集合
- ✅ 直接在 MongoDB 命令行中执行删除命令
- ✅ 提醒用户手动清理数据库，而不是自动执行

**原因**: 避免误删数据，确保数据安全，让用户有完全的控制权

---

## 7. 网页与文档解析规则

### 7.1 爬虫/抓取规则

#### 7.1.1 法律合规

- **遵守 robots.txt**: 请求前读取并尊重 `robots.txt`
- **遵守网站条款**: 若禁止抓取则跳过或记录需人工授权
- **版权保护**: 只做解析/引用，保留来源
- **学术使用**: 明确标注本项目为学术研究/竞赛项目

#### 7.1.2 技术规范

- **速率限制**: 默认每域名不超过 1 请求/秒（可配置）
- **User-Agent**: 标明项目名与联系邮箱
  ```
  AICompetitionAssistantBot/1.0 (+mailto:your@domain.com)
  ```
- **超时设置**: 设置合理的请求超时（如 10 秒）
- **重试机制**: 失败时使用指数退避策略（最多 3 次）

**实现示例**:
```python
import requests
from time import sleep

class Crawler:
    def __init__(self, delay=1.0):
        self.delay = delay
        self.headers = {
            'User-Agent': 'AICompetitionAssistantBot/1.0 (+mailto:your@domain.com)'
        }
    
    def fetch(self, url: str, max_retries=3) -> str:
        """抓取网页内容"""
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=10
                )
                response.raise_for_status()
                sleep(self.delay)
                return response.text
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                sleep(2 ** attempt)  # 指数退避
```

#### 7.1.3 抓取边界

- 不尝试绕过登录/验证码/反爬机制
- 如需抓取内部入口必须获得授权
- 只抓取公开页面

#### 7.1.4 溯源记录

保存以下信息：
- 抓取的原始 HTML
- 抓取时间
- HTTP 响应头与响应码
- 来源 URL

### 7.2 PDF 解析规范

#### 7.2.1 解析库选择

推荐使用 `PyMuPDF` (fitz)，备选 `pdfplumber`

**示例代码**:
```python
import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path: str) -> str:
    """从PDF提取文本"""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text
```

#### 7.2.2 文本清洗

- 移除多余空白字符
- 处理换行符
- 保留必要的格式信息

```python
import re

def clean_text(text: str) -> str:
    """清洗提取的文本"""
    # 替换多个空格为单个空格
    text = re.sub(r' +', ' ', text)
    # 替换多个换行为两个换行
    text = re.sub(r'\n\n+', '\n\n', text)
    # 去除首尾空白
    text = text.strip()
    return text
```

#### 7.2.3 结构化提取

- 识别标题、段落、列表
- 提取表格数据
- 保留重要的布局信息

### 7.3 HTML 解析规范

#### 7.3.1 解析库使用

使用 `BeautifulSoup4` + `lxml` 解析器

**示例代码**:
```python
from bs4 import BeautifulSoup

def parse_html(html_content: str) -> BeautifulSoup:
    """解析HTML内容"""
    return BeautifulSoup(html_content, 'lxml')

def extract_links(html_content: str, keywords: list) -> list:
    """提取包含特定关键词的链接"""
    soup = parse_html(html_content)
    links = []
    
    for a in soup.find_all('a', href=True):
        text = a.get_text().strip().lower()
        href = a['href']
        
        # 检查链接文本是否包含关键词
        if any(keyword in text for keyword in keywords):
            links.append({
                'text': a.get_text().strip(),
                'href': href,
                'full_url': urljoin(base_url, href)
            })
    
    return links
```

#### 7.3.2 关键信息识别

- **参赛者入口**: 关键词包括"报名"、"参赛"、"注册"、"提交作品"、"entrance"、"register"
- **教师入口**: 关键词包括"教师"、"指导老师"、"导师"、"teacher"、"mentor"、"advisor"
- **截止日期**: 识别日期格式，如"2025-10-06"、"2025年10月6日"
- **联系方式**: 邮箱、电话号码模式匹配

### 7.4 内容使用规范

对抓取内容作引用或摘要时：
- 保留来源 URL
- 在 UI 上标注"来源 URL 与抓取日期"
- 添加免责声明："信息来自网络抓取，仅供参考，请以官方为准"

---

## 8. AI/LLM 使用规则

### 8.1 隐私保护

**敏感信息过滤**: 发送给外部 LLM 前必须过滤或匿名化 PII：
- 姓名
- 身份证号
- 联系方式
- 学生学号

**实现示例**:
```python
import re

def anonymize_text(text: str) -> str:
    """匿名化敏感信息"""
    # 隐藏手机号
    text = re.sub(r'1[3-9]\d{9}', '[手机号已隐藏]', text)
    # 隐藏邮箱
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[邮箱已隐藏]', text)
    # 隐藏身份证号
    text = re.sub(r'\d{17}[\dXx]', '[身份证号已隐藏]', text)
    return text
```

### 8.2 审计与日志

每次调用 LLM 保存：
- `prompt_id`: prompt 模板标识
- `prompt_text`: 实际发送的 prompt（或脱敏版）
- `model`: 模型名称
- `model_version`: 模型版本
- `response`: 模型返回（或脱敏版）
- `timestamp`: 调用时间
- `confidence`: 置信度评分
- `tokens_used`: 消耗的 token 数量（如适用）

```python
async def log_llm_call(
    prompt_id: str,
    prompt_text: str,
    model: str,
    response: str,
    confidence: float
):
    """记录LLM调用日志"""
    await db.llm_logs.insert_one({
        "prompt_id": prompt_id,
        "prompt_text": anonymize_text(prompt_text),
        "model": model,
        "response": response,
        "confidence": confidence,
        "timestamp": datetime.utcnow()
    })
```

保留时长: 90-365 天（按需决定）

### 8.3 Prompt 版本化

- 在仓库 `backend/prompts/` 目录维护所有 prompt 模板
- 每个 prompt 包含：
  - 用途说明
  - 输入格式
  - 期望输出格式（JSON schema）
  - 版本号与变更记录

### 8.4 优先级策略

**确定性优先**: 关键字段（URL、时间）先用正则/解析器提取，再用 LLM 补充或校验

**两阶段策略**:
1. 使用规则/正则进行初步提取
2. 将"初步结果 + 原文"交给 LLM 二次确认/补充

**实现流程**:
```python
async def extract_contest_info(html_content: str) -> dict:
    """提取竞赛信息（混合策略）"""
    # 第一阶段：规则提取
    rule_based_result = extract_with_rules(html_content)
    
    # 第二阶段：AI确认
    ai_result = await extract_with_ai(
        html_content,
        initial_result=rule_based_result
    )
    
    # 合并结果，规则优先
    final_result = merge_results(rule_based_result, ai_result)
    
    return final_result
```

### 8.5 低置信度处理

- 若模型 `confidence` < 阈值（如 0.6），标记为"需人工复核"
- UI 显示"模型不确定，请人工核对"
- 提供人工编辑接口

```python
def assess_confidence(extracted_data: dict) -> float:
    """评估提取结果的置信度"""
    score = 0.0
    total_fields = 0
    
    critical_fields = ['entrant_url', 'teacher_url', 'deadline']
    
    for field in critical_fields:
        total_fields += 1
        if extracted_data.get(field):
            score += 1.0
    
    return score / total_fields if total_fields > 0 else 0.0
```

### 8.6 缓存机制

大型模型调用结果应缓存：
- Key: `hash(源URL + prompt版本 + model版本)`
- TTL: 7天（可配置）
- 避免重复调用产生成本

```python
import hashlib
import json

def get_cache_key(source_url: str, prompt_version: str, model: str) -> str:
    """生成缓存键"""
    data = f"{source_url}|{prompt_version}|{model}"
    return hashlib.md5(data.encode()).hexdigest()

async def extract_with_cache(url: str, prompt_version: str, model: str):
    """带缓存的提取"""
    cache_key = get_cache_key(url, prompt_version, model)
    
    # 检查缓存
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # 调用AI提取
    result = await extract_with_ai(url)
    
    # 保存缓存
    await redis.setex(cache_key, 604800, json.dumps(result))  # 7天
    
    return result
```

### 8.7 模型选择

- **隐私敏感场景**: 优先使用本地开源模型（Llama2/Vicuna/ChatGLM）
- **云模型**: 需声明并获得必要许可（OpenAI/Claude/文心一言）
- **备用方案**: 准备降级策略，模型不可用时使用规则提取

### 8.8 禁止事项

- 不存储"链式思考（chain-of-thought）"的内部推理细节
- 不在日志中保存用户隐私数据
- 不将提取结果用于其他商业用途

---

## 9. 文件上传与存储

### 9.1 文件类型限制

- **允许类型**: `.pdf`, `.docx`, `.txt`, `.html`
- **单文件大小**: 上限 20MB（可配置）
- **文件名**: 仅允许字母、数字、下划线、连字符、点号

### 9.2 安全检查

- 上传后进行文件类型验证（magic number）
- 防止压缩炸弹（zip bomb）
- 防止路径遍历攻击
- 理想情况下进行病毒扫描（ClamAV）

**实现示例**:
```python
import magic
from fastapi import UploadFile, HTTPException

ALLOWED_TYPES = {
    'application/pdf': '.pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'text/plain': '.txt',
    'text/html': '.html'
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

async def validate_upload_file(file: UploadFile):
    """验证上传文件"""
    # 读取文件内容
    content = await file.read()
    await file.seek(0)  # 重置文件指针
    
    # 检查文件大小
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过限制")
    
    # 检查文件类型（magic number）
    mime_type = magic.from_buffer(content, mime=True)
    if mime_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="不支持的文件类型")
    
    return True
```

### 9.3 存储策略

- 保存原始文件到 `uploads/` 目录或对象存储（S3/MinIO/阿里云OSS）
- 文件命名：`{timestamp}_{random}_{original_name}`
- 记录元数据到 `documents` 集合：
  - 上传人
  - 上传时间
  - 文件来源
  - 文件大小
  - SHA256 哈希

```python
import hashlib
from datetime import datetime
from pathlib import Path

async def save_upload_file(file: UploadFile, user_id: str) -> dict:
    """保存上传文件"""
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_str = secrets.token_hex(8)
    filename = f"{timestamp}_{random_str}_{file.filename}"
    
    # 保存文件
    file_path = Path("uploads") / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    content = await file.read()
    file_path.write_bytes(content)
    
    # 计算哈希
    file_hash = hashlib.sha256(content).hexdigest()
    
    # 保存元数据
    doc_meta = {
        "filename": file.filename,
        "saved_filename": filename,
        "file_path": str(file_path),
        "file_type": file.content_type,
        "file_size": len(content),
        "file_hash": file_hash,
        "uploaded_by": user_id,
        "uploaded_at": datetime.utcnow(),
        "parse_status": "pending"
    }
    
    result = await db.documents.insert_one(doc_meta)
    doc_meta["_id"] = result.inserted_id
    
    return doc_meta
```

### 9.4 解析流程

1. 先存原文
2. 异步解析（任务队列或后台任务）
3. 解析失败要上报并留痕
4. 更新 `documents` 集合的 `parse_status`

```python
from fastapi import BackgroundTasks

@app.post("/api/v1/documents/upload")
async def upload_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """上传文档"""
    # 验证文件
    await validate_upload_file(file)
    
    # 保存文件
    doc_meta = await save_upload_file(file, current_user["_id"])
    
    # 添加后台解析任务
    background_tasks.add_task(parse_document, doc_meta["_id"])
    
    return success(doc_meta, message="文件上传成功，正在解析...")

async def parse_document(doc_id: str):
    """后台解析文档"""
    try:
        doc = await db.documents.find_one({"_id": ObjectId(doc_id)})
        
        if doc["file_type"] == "application/pdf":
            text = extract_text_from_pdf(doc["file_path"])
        # ... 其他类型处理
        
        # 更新解析状态
        await db.documents.update_one(
            {"_id": ObjectId(doc_id)},
            {
                "$set": {
                    "parsed_text": text,
                    "parse_status": "success"
                }
            }
        )
        
        # 触发AI提取
        await extract_with_ai(doc_id)
        
    except Exception as e:
        await db.documents.update_one(
            {"_id": ObjectId(doc_id)},
            {
                "$set": {
                    "parse_status": "failed",
                    "parse_error": str(e)
                }
            }
        )
```

---

## 10. 知识图谱生成规范

### 10.1 图谱数据模型

知识图谱采用"节点-边"模型：

**节点类型**:
- `contest`: 竞赛本体
- `stage`: 竞赛阶段（初赛、复赛、决赛）
- `requirement`: 参赛要求
- `skill`: 所需技能
- `resource`: 学习资源
- `deadline`: 截止日期
- `organization`: 主办方

**边类型**:
- `has_stage`: 竞赛包含阶段
- `requires`: 需要某项技能/要求
- `leads_to`: 阶段顺序
- `provides`: 提供资源
- `related_to`: 相关联系

### 10.2 图谱生成策略

#### 10.2.1 基于规则生成

从结构化数据直接生成图谱：

```python
def generate_knowledge_graph(contest_data: dict) -> dict:
    """从竞赛数据生成知识图谱"""
    nodes = []
    edges = []
    
    # 添加竞赛节点
    contest_node = {
        "id": f"contest_{contest_data['_id']}",
        "label": contest_data['name'],
        "type": "contest",
        "properties": {
            "organizer": contest_data.get('organizer'),
            "status": contest_data.get('status')
        }
    }
    nodes.append(contest_node)
    
    # 添加阶段节点
    for idx, stage in enumerate(contest_data.get('stages', [])):
        stage_node = {
            "id": f"stage_{idx}",
            "label": stage['name'],
            "type": "stage",
            "properties": {
                "deadline": stage.get('deadline')
            }
        }
        nodes.append(stage_node)
        
        # 添加边：竞赛->阶段
        edges.append({
            "source": contest_node["id"],
            "target": stage_node["id"],
            "relation": "has_stage"
        })
        
        # 添加阶段间的顺序关系
        if idx > 0:
            edges.append({
                "source": f"stage_{idx-1}",
                "target": stage_node["id"],
                "relation": "leads_to"
            })
    
    # 添加要求节点
    for idx, req in enumerate(contest_data.get('requirements', [])):
        req_node = {
            "id": f"req_{idx}",
            "label": req,
            "type": "requirement"
        }
        nodes.append(req_node)
        
        edges.append({
            "source": contest_node["id"],
            "target": req_node["id"],
            "relation": "requires"
        })
    
    return {
        "nodes": nodes,
        "edges": edges
    }
```

#### 10.2.2 基于AI生成

使用 LLM 分析竞赛文本，生成更丰富的图谱：

```python
async def generate_kg_with_ai(contest_id: str) -> dict:
    """使用AI生成知识图谱"""
    # 获取竞赛信息
    contest = await db.contests.find_one({"_id": ObjectId(contest_id)})
    
    # 获取相关文档
    docs = await db.documents.find({"contest_id": ObjectId(contest_id)}).to_list(length=10)
    
    # 合并文本
    full_text = f"竞赛名称：{contest['name']}\n"
    for doc in docs:
        if doc.get('parsed_text'):
            full_text += doc['parsed_text'] + "\n"
    
    # 调用LLM
    prompt = load_prompt("knowledge_graph_generation_v1.txt")
    prompt = prompt.replace("<<CONTEST_TEXT>>", full_text)
    
    response = await call_llm(prompt, model="gpt-4")
    
    # 解析响应
    kg_data = parse_kg_response(response)
    
    return kg_data
```

### 10.3 图谱可视化

前端使用图可视化库展示：
- **推荐库**: ECharts、G6、Cytoscape.js、vis.js
- **布局算法**: Force-directed、Hierarchical
- **交互功能**: 
  - 节点点击查看详情
  - 节点拖拽
  - 缩放和平移
  - 节点搜索和高亮

### 10.4 图谱更新机制

- 竞赛信息更新时自动重新生成图谱
- 支持人工编辑图谱节点和边
- 保留图谱版本历史

---

## 11. 安全与防护

### 11.1 配置管理

- **禁止公开敏感信息**: 密钥/凭证不能写入文档或公开文件
- **环境变量**: 使用 `.env` 文件（不要公开分享）
- **提供模板**: 创建 `.env.example` 作为配置示例
- **密钥轮换**: 定期更换API密钥和JWT密钥
- **敏感文件**: `.env` 文件仅在本地保存，不要分享或上传

### 11.2 依赖审查

- 定期扫描依赖漏洞（pip-audit / safety）
- 及时更新有安全问题的依赖
- 使用 `requirements.txt` 锁定版本

### 11.3 输入校验

- 所有外部输入必须校验（schema + length + type）
- 防止 SQL/NoSQL 注入
- 防止 XSS 攻击
- 使用 Pydantic 模型进行数据验证

```python
from pydantic import BaseModel, validator, Field

class ContestCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    organizer: str = Field(..., min_length=1, max_length=100)
    default_url: Optional[str] = None
    
    @validator('default_url')
    def validate_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('URL必须以http://或https://开头')
        return v
```

### 11.4 SSRF 防护

当后端访问任意 URL（爬虫/抓取）时：
- 白名单规则或域名解析限制
- 避免访问内网地址（10.x, 172.x, 192.168.x, 127.x）
- 避免访问元数据服务（169.254.169.254）
- 避免访问 localhost 和回环地址

```python
import ipaddress
from urllib.parse import urlparse

BLOCKED_NETWORKS = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('169.254.0.0/16'),
]

def is_safe_url(url: str) -> bool:
    """检查URL是否安全（防SSRF）"""
    try:
        parsed = urlparse(url)
        
        # 只允许http和https
        if parsed.scheme not in ('http', 'https'):
            return False
        
        # 解析IP
        hostname = parsed.hostname
        ip = ipaddress.ip_address(hostname)
        
        # 检查是否在黑名单网络中
        for network in BLOCKED_NETWORKS:
            if ip in network:
                return False
        
        return True
    except:
        return False
```

### 11.5 CORS / CSP

- 前端配置严格 CORS
- 服务端设置 Content-Security-Policy 防止 XSS

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 生产环境改为实际域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 11.6 日志脱敏

- 日志中不写入明文密码/token
- 异常日志中省略用户敏感数据
- 生产环境不输出详细堆栈

```python
import logging

def sanitize_log(message: str) -> str:
    """日志脱敏"""
    # 隐藏token
    message = re.sub(r'Bearer [A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_.+/=]*', 
                     'Bearer [TOKEN]', message)
    # 隐藏密码
    message = re.sub(r'password["\']?\s*[:=]\s*["\']?[^"\'\s]+', 
                     'password=[HIDDEN]', message, flags=re.I)
    return message

logger = logging.getLogger(__name__)
```

---

## 12. 测试与质量保证

### 12.1 测试框架

- **后端**: `pytest` + `pytest-asyncio`
- **前端**: `vitest` / `jest` + `@testing-library`
- **E2E**: `playwright` / `cypress`

### 12.2 测试类型

#### 12.2.1 单元测试

测试独立的函数和类：

```python
# tests/unit/test_pdf_parser.py
import pytest
from backend.utils.pdf_parser import extract_text_from_pdf, clean_text

def test_clean_text():
    """测试文本清洗"""
    input_text = "Hello    World\n\n\nTest"
    expected = "Hello World\n\nTest"
    assert clean_text(input_text) == expected

@pytest.mark.asyncio
async def test_extract_pdf():
    """测试PDF提取"""
    text = extract_text_from_pdf("tests/fixtures/sample.pdf")
    assert len(text) > 0
    assert "竞赛" in text
```

#### 12.2.2 集成测试

测试 API 端点：

```python
# tests/integration/test_contests_api.py
import pytest
from httpx import AsyncClient
from backend.main import app

@pytest.mark.asyncio
async def test_get_contests():
    """测试获取竞赛列表"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/contests")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "items" in data["data"]

@pytest.mark.asyncio
async def test_redirect_to_official(auth_token):
    """测试角色跳转"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = await client.get("/api/v1/contests/123/redirect", headers=headers)
        assert response.status_code == 200
```

#### 12.2.3 AI 模块测试

固定输入验证输出结构：

```python
# tests/unit/test_ai_extract.py
@pytest.mark.asyncio
async def test_extract_urls_from_html():
    """测试从HTML提取URL"""
    html_content = """
    <html>
        <body>
            <a href="/student/register">参赛者报名</a>
            <a href="/teacher/login">教师入口</a>
        </body>
    </html>
    """
    
    result = await extract_urls_from_html(html_content, base_url="https://example.com")
    
    assert "entrant_url" in result
    assert "teacher_url" in result
    assert "example.com" in result["entrant_url"]
```

### 12.3 测试覆盖率

- 核心业务模块覆盖率 ≥ 70%
- MVP 阶段整体覆盖率 ≥ 60%
- 使用 `pytest-cov` 生成报告

```bash
pytest --cov=backend --cov-report=html
```

### 12.4 QA 检查清单

功能测试：
- ✅ 用户注册/登录
- ✅ 角色识别与跳转
- ✅ 文件上传与解析
- ✅ AI 信息提取
- ✅ 知识图谱生成

安全测试：
- ✅ SQL/NoSQL 注入防护
- ✅ XSS 防护
- ✅ SSRF 防护
- ✅ 文件上传安全
- ✅ 认证授权机制

性能测试：
- ✅ API 响应时间 < 2秒
- ✅ 文件解析时间合理
- ✅ 并发请求处理能力

---

## 13. 本地部署与运行

### 13.1 环境准备

1. **安装Python**（3.10+）
2. **安装Node.js**（18+）
3. **安装MongoDB**（5.0+）

### 13.2 后端启动

```bash
# 进入后端目录
cd backend

# 创建conda虚拟环境
conda create -n jishe python=3.10 -y

# 激活虚拟环境
conda activate jishe

# 安装依赖
pip install -r requirements.txt

# 复制环境变量模板
copy .env.example .env
# 编辑 .env 文件，填入实际配置

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 13.3 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 13.4 环境配置

**MongoDB 安装**:
- Windows: 下载安装包 https://www.mongodb.com/try/download/community
- macOS: `brew install mongodb-community && brew services start mongodb-community`
- Linux: `sudo apt-get install mongodb && sudo systemctl start mongodb`

**Python 环境 (Conda)**:
```bash
# 创建conda虚拟环境
conda create -n jishe python=3.10 -y

# 激活虚拟环境
conda activate jishe

# 安装依赖
pip install -r requirements.txt
```

**Node.js 环境**:
```bash
npm install
npm run dev
```

### 13.5 初始化数据

```python
# backend/scripts/init_db.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def init_database():
    """初始化数据库"""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.ai_competition_assistant
    
    # 创建索引
    await db.users.create_index([("username", 1)], unique=True)
    await db.contests.create_index([("name", 1)])
    await db.contests.create_index([("deadline", 1)])
    
    # 插入示例数据
    await db.contests.insert_one({
        "name": "全国大学生计算机设计大赛",
        "organizer": "教育部高等学校计算机类专业教学指导委员会",
        "entrant_url": "https://example.com/student",
        "teacher_url": "https://example.com/teacher",
        "default_url": "https://example.com",
        "deadline": datetime(2025, 10, 30),
        "status": "ongoing",
        "requirements": ["本科或研究生在校学生", "团队2-5人"],
        "created_at": datetime.utcnow()
    })
    
    print("数据库初始化完成")

if __name__ == "__main__":
    asyncio.run(init_database())
```

---

## 14. 前端与 UX 规范

### 14.1 角色差异化

#### 14.1.1 登录后导航栏

参赛者和教师看到的导航不同：

```javascript
// router/index.js
const routes = [
  {
    path: '/contests',
    name: 'Contests',
    component: Contests,
    meta: { requiresAuth: true, roles: ['entrant', 'teacher'] }
  },
  {
    path: '/my-projects',
    name: 'MyProjects',
    component: MyProjects,
    meta: { requiresAuth: true, roles: ['entrant'] }
  },
  {
    path: '/manage-students',
    name: 'ManageStudents',
    component: ManageStudents,
    meta: { requiresAuth: true, roles: ['teacher'] }
  }
]

router.beforeEach((to, from, next) => {
  const user = store.state.user
  
  if (to.meta.requiresAuth && !user) {
    next('/login')
  } else if (to.meta.roles && !to.meta.roles.includes(user.role)) {
    next('/unauthorized')
  } else {
    next()
  }
})
```

#### 14.1.2 跳转按钮

调用后端 `/contests/{id}/redirect` 接口：

```vue
<template>
  <button @click="redirectToOfficial" class="btn-primary">
    {{ user.role === 'teacher' ? '教师入口' : '参赛入口' }}
  </button>
</template>

<script>
export default {
  methods: {
    async redirectToOfficial() {
      try {
        const response = await api.get(`/contests/${this.contestId}/redirect`)
        if (response.data.status === 'success') {
          window.open(response.data.data.url, '_blank')
        }
      } catch (error) {
        this.$message.error('跳转失败，请稍后再试')
      }
    }
  }
}
</script>
```

### 14.2 AI 结果展示

展示 AI 抽取结果时必须标注：

```vue
<template>
  <div class="ai-extraction-result">
    <div class="confidence-badge" :class="getConfidenceClass()">
      置信度: {{ (extraction.confidence * 100).toFixed(0) }}%
    </div>
    
    <div class="info-item">
      <label>报名截止日期:</label>
      <span>{{ extraction.extracted_json.deadline || '未提取到' }}</span>
    </div>
    
    <div class="info-item">
      <label>参赛者入口:</label>
      <a :href="extraction.extracted_json.entrant_url" target="_blank">
        {{ extraction.extracted_json.entrant_url || '未提取到' }}
      </a>
    </div>
    
    <div class="metadata">
      <small>
        来源: <a :href="extraction.source_url" target="_blank">{{ extraction.source_url }}</a><br>
        提取时间: {{ formatDate(extraction.extraction_time) }}<br>
        模型: {{ extraction.model }}
      </small>
    </div>
    
    <div class="disclaimer">
      ⚠️ 以上信息由AI自动提取，仅供参考，请以官方网站为准
    </div>
    
    <button v-if="extraction.confidence < 0.6" @click="requestReview">
      信息有误？提交人工审核
    </button>
  </div>
</template>

<script>
export default {
  props: ['extraction'],
  methods: {
    getConfidenceClass() {
      const conf = this.extraction.confidence
      if (conf >= 0.8) return 'high'
      if (conf >= 0.6) return 'medium'
      return 'low'
    },
    formatDate(date) {
      return new Date(date).toLocaleString('zh-CN')
    },
    requestReview() {
      // 提交审核请求
    }
  }
}
</script>

<style scoped>
.confidence-badge.high { background: #52c41a; }
.confidence-badge.medium { background: #faad14; }
.confidence-badge.low { background: #f5222d; }
.disclaimer {
  color: #ff4d4f;
  padding: 10px;
  background: #fff1f0;
  border-left: 3px solid #ff4d4f;
}
</style>
```

### 14.3 可访问性

遵循基本 WCAG 原则：

- **文本可放大**: 使用相对单位（rem/em）
- **可键盘操作**: 所有交互元素支持 Tab 导航
- **足够对比度**: 文本与背景对比度 ≥ 4.5:1
- **Alt 文本**: 图片必须有 alt 属性
- **语义化HTML**: 使用正确的标签（header、nav、main、footer）

### 14.4 错误与加载状态

#### 14.4.1 加载状态

```vue
<template>
  <div v-if="loading" class="loading-container">
    <div class="spinner"></div>
    <p>AI正在解析文档，请稍候...</p>
  </div>
  <div v-else-if="error" class="error-container">
    <p>{{ error }}</p>
    <button @click="retry">重试</button>
  </div>
  <div v-else>
    <!-- 正常内容 -->
  </div>
</template>
```

#### 14.4.2 友好的错误提示

```javascript
const errorMessages = {
  'NETWORK_ERROR': '网络连接失败，请检查您的网络',
  'AUTH_FAILED': '登录已过期，请重新登录',
  'FILE_TOO_LARGE': '文件大小超过限制（最大20MB）',
  'UNSUPPORTED_FILE': '不支持该文件类型',
  'EXTRACTION_FAILED': 'AI解析失败，您可以尝试重新上传或手动输入信息'
}

function handleError(error) {
  const message = errorMessages[error.code] || '操作失败，请稍后再试'
  this.$message.error(message)
}
```

### 14.5 响应式设计

- 支持桌面端（≥1200px）
- 支持平板（768px-1199px）
- 支持移动端（<768px）

---

## 15. 数据评估与验收标准

### 15.1 评价指标

#### 15.1.1 URL 提取准确率

- **Precision（精确率）**: 提取的URL中正确的比例
- **Recall（召回率）**: 正确URL中被提取的比例
- **F1 Score**: Precision 和 Recall 的调和平均

#### 15.1.2 时间抽取准确率

- 格式正确性（ISO8601）
- 日期准确性
- 时区处理

#### 15.1.3 整体完整率

关键字段完整率 = (已提取字段数 / 总字段数) × 100%

### 15.2 MVP 阈值

| 指标 | 目标值 |
|------|--------|
| URL提取准确率 | ≥ 90% |
| 截止日期提取准确率 | ≥ 85% |
| 关键字段完整率 | ≥ 80% |
| 系统可用性 | ≥ 95% |
| API平均响应时间 | < 2秒 |
| AI提取平均时间 | < 30秒 |

### 15.3 人工复核机制

低置信度（< 0.6）条目处理：
1. 标记为"需人工复核"
2. 通知管理员审核
3. 人工修正后更新数据
4. 将修正结果加入训练数据（如果使用微调）

### 15.4 反馈循环

建立用户反馈机制：
- 用户可标记错误信息
- 收集反馈数据
- 定期分析常见错误
- 优化提取算法

---

## 16. 合规与伦理

### 16.1 明确披露

在 UI/README 中告知用户：

> **免责声明**
> 
> 本系统使用 AI 模型自动抽取竞赛信息，结果可能不完全准确，仅供参考。
> 所有竞赛相关的官方信息请以主办方官网发布为准。
> 
> 本系统仅用于学术研究和学习辅助，不承担因信息不准确导致的任何责任。

### 16.2 版权保护

- 不得未经授权大规模分发受版权保护的材料
- 仅做解析/引用并保留来源
- 尊重内容创作者的权益
- 遵守《著作权法》相关规定

### 16.3 用户同意

上传文件/授权爬取前必须：

```vue
<template>
  <div class="upload-form">
    <input type="file" @change="handleFileChange" />
    
    <div class="terms-agreement">
      <label>
        <input type="checkbox" v-model="agreed" />
        我已阅读并同意
        <a href="/terms" target="_blank">使用条款</a>
        和
        <a href="/privacy" target="_blank">隐私政策</a>
      </label>
    </div>
    
    <button :disabled="!agreed" @click="uploadFile">
      上传文件
    </button>
  </div>
</template>

<script>
export default {
  data() {
    return {
      agreed: false,
      file: null
    }
  },
  methods: {
    async uploadFile() {
      if (!this.agreed) {
        this.$message.warning('请先同意使用条款')
        return
      }
      
      // 记录用户同意
      await api.post('/consent', {
        action: 'file_upload',
        agreed_at: new Date().toISOString()
      })
      
      // 上传文件
      // ...
    }
  }
}
</script>
```

### 16.4 禁止用途

本项目禁止用于：
- ❌ 未授权的信息采集
- ❌ 骚扰行为
- ❌ 窃取他人资料
- ❌ 商业化转卖数据
- ❌ 其他违法违规用途

---

## 17. Prompt 管理与模板

### 17.1 存储位置

所有 prompt 必须存放在 `backend/prompts/` 目录

### 17.2 Prompt 文件格式

文件命名: `<用途>_v<版本>.txt`

示例: 
- `html_extraction_v1.txt`
- `pdf_extraction_v1.txt`
- `knowledge_graph_generation_v1.txt`

### 17.3 Prompt 内容要求

每个 prompt 文件必须包含：

1. **任务描述**: 清楚说明要做什么
2. **输入格式**: 说明输入数据的结构
3. **输出格式**: JSON schema 或示例
4. **约束条件**: 如"不要虚构数据"、"找不到返回 null"
5. **变更日志**: 记录每次修改的原因

### 17.4 HTML 提取模板示例

**backend/prompts/html_extraction_v1.txt**:
```
任务：从 HTML 内容中提取参赛者入口（entrant_url）和指导老师入口（teacher_url）

要求：
- 只返回有效的绝对 URL（或 null）
- 识别包含"报名/参赛/注册/提交作品/submit/entrance/register"关键词的链接为 entrant_url
- 识别包含"教师/指导/老师/导师/teacher/mentor/advisor"关键词的链接为 teacher_url
- 如果无法确定，填 null 并在 notes 字段说明原因
- 不要虚构链接
- 返回完整的URL（包含协议和域名）

输入：
<<HTML_CONTENT>>

输出（严格 JSON）：
{
  "entrant_url": "完整URL 或 null",
  "teacher_url": "完整URL 或 null",
  "confidence": 0.0-1.0,
  "notes": "可选备注"
}

示例：
输入HTML包含：<a href="/student/register">学生报名入口</a>
输出：{"entrant_url": "https://example.com/student/register", "teacher_url": null, "confidence": 0.9}

版本：v1
最后更新：2025-10-06
变更日志：
- v1: 初始版本，支持中英文关键词识别
```

### 17.5 PDF 提取模板示例

**backend/prompts/pdf_extraction_v1.txt**:
```
任务：从 PDF 文本中提取关键竞赛信息

要求：
- 提取报名截止日期（deadline），尽量返回 ISO8601 格式（YYYY-MM-DD）
- 提取报名要求（requirements）列表
- 提取参赛者入口（entrant_url）
- 提取指导老师入口（teacher_url）
- 提取奖项信息（prize_info）
- 提取联系方式（contact_info）
- 保留原始文本片段（raw_snippet）
- 找不到的字段返回 null
- 不要虚构信息

输入：
<<PDF_TEXT>>

输出（严格 JSON）：
{
  "deadline": "YYYY-MM-DD 或 null",
  "requirements": ["要求1", "要求2"] 或 [],
  "entrant_url": "完整URL 或 null",
  "teacher_url": "完整URL 或 null",
  "prize_info": "奖项描述 或 null",
  "contact_info": "联系方式 或 null",
  "raw_snippet": "原始文本片段",
  "confidence": 0.0-1.0,
  "notes": "可选备注"
}

版本：v1
最后更新：2025-10-06
变更日志：
- v1: 初始版本
```

### 17.6 知识图谱生成模板

**backend/prompts/knowledge_graph_generation_v1.txt**:
```
任务：从竞赛文本中提取实体和关系，生成知识图谱

要求：
- 识别关键实体：竞赛阶段、技能要求、参赛要求、资源、截止日期
- 识别实体间的关系：包含、需要、先于、相关
- 每个节点必须有唯一ID、标签和类型
- 每条边必须有源节点、目标节点和关系类型

输入：
<<CONTEST_TEXT>>

输出（严格 JSON）：
{
  "nodes": [
    {
      "id": "stage_1",
      "label": "初赛",
      "type": "stage",
      "properties": {
        "deadline": "2025-11-01",
        "description": "提交作品"
      }
    },
    {
      "id": "skill_1",
      "label": "Python编程",
      "type": "skill"
    }
  ],
  "edges": [
    {
      "source": "stage_1",
      "target": "skill_1",
      "relation": "requires"
    }
  ]
}

节点类型：
- stage: 竞赛阶段
- requirement: 参赛要求
- skill: 技能要求
- resource: 学习资源
- deadline: 截止日期

关系类型：
- requires: 需要
- leads_to: 先于
- related_to: 相关
- provides: 提供

版本：v1
最后更新：2025-10-06
变更日志：
- v1: 初始版本
```

### 17.7 Prompt 版本控制

- 每次修改 prompt 时创建新版本（v1 → v2）
- 保留旧版本以便回滚
- 在数据库中记录使用的 prompt 版本
- 对比不同版本的效果

### 17.8 Prompt 加载

```python
# backend/utils/prompt_loader.py
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

def load_prompt(prompt_file: str) -> str:
    """加载prompt模板"""
    prompt_path = PROMPTS_DIR / prompt_file
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    
    return prompt_path.read_text(encoding='utf-8')

def get_latest_prompt_version(prompt_name: str) -> str:
    """获取最新版本的prompt"""
    versions = list(PROMPTS_DIR.glob(f"{prompt_name}_v*.txt"))
    if not versions:
        raise FileNotFoundError(f"No prompt found for: {prompt_name}")
    
    # 按版本号排序，返回最新版
    latest = sorted(versions, key=lambda p: p.stem.split('_v')[-1])[-1]
    return latest.name
```

---

## 18. 开发阶段与里程碑

### 18.1 第一阶段：MVP（最小可行产品）

**目标**: 完成核心功能演示

**功能清单**:
- ✅ 用户注册/登录（JWT认证）
- ✅ 角色选择（参赛者/教师）
- ✅ 竞赛列表展示
- ✅ 角色跳转功能
- ✅ PDF/HTML 基础解析
- ✅ AI 信息提取（URL、截止日期、要求）
- ✅ 简单的知识图谱展示

**时间估算**: 2-3周

### 18.2 第二阶段：增强功能

**功能清单**:
- 文件上传与管理
- AI 提取结果审核
- 知识图谱高级可视化
- 搜索与筛选功能
- 用户个人中心

**时间估算**: 2周

### 18.3 第三阶段：优化与完善

**功能清单**:
- 性能优化
- 测试覆盖提升
- 错误处理完善
- UI/UX 优化
- 文档完善

**时间估算**: 1-2周

### 18.4 里程碑验收

每个阶段完成后进行验收：

1. **功能验收**: 所有功能正常运行
2. **性能验收**: 满足性能指标
3. **安全验收**: 通过安全检查
4. **用户验收**: 用户体验良好

---

## 19. AI IDE 使用规范

### 19.1 Cursor/AI 辅助开发原则

- **明确需求**: 给AI明确的任务描述
- **分步实现**: 将大任务拆分成小步骤
- **代码审查**: 不盲目接受AI生成的代码，必须审查
- **测试验证**: AI生成的代码必须经过测试

### 19.2 有效的提示词（Prompts）

**好的提示词示例**:
```
请帮我创建一个FastAPI路由，实现竞赛列表的分页查询功能。
要求：
- 路径：/api/v1/contests
- 支持分页参数：skip（默认0）、limit（默认10）
- 支持筛选参数：status（可选）
- 返回统一格式的JSON响应
- 包含错误处理
```

**不好的提示词**:
```
写个竞赛接口
```

### 19.3 代码生成后的检查清单

- [ ] 代码符合项目规范
- [ ] 包含必要的类型注解
- [ ] 包含错误处理
- [ ] 包含注释说明
- [ ] 没有安全隐患
- [ ] 可以正常运行

### 19.4 利用AI进行代码重构

**重构提示示例**:
```
请帮我重构这个函数，优化以下方面：
1. 提取重复代码
2. 改善变量命名
3. 添加类型注解
4. 优化错误处理
5. 添加docstring

[粘贴要重构的代码]
```

### 19.5 AI 辅助调试

**调试提示示例**:
```
我遇到了以下错误：
[错误信息]

相关代码：
[粘贴代码]

可能的原因是什么？如何修复？
```

### 19.6 启动脚本规范

**禁止自动创建启动脚本**:
- 不要主动创建 `.bat`、`.sh` 或其他启动脚本文件
- 用户明确要求时才创建启动脚本
- 启动脚本必须经过用户确认才能创建

**启动脚本命名规范**:
- Windows: `start_backend.bat`、`start_frontend.bat`、`start_all.bat`
- Linux/Mac: `start_backend.sh`、`start_frontend.sh`、`start_all.sh`

**启动脚本内容规范**:
- 必须包含错误检查
- 必须包含环境检查
- 必须包含清晰的提示信息
- 必须支持用户中断（pause命令）

### 19.7 PowerShell 命令行规范

**PowerShell 命令使用规范**:
- 优先使用 PowerShell 命令而不是 CMD 命令
- 使用 PowerShell 的现代语法和功能
- 避免使用过时的 CMD 命令

**文件操作**:
```powershell
# 创建文件
New-Item -ItemType File -Name "filename.txt"

# 复制文件
Copy-Item "source.txt" "destination.txt"

# 移动文件
Move-Item "source.txt" "destination.txt"

# 删除文件
Remove-Item "filename.txt"

# 检查文件是否存在
Test-Path "filename.txt"
```

**目录操作**:
```powershell
# 列出目录内容
Get-ChildItem
# 或简写
ls

# 创建目录
New-Item -ItemType Directory -Name "dirname"

# 切换目录
Set-Location "path"
# 或简写
cd "path"

# 显示当前目录
Get-Location
# 或简写
pwd
```

**环境变量操作**:
```powershell
# 设置环境变量
$env:VARIABLE_NAME = "value"

# 读取环境变量
$env:VARIABLE_NAME

# 永久设置环境变量
[Environment]::SetEnvironmentVariable("VARIABLE_NAME", "value", "User")
```

**文本文件操作**:
```powershell
# 写入文本到文件
"content" | Out-File -FilePath "file.txt" -Encoding UTF8

# 追加文本到文件
"content" | Add-Content -Path "file.txt" -Encoding UTF8

# 读取文件内容
Get-Content "file.txt"

# 多行文本写入
@"
line1
line2
line3
"@ | Out-File -FilePath "file.txt" -Encoding UTF8
```

**进程和服务操作**:
```powershell
# 启动进程
Start-Process "program.exe" -ArgumentList "arg1", "arg2"

# 停止进程
Stop-Process -Name "processname"

# 检查进程是否运行
Get-Process -Name "processname" -ErrorAction SilentlyContinue
```

**网络操作**:
```powershell
# 测试网络连接
Test-NetConnection -ComputerName "localhost" -Port 8000

# 下载文件
Invoke-WebRequest -Uri "url" -OutFile "filename"

# 检查端口是否被占用
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
```

**错误处理**:
```powershell
# 忽略错误继续执行
command -ErrorAction SilentlyContinue

# 捕获错误
try {
    command
} catch {
    Write-Error "Error occurred: $_"
}

# 检查命令执行结果
if ($LASTEXITCODE -ne 0) {
    Write-Error "Command failed with exit code $LASTEXITCODE"
}
```

**条件判断和循环**:
```powershell
# 条件判断
if (condition) {
    # do something
} elseif (other_condition) {
    # do something else
} else {
    # do default
}

# 循环
foreach ($item in $collection) {
    # process $item
}

# while 循环
while (condition) {
    # do something
}
```

**常用别名**:
```powershell
# 常用命令别名
ls = Get-ChildItem
cd = Set-Location
pwd = Get-Location
cat = Get-Content
echo = Write-Output
```

**项目特定命令**:
```powershell
# 激活conda环境
conda activate jishe

# 启动后端服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 启动前端服务
npm run dev

# 检查MongoDB连接
Test-NetConnection -ComputerName "localhost" -Port 27017
```

---

## 附录

### A. 常用命令

**后端**:
```bash
# 激活conda环境
conda activate jishe

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn main:app --reload

# 运行测试
pytest

# 生成测试覆盖率报告
pytest --cov=backend --cov-report=html

# 代码格式化
black .
isort .
```

**前端**:
```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 运行测试
npm test

# 代码格式化
npm run format
```

**本地开发 (Windows + Conda)**:
```bash
# 启动MongoDB
# Windows: 启动MongoDB服务

# 启动后端
cd backend
conda activate jishe
uvicorn main:app --reload

# 启动前端
cd frontend
npm run dev
```

### B. 常见问题解决

**Q: MongoDB 连接失败**
```
A: 检查 MongoDB 是否启动，检查 .env 中的连接字符串是否正确
```

**Q: AI 模型调用失败**
```
A: 检查 API Key 是否正确，检查网络连接，查看是否超出配额
```

**Q: 文件上传失败**
```
A: 检查文件大小是否超限，检查文件类型是否支持，检查 uploads 目录权限
```

**Q: 前端无法连接后端**
```
A: 检查 CORS 配置，检查后端是否启动，检查前端 API 地址配置
```

### C. 参考资料

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [MongoDB 官方文档](https://docs.mongodb.com/)
- [Vue 3 官方文档](https://vuejs.org/)
- [LangChain 文档](https://python.langchain.com/)
- [PyMuPDF 文档](https://pymupdf.readthedocs.io/)

---

## 20. 文件管理与文档更新规范

### 20.1 文件创建原则

**禁止随意创建文件**:
- ❌ 不要创建不必要的测试文件（如test_*.py, *_test.py）
- ❌ 不要创建示例文件（如example_*.py, demo_*.py）
- ❌ 不要创建临时文件或脚本
- ❌ 不要创建重复的文档文件
- ✅ 只在用户明确要求时才创建新文件
- ✅ 优先编辑现有文件而非创建新文件

**允许创建的文件类型**:
- 核心功能模块（经用户确认）
- 必要的配置文件
- 数据模型文件
- API路由文件
- 前端组件（按需）

### 20.2 文档更新强制规范

**每次功能更新必须同步更新以下文档**:

1. **README.md** - 主项目说明文档
   - 更新功能列表
   - 更新技术栈（如有新依赖）
   - 更新快速开始步骤
   - 更新使用示例
   - 更新版本号和更新日期

2. **CHANGELOG.md** - 更新日志
   - 记录新增功能
   - 记录修改内容
   - 记录依赖变更
   - 记录API变更
   - 按版本号组织

3. **QUICKSTART.md** - 快速启动指南
   - 更新环境要求
   - 更新安装步骤
   - 更新配置说明
   - 更新启动命令

4. **requirements.txt / package.json** - 依赖清单
   - 添加新的Python依赖到requirements.txt
   - 添加新的npm依赖到package.json
   - 标注依赖用途（注释）

5. **API文档** - 接口文档（如适用）
   - 记录新的API端点
   - 更新请求/响应格式
   - 添加使用示例
   - 更新错误码说明

### 20.3 文档更新检查清单

每次提交代码前检查：

- [ ] README.md 是否已更新功能描述？
- [ ] CHANGELOG.md 是否已记录本次变更？
- [ ] 启动文档是否已更新（如有配置变化）？
- [ ] 依赖文件是否已更新（如有新依赖）？
- [ ] API文档是否已更新（如有新接口）？
- [ ] 是否删除了不必要的临时文件？
- [ ] 是否删除了测试/示例文件？

### 20.4 文档编写规范

**README.md 结构**:
```markdown
# 项目名称

## 项目简介
## 核心功能（带图标和说明）
## 最新功能（突出显示）
## 快速开始
  ### 环境要求
  ### 安装步骤
  ### 启动服务
  ### 访问应用
## 技术栈
## 功能配置（如AI密钥等）
## 文档链接
## 主要功能模块
## 项目结构
## 开发指南
## 使用示例
## 注意事项
## 故障排查
## 贡献指南
## 许可证
## 联系方式
## 致谢
```

**CHANGELOG.md 结构**:
```markdown
# 更新日志

## [版本号] - 日期

### ✨ 新增功能
- 功能1描述
- 功能2描述

### 📦 新增依赖
- 依赖1及其用途
- 依赖2及其用途

### 📝 文档更新
- 更新的文档列表

### 🏗️ 架构改进
- 架构改进说明

### 🔒 安全改进
- 安全相关改进

### 🐛 Bug修复
- 修复的问题

### 🗑️ 移除内容
- 移除的功能或文件

---

## [未来计划]
- [ ] 计划功能1
- [ ] 计划功能2
```

### 20.5 启动文档规范

**QUICKSTART.md 必须包含**:
1. 环境准备（版本要求）
2. 依赖安装（详细命令）
3. 配置步骤（环境变量等）
4. 启动命令（前后端）
5. 访问地址
6. 常见问题（至少3个）
7. 验证方法（如何确认启动成功）

**启动命令格式**:
```bash
# 后端启动
cd backend
conda activate jishe
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 前端启动
cd frontend
npm run dev
```

### 20.6 文件清理规范

**定期清理以下文件**:
- 测试文件（test_*.py, *_test.py, *.test.js）
- 示例文件（example_*.py, demo_*.js）
- 临时文件（*.tmp, *.bak, *~）
- 编译文件（*.pyc, __pycache__/）
- 构建文件（dist/, build/）
- 日志文件（*.log）

**保留的文件**:
- 核心功能模块
- 必要的配置文件
- 正式的文档文件
- 依赖清单文件

### 20.7 代码变更记录规范

**变更记录格式**:
```
[日期] 类型(范围): 简短描述

详细说明（可选）

相关文档更新：
- README.md
- CHANGELOG.md
```

**类型标识**:
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具变动

**示例**:
```
[2025-10-06] feat(ai-extract): 添加多AI提供商支持

- 集成Cloudflare、Google Gemini、豆包三个AI提供商
- 实现智能能力检测和自动降级
- 添加完整的错误提示机制

相关文档更新：
- README.md - 添加AI功能介绍
- CHANGELOG.md - 记录v1.0.0变更
- QUICKSTART_AI.md - 新增快速开始指南
- requirements_ai.txt - 添加AI相关依赖
```

**注意**: 本项目不使用Git，变更记录直接写入CHANGELOG.md文件

### 20.8 代码审查检查点

提交前自查：
1. ✅ 是否有不必要的文件？
2. ✅ 文档是否已全部更新？
3. ✅ 代码是否符合项目规范？
4. ✅ 是否包含敏感信息？
5. ✅ 依赖文件是否正确？
6. ✅ 启动文档是否准确？

### 20.9 文档版本管理

- 每次重大更新增加版本号
- 在文档末尾标注版本和更新日期
- 保留历史版本的CHANGELOG记录
- 定期归档过期文档

**文档版本格式**:
```markdown
---

**文档版本**: v1.1.0
**最后更新**: 2025-10-06
**维护者**: 项目开发团队
**本次更新**: 添加AI智能提取功能
```

---

**文档版本**: v1.1  
**最后更新**: 2025-10-06  
**维护者**: 项目开发团队  
**本次更新**: 添加文件管理与文档更新规范
