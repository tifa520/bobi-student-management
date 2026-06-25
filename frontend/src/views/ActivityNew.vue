<template>
  <div class="activity-new">
    <!-- 面包屑导航 -->
    <el-breadcrumb separator="/" class="breadcrumb">
      <el-breadcrumb-item :to="{ path: '/activities' }">活动管理</el-breadcrumb-item>
      <el-breadcrumb-item>{{ isEdit ? '编辑活动' : '新建活动' }}</el-breadcrumb-item>
    </el-breadcrumb>

    <div class="form-container" v-loading="loading">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px" class="activity-form">
        <!-- 基本信息 -->
        <el-card class="form-card" shadow="never">
          <template #header><span class="card-title">基本信息</span></template>
          <el-row :gutter="24">
            <el-col :span="24">
              <el-form-item label="活动名称" prop="name">
                <el-input v-model="form.name" placeholder="请输入活动名称" maxlength="50" size="default" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="活动类型" prop="activity_type">
                <el-select v-model="form.activity_type" placeholder="请选择活动类型" size="default" style="width:100%">
                  <el-option label="音乐会" value="音乐会" />
                  <el-option label="画展" value="画展" />
                  <el-option label="比赛" value="比赛" />
                  <el-option label="研学" value="研学" />
                  <el-option label="试听课" value="试听课" />
                  <el-option label="生日会" value="生日会" />
                  <el-option label="艺术游学" value="艺术游学" />
                  <el-option label="写生" value="写生" />
                  <el-option label="家长沙龙" value="家长沙龙" />
                  <el-option label="节日派对" value="节日派对" />
                  <el-option label="其他" value="其他" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="活动地点" prop="location">
                <el-input v-model="form.location" placeholder="请输入活动地点" size="default" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="活动开始时间" prop="start_date">
                <el-date-picker v-model="form.start_date" type="datetime" placeholder="选择开始时间" value-format="YYYY-MM-DD HH:mm:ss" size="default" style="width:100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="活动结束时间" prop="end_date">
                <el-date-picker v-model="form.end_date" type="datetime" placeholder="选择结束时间" value-format="YYYY-MM-DD HH:mm:ss" size="default" style="width:100%" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-card>

        <!-- 报名设置 -->
        <el-card class="form-card" shadow="never">
          <template #header><span class="card-title">报名设置</span></template>
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="报名开始时间" prop="registration_start">
                <el-date-picker v-model="form.registration_start" type="datetime" placeholder="选择报名开始时间" value-format="YYYY-MM-DD HH:mm:ss" size="default" style="width:100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="报名截止时间" prop="registration_end">
                <el-date-picker v-model="form.registration_end" type="datetime" placeholder="选择报名截止时间" value-format="YYYY-MM-DD HH:mm:ss" size="default" style="width:100%" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="报名人数上限" prop="max_participants">
                <el-input-number
                  v-model="form.max_participants"
                  :min="0"
                  placeholder="0表示不限制"
                  :controls="false"
                  size="default"
                  style="width:100%"
                />
                <span class="hint-text">0表示不限制</span>
              </el-form-item>
            </el-col>
          </el-row>
        </el-card>

        <!-- 收费设置 -->
        <el-card class="form-card" shadow="never">
          <template #header><span class="card-title">收费设置</span></template>
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="收费模式" prop="charge_mode">
                <el-radio-group v-model="form.charge_mode" @change="onChargeModeChange">
                  <el-radio label="free" value="free">免费</el-radio>
                  <el-radio label="paid" value="paid">收费</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col :span="12" v-if="form.charge_mode === 'paid'">
              <el-form-item label="活动费用" prop="fee">
                <el-input
                  v-model.number="form.fee"
                  type="number"
                  size="default"
                  style="width:100%"
                  placeholder="请输入费用"
                >
                  <template #suffix>
                    <span style="color: #909399; font-size: 14px;">元</span>
                  </template>
                </el-input>
              </el-form-item>
            </el-col>
          </el-row>
        </el-card>

        <!-- 抽奖设置 -->
        <el-card class="form-card" shadow="never">
          <template #header><span class="card-title">抽奖设置</span></template>
          <el-row :gutter="24">
            <el-col :span="24">
              <el-form-item label="启用抽奖">
                <el-switch v-model="form.enable_lottery" />
                <span class="hint-text">开启后，学员可在活动页面参与抽奖</span>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="24" v-if="form.enable_lottery">
            <el-col :span="12">
              <el-form-item label="每人可抽次数" prop="lottery_times">
                <el-input
                  v-model.number="form.lottery_times"
                  type="number"
                  size="default"
                  style="width:100%"
                  placeholder="请输入次数"
                >
                  <template #suffix>
                    <span style="color: #909399; font-size: 14px;">次</span>
                  </template>
                </el-input>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="每人最多中奖次数" prop="max_win_times">
                <el-input
                  v-model.number="form.max_win_times"
                  type="number"
                  size="default"
                  style="width:100%"
                  placeholder="请输入次数"
                >
                  <template #suffix>
                    <span style="color: #909399; font-size: 14px;">次</span>
                  </template>
                </el-input>
              </el-form-item>
            </el-col>
          </el-row>
        </el-card>

        <!-- 图片设置 -->
        <el-card class="form-card" shadow="never">
          <template #header><span class="card-title">图片设置</span></template>
          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item label="轮播大图">
                <div class="upload-tip">支持 JPG/PNG/GIF/WebP，大小≤5MB，建议 1920×800</div>
                <el-upload :http-request="customUploadBanner" :show-file-list="false" class="image-upload">
                  <el-button type="primary" size="default">上传图片</el-button>
                </el-upload>
                <div v-if="form.banner_image" class="upload-preview">
                  <el-image :src="form.banner_image" fit="cover" style="width:200px; height:100px; border-radius:8px;" />
                  <el-button type="danger" link size="default" @click="form.banner_image = ''">删除</el-button>
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="封面图">
                <div class="upload-tip">建议 600×400，用于列表展示</div>
                <!-- ★★★ 上传按钮在提示下方，左对齐 ★★★ -->
                <div style="margin-top: 4px;">
                  <el-upload :http-request="customUploadCover" :show-file-list="false" class="image-upload">
                    <el-button type="primary" size="default">上传图片</el-button>
                  </el-upload>
                </div>
                <div v-if="form.cover_image" class="upload-preview">
                  <el-image :src="form.cover_image" fit="cover" style="width:200px; height:100px; border-radius:8px;" />
                  <el-button type="danger" link size="default" @click="form.cover_image = ''">删除</el-button>
                </div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-card>

        <!-- 推荐设置 -->
        <el-card class="form-card" shadow="never">
          <template #header><span class="card-title">推荐设置</span></template>
          <el-row :gutter="24">
            <el-col :span="24">
              <el-form-item label="设为推荐">
                <el-switch v-model="form.is_featured" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="24" v-if="form.is_featured">
            <el-col :span="12">
              <el-form-item label="推荐类型" prop="recommend_type">
                <el-radio-group v-model="form.recommend_type">
                  <el-radio label="grid" value="grid">网格区</el-radio>
                  <el-radio label="carousel" value="carousel">轮播区</el-radio>
                  <el-radio label="both" value="both">两者</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="推荐排序" prop="featured_order">
                <el-input-number
                  v-model="form.featured_order"
                  :min="0"
                  :controls="false"
                  size="default"
                  style="width:100%"
                />
                <span class="hint-text">数值越小越靠前</span>
              </el-form-item>
            </el-col>
          </el-row>
        </el-card>

        <!-- 活动介绍 -->
        <el-card class="form-card" shadow="never">
          <template #header><span class="card-title">活动介绍</span></template>
          <el-form-item label="活动介绍" prop="content">
            <el-input v-model="form.content" type="textarea" :rows="6" placeholder="请输入活动详细介绍" size="default" />
          </el-form-item>
        </el-card>
      </el-form>
    </div>

    <!-- 底部固定操作栏 -->
    <div class="fixed-footer">
      <el-button size="default" @click="$router.push('/activities')">取消</el-button>
      <el-button type="primary" size="default" @click="handleSave" :loading="saving">保存</el-button>
      <el-button v-if="isEdit && form.status === 'draft'" type="success" size="default" @click="handleSaveAndPublish" :loading="saving">保存并发布</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getActivityDetail, createActivity, updateActivity, publishActivity } from '@/api/activity'
