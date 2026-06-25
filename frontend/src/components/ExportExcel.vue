<template>
  <el-button :loading="loading" @click="handleExport" :type="btnType"><slot>导出 Excel</slot></el-button>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
const props = defineProps({ fetchFn: { type: Function, required: false }, data: { type: Array, required: false }, columns: { type: Array, required: false }, filename: { type: String, default: 'export.xlsx' }, btnType: { type: String, default: 'default' } })
const loading = ref(false)
async function handleExport() {
  loading.value = true
  try {
    if (props.fetchFn) {
      const res = await props.fetchFn()
      const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a'); link.href = url; link.download = props.filename; link.click(); window.URL.revokeObjectURL(url)
    } else if (props.data && props.columns) {
      const XLSX = await import('xlsx')
      const ws = XLSX.utils.json_to_sheet(props.data, { header: props.columns.map(c => c.prop) })
      const wb = XLSX.utils.book_new(); XLSX.utils.book_append_sheet(wb, ws, 'Sheet1'); XLSX.writeFile(wb, props.filename)
    }
    ElMessage.success('导出成功')
  } catch { ElMessage.error('导出失败') } finally { loading.value = false }
}
</script>