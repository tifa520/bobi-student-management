<template>
  <div class="login-container" :style="backgroundStyle">
    <div class="login-bg-decoration">
      <div class="blob blob-1"></div>
      <div class="blob blob-2"></div>
      <div class="blob blob-3"></div>
      <div class="pattern-overlay"></div>
    </div>

    <div class="login-layout">
      <div class="login-brand-side">
        <div class="brand-content">
          <div class="brand-logo">
            <span class="logo-mark">B</span>
          </div>
          <h1 class="brand-title">Bobi 艺术</h1>
          <p class="brand-subtitle">学员管理系统</p>
          <div class="brand-divider">
            <span class="divider-line"></span>
            <span class="divider-icon">🎨</span>
            <span class="divider-line"></span>
          </div>
          <div class="brand-features">
            <div class="feature-item">
              <span class="feature-icon">📚</span>
              <span>全生命周期学员管理</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">💰</span>
              <span>精细化财务课消核算</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">🎯</span>
              <span>智能排课与考勤系统</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">📊</span>
              <span>多维度数据可视化</span>
            </div>
          </div>
        </div>
        <div class="brand-footer">
          <span>© 2026 Bobi Art Studio</span>
        </div>
      </div>

      <div class="login-form-side">
        <div class="form-card">
          <div class="form-header">
            <div class="form-avatar">
              <span class="avatar-icon">👋</span>
            </div>
            <h2 class="form-title">欢迎回来</h2>
            <p class="form-desc">请登录您的账号以继续</p>
          </div>

          <el-form :model="form" :rules="rules" ref="formRef" class="login-form">
            <el-form-item prop="username">
              <el-input
                v-model="form.username"
                placeholder="用户名"
                size="large"
                class="bobi-input"
              >
                <template #prefix>
                  <el-icon class="input-icon"><User /></el-icon>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="密码"
                show-password
                size="large"
                class="bobi-input"
                @keyup.enter="handleLogin"
              >
                <template #prefix>
                  <el-icon class="input-icon"><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="handleLogin"
                :loading="loading"
                size="large"
                class="login-btn"
              >
                <span v-if="!loading">登 录</span>
                <span v-else>登录中...</span>
              </el-button>
            </el-form-item>
          </el-form>

          <div v-if="showCreateAdmin" class="create-admin-section">
            <div class="divider-with-text">
              <span class="divider-text">首次使用</span>
            </div>
            <el-button
              @click="openCreateAdminDialog"
              size="large"
              class="create-admin-btn"
            >
              <el-icon><UserFilled /></el-icon>
              创建管理员账号
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="createAdminDialogVisible"
      title="创建管理员账号"
      width="520px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      class="create-admin-dialog"
    >
      <el-form
        :model="adminForm"
        :rules="adminRules"
        ref="adminFormRef"
        label-width="90px"
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

      <el-alert
        title="创建后请妥善保管账号密码，管理员拥有系统所有权限"
        type="info"
        :closable="false"
        show-icon
        style="margin-top: 8px;"
      />

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
import { User, Lock, UserFilled } from '@element-plus/icons-vue'
import { login as loginApi, hasAdmin, createAdmin } from '@/api/auth'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const form = reactive({ username: '', password: '' })
const loading = ref(false)
const formRef = ref()

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const bgImageUrl = ref('')

