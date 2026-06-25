<template>
  <div class="page-container">
    <el-table :data="tableData" v-loading="loading" border stripe>
      <el-table-column prop="name" label="姓名" />
      <el-table-column prop="phone" label="手机" />
      <el-table-column prop="gender" label="性别" />
      <el-table-column prop="age" label="年龄" />
      <el-table-column prop="total_integral" label="总积分" />
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getGraduatedStudents } from '@/api/student'

const tableData = ref([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const res = await getGraduatedStudents({ page: 1, page_size: 100 })
    // 后端返回格式可能是 { data: { items: [], total: 0 } } 或直接数组
    tableData.value = res.data?.items || res.data || []
  } finally {
    loading.value = false
  }
})
</script>