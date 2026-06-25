// src/stores/tagsView.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import router from '@/router'

export const useTagsViewStore = defineStore('tagsView', () => {
  const visitedViews = ref([])
  const activeView = ref('')

  function getViewKey(route) {
    const queryStr = route.query && Object.keys(route.query).length
      ? '?' + new URLSearchParams(route.query).toString()
      : ''
    return route.path + queryStr
  }

  function addView(route) {
    const key = getViewKey(route)
    const existing = visitedViews.value.find(v => v.key === key)
    if (existing) {
      existing.title = route.meta?.title || route.name || '未命名'
      activeView.value = key
      return
    }
    // 如果标签页数量超过 20，自动关闭最早的非固定标签页
    const nonAffixCount = visitedViews.value.filter(v => !v.affix).length
    if (nonAffixCount >= 20) {
      const toRemove = visitedViews.value.find(v => !v.affix)
      if (toRemove) {
        visitedViews.value = visitedViews.value.filter(v => v.key !== toRemove.key)
      }
    }
    visitedViews.value.push({
      key,
      path: route.path,
      query: route.query || {},
      title: route.meta?.title || route.name || '未命名',
      name: route.name,
      affix: route.meta?.affix || false
    })
    activeView.value = key
  }

  function switchView(key) {
    const view = visitedViews.value.find(v => v.key === key)
    if (view) {
      activeView.value = key
      router.push({ path: view.path, query: view.query })
    }
  }

  function closeView(key) {
    const index = visitedViews.value.findIndex(v => v.key === key)
    if (index === -1) return
    const view = visitedViews.value[index]
    if (view.affix) return

    visitedViews.value.splice(index, 1)

    if (activeView.value === key) {
      const nextView = visitedViews.value[index] || visitedViews.value[index - 1]
      if (nextView) {
        switchView(nextView.key)
      } else if (visitedViews.value.length > 0) {
        switchView(visitedViews.value[0].key)
      } else {
        router.push('/dashboard')
        activeView.value = ''
      }
    }
  }

  function closeOtherViews(key) {
    const view = visitedViews.value.find(v => v.key === key)
    if (!view) return
    visitedViews.value = visitedViews.value.filter(v =>
      v.key === key || v.affix
    )
    activeView.value = key
  }

  function closeAllViews() {
    visitedViews.value = visitedViews.value.filter(v => v.affix)
    if (visitedViews.value.length > 0) {
      switchView(visitedViews.value[0].key)
    } else {
      router.push('/dashboard')
      activeView.value = ''
    }
  }

  function refreshView(key) {
    const view = visitedViews.value.find(v => v.key === key)
    if (view) {
      const currentPath = router.currentRoute.value.fullPath
      router.replace('/redirect' + currentPath)
    }
  }

  return {
    visitedViews,
    activeView,
    addView,
    switchView,
    closeView,
    closeOtherViews,
    closeAllViews,
    refreshView,
    getViewKey
  }
})