<template>
  <el-dialog v-model="dialogVisible" title="个人中心" width="550px" @close="handleClose">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="基本信息" name="info">
        <el-form :model="infoForm" label-width="80px">
          <el-form-item label="用户名">
            <el-input v-model="infoForm.name" placeholder="请输入用户名" />
          </el-form-item>
          <el-form-item label="手机号">
            <el-input v-model="infoForm.phone" placeholder="请输入手机号" />
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="头像" name="avatar">
        <div class="avatar-section">
          <AppImage :src="avatarUrl" :size="100" class="avatar-preview" />
          <el-button type="primary" link @click="triggerUpload">更换头像</el-button>
          <input ref="avatarInput" type="file" accept="image/*" style="display: none" @change="handleAvatarChange" />
        </div>
      </el-tab-pane>

      <el-tab-pane label="修改密码" name="password">
        <el-form :model="pwdForm" label-width="100px">
          <el-form-item label="原密码">
            <el-input v-model="pwdForm.old_password" type="password" show-password placeholder="请输入原密码" />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="请输入新密码" />
          </el-form-item>
          <el-form-item label="确认新密码">
            <el-input v-model="pwdForm.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>

    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="saveCurrentTab" :loading="saving">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const props = defineProps({
  visible: Boolean,
  user: { type: Object, default: () => ({ name: '', phone: '', avatar: '' }) }
})
const emit = defineEmits(['update:visible', 'update-user'])

const dialogVisible = ref(false)
const activeTab = ref('info')
const saving = ref(false)
const avatarInput = ref(null)
const infoForm = reactive({ name: '', phone: '' })
const avatarUrl = ref('')

watch(() => props.visible, (val) => {
  dialogVisible.value = val
  if (val) {
    infoForm.name = props.user.name || ''
    infoForm.phone = props.user.phone || ''
    avatarUrl.value = props.user.avatar || ''
  }
})
watch(dialogVisible, (val) => emit('update:visible', val))

function triggerUpload() {
  avatarInput.value?.click()
}

async function handleAvatarChange(e) {
  const file = e.target.files[0]
  if (!file) return
  const formData = new FormData()
  formData.append('file', file)
  try {
    const res = await request.post('/auth/user/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    if (res.code === 0) {
      avatarUrl.value = res.data.avatar_url
      ElMessage.success('头像更新成功')
      // 更新本地存储的用户信息
      const userStr = localStorage.getItem('user')
      if (userStr) {
        const user = JSON.parse(userStr)
        user.avatar = res.data.avatar_url
        localStorage.setItem('user', JSON.stringify(user))
        emit('update-user', user)
      }
    } else {
      ElMessage.error(res.message || '上传失败')
    }
  } catch (error) {
    ElMessage.error('上传失败')
  }
  e.target.value = ''
}

// 保存当前选项卡
async function saveCurrentTab() {
  saving.value = true
  try {
    if (activeTab.value === 'info') {
      await request.put('/auth/user/me', {
        name: infoForm.name,
        phone: infoForm.phone
      })
      ElMessage.success('基本信息更新成功')
      // 更新本地存储
      const userStr = localStorage.getItem('user')
      if (userStr) {
        const user = JSON.parse(userStr)
        user.name = infoForm.name
        user.phone = infoForm.phone
        localStorage.setItem('user', JSON.stringify(user))
        emit('update-user', user)
      }
      dialogVisible.value = false
    } else if (activeTab.value === 'password') {
      if (pwdForm.new_password !== pwdForm.confirm_password) {
        ElMessage.warning('两次输入的新密码不一致')
        return
      }
      if (pwdForm.new_password.length < 6) {
        ElMessage.warning('新密码长度不能少于6位')
        return
      }
      await request.post('/auth/change-password', {
        old_password: pwdForm.old_password,
        new_password: pwdForm.new_password
      })
      ElMessage.success('密码修改成功，请重新登录')
      // 清除登录信息并跳转
      localStorage.clear()
      window.location.href = '/login'
    }
  } catch (error) {
    const msg = error.response?.data?.detail || '操作失败'
    ElMessage.error(msg)
  } finally {
    saving.value = false
  }
}

function handleClose() {
  dialogVisible.value = false
}
</script>

<style scoped>
.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 20px 0;
}
.avatar-preview {
  border: 2px solid var(--primary-color);
  border-radius: 50%;
}
</style>