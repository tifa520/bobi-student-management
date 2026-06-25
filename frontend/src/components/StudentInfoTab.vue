<template>
  <div class="info-content">
    <!-- 头像和背景图设置区域 -->
    <div class="info-panel-modern">
      <!-- 左侧：头像设置 -->
      <div class="info-left">
        <div class="section-title">头像</div>
        <div class="avatar-section">
          <AppImage :src="avatarUrl" :size="100" class="student-avatar" />
        </div>
        <div class="avatar-actions">
          <el-upload
            class="avatar-uploader"
            :action="avatarUploadUrl"
            :headers="uploadHeaders"
            :show-file-list="false"
            :before-upload="beforeAvatarUpload"
            :on-success="handleAvatarSuccess"
            :on-error="handleAvatarError"
          >
            <el-button type="primary" size="small">更换头像</el-button>
          </el-upload>
          <el-button v-if="hasAvatar" type="danger" size="small" link @click="removeAvatar">删除头像</el-button>
        </div>
        <div class="upload-tip">建议尺寸 200x200，不超过 2MB</div>
      </div>

      <!-- 右侧：卡片背景图设置 -->
      <div class="info-right">
        <div class="section-title">卡片背景图</div>
        <div v-if="cardBackgroundUrl" class="bg-preview-wrapper">
          <div class="bg-preview-label">当前背景图：</div>
          <div class="bg-preview">
            <el-image :src="cardBackgroundUrl" fit="cover" class="bg-preview-img" @error="handleBgImageError" />
          </div>
          <div class="bg-actions">
            <el-upload
              class="bg-uploader"
              :action="cardBgUploadUrl"
              :headers="uploadHeaders"
              :show-file-list="false"
              :before-upload="beforeCardBgUpload"
              :on-success="handleCardBgSuccess"
              :on-error="handleCardBgError"
            >
              <el-button type="primary" size="small">更换背景</el-button>
            </el-upload>
            <el-button type="danger" size="small" link @click="removeCardBackground">删除背景</el-button>
          </div>
        </div>
        <div v-else class="bg-empty">
          <el-upload
            class="bg-uploader"
            :action="cardBgUploadUrl"
            :headers="uploadHeaders"
            :show-file-list="false"
            :before-upload="beforeCardBgUpload"
            :on-success="handleCardBgSuccess"
            :on-error="handleCardBgError"
          >
            <el-button type="primary">上传背景图</el-button>
          </el-upload>
          <div class="upload-tip">建议尺寸 800x400，不超过 500KB</div>
        </div>
      </div>
    </div>

    <!-- 基本信息表单 -->
    <div class="contacts-section-modern">
      <h4>基本信息</h4>
      <el-form :model="formData" label-width="100px" class="info-form-modern">
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="姓名">
              <el-input v-model="formData.name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手机">
              <el-input v-model="formData.phone" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="性别">
              <el-radio-group v-model="formData.gender">
                <el-radio label="男" value="男">男</el-radio>
                <el-radio label="女" value="女">女</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="出生日期">
              <el-date-picker v-model="formData.birthday" type="date" value-format="YYYY-MM-DD" style="width:100%" placeholder="选择日期" />
            </el-form-item>
          </el-col>
          <!-- ★ 新增字段 -->
          <el-col :span="12">
            <el-form-item label="民族">
              <el-input v-model="formData.nation" placeholder="请输入民族" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="身份证号码">
              <el-input v-model="formData.id_card" placeholder="请输入身份证号码" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="就读学校">
              <el-input v-model="formData.school" placeholder="请输入就读学校" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="介绍人">
              <el-input v-model="formData.introducer" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注">
              <el-input v-model="formData.note" type="textarea" :rows="3" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </div>

    <!-- 联系人信息 -->
    <div class="contacts-section-modern">
      <h4>联系人</h4>
      <div v-for="(contact, index) in contacts" :key="index" class="contact-item-modern">
        <el-row :gutter="16" align="middle">
          <el-col :span="6">
            <el-input v-model="contact.name" placeholder="姓名" />
          </el-col>
          <el-col :span="6">
            <el-input v-model="contact.relation" placeholder="关系" />
          </el-col>
          <el-col :span="8">
            <el-input v-model="contact.phone" placeholder="联系方式" />
          </el-col>
          <el-col :span="4">
            <el-button type="danger" link @click="removeContact(index)">删除</el-button>
          </el-col>
        </el-row>
      </div>
      <el-button type="primary" link @click="addContact">
        <el-icon><Plus /></el-icon> 添加联系人
      </el-button>
    </div>

    <div class="form-actions">
      <el-button type="primary" @click="handleSave" :loading="saving">保存修改</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { updateStudent, getStudentDetail, uploadAvatar, deleteAvatar, uploadCardBackground, deleteCardBackground } from '@/api/student'
