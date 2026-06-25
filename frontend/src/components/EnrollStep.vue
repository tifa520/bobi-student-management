<template>
  <div class="enroll-step-container">
    <div class="steps-wrapper">
      <div class="step-item" :class="{ 'step-finish': currentStep > 1, 'step-process': currentStep === 1 }">
        <div class="step-icon">{{ currentStep > 1 ? '✓' : '1' }}</div>
        <div class="step-title">学员信息</div>
      </div>
      <div class="step-line" :class="{ active: currentStep >= 2 }"></div>
      <div class="step-item" :class="{ 'step-finish': currentStep > 2, 'step-process': currentStep === 2 }">
        <div class="step-icon">{{ currentStep > 2 ? '✓' : '2' }}</div>
        <div class="step-title">报名信息</div>
      </div>
      <div class="step-line" :class="{ active: currentStep >= 3 }"></div>
      <div class="step-item" :class="{ 'step-process': currentStep === 3 }">
        <div class="step-icon">3</div>
        <div class="step-title">费用结算</div>
      </div>
    </div>
    <div class="step-content">
      <slot :name="'step' + currentStep" />
    </div>
    <div class="step-actions" v-if="showActions">
      <el-button v-if="currentStep > 1" @click="$emit('prev')" class="btn-prev">上一步</el-button>
      <el-button v-if="currentStep < 3" type="primary" @click="$emit('next')" class="btn-next">下一步</el-button>
      <el-button v-if="currentStep === 3" type="primary" @click="$emit('submit')" :loading="submitting">提交报名</el-button>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  currentStep: { type: Number, required: true },
  showActions: { type: Boolean, default: true },
  submitting: { type: Boolean, default: false }
})
const emit = defineEmits(['prev', 'next', 'submit'])
</script>

<style scoped>
.enroll-step-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.steps-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  padding: 0 10px;
}

.step-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: bold;
  transition: all 0.2s;
  border: 1px solid #c0c4cc;
  background-color: white;
  color: #c0c4cc;
}

.step-title {
  margin-top: 8px;
  font-size: 14px;
  color: #c0c4cc;
}

.step-process .step-icon {
  background-color: #36b459;
  border: none;
  color: white;
}

.step-process .step-title {
  color: #36b459;
  font-weight: 500;
}

.step-finish .step-icon {
  background-color: #36b459;
  border: none;
  color: white;
}

.step-finish .step-title {
  color: #36b459;
}

.step-line {
  flex: 1;
  height: 1px;
  background-image: repeating-linear-gradient(to right, #c0c4cc 0px, #c0c4cc 4px, transparent 4px, transparent 8px);
  background-repeat: repeat-x;
  background-size: 8px 1px;
  margin: 0 8px;
  position: relative;
  top: -13px;
}

.step-line.active {
  background-image: none;
  background-color: #36b459;
}

.step-content {
  min-height: 300px;
}

.step-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 32px;
}

/* 按钮样式使用全局样式，这里只保留特定修饰 */
.btn-prev {
  background: var(--white);
  border-color: var(--border-color);
  color: var(--text-regular);
}

.btn-prev:hover {
  background: var(--primary-color);
  border-color: var(--primary-color);
  color: white;
}

.btn-next {
  background: var(--primary-color);
  border-color: var(--primary-color);
}

.btn-next:hover {
  background: var(--primary-light);
  border-color: var(--primary-light);
}
</style>