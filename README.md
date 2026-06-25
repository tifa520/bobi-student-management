# Bobi艺术·学员管理系统

## 快速开始

### 本地开发

```bash
# 前端开发
cd frontend
npm install
npm run dev

# 后端开发
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Docker 部署

```bash
# 构建并启动
docker compose up -d --build

# 查看日志
docker compose logs -f backend
docker compose logs -f frontend

# 重启
docker compose restart backend
```

### 更新部署（Git 方式）

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker compose build --no-cache backend frontend
docker compose up -d
```

## 目录结构

```
bobi-student-management/
├── backend/          # FastAPI 后端
├── frontend/         # Vue 3 前端
├── data/             # SQLite 数据库（git 忽略）
├── logs/             # 日志文件（git 忽略）
├── media/            # 媒体文件（git 忽略）
├── uploads/          # 上传文件（git 忽略）
├── redis-data/       # Redis 数据（git 忽略）
├── docker-compose.yml
└── .env              # 环境变量
```

## 环境变量

复制 `.env.example` 为 `.env` 并修改：

- `SECRET_KEY`: JWT 密钥（生产环境必须修改）
- `ACCESS_TOKEN_EXPIRE_MINUTES`: token 过期时间
- `ENABLE_AUTH_MIDDLEWARE`: 是否启用认证中间件

## 端口

- 前端 + API: `5050`
