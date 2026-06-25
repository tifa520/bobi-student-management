FROM node:18-alpine AS builder

WORKDIR /app

# 使用淘宝镜像加速
RUN npm config set registry https://registry.npmmirror.com

# 复制 package.json
COPY frontend/package*.json ./

# 安装依赖（使用 legacy-peer-deps 解决依赖冲突）
RUN npm install --legacy-peer-deps

# 复制源代码
COPY frontend/ .

# 构建
RUN npm run build

# 生产镜像
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 设置权限
RUN chmod -R 755 /usr/share/nginx/html

# 复制 nginx 配置
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]