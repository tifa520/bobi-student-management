import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getAggregatedStudents } from '@/api/student'

export const useStudentStore = defineStore('student', () => {
  // 状态
  const students = ref([])
  const total = ref(0)
  const loading = ref(false)

  // 获取列表（支持分页和筛选）
  async function fetchStudents(params) {
    loading.value = true
    try {
      const res = await getAggregatedStudents(params)
      students.value = res.data?.items || []
      total.value = res.data?.total || 0
    } finally {
      loading.value = false
    }
  }

  // ========== 核心：更新头像（关键方法） ==========
  function updateAvatar(studentId, newAvatar) {
    const student = students.value.find(s => s.id === studentId)
    if (student) {
      student.avatar = newAvatar
    }
    // 如果列表中有嵌套的 courses 也需要更新 avatar，但字段通常只在顶层
    // 如果学员在列表中以 course 展开的形式存在（每个课程一条记录），需按 student_id 批量更新
    // 但您的列表是按学员聚合的（每个学员一条），所以直接 find 即可
  }

  // 更新卡片背景
  function updateCardBackground(studentId, newBg) {
    const student = students.value.find(s => s.id === studentId)
    if (student) {
      student.card_background = newBg
    }
  }

  // 清除数据
  function clear() {
    students.value = []
    total.value = 0
  }

  return {
    students,
    total,
    loading,
    fetchStudents,
    updateAvatar,
    updateCardBackground,
    clear
  }
})