import request from '@/api/request'

const route = useRoute()
const router = useRouter()
const formRef = ref(null)
const saving = ref(false)
const loading = ref(false)

const isEdit = computed(() => !!route.query.id)

const form = reactive({
  name: '',
  activity_type: '其他',
  location: '',
  start_date: '',
  end_date: '',
  registration_start: '',
  registration_end: '',
  max_participants: 0,
  charge_mode: 'free',
  fee: 0,
  points_cost: 0,
  pay_option: 'both',
  banner_image: '',
  cover_image: '',
  is_featured: false,
  recommend_type: 'grid',
  featured_order: 0,
  content: '',
  status: 'draft',
  enable_lottery: false,
  lottery_times: 1,
  max_win_times: 1
})

const rules = {
  name: [{ required: true, message: '请输入活动名称', trigger: 'blur' }],
  activity_type: [{ required: true, message: '请选择活动类型', trigger: 'change' }],
  start_date: [{ required: true, message: '请选择活动开始时间', trigger: 'change' }],
  end_date: [{ required: true, message: '请选择活动结束时间', trigger: 'change' }],
  registration_start: [{ required: true, message: '请选择报名开始时间', trigger: 'change' }],
  registration_end: [{ required: true, message: '请选择报名截止时间', trigger: 'change' }],
  charge_mode: [{ required: true, message: '请选择收费模式', trigger: 'change' }],
  fee: [
    { required: true, message: '请输入活动费用', trigger: 'blur' },
    { type: 'number', min: 0, message: '费用不能小于0', trigger: 'blur' }
  ]
}