const backgroundStyle = computed(() => {
  if (bgImageUrl.value) {
    return {
      backgroundImage: `url(${bgImageUrl.value})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }
  return {}
})

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
  background:
    radial-gradient(ellipse at 20% 20%, rgba(30, 168, 82, 0.12), transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(212, 148, 26, 0.1), transparent 50%),
    linear-gradient(135deg, #f0f7ee 0%, #e8f1e4 50%, #f5f0e6 100%);
}

.login-bg-decoration {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
  animation: floatBlob 20s ease-in-out infinite;
}

.blob-1 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(30, 168, 82, 0.3), transparent 70%);
  top: -100px;
  left: -100px;
  animation-delay: 0s;
}

.blob-2 {
  width: 350px;
  height: 350px;
  background: radial-gradient(circle, rgba(212, 148, 26, 0.25), transparent 70%);
  bottom: -50px;
  right: -50px;
  animation-delay: -7s;
}

.blob-3 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(61, 120, 184, 0.2), transparent 70%);
  top: 50%;
  left: 60%;
  animation-delay: -14s;
}

@keyframes floatBlob {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(30px, -20px) scale(1.05); }
  50% { transform: translate(-20px, 30px) scale(0.95); }
  75% { transform: translate(-30px, -10px) scale(1.02); }
}

.pattern-overlay {
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(circle at 1px 1px, rgba(15, 38, 25, 0.08) 1px, transparent 0);
  background-size: 32px 32px;
  mask-image:
    radial-gradient(ellipse at center, rgba(0, 0, 0, 0.5), transparent 75%);
}

.login-layout {
  position: relative;
  z-index: 1;
  display: flex;
  height: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 60px;
  gap: 60px;
  align-items: center;
  justify-content: center;
}

.login-brand-side {
  flex: 1;
  max-width: 520px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100%;
  padding: 40px 0;
}

.brand-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.brand-logo {
  margin-bottom: 32px;
}

.logo-mark {
  width: 72px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  font-weight: 900;
  color: #fff;
  background: linear-gradient(135deg, var(--brand-500), var(--brand-700));
  border-radius: 20px;
  box-shadow: 0 16px 40px rgba(30, 168, 82, 0.35);
  font-family: var(--font-display);
  letter-spacing: 2px;
}

.brand-title {
  font-size: 52px;
  font-weight: 700;
  margin: 0 0 8px 0;
  font-family: var(--font-display);
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, var(--gray-900) 0%, var(--brand-700) 50%, var(--gold-600) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-subtitle {
  font-size: 20px;
  color: var(--text-secondary);
  margin: 0 0 36px 0;
  font-weight: 500;
  letter-spacing: 0.1em;
}

.brand-divider {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 36px;
}

.divider-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border-color), transparent);
}

.divider-icon {
  font-size: 20px;
  animation: float 3s ease-in-out infinite;
}

.brand-features {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  backdrop-filter: blur(10px);
  font-size: 14px;
  color: var(--text-regular);
  font-weight: 500;
  transition: all 0.3s var(--ease-soft);
}

.feature-item:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.85);
  box-shadow: 0 8px 24px rgba(15, 38, 25, 0.08);
  border-color: rgba(30, 168, 82, 0.2);
}

.feature-icon {
  font-size: 22px;
  flex-shrink: 0;
}

.brand-footer {
  color: var(--text-placeholder);
  font-size: 13px;
  text-align: center;
}

.login-form-side {
  flex-shrink: 0;
  width: 440px;
}

.form-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 28px;
  padding: 48px 44px;
  box-shadow:
    0 8px 32px rgba(15, 38, 25, 0.08),
    0 32px 64px rgba(15, 38, 25, 0.06);
  position: relative;
  overflow: hidden;
}

.form-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg,
    var(--brand-400),
    var(--brand-600),
    var(--gold-500),
    var(--brand-500));
}

.form-header {
  text-align: center;
  margin-bottom: 36px;
}

.form-avatar {
  width: 64px;
  height: 64px;
  margin: 0 auto 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  background: linear-gradient(135deg, var(--brand-100), var(--brand-200));
  border-radius: 20px;
  animation: float 4s ease-in-out infinite;
}

.form-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 8px 0;
  font-family: var(--font-display);
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.form-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.login-form {
  margin-bottom: 8px;
}

.bobi-input {
  --el-input-height: 48px;
}

.bobi-input :deep(.el-input__wrapper) {
  padding: 0 18px;
  box-shadow: 0 0 0 1px var(--border-light) inset;
  background: rgba(255, 255, 255, 0.9);
  transition: all 0.25s var(--ease-soft);
}

.bobi-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(30, 168, 82, 0.4) inset;
}

.bobi-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--brand-500) inset, 0 0 0 4px rgba(30, 168, 82, 0.1);
}

.input-icon {
  color: var(--text-placeholder);
  font-size: 18px;
}

.login-btn {
  width: 100%;
  height: 48px !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  letter-spacing: 0.05em !important;
}

.create-admin-section {
  margin-top: 16px;
}

.divider-with-text {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 20px 0 16px;
}

.divider-with-text::before,
.divider-with-text::after {
  content: "";
  flex: 1;
  height: 1px;
  background: var(--border-light);
}

.divider-text {
  color: var(--text-placeholder);
  font-size: 13px;
}

.create-admin-btn {
  width: 100%;
  height: 44px !important;
  background: linear-gradient(135deg, var(--gold-400), var(--gold-600)) !important;
  border-color: transparent !important;
  color: #fff !important;
  font-weight: 600 !important;
  box-shadow: 0 6px 20px rgba(212, 148, 26, 0.25) !important;
}

.create-admin-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 28px rgba(212, 148, 26, 0.35) !important;
}

.create-admin-dialog :deep(.el-dialog__body) {
  padding: 24px 28px;
}

.create-admin-dialog :deep(.el-form-item) {
  margin-bottom: 18px;
}

@media (max-width: 1100px) {
  .login-brand-side {
    display: none;
  }

  .login-layout {
    justify-content: center;
    padding: 40px 20px;
  }
}

@media (max-width: 520px) {
  .login-form-side {
    width: 100%;
  }

  .form-card {
    padding: 36px 28px;
    border-radius: 24px;
  }

  .brand-title {
    font-size: 40px;
  }
}
</style>
