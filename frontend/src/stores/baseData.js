import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getCourseListSimple, getClassList, getEnabledTeachers, getEnabledClassrooms } from '@/api/basic'

export const useBaseDataStore = defineStore('baseData', () => {
  const courses = ref([])
  const classes = ref([])
  const teachers = ref([])
  const classrooms = ref([])
  const lastFetch = ref(0)
  const CACHE_DURATION = 10 * 60 * 1000 // 10分钟
  const cacheVersion = ref(0)

  function isExpired() {
    return Date.now() - lastFetch.value > CACHE_DURATION
  }

  function invalidate() {
    cacheVersion.value++
    lastFetch.value = 0
    courses.value = []
    classes.value = []
    teachers.value = []
    classrooms.value = []
  }

  function ensureArray(data) {
    if (Array.isArray(data)) return data
    if (data && typeof data === 'object') {
      if (Array.isArray(data.items)) return data.items
      if (Array.isArray(data.data)) return data.data
      if (Array.isArray(data.records)) return data.records
    }
    return []
  }

  async function fetchCourses(force = false) {
    if (!force && courses.value.length && !isExpired()) return courses.value
    try {
      const res = await getCourseListSimple()
      courses.value = ensureArray(res.data)
      lastFetch.value = Date.now()
      return courses.value
    } catch {
      courses.value = []
      return []
    }
  }

  async function fetchClasses(force = false) {
    if (!force && classes.value.length && !isExpired()) return classes.value
    try {
      const res = await getClassList()
      classes.value = ensureArray(res.data)
      lastFetch.value = Date.now()
      return classes.value
    } catch {
      classes.value = []
      return []
    }
  }

  async function fetchTeachers(force = false) {
    if (!force && teachers.value.length && !isExpired()) return teachers.value
    try {
      const res = await getEnabledTeachers()
      teachers.value = ensureArray(res.data)
      lastFetch.value = Date.now()
      return teachers.value
    } catch {
      teachers.value = []
      return []
    }
  }

  async function fetchClassrooms(force = false) {
    if (!force && classrooms.value.length && !isExpired()) return classrooms.value
    try {
      const res = await getEnabledClassrooms()
      classrooms.value = ensureArray(res.data)
      lastFetch.value = Date.now()
      return classrooms.value
    } catch {
      classrooms.value = []
      return []
    }
  }

  async function fetchAll(force = false) {
    if (force) {
      // 强制刷新：清空已有数据并重置缓存时间
      courses.value = []
      classes.value = []
      teachers.value = []
      classrooms.value = []
      lastFetch.value = 0
    }
    await Promise.all([
      fetchCourses(force),
      fetchClasses(force),
      fetchTeachers(force),
      fetchClassrooms(force)
    ])
  }

  return {
    courses,
    classes,
    teachers,
    classrooms,
    fetchCourses,
    fetchClasses,
    fetchTeachers,
    fetchClassrooms,
    fetchAll,
    invalidate
  }
})