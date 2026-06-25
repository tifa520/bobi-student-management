import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { enrollApi } from '@/api/enroll'

export const useEnrollStore = defineStore('enroll', () => {
  const sessionId = ref(null)
  const currentStep = ref(1)
  const step1Data = ref(null)
  const step2Data = ref(null)
  const step3Data = ref(null)

  const isStep1Done = computed(() => !!step1Data.value)
  const isStep2Done = computed(() => !!step2Data.value)

  function setSessionId(id) {
    sessionId.value = id
    localStorage.setItem('enroll-session', id)
  }

  function loadSessionId() {
    const saved = localStorage.getItem('enroll-session')
    if (saved) sessionId.value = saved
  }

  function clearSession() {
    sessionId.value = null
    currentStep.value = 1
    step1Data.value = null
    step2Data.value = null
    step3Data.value = null
    localStorage.removeItem('enroll-session')
  }

  async function saveStep1(data) {
    const res = await enrollApi.step1(data, sessionId.value)
    const sid = res.session_id
    if (sid) setSessionId(sid)
    step1Data.value = data
    currentStep.value = 1
  }

  async function saveStep2(data) {
    await enrollApi.step2(data, sessionId.value)
    step2Data.value = data
    currentStep.value = 2
  }

  async function submitStep3(data) {
    const res = await enrollApi.step3Submit(data, sessionId.value)
    clearSession()
    return res
  }

  return {
    sessionId,
    currentStep,
    step1Data,
    step2Data,
    step3Data,
    isStep1Done,
    isStep2Done,
    setSessionId,
    loadSessionId,
    clearSession,
    saveStep1,
    saveStep2,
    submitStep3
  }
})