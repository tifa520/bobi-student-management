<!-- frontend/src/views/Profile.vue -->
<template>
  <div class="profile-page">
    <div class="profile-container">
      <!-- 左侧：头像 -->
      <div class="profile-left">
        <div class="avatar-section">
          <AppImage :src="user.avatar" :size="120" shape="circle" class="profile-avatar" />
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
          </div>
          <div class="avatar-tip">支持 JPG/PNG，不超过 2MB</div>
        </div>
        <div class="user-role-badge">
          <el-tag :type="user.role === '超级管理员' ? 'danger' : 'primary'" size="large">
            {{ user.role || '管理员' }}
          </el-tag>
        </div>
      </div>

      <!-- 右侧：信息表单 -->
      <div class="profile-right">
        <div class="profile-header">
          <span class="profile-title">个人中心</span>
          <span class="profile-subtitle">管理您的个人信息</span>
        </div>

        <el-form
          :model="form"
          :rules="rules"
          ref="formRef"
          label-width="100px"
          class="profile-form"
        >
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" disabled />
          </el-form-item>
          <el-form-item label="姓名" prop="name">
            <el-input v-model="form.name" placeholder="请输入姓名" />
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="form.email" placeholder="请输入邮箱" />
          </el-form-item>
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="form.phone" placeholder="请输入手机号" />
          </el-form-item>
          <el-form-item label="角色" prop="role">
            <el-input :value="user.role || '管理员'" disabled />
          </el-form-item>

          <el-divider>修改密码</el-divider>

          <el-form-item label="当前密码" prop="old_password">
            <el-input
              v-model="passwordForm.old_password"
              type="password"
              placeholder="请输入当前密码"
              show-password
            />
          </el-form-item>
          <el-form-item label="新密码" prop="new_password">
            <el-input
              v-model="passwordForm.new_password"
              type="password"
              placeholder="请输入新密码（至少6位）"
              show-password
            />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirm_password">
            <el-input
              v-model="passwordForm.confirm_password"
              type="password"
              placeholder="请再次输入新密码"
              show-password
            />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="saveProfile" :loading="saving">
              保存信息
            </el-button>
            <el-button type="success" @click="submitChangePassword" :loading="changingPassword">
              修改密码
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { changePassword } from '@/api/auth'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'
import { DEFAULT_AVATAR_SVG } from '@/utils/constants'

const userStore = useUserStore()
const { user } = storeToRefs(userStore)

const form = reactive({
  username: '',
  name: '',
  email: '',
  phone: '',
  role: ''
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const saving = ref(false)
const changingPassword = ref(false)
const formRef = ref()

// 表单校验规则
const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  email: [{ type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }],
  phone: [{ pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }]
}

// 头像上传
const avatarUploadUrl = '/api/auth/avatar'
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('access_token')}`
}))

function beforeAvatarUpload(file) {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isImage) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB')
    return false
  }
  return true
}

function handleAvatarSuccess(res) {
  if (res.code === 0 && res.data?.avatar_url) {
    userStore.updateAvatar(res.data.avatar_url)
    ElMessage.success('头像更新成功')
  } else {
    ElMessage.error(res.message || '上传失败')
  }
}

function handleAvatarError() {
  ElMessage.error('上传失败')
}

// 加载用户信息
async function loadUserInfo() {
  try {
    await userStore.fetchCurrentUser()
    form.username = user.value.username || ''
    form.name = user.value.name || ''
    form.email = user.value.email || ''
    form.phone = user.value.phone || ''
    form.role = user.value.role || ''
    if (!user.value.avatar) {
      user.value.avatar = DEFAULT_AVATAR_SVG
    }
  } catch (error) {
    console.error('加载用户信息失败', error)
    ElMessage.error('加载用户信息失败')
  }
}

// 保存个人信息
async function saveProfile() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    await request.put('/auth/me', {
      name: form.name,
      phone: form.phone
    })
    await userStore.fetchCurrentUser()
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

// 修改密码（改名避免与导入冲突）
async function submitChangePassword() {
  if (!passwordForm.old_password) {
    ElMessage.warning('请输入当前密码')
    return
  }
  if (!passwordForm.new_password || passwordForm.new_password.length < 6) {
    ElMessage.warning('新密码至少 6 位')
    return
  }
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }

  changingPassword.value = true
  try {
    await changePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    })
    ElMessage.success('密码修改成功，请重新登录')
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    setTimeout(() => {
      localStorage.clear()
      userStore.setUser({})
      window.location.href = '/login'
    }, 1500)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '修改密码失败')
  } finally {
    changingPassword.value = false
  }
}

onMounted(() => {
  loadUserInfo()
})
</script>

<style scoped>
.profile-page {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: var(--app-bg);
}
.profile-container {
  display: flex;
  gap: 40px;
  width: 100%;
  max-width: 900px;
  background: var(--surface);
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}
.profile-left {
  flex: 0 0 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.profile-avatar {
  border: 4px solid var(--brand-50);
  border-radius: 50%;
}
.avatar-actions {
  display: flex;
  gap: 8px;
}
.avatar-tip {
  font-size: 12px;
  color: var(--text-placeholder);
}
.user-role-badge {
  margin-top: 8px;
}
.profile-right {
  flex: 1;
  min-width: 0;
}
.profile-header {
  margin-bottom: 24px;
}
.profile-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}
.profile-subtitle {
  font-size: 14px;
  color: var(--text-placeholder);
  margin-left: 12px;
}
.profile-form {
  max-width: 500px;
}
.profile-form :deep(.el-form-item) {
  margin-bottom: 18px;
}
.profile-form :deep(.el-input__wrapper) {
  height: 36px;
}
</style>