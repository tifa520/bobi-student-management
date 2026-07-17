#!/bin/bash
# ============================================================
# NAS 一键设置脚本 - 在 NAS 上运行此脚本完成初始配置
# 运行方式: chmod +x setup-nas.sh && ./setup-nas.sh
# ============================================================

set -e

PROJECT_DIR="/vol1/1000/Docker/bobi-student-management"
GITEE_REMOTE="https://gitee.com/steven985/bobi-student-management.git"

echo "============================================"
echo "  bobi-student-management NAS 部署设置"
echo "============================================"
echo ""

# 1. 检查项目目录
if [ ! -d "$PROJECT_DIR" ]; then
    echo "[错误] 项目目录不存在: $PROJECT_DIR"
    echo "请先在 NAS 上克隆项目:"
    echo "  git clone https://gitee.com/steven985/bobi-student-management.git $PROJECT_DIR"
    exit 1
fi
echo "[OK] 项目目录已存在"

cd "$PROJECT_DIR"

# 2. 确保 Gitee 远程存在
if ! git remote | grep -q gitee; then
    git remote add gitee "$GITEE_REMOTE"
    echo "[OK] 已添加 Gitee 远程"
else
    echo "[OK] Gitee 远程已存在"
fi

# 3. 设置 auto-deploy.sh
if [ -f "$PROJECT_DIR/auto-deploy.sh" ]; then
    chmod +x "$PROJECT_DIR/auto-deploy.sh"
    echo "[OK] auto-deploy.sh 已就绪"
else
    echo "[警告] auto-deploy.sh 不存在，请先从开发环境同步"
fi

# 4. 设置 cron 定时任务（每 5 分钟检查一次）
CRON_JOB="*/5 * * * * $PROJECT_DIR/auto-deploy.sh >> $PROJECT_DIR/deploy.log 2>&1"
if crontab -l 2>/dev/null | grep -q "auto-deploy.sh"; then
    echo "[OK] cron 任务已存在"
else
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "[OK] 已添加 cron 任务（每 5 分钟检查一次）"
fi

echo ""
echo "============================================"
echo "  设置完成！"
echo "  - 项目目录: $PROJECT_DIR"
echo "  - 日志文件: $PROJECT_DIR/deploy.log"
echo "  - 检查频率: 每 5 分钟"
echo ""
echo "  手动测试: $PROJECT_DIR/auto-deploy.sh"
echo "  查看日志: tail -f $PROJECT_DIR/deploy.log"
echo "============================================"