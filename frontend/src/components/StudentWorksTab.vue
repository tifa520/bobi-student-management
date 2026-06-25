<template>
  <div class="student-works">
    <!-- 上传区域 -->
    <div class="upload-area">
      <el-upload
        ref="uploadRef"
        :action="uploadUrl"
        :headers="uploadHeaders"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :before-upload="beforeUpload"
        :show-file-list="false"
        accept="image/*,video/*"
        multiple
      >
        <el-button type="primary">
          <el-icon><Upload /></el-icon> 上传作品
        </el-button>
      </el-upload>
      <span class="upload-tip">支持图片（jpg/png/gif/webp）和视频（mp4/avi/mov），单个文件不超过 100MB</span>
    </div>

    <!-- 操作栏 -->
    <div class="works-toolbar" v-if="works.length > 0">
      <el-checkbox v-model="selectAll" @change="toggleSelectAll">全选</el-checkbox>
      <el-button type="primary" :disabled="selectedIds.length === 0" @click="downloadSelected">
        <el-icon><Download /></el-icon> 下载原图 ({{ selectedIds.length }})
      </el-button>
      <el-button type="danger" :disabled="selectedIds.length === 0" @click="deleteSelected">
        <el-icon><Delete /></el-icon> 删除选中
      </el-button>
    </div>

    <!-- 作品列表（时间线倒序） -->
    <div class="works-grid" v-loading="loading">
      <div
        v-for="item in works"
        :key="item.id"
        class="work-item"
        :class="{ selected: selectedIds.includes(item.id) }"
        @click="toggleSelect(item.id)"
      >
        <div class="work-thumbnail">
          <img v-if="item.type === 'image'" :src="item.thumbnail_url" :alt="item.name" />
          <video v-else-if="item.type === 'video'" :src="item.thumbnail_url" muted></video>
          <div v-else class="file-icon"><el-icon><Document /></el-icon></div>
          <div class="work-checkbox">
            <el-checkbox :model-value="selectedIds.includes(item.id)" @click.stop />
          </div>
          <div class="work-download" @click.stop="downloadSingle(item)">
            <el-icon><Download /></el-icon>
          </div>
        </div>
        <div class="work-info">
          <div class="work-name">{{ item.name }}</div>
          <div class="work-time">{{ item.created_at }}</div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty v-if="works.length === 0 && !loading" description="暂无作品，点击上传" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Download, Delete, Document } from '@element-plus/icons-vue'
import request from '@/api/request'
import JSZip from 'jszip'
import { saveAs } from 'file-saver'

const props = defineProps({
  studentId: {
    type: Number,
    required: true
  }
})

const works = ref([])
const loading = ref(false)
const selectedIds = ref([])

const uploadUrl = computed(() => `/api/student/works/${props.studentId}/upload`)
const uploadHeaders = computed(() => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }))

const selectAll = computed({
  get: () => works.value.length > 0 && selectedIds.value.length === works.value.length,
  set: (val) => {
    if (val) {
      selectedIds.value = works.value.map(w => w.id)
    } else {
      selectedIds.value = []
    }
  }
})

// 加载作品列表
async function fetchWorks() {
  if (!props.studentId) return
  loading.value = true
  try {
    const res = await request.get(`/student/works/${props.studentId}`)
    works.value = res.data || []
  } catch (e) {
    console.error(e)
    ElMessage.error('加载作品失败')
  } finally {
    loading.value = false
  }
}

// 上传前校验
function beforeUpload(file) {
  const isImage = file.type.startsWith('image/')
  const isVideo = file.type.startsWith('video/')
  const isValidType = isImage || isVideo
  const isLt100M = file.size / 1024 / 1024 < 100
  if (!isValidType) {
    ElMessage.error('仅支持图片或视频文件')
    return false
  }
  if (!isLt100M) {
    ElMessage.error('文件大小不能超过 100MB')
    return false
  }
  return true
}

function handleUploadSuccess(res) {
  if (res.code === 0) {
    ElMessage.success('上传成功')
    fetchWorks()
  } else {
    ElMessage.error(res.message || '上传失败')
  }
}

function handleUploadError() {
  ElMessage.error('上传失败')
}

// 切换选择
function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx > -1) {
    selectedIds.value.splice(idx, 1)
  } else {
    selectedIds.value.push(id)
  }
}

// 下载单个
function downloadSingle(item) {
  const a = document.createElement('a')
  a.href = item.original_url
  a.download = item.name
  a.target = '_blank'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

// 批量下载（打包ZIP）
async function downloadSelected() {
  if (selectedIds.value.length === 0) return
  const zip = new JSZip()
  const selectedWorks = works.value.filter(w => selectedIds.value.includes(w.id))
  try {
    for (const item of selectedWorks) {
      const response = await fetch(item.original_url)
      const blob = await response.blob()
      zip.file(item.name, blob)
    }
    const zipBlob = await zip.generateAsync({ type: 'blob' })
    saveAs(zipBlob, `学员作品_${props.studentId}_${new Date().toISOString().slice(0,10)}.zip`)
    ElMessage.success('下载成功')
  } catch (e) {
    console.error(e)
    ElMessage.error('下载失败')
  }
}

// 删除选中
async function deleteSelected() {
  if (selectedIds.value.length === 0) return
  try {
    await ElMessageBox.confirm('确认删除选中的作品？', '提示', { type: 'warning' })
    await request.delete(`/student/works/${props.studentId}`, { data: { ids: selectedIds.value } })
    ElMessage.success('删除成功')
    selectedIds.value = []
    fetchWorks()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(() => {
  fetchWorks()
})
</script>

<style scoped>
.student-works {
  padding: 0;
}
.upload-area {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.upload-tip {
  font-size: 12px;
  color: #909399;
}
.works-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.works-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}
.work-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  background: #fff;
}
.work-item:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.work-item.selected {
  border-color: #36b459;
  box-shadow: 0 0 0 2px #36b459;
}
.work-thumbnail {
  position: relative;
  width: 100%;
  padding-top: 75%; /* 4:3 */
  background: #f5f7fa;
  overflow: hidden;
}
.work-thumbnail img,
.work-thumbnail video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.work-thumbnail .file-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 48px;
  color: #c0c4cc;
}
.work-checkbox {
  position: absolute;
  top: 6px;
  left: 6px;
  background: rgba(255,255,255,0.8);
  border-radius: 4px;
  padding: 2px;
}
.work-download {
  position: absolute;
  bottom: 6px;
  right: 6px;
  background: rgba(0,0,0,0.5);
  color: #fff;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;
}
.work-download:hover {
  background: rgba(0,0,0,0.7);
}
.work-info {
  padding: 8px 10px;
}
.work-name {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.work-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>