import { DEFAULT_AVATAR_SVG } from '@/utils/constants'
import request from '@/api/request'

// AppImage 已全局注册

const props = defineProps({
  student: { type: Object, required: true },
  studentId: { type: Number, required: true }
})
const emit = defineEmits(['update:success', 'update:avatar', 'update:card_background'])

// 表单数据
const formData = reactive({
  name: '',
  phone: '',
  gender: '',
  birthday: '',
  introducer: '',
  note: '',
  nation: '',      // 新增
  id_card: '',     // 新增
  school: ''       // 新增
})
const contacts = ref([])
const avatarUrl = ref(DEFAULT_AVATAR_SVG)
const cardBackgroundUrl = ref('')
const saving = ref(false)
const initialized = ref(false)

const hasAvatar = computed(() => avatarUrl.value !== DEFAULT_AVATAR_SVG && avatarUrl.value !== '')
const avatarUploadUrl = computed(() => `/api/student/student/${props.studentId}/avatar`)
const cardBgUploadUrl = computed(() => `/api/student/student/${props.studentId}/card-background`)
const uploadHeaders = computed(() => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }))

function initFormData(force = false) {
  if (!force && initialized.value) {
    formData.name = props.student.name || ''
    formData.phone = props.student.phone || ''
    formData.gender = props.student.gender || ''
    formData.birthday = props.student.birthday || ''
    formData.introducer = props.student.introducer || ''
    formData.note = props.student.note || ''
    contacts.value = props.student.contacts?.map(c => ({ ...c })) || []
    return
  }

  if (props.student) {
    formData.name = props.student.name || ''
    formData.phone = props.student.phone || ''
    formData.gender = props.student.gender || ''
    formData.birthday = props.student.birthday || ''
    formData.introducer = props.student.introducer || ''
    formData.note = props.student.note || ''
    contacts.value = props.student.contacts?.map(c => ({ ...c })) || []
    if (!avatarUrl.value || avatarUrl.value === DEFAULT_AVATAR_SVG) {
      avatarUrl.value = props.student.avatar || DEFAULT_AVATAR_SVG
    }
    if (!cardBackgroundUrl.value) {
      cardBackgroundUrl.value = props.student.card_background || ''
    }
    initialized.value = true
  }
}

function refreshFormData() {
  initialized.value = false
  initFormData(true)
}

async function refreshStudentInfo() {
  try {
    const res = await getStudentDetail(props.studentId)
    if (res.code === 0 && res.data) {
      formData.name = res.data.name || ''
      formData.phone = res.data.phone || ''
      formData.gender = res.data.gender || ''
      formData.birthday = res.data.birthday || ''
      formData.introducer = res.data.introducer || ''
      formData.note = res.data.note || ''
      contacts.value = res.data.contacts?.map(c => ({ ...c })) || []
      if (!avatarUrl.value || avatarUrl.value === DEFAULT_AVATAR_SVG) {
        avatarUrl.value = res.data.avatar || DEFAULT_AVATAR_SVG
      }
      if (!cardBackgroundUrl.value) {
        cardBackgroundUrl.value = res.data.card_background || ''
      }
      emit('update:success')
    }
  } catch (error) {
    console.error('刷新学员信息失败', error)
  }
}

watch(() => props.student, () => {
  initFormData()
}, { deep: true, immediate: true })

defineExpose({ refreshFormData, refreshStudentInfo })

function addContact() {
  contacts.value.push({ name: '', relation: '', phone: '' })
}
function removeContact(index) {
  contacts.value.splice(index, 1)
}

