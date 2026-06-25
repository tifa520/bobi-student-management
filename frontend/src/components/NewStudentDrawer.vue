<template>
  <el-drawer v-model="visible" title="新建学员" direction="rtl" size="500px" @close="resetForm">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="90px" class="new-student-form">
      <el-form-item label="姓名" prop="name">
        <el-input v-model="form.name" placeholder="请输入姓名" />
      </el-form-item>
      <el-form-item label="手机号" prop="phone">
        <el-input v-model="form.phone" placeholder="请输入手机号" />
      </el-form-item>
      <el-form-item label="性别">
        <el-radio-group v-model="form.gender">
          <el-radio value="男">男</el-radio>
          <el-radio value="女">女</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="出生日期">
        <el-date-picker v-model="form.birthDate" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width:100%" @change="calcAge" />
      </el-form-item>
      <el-form-item label="年龄">
        <el-input v-model="form.age" disabled placeholder="自动计算" />
      </el-form-item>
      <el-form-item label="介绍人">
        <el-input v-model="form.introducer" placeholder="选填" />
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="form.note" type="textarea" placeholder="选填" />
      </el-form-item>
      <el-divider content-position="left">联系人</el-divider>
      <div v-for="(contact, index) in form.contacts" :key="index" class="contact-item">
        <el-row :gutter="8" align="middle">
          <el-col :span="7"><el-input v-model="contact.name" placeholder="姓名" /></el-col>
          <el-col :span="6"><el-input v-model="contact.relation" placeholder="关系" /></el-col>
          <el-col :span="8"><el-input v-model="contact.phone" placeholder="联系方式" /></el-col>
          <el-col :span="3"><el-button type="danger" :icon="Delete" circle size="small" @click="removeContact(index)" /></el-col>
        </el-row>
      </div>
      <el-button type="primary" link @click="addContact"><el-icon><Plus /></el-icon> 添加联系人</el-button>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="submitForm" :loading="submitting">保存</el-button>
    </template>
  </el-drawer>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { Delete, Plus } from '@element-plus/icons-vue'
import { quickCreateStudent } from '@/api/enroll'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'

const props = defineProps({ visible: Boolean })
const emit = defineEmits(['update:visible', 'student-created'])

const visible = ref(props.visible)
watch(() => props.visible, (v) => { visible.value = v })
watch(visible, (v) => emit('update:visible', v))

const formRef = ref(null)
const submitting = ref(false)
const form = reactive({ name: '', phone: '', gender: '', birthDate: '', age: '', introducer: '', note: '', contacts: [] })

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }, { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }]
}

function calcAge() {
  if (form.birthDate) {
    const now = dayjs()
    const birth = dayjs(form.birthDate)
    if (birth.isValid() && birth.isBefore(now)) form.age = String(now.diff(birth, 'year'))
    else form.age = ''
  } else form.age = ''
}

function addContact() { form.contacts.push({ name: '', relation: '', phone: '' }) }
function removeContact(index) { form.contacts.splice(index, 1) }

function resetForm() {
  formRef.value?.resetFields()
  form.age = ''
  form.contacts = []
}

async function submitForm() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const payload = {
      name: form.name,
      phone: form.phone,
      gender: form.gender || null,
      birth_date: form.birthDate || null,
      introducer: form.introducer || null,
      note: form.note || null,
      contacts: form.contacts.length ? form.contacts : undefined
    }
    const res = await quickCreateStudent(payload)
    ElMessage.success('学员创建成功')
    emit('student-created', res.data)
    visible.value = false
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.new-student-form .el-form-item { margin-bottom: 24px; }
.contact-item { margin-bottom: 8px; }
</style>