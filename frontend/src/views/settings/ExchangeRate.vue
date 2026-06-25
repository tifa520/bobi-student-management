<template>
  <div class="settings-page">
    <div class="settings-card">
      <div class="card-header">
        <span class="card-title">积分汇率设置</span>
        <el-button type="primary" @click="saveRate" :loading="saving" size="default">保存设置</el-button>
      </div>
      <div class="content-container">
        <div class="rate-info">
          <div class="info-item">
            <span class="label">当前汇率</span>
            <span class="value">1元 = {{ rate }} 积分</span>
          </div>
          <div class="info-item">
            <span class="label">修改汇率</span>
            <div class="control-group">
              <el-input-number v-model="rate" :min="1" :step="1" controls-position="right" style="width: 160px" />
              <span class="unit">积分 / 元</span>
            </div>
          </div>
        </div>
        <el-alert type="warning" show-icon :closable="false" class="warning-tip">
          <template #title>注意</template>
          汇率变更后，仅影响新增的销售订单，历史已完成的销售不会受汇率变化影响。
        </el-alert>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
import { getExchangeRate, updateExchangeRate } from '@/api/settings'

const rate = ref(10)
const saving = ref(false)

async function fetchRate() {
  try {
    const res = await getExchangeRate()
    if (res.code === 0 && res.data) {
      rate.value = res.data
    } else {
      rate.value = 10
    }
  } catch (e) {
    console.error('加载汇率失败，使用默认值', e)
    rate.value = 10
  }
}

async function saveRate() {
  saving.value = true
  try {
    await updateExchangeRate(rate.value)
    ElMessage.success('保存成功')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(fetchRate)
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
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-light);
}
.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}
.content-container {
  padding: 24px;
}
.rate-info {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-bottom: 24px;
}
.info-item {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-light);
}
.info-item .label {
  width: 100px;
  font-size: 14px;
  color: var(--text-secondary);
}
.info-item .value {
  font-size: 20px;
  font-weight: 600;
  color: var(--brand-500);
}
.control-group {
  display: flex;
  align-items: center;
  gap: 12px;
}
.unit {
  font-size: 14px;
  color: var(--text-secondary);
}
.warning-tip {
  margin-top: 20px;
  border-radius: 8px;
}
</style>