# 前端应用说明

## 项目结构

```
frontend/
├── src/
│   ├── main.js             # 应用入口
│   ├── App.vue             # 根组件
│   ├── pages/              # 页面组件
│   ├── components/         # 通用组件
│   ├── router/             # 路由配置
│   ├── store/              # 状态管理
│   └── api/                # API 接口
├── index.html              # HTML 模板
├── vite.config.js          # Vite 配置
└── package.json
```

## 安装依赖

```bash
npm install
```

## 开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

## 构建生产版本

```bash
npm run build
```

## 页面路由

- `/login` - 登录页面
- `/register` - 注册页面
- `/home` - 首页
- `/contests` - 竞赛列表
- `/contests/:id` - 竞赛详情
- `/ai-extract` - AI 智能提取

## 状态管理

使用 Pinia 管理用户状态：

```javascript
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
userStore.setUser(userData)
userStore.setToken(token)
```

## API 调用

```javascript
import { contestAPI } from '@/api'

const res = await contestAPI.getList(params)
```

