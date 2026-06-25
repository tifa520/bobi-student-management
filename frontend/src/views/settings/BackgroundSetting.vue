<template>
  <div class="settings-page">
    <div class="settings-card">
      <div class="card-header">
        <span class="card-title">登录页背景设置</span>
      </div>
      <div class="content-container">
        <div class="upload-area">
          <el-upload
            class="bg-upload"
            drag
            :action="uploadUrl"
            :headers="uploadHeaders"
            :on-success="handleSuccess"
            :on-error="handleError"
            :show-file-list="false"
            :before-upload="beforeUpload"
            :limit="1"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              拖拽图片到此处或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                建议使用 1920x1080 以上的高清图片，支持 jpg/png/webp，不超过 5MB
              </div>
            </template>
          </el-upload>
        </div>
        <div v-if="currentBgUrl" class="preview-area">
          <div class="preview-label">当前背景预览：</div>
          <div class="preview-image-wrapper">
            <el-image 
              :src="currentBgUrl" 
              fit="cover" 
              class="preview-image"
              :preview-src-list="[currentBgUrl]"
              :initial-index="0"
              :z-index="9999"
            />
          </div>
          <div class="preview-tip">点击图片可查看大图</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import request from '@/api/request'
import { getLoginBg, uploadLoginBg } from '@/api/settings'

const currentBgUrl = ref('')
const uploadUrl = '/api/upload/login-bg'

const uploadHeaders = computed(() => {
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('access_token') : null
  return token ? { Authorization: `Bearer ${token}` } : {}
})

function beforeUpload(file) {
  const isImage = file.type.startsWith('image/')
  const isLt5M = file.size / 1024 / 1024 < 5
  if (!isImage) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB')
    return false
  }
  return true
}

async function fetchBgUrl() {
  try {
    const res = await getLoginBg()
    if (res.code === 0 && res.data?.url) {
      currentBgUrl.value = res.data.url
    }
  } catch (e) {
    console.error('获取背景失败', e)
  }
}

function handleSuccess(res) {
  if (res.code === 0 && res.data?.url) {
    ElMessage.success('背景更新成功')
    currentBgUrl.value = res.data.url
  } else {
    ElMessage.error(res.message || '上传失败')
  }
}

function handleError() {
  ElMessage.error('上传失败，请重试')
}

onMounted(() => {
  fetchBgUrl()
})
</script>

<style scoped>
.settings-page {
  padding: 24px;
  background: var(--app-bg);
  min-height: 100%;
}
.settings-card {
  background: var(--surface);
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}
.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-light);
}
.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}
.content-container {
  padding: 24px;
}
.upload-area {
  margin-bottom: 24px;
}
.bg-upload :deep(.el-upload-dragger) {
  width: 100%;
  padding: 40px 20px;
  border-radius: 12px;
  background-color: var(--surface-soft);
  border: 1px dashed var(--border-color);
}
.bg-upload :deep(.el-icon--upload) {
  font-size: 48px;
  color: var(--gray-400);
  margin-bottom: 16px;
}
.preview-area {
  margin-top: 24px;
  border-top: 1px solid var(--border-light);
  padding-top: 20px;
}
.preview-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 12px;
}
.preview-image-wrapper {
  width: 100%;
  max-height: 400px;
  overflow: hidden;
  border-radius: 8px;
  border: 1px solid var(--border-light);
  background: var(--app-bg);
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
}
.preview-image {
  width: 100%;
  height: auto;
  max-height: 400px;
  object-fit: contain;
  transition: transform 0.2s;
}
.preview-image:hover {
  transform: scale(1.02);
}
.preview-tip {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  text-align: center;
}
</style>