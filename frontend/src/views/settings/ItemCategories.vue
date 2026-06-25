<template>
  <div class="settings-page">
    <div class="settings-card">
      <div class="card-header">
        <span class="card-title">商品类别</span>
        <el-button type="primary" @click="saveCategories" :loading="saving" size="default">保存设置</el-button>
      </div>
      <div class="content-container">
        <div class="categories-grid">
          <div
            v-for="(cat, index) in categories"
            :key="index"
            class="category-card"
            :class="{ 'category-card-new': isNewCategory(index) }"
          >
            <div class="category-icon">
              <el-icon :size="28"><Goods /></el-icon>
            </div>
            <div class="category-content">
              <el-input
                v-model="categories[index]"
                placeholder="类别名称"
                class="category-input"
                :class="{ 'is-new': isNewCategory(index) }"
              />
            </div>
            <div class="category-actions">
              <el-button
                type="danger"
                link
                size="small"
                @click="removeCategory(index)"
                :disabled="isDefaultCategory(cat)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </div>

        <div class="add-category-section">
          <el-button type="primary" plain @click="addCategory" class="add-btn">
            <el-icon><Plus /></el-icon> 添加新类别
          </el-button>
        </div>

        <div class="default-categories-hint" v-if="defaultCategories.length > 0">
          <el-alert
            title="默认类别"
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              <div class="default-tags">
                <el-tag
                  v-for="cat in defaultCategories"
                  :key="cat"
                  size="small"
                  type="info"
                  effect="plain"
                >
                  {{ cat }}
                </el-tag>
              </div>
              <div class="hint-text">默认类别不可删除，但可以修改名称</div>
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
import { Delete, Plus, Goods } from '@element-plus/icons-vue'
import request from '@/api/request'
import { getItemCategories, updateItemCategories } from '@/api/settings'

const categories = ref([])
const saving = ref(false)
const newCategoryIndices = ref(new Set())

// 默认类别列表（不可删除，但可修改）
const defaultCategoryNames = ['教材', '教具', '礼品', '办公用品', '其他']

const defaultCategories = computed(() => {
  return categories.value.filter(cat => defaultCategoryNames.includes(cat))
})

function isDefaultCategory(cat) {
  return defaultCategoryNames.includes(cat)
}

function isNewCategory(index) {
  return newCategoryIndices.value.has(index)
}

async function fetchCategories() {
  try {
    const res = await getItemCategories()
    if (res.code === 0 && res.data) {
      categories.value = res.data
    } else {
      categories.value = [...defaultCategoryNames]
    }
  } catch (e) {
    console.error('加载商品类别失败，使用默认值', e)
    categories.value = [...defaultCategoryNames]
  }
}

async function saveCategories() {
  saving.value = true
  try {
    await updateItemCategories(categories.value)
    ElMessage.success('保存成功')
    newCategoryIndices.value.clear()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

function addCategory() {
  const newIndex = categories.value.length
  categories.value.push('新类别')
  newCategoryIndices.value.add(newIndex)
  // 自动聚焦到新输入框
  setTimeout(() => {
    const inputs = document.querySelectorAll('.category-input')
    const lastInput = inputs[inputs.length - 1]
    if (lastInput) {
      const inputElement = lastInput.querySelector('input')
      if (inputElement) inputElement.focus()
    }
  }, 100)
}

function removeCategory(index) {
  const cat = categories.value[index]
  if (defaultCategoryNames.includes(cat)) {
    ElMessage.warning(`"${cat}" 是默认类别，不可删除，如需修改请直接编辑名称`)
    return
  }
  categories.value.splice(index, 1)
  newCategoryIndices.value.delete(index)
  // 重新调整 newCategoryIndices 中的索引
  const updatedIndices = new Set()
  for (let idx of newCategoryIndices.value) {
    if (idx > index) updatedIndices.add(idx - 1)
    else if (idx < index) updatedIndices.add(idx)
  }
  newCategoryIndices.value = updatedIndices
}

onMounted(fetchCategories)
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
.categories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 28px;
}

/* 单个类别卡片 */
.category-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: var(--surface-soft);
  border-radius: 12px;
  border: 1px solid var(--border-light);
  transition: all 0.2s ease;
}

.category-card:hover {
  border-color: var(--brand-500);
  box-shadow: 0 4px 12px rgba(54, 180, 89, 0.1);
  background: var(--surface);
}

.category-card-new {
  background: var(--surface-green);
  border-color: var(--brand-500);
}

/* 图标区域 */
.category-icon {
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
.category-content {
  flex: 1;
  min-width: 0;
}

.category-input {
  width: 100%;
}

.category-input :deep(.el-input__wrapper) {
  background: transparent;
  box-shadow: none;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.category-input :deep(.el-input__wrapper:hover) {
  border-color: var(--brand-500);
  box-shadow: 0 0 0 1px var(--brand-500) inset;
}

.category-input :deep(.el-input__wrapper.is-focus) {
  border-color: var(--brand-500);
  box-shadow: 0 0 0 1px var(--brand-500) inset;
  background: var(--surface);
}

.category-input.is-new :deep(.el-input__wrapper) {
  border-color: var(--brand-500);
  background: var(--surface);
}

/* 操作按钮区域 */
.category-actions {
  flex-shrink: 0;
}

.category-actions .el-button {
  padding: 6px;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.category-card:hover .category-actions .el-button {
  opacity: 1;
}

/* 添加按钮区域 */
.add-category-section {
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

/* 默认类别提示区域 */
.default-categories-hint {
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