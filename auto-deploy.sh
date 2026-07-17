#!/bin/bash
# ============================================================
# bobi-student-management NAS 自动部署脚本
# 用途：定时检查远程仓库是否有新提交，有则自动拉取并重建
# 用法：将此脚本放到 NAS 的 /vol1/1000/Docker/bobi-student-management/
#       然后设置 cron 定时执行，例如每 5 分钟检查一次：
#       */5 * * * * /vol1/1000/Docker/bobi-student-management/auto-deploy.sh >> /vol1/1000/Docker/bobi-student-management/deploy.log 2>&1
# ============================================================

set -e

PROJECT_DIR="/vol1/1000/Docker/bobi-student-management"
LOCK_FILE="/tmp/bobi-auto-deploy.lock"
LOG_FILE="$PROJECT_DIR/deploy.log"

# 防止并发执行
if [ -f "$LOCK_FILE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 上一次部署仍在进行中，跳过本次检查"
    exit 0
fi
touch "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

cd "$PROJECT_DIR" || { log "错误: 无法进入项目目录 $PROJECT_DIR"; exit 1; }

log "开始检查远程仓库更新..."

# 记录当前 HEAD
BEFORE=$(git rev-parse HEAD 2>/dev/null)

# 拉取远程更新
git fetch origin 2>&1 || { log "错误: git fetch 失败"; exit 1; }

# 尝试合并（使用 --ff-only 避免冲突）
if git merge --ff-only origin/main 2>/dev/null; then
    AFTER=$(git rev-parse HEAD)
    if [ "$BEFORE" != "$AFTER" ]; then
        log "检测到新提交: ${AFTER:0:8}"
        log "最新提交信息: $(git log -1 --oneline)"

        log "开始重新构建 Docker 镜像..."
        docker compose build backend frontend 2>&1 || { log "错误: Docker 构建失败"; exit 1; }

        log "开始重启服务..."
        docker compose up -d 2>&1 || { log "错误: Docker 启动失败"; exit 1; }

        # 清理旧镜像（保留最近 3 个）
        docker image prune -f --filter "until=72h" 2>/dev/null

        log "部署完成！"
    else
        log "无新提交，跳过部署"
    fi
else
    log "无新提交或合并失败（可能需要手动处理）"
    # 重置到远程状态，放弃本地修改
    git reset --hard origin/main 2>/dev/null || log "警告: git reset 失败"
fi