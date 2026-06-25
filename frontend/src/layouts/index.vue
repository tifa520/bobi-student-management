<!-- src/layouts/index.vue -->
<template>
  <div class="app-wrapper">
    <!-- Header -->
    <header class="app-topbar-shell">
      <Header />
    </header>

    <!-- Body -->
    <div class="app-body">
      <!-- Aside -->
      <aside class="app-aside" :style="{ width: sidebarWidth }">
        <Sidebar />
      </aside>

      <!-- Main -->
      <main class="app-main">
        <!-- TagsView -->
        <TagsView />
        <!-- PageContent -->
        <div class="page-content">
          <router-view v-slot="{ Component }">
            <keep-alive :include="cachedViews">
              <component :is="Component" :key="$route.fullPath" />
            </keep-alive>
          </router-view>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'
import { useTagsViewStore } from '@/stores/tagsView'
import Header from '@/components/Header/index.vue'
import Sidebar from '@/components/Sidebar/index.vue'
import TagsView from '@/components/TagsView/index.vue'

const appStore = useAppStore()
const tagsStore = useTagsViewStore()

const sidebarCollapsed = computed(() => appStore.sidebarCollapsed)
const sidebarWidth = computed(() => sidebarCollapsed.value ? '72px' : '216px')

const cachedViews = computed(() => {
  return tagsStore.visitedViews
    .filter(v => v.name)
    .map(v => v.name)
})
</script>

<style scoped>
/* 布局基础样式已收敛到 global.css，避免布局组件与全局样式重复维护 */
</style>