function beforeAvatarUpload(file) {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isImage) { ElMessage.error('只能上传图片文件!'); return false }
  if (!isLt2M) { ElMessage.error('图片大小不能超过 2MB!'); return false }
  return true
}

function handleAvatarSuccess(response) {
  if (response.code === 0 && response.data?.avatar_url) {
    const newAvatar = response.data.avatar_url
    avatarUrl.value = newAvatar
    emit('update:avatar', newAvatar)
    ElMessage.success('头像更新成功')
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}

function handleAvatarError() {
  ElMessage.error('上传失败')
}

async function removeAvatar() {
  try {
    await ElMessageBox.confirm('确认删除头像？', '提示')
    const res = await deleteAvatar(props.studentId)
    if (res.code === 0) {
      avatarUrl.value = DEFAULT_AVATAR_SVG
      emit('update:avatar', '')
      ElMessage.success('头像已删除')
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

function beforeCardBgUpload(file) {
  const isImage = file.type.startsWith('image/')
  const isLt500K = file.size / 1024 < 500
  if (!isImage) { ElMessage.error('只能上传图片文件'); return false }
  if (!isLt500K) { ElMessage.error('图片大小不能超过 500KB'); return false }
  return true
}

function handleCardBgSuccess(response) {
  if (response.code === 0 && response.data?.card_background_url) {
    const newBg = response.data.card_background_url
    cardBackgroundUrl.value = newBg
    emit('update:card_background', newBg)
    ElMessage.success('背景图更新成功')
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}

function handleCardBgError() {
  ElMessage.error('上传失败')
}

function handleBgImageError() {
  console.warn('背景图加载失败')
}

async function removeCardBackground() {
  try {
    await ElMessageBox.confirm('确认删除卡片背景图？', '提示', { type: 'warning' })
    const res = await deleteCardBackground(props.studentId)
    if (res.code === 0) {
      cardBackgroundUrl.value = ''
      emit('update:card_background', '')
      ElMessage.success('背景图已删除')
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

async function handleSave() {
  saving.value = true
  try {
    const res = await updateStudent(props.studentId, {
      name: formData.name,
      phone: formData.phone,
      gender: formData.gender,
      birth_date: formData.birthday,
      introducer: formData.introducer,
      note: formData.note,
      contacts: contacts.value,
      nation: formData.nation,        // 新增
      id_card: formData.id_card,      // 新增
      school: formData.school         // 新增
    })
    if (res.code === 0) {
      ElMessage.success('更新成功')
      await refreshStudentInfo()
      emit('update:success')
    } else {
      ElMessage.error(res.message || '更新失败')
    }
  } catch (error) {
    ElMessage.error('更新失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.info-content {
  width: 100%;
}

.info-panel-modern {
  display: flex;
  gap: 40px;
  margin-bottom: 32px;
  padding: 24px;
  background: #fafafa;
  border-radius: 12px;
}

.info-left {
  flex: 1;
  text-align: center;
}

.info-right {
  flex: 1;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #1e293b;
}

.student-avatar {
  width: 100px;
  height: 100px;
  margin-bottom: 12px;
  border: 2px solid #e8f5e9;
  border-radius: 50%;
}

.avatar-actions,
.bg-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 8px;
}

.bg-preview-wrapper {
  text-align: center;
}

.bg-preview-label {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
  text-align: left;
}

.bg-preview {
  margin-bottom: 12px;
}

.bg-preview-img {
  width: 100%;
  max-height: 150px;
  border-radius: 12px;
  object-fit: cover;
  border: 1px solid #e2e8f0;
}

.bg-empty {
  text-align: center;
  padding: 40px 20px;
  background: #f1f5f9;
  border-radius: 12px;
}

.upload-tip {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 8px;
}

.contacts-section-modern {
  background: #fafafa;
  border-radius: 12px;
  padding: 20px 24px;
  margin-top: 20px;
}

.contacts-section-modern h4 {
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
}

.contact-item-modern {
  margin-bottom: 16px;
}

.form-actions {
  margin-top: 24px;
  text-align: right;
}
</style>