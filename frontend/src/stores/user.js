// frontend/src/stores/user.js
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { DEFAULT_AVATAR_SVG } from '@/utils/constants'
import { getCurrentUser } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const user = ref({
    id: null,
    username: '',
    name: '',
    email: '',
    phone: '',
    role: '',
    avatar: DEFAULT_AVATAR_SVG
  })

  function setUser(data) {
    user.value = { ...user.value, ...data }
    // 同步到 localStorage
    localStorage.setItem('user', JSON.stringify(user.value))
  }

  function updateAvatar(avatarUrl) {
    user.value.avatar = avatarUrl
    // 更新 localStorage
    const userStr = localStorage.getItem('user')
    if (userStr) {
      try {
        const parsed = JSON.parse(userStr)
        parsed.avatar = avatarUrl
        localStorage.setItem('user', JSON.stringify(parsed))
      } catch (e) {}
    }
  }

  function loadFromStorage() {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      try {
        const parsed = JSON.parse(userStr)
        user.value = { ...user.value, ...parsed }
        if (!user.value.avatar) {
          user.value.avatar = DEFAULT_AVATAR_SVG
        }
      } catch (e) {}
    }
  }

  async function fetchCurrentUser() {
    try {
      const res = await getCurrentUser()
      if (res.code === 0) {
        setUser(res.data)
        return res.data
      }
    } catch (e) {
      console.error('获取用户信息失败', e)
    }
  }

  return {
    user,
    setUser,
    updateAvatar,
    loadFromStorage,
    fetchCurrentUser
  }
})