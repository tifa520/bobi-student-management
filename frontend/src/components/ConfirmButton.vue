<template>
  <el-popconfirm
    :title="title"
    :confirm-button-text="confirmText"
    :cancel-button-text="cancelText"
    confirm-button-type="danger"
    @confirm="handleConfirm"
  >
    <template #reference>
      <el-button :type="type" :loading="loading">
        <slot>删除</slot>
      </el-button>
    </template>
  </el-popconfirm>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  title: { type: String, default: '确认执行此操作吗？' },
  confirmText: { type: String, default: '确认' },
  cancelText: { type: String, default: '取消' },
  type: { type: String, default: 'danger' },
  beforeAction: { type: Function, default: null }
})
const emit = defineEmits(['confirm'])
const loading = ref(false)

async function handleConfirm() {
  loading.value = true
  try {
    if (props.beforeAction) await props.beforeAction()
    emit('confirm')
  } finally { loading.value = false }
}
</script>