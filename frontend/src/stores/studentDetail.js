import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getStudentDetail, getStudentCourses } from '@/api/student'
import { getStudentScore } from '@/api/score'
import { getOrderList } from '@/api/order'

export const useStudentDetailStore = defineStore('studentDetail', () => {
  const student = ref(null)
  const courses = ref([])
  const integrals = ref([])
  const orders = ref([])
  const loading = ref(false)

  async function fetchAll(studentId) {
    loading.value = true
    try {
      const [detailRes, coursesRes, scoreRes, orderRes] = await Promise.all([
        getStudentDetail(studentId),
        getStudentCourses(studentId),
        getStudentScore(studentId),
        getOrderList({ search: '' })
      ])
      student.value = detailRes.data
      courses.value = coursesRes.data || []
      integrals.value = scoreRes.data?.history || []
      student.value.total_integral = scoreRes.data?.total_integral || 0
      orders.value = (orderRes.data || []).filter(o => o.student_id === studentId)
    } catch (e) {
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  function clear() {
    student.value = null
    courses.value = []
    integrals.value = []
    orders.value = []
  }

  return { student, courses, integrals, orders, loading, fetchAll, clear }
})