async function loadActivity() {
  const id = route.query.id
  if (!id) return
  loading.value = true
  try {
    const res = await getActivityDetail(id)
    if (res.code === 0) {
      const data = res.data.activity
      Object.keys(form).forEach(key => {
        if (data[key] !== undefined) {
          form[key] = data[key]
        }
      })
      if (!form.status) form.status = 'draft'
    } else {
      ElMessage.error('加载活动数据失败')
    }
  } catch (e) {
    console.error('加载活动失败', e)
    ElMessage.error('加载活动数据失败')
  } finally {
    loading.value = false
  }
}

const customUploadBanner = async (options) => {
  const formData = new FormData()
  formData.append('file', options.file)
  try {
    const res = await request.post('/activity/upload-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    if (res.code === 0 && res.data?.url) {
      form.banner_image = res.data.url
      ElMessage.success('上传成功')
    } else {
      ElMessage.error(res.message || '上传失败')
    }
  } catch (e) {
    ElMessage.error('上传失败')
  } finally {
    options.onSuccess && options.onSuccess()
  }
}

const customUploadCover = async (options) => {
  const formData = new FormData()
  formData.append('file', options.file)
  try {
    const res = await request.post('/activity/upload-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    if (res.code === 0 && res.data?.url) {
      form.cover_image = res.data.url
      ElMessage.success('上传成功')
    } else {
      ElMessage.error(res.message || '上传失败')
    }
  } catch (e) {
    ElMessage.error('上传失败')
  } finally {
    options.onSuccess && options.onSuccess()
  }
}

function onChargeModeChange() {
  if (form.charge_mode === 'free') {
    form.fee = 0
  }
}

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const url = isEdit.value ? `/activity/activities/${route.query.id}` : '/activity/activities'
    const method = isEdit.value ? 'put' : 'post'
    const res = await request[method](url, form)
    if (res.code === 0) {
      ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
      const id = res.data?.id || route.query.id
      router.push(`/activities/detail?id=${id}`)
    } else {
      ElMessage.error(res.message || '保存失败')
    }
  } catch (e) {
    console.error('保存失败', e)
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleSaveAndPublish() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    let activityId = route.query.id
    if (!isEdit.value) {
      const res = await createActivity(form)
      if (res.code === 0) {
        activityId = res.data.id
      } else {
        ElMessage.error(res.message || '创建失败')
        return
      }
    } else {
      await updateActivity(activityId, form)
    }
    await publishActivity(activityId)
    ElMessage.success('保存并发布成功')
    router.push(`/activities/detail?id=${activityId}`)
  } catch (e) {
    console.error('保存并发布失败', e)
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  if (isEdit.value) {
    loadActivity()
  }
})
</script>

<style scoped>
.activity-new {
  padding: 20px 20px 80px 20px; /* 底部留出固定栏空间 */
  background: var(--app-bg);
  min-height: 100vh;
  position: relative;
}

.breadcrumb {
  margin-bottom: 16px;
  background: transparent;
  padding: 0;
}

.form-container {
  max-width: 1000px;
  margin: 0 auto;
}

.form-card {
  margin-bottom: 20px;
  border-radius: 12px;
}
.form-card :deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-light);
}
.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.activity-form {
  padding: 4px 0;
}
.activity-form :deep(.el-form-item) {
  margin-bottom: 18px;
}
.activity-form :deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--text-secondary);
}

.hint-text {
  margin-left: 8px;
  font-size: 12px;
  color: var(--text-placeholder);
}

.upload-tip {
  font-size: 12px;
  color: var(--text-placeholder);
  margin-bottom: 4px;
}
.image-upload {
  display: inline-block;
}
.upload-preview {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 固定底部操作栏 */
.fixed-footer {
  position: fixed;
  bottom: 0;
  left: 140px; /* 左侧导航宽度 */
  right: 0;
  height: 64px;
  background: var(--surface);
  border-top: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 24px;
  gap: 12px;
  z-index: 100;
  box-shadow: 0 -2px 8px rgba(0,0,0,0.04);
}

/* 统一控件尺寸 */
:deep(.el-input__wrapper) {
  border-radius: 8px;
  height: 40px;
}
:deep(.el-select .el-input__wrapper) {
  height: 40px;
}
:deep(.el-input-number .el-input__wrapper) {
  height: 40px;
}
:deep(.el-button) {
  border-radius: 20px;
  height: 40px;
  padding: 0 20px;
}
:deep(.el-textarea .el-textarea__inner) {
  border-radius: 8px;
  border: 1px solid var(--border-color);
}
:deep(.el-textarea .el-textarea__inner:focus) {
  border-color: var(--brand-500);
}

/* 隐藏 input number 的增减按钮 */
:deep(.el-input-number .el-input-number__decrease),
:deep(.el-input-number .el-input-number__increase) {
  display: none;
}
:deep(.el-input-number .el-input__wrapper) {
  padding-left: 12px;
  padding-right: 12px;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .fixed-footer {
    left: 0; /* 移动端左导航可能收起，这里根据实际调整 */
  }
}
</style>