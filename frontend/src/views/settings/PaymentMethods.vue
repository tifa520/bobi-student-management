<template>
  <div class="settings-page">
    <div class="settings-card">
      <div class="card-header">
        <span class="card-title">支付方式</span>
        <el-button type="primary" @click="saveMethods" :loading="saving" size="default">保存设置</el-button>
      </div>
      <div class="content-container">
        <div class="methods-grid">
          <div
            v-for="(method, index) in methods"
            :key="index"
            class="method-card"
            :class="{ 'method-card-new': isNewMethod(index) }"
          >
            <div class="method-icon">
              <el-icon :size="28">
                <component :is="getMethodIcon(method)" />
              </el-icon>
            </div>
            <div class="method-content">
              <el-input
                v-model="methods[index]"
                placeholder="支付方式名称"
                class="method-input"
                :class="{ 'is-new': isNewMethod(index) }"
              />
            </div>
            <div class="method-actions">
              <el-button
                type="danger"
                link
                size="small"
                @click="removeMethod(index)"
                :disabled="isDefaultMethod(method)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </div>

        <div class="add-method-section">
          <el-button type="primary" plain @click="addMethod" class="add-btn">
            <el-icon><Plus /></el-icon> 添加支付方式
          </el-button>
        </div>

        <div class="default-methods-hint" v-if="defaultMethods.length > 0">
          <el-alert
            title="默认支付方式"
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              <div class="default-tags">
                <el-tag
                  v-for="method in defaultMethods"
                  :key="method"
                  size="small"
                  type="info"
                  effect="plain"
                >
                  {{ method }}
                </el-tag>
              </div>
              <div class="hint-text">默认支付方式不可删除，但可以修改名称</div>
            </template>
          </el-alert>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, Plus, Wallet, Money, CreditCard, Coin, Tickets } from '@element-plus/icons-vue'
import request from '@/api/request'
import { getPaymentMethods, updatePaymentMethods } from '@/api/settings'

const methods = ref([])
const saving = ref(false)
const newMethodIndices = ref(new Set())

// 默认支付方式列表（不可删除，但可修改）
const defaultMethodNames = ['微信支付', '支付宝', '现金', '银行转账']

const defaultMethods = computed(() => {
  return methods.value.filter(method => defaultMethodNames.includes(method))
})

function isDefaultMethod(method) {
  return defaultMethodNames.includes(method)
}

function isNewMethod(index) {
  return newMethodIndices.value.has(index)
}

// 根据支付方式名称返回对应图标
function getMethodIcon(method) {
  if (method.includes('微信')) return 'Wallet'
  if (method.includes('支付宝')) return 'CreditCard'
  if (method.includes('现金')) return 'Money'
  if (method.includes('银行')) return 'Coin'
  return 'Tickets'
}

async function fetchMethods() {
  try {
    const res = await getPaymentMethods()
    if (res.code === 0 && res.data) {
      methods.value = res.data
    } else {
      methods.value = [...defaultMethodNames]
    }
  } catch (e) {
    console.error('加载支付方式失败，使用默认值', e)
    methods.value = [...defaultMethodNames]
  }
}

async function saveMethods() {
  saving.value = true
  try {
    await updatePaymentMethods(methods.value)
    ElMessage.success('保存成功')
    newMethodIndices.value.clear()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

function addMethod() {
  const newIndex = methods.value.length
  methods.value.push('新支付方式')
  newMethodIndices.value.add(newIndex)
  // 自动聚焦到新输入框
  setTimeout(() => {
    const inputs = document.querySelectorAll('.method-input')
    const lastInput = inputs[inputs.length - 1]
    if (lastInput) {
      const inputElement = lastInput.querySelector('input')
      if (inputElement) inputElement.focus()
    }
  }, 100)
}

function removeMethod(index) {
  const method = methods.value[index]
  if (defaultMethodNames.includes(method)) {
    ElMessage.warning(`"${method}" 是默认支付方式，不可删除，如需修改请直接编辑名称`)
    return
  }
  methods.value.splice(index, 1)
  newMethodIndices.value.delete(index)
  // 重新调整 newMethodIndices 中的索引
  const updatedIndices = new Set()
  for (let idx of newMethodIndices.value) {
    if (idx > index) updatedIndices.add(idx - 1)
    else if (idx < index) updatedIndices.add(idx)
  }
  newMethodIndices.value = updatedIndices
}

onMounted(fetchMethods)
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 28px;
  border-bottom: 1px solid var(--border-light);
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.content-container {
  padding: 28px;
}

/* 卡片网格布局 */
.methods-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 28px;
}

/* 单个支付方式卡片 */
.method-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: var(--surface-soft);
  border-radius: 12px;
  border: 1px solid var(--border-light);
  transition: all 0.2s ease;
}

.method-card:hover {
  border-color: var(--brand-500);
  box-shadow: 0 4px 12px rgba(54, 180, 89, 0.1);
  background: var(--surface);
}

.method-card-new {
  background: var(--surface-green);
  border-color: var(--brand-500);
}

/* 图标区域 */
.method-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--brand-50);
  border-radius: 12px;
  color: var(--brand-500);
  flex-shrink: 0;
}

/* 内容区域 */
.method-content {
  flex: 1;
  min-width: 0;
}

.method-input {
  width: 100%;
}

.method-input :deep(.el-input__wrapper) {
  background: transparent;
  box-shadow: none;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.method-input :deep(.el-input__wrapper:hover) {
  border-color: var(--brand-500);
  box-shadow: 0 0 0 1px var(--brand-500) inset;
}

.method-input :deep(.el-input__wrapper.is-focus) {
  border-color: var(--brand-500);
  box-shadow: 0 0 0 1px var(--brand-500) inset;
  background: var(--surface);
}

.method-input.is-new :deep(.el-input__wrapper) {
  border-color: var(--brand-500);
  background: var(--surface);
}

/* 操作按钮区域 */
.method-actions {
  flex-shrink: 0;
}

.method-actions .el-button {
  padding: 6px;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.method-card:hover .method-actions .el-button {
  opacity: 1;
}

/* 添加按钮区域 */
.add-method-section {
  text-align: center;
  margin-bottom: 28px;
  padding-top: 8px;
  border-top: 1px solid var(--border-light);
}

.add-btn {
  min-width: 160px;
  border-radius: 24px;
  padding: 10px 24px;
  font-size: 14px;
  transition: all 0.2s;
}

.add-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(54, 180, 89, 0.2);
}

/* 默认支付方式提示区域 */
.default-methods-hint {
  margin-top: 20px;
}

.default-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 10px;
}

.hint-text {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 8px;
}

:deep(.el-alert) {
  border-radius: 12px;
  background-color: var(--app-bg);
}
</style>