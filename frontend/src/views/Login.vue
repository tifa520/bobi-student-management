<template>
  <div class="login-container" :style="backgroundStyle">
    <div class="login-card-wrapper">
      <el-card class="login-card">
        <!-- Logo -->
        <div class="login-logo">
          <span class="logo-icon">🎨</span>
          <span class="logo-text">Bobi艺术</span>
        </div>
        <p class="login-subtitle">学员管理系统</p>

        <!-- 登录表单 -->
        <el-form :model="form" :rules="rules" ref="formRef">
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              placeholder="用户名"
              prefix-icon="User"
              size="large"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="密码"
              prefix-icon="Lock"
              show-password
              size="large"
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              @click="handleLogin"
              :loading="loading"
              style="width:100%"
              size="large"
            >
              登 录
            </el-button>
          </el-form-item>
        </el-form>

        <!-- ★ 创建管理员入口（仅当无管理员时显示） ★ -->
        <div v-if="showCreateAdmin" class="create-admin-section">
          <el-divider>
            <span style="color: #909399; font-size: 13px;">首次使用</span>
          </el-divider>
          <el-button
            type="warning"
            plain
            @click="openCreateAdminDialog"
            style="width:100%"
            size="default"
          >
            <el-icon><UserFilled /></el-icon> 创建管理员账号
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- ★ 创建管理员弹窗 ★ -->
    <el-dialog
      v-model="createAdminDialogVisible"
      title="创建管理员账号"
      width="480px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      class="create-admin-dialog"
    >
      <el-form
        :model="adminForm"
        :rules="adminRules"
        ref="adminFormRef"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="adminForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="adminForm.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="adminForm.password"
            type="password"
            placeholder="请输入密码（至少6位）"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="adminForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="adminForm.email" placeholder="选填" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="adminForm.phone" placeholder="选填" />
        </el-form-item>
      </el-form>

      <div class="dialog-tip">
        <el-alert
          title="提示：创建后请妥善保管账号密码，管理员拥有系统所有权限"
          type="info"
          :closable="false"
          show-icon
        />
      </div>

      <template #footer>
        <el-button @click="createAdminDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreateAdmin" :loading="creating">
          确认创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UserFilled } from '@element-plus/icons-vue'
import { login as loginApi, hasAdmin, createAdmin } from '@/api/auth'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

// ========== 登录表单 ==========
const form = reactive({ username: '', password: '' })
const loading = ref(false)
const formRef = ref()

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// ========== 背景图 ==========
const bgImageUrl = ref('')

const backgroundStyle = computed(() => {
  if (bgImageUrl.value) {
    return {
      backgroundImage: `url(${bgImageUrl.value})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat'
    }
  }
  return { backgroundColor: '#f0f2f5' }
})

// ========== 登录方法 ==========
async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await loginApi(form)
    if (res.code === 0) {
      userStore.setUser(res.data.user)
      localStorage.setItem('access_token', res.data.access_token)
      localStorage.setItem('refresh_token', res.data.refresh_token)
      localStorage.setItem('user', JSON.stringify(res.data.user))
      ElMessage.success('登录成功')
      await router.push('/dashboard')
    } else {
      ElMessage.error(res.message || '登录失败')
    }
  } catch (error) {
    ElMessage.error('登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}

// ========== ★ 创建管理员账号 ==========
const showCreateAdmin = ref(false)
const createAdminDialogVisible = ref(false)
const creating = ref(false)
const adminFormRef = ref()

const adminForm = reactive({
  username: '',
  name: '',
  password: '',
  confirmPassword: '',
  email: '',
  phone: ''
})

// 自定义验证：确认密码
const validateConfirmPassword = (rule, value, callback) => {
  if (value !== adminForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const adminRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

async function checkHasAdmin() {
  try {
    const res = await hasAdmin()
    if (res.code === 0) {
      showCreateAdmin.value = !res.data.has_admin
    }
  } catch (error) {
    console.error('检查管理员状态失败', error)
    showCreateAdmin.value = true
  }
}

function openCreateAdminDialog() {
  adminForm.username = ''
  adminForm.name = ''
  adminForm.password = ''
  adminForm.confirmPassword = ''
  adminForm.email = ''
  adminForm.phone = ''
  createAdminDialogVisible.value = true
}

async function submitCreateAdmin() {
  const valid = await adminFormRef.value?.validate().catch(() => false)
  if (!valid) return

  creating.value = true
  try {
    const res = await createAdmin({
      username: adminForm.username,
      password: adminForm.password,
      name: adminForm.name,
      email: adminForm.email || undefined,
      phone: adminForm.phone || undefined
    })

    if (res.code === 0) {
      ElMessage.success('管理员账号创建成功，请登录')
      createAdminDialogVisible.value = false
      showCreateAdmin.value = false
      form.username = adminForm.username
      form.password = ''
    } else {
      ElMessage.error(res.message || '创建失败')
    }
  } catch (error) {
    const msg = error.response?.data?.detail || '创建失败，请重试'
    ElMessage.error(msg)
  } finally {
    creating.value = false
  }
}

// ========== 加载背景图 ==========
async function loadBgImage() {
  try {
    const res = await request.get('/upload/login-bg')
    if (res.code === 0 && res.data?.url) {
      bgImageUrl.value = res.data.url
    }
  } catch (error) {
    console.error('获取背景失败', error)
  }
}

// ========== 生命周期 ==========
onMounted(() => {
  checkHasAdmin()
  loadBgImage()
})
</script>

<style scoped>
.login-container {
  position: relative;
  height: 100vh;
  width: 100%;
  overflow: hidden;
}

.login-card-wrapper {
  position: absolute;
  right: 10%;
  top: 50%;
  transform: translateY(-50%);
  width: 420px;
}

.login-card {
  padding: 40px 36px 50px 36px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.login-logo {
  text-align: center;
  margin-bottom: 8px;
}
.logo-icon {
  font-size: 32px;
}
.logo-text {
  font-size: 26px;
  font-weight: 700;
  color: var(--brand-500);
  letter-spacing: 0.5px;
  margin-left: 6px;
}

.login-subtitle {
  text-align: center;
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 32px;
}

.login-card :deep(.el-form-item) {
  margin-bottom: 22px;
}
.login-card :deep(.el-input__wrapper) {
  height: 44px;
  background: rgba(255, 255, 255, 0.9);
}
.login-card :deep(.el-button) {
  height: 44px;
  font-size: 16px;
}

.create-admin-section {
  margin-top: 8px;
}
.create-admin-section .el-divider {
  margin: 16px 0 12px 0;
}

.create-admin-dialog :deep(.el-dialog__body) {
  padding: 20px 24px;
}
.create-admin-dialog :deep(.el-form-item) {
  margin-bottom: 16px;
}
.create-admin-dialog :deep(.el-input__wrapper) {
  height: 36px;
}

.dialog-tip {
  margin-top: 16px;
}
</style>