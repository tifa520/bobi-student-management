<!-- src/components/TagsView/index.vue -->
<template>
  <div class="tags-view">
    <!-- ★ 折叠图标（靠左第一个） ★ -->
    <el-icon class="collapse-icon" @click="appStore.toggleSidebar()">
      <Fold v-if="!appStore.sidebarCollapsed" />
      <Expand v-else />
    </el-icon>

    <div class="tags-scroll" ref="scrollContainer">
      <div
        v-for="view in visitedViews"
        :key="view.key"
        class="tag-item"
        :class="{ active: activeView === view.key }"
        @click="switchView(view.key)"
        @contextmenu.prevent="openContextMenu($event, view)"
      >
        <span>{{ view.title }}</span>
        <el-icon
          v-if="!view.affix"
          class="tag-close"
          @click.stop="closeView(view.key)"
        >
          <Close />
        </el-icon>
      </div>
    </div>

    <!-- 右键菜单 -->
    <ul
      v-show="contextMenuVisible"
      class="context-menu"
      :style="{ left: contextMenuX + 'px', top: contextMenuY + 'px' }"
      @click.stop
    >
      <li @click="handleRefresh">刷新</li>
      <li @click="handleCloseCurrent">关闭</li>
      <li @click="handleCloseOther">关闭其他</li>
      <li @click="handleCloseAll">关闭所有</li>
    </ul>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { Close, Fold, Expand } from '@element-plus/icons-vue'
import { useTagsViewStore } from '@/stores/tagsView'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const tagsStore = useTagsViewStore()
const appStore = useAppStore()

const visitedViews = computed(() => tagsStore.visitedViews)
const activeView = computed(() => tagsStore.activeView)

const scrollContainer = ref(null)
const contextMenuVisible = ref(false)
const contextMenuX = ref(0)
const contextMenuY = ref(0)
const contextMenuTarget = ref(null)

function switchView(key) {
  tagsStore.switchView(key)
}

function closeView(key) {
  tagsStore.closeView(key)
}

function openContextMenu(event, view) {
  contextMenuTarget.value = view
  contextMenuX.value = event.clientX
  contextMenuY.value = event.clientY
  contextMenuVisible.value = true
}

function handleRefresh() {
  if (contextMenuTarget.value) {
    tagsStore.refreshView(contextMenuTarget.value.key)
  }
  contextMenuVisible.value = false
}

function handleCloseCurrent() {
  if (contextMenuTarget.value) {
    tagsStore.closeView(contextMenuTarget.value.key)
  }
  contextMenuVisible.value = false
}

function handleCloseOther() {
  if (contextMenuTarget.value) {
    tagsStore.closeOtherViews(contextMenuTarget.value.key)
  }
  contextMenuVisible.value = false
}

function handleCloseAll() {
  tagsStore.closeAllViews()
  contextMenuVisible.value = false
}

function handleClickOutside() {
  contextMenuVisible.value = false
}

function scrollToActiveTab() {
  nextTick(() => {
    const container = scrollContainer.value
    if (!container) return
    const activeElement = container.querySelector('.tag-item.active')
    if (activeElement) {
      activeElement.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
        inline: 'nearest'
      })
    }
  })
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})

defineExpose({ scrollToActiveTab })
</script>

<style scoped>
.tags-view {
  height: var(--tags-height);
  min-height: var(--tags-height);
  max-height: var(--tags-height);
  background: rgba(255, 255, 255, 0.52);
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  padding: 0 14px;
  overflow: hidden;
  flex-shrink: 0;
  width: 100%;
  box-sizing: border-box;
  backdrop-filter: blur(14px);
}

.collapse-icon {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid var(--border-subtle);
  font-size: 16px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: color 0.18s, background 0.18s;
  flex-shrink: 0;
  margin-right: 8px;
}

.collapse-icon:hover {
  color: var(--brand-700);
  background: var(--surface-green);
}

.tags-scroll {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow-x: auto;
  overflow-y: hidden;
  height: 100%;
  flex: 1;
  scrollbar-width: none;
}
.tags-scroll::-webkit-scrollbar {
  display: none;
}

.tag-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 14px;
  height: 32px;
  border-radius: var(--radius-pill);
  font-size: 13px;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.62);
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: background 0.18s, color 0.18s, border-color 0.18s, box-shadow 0.18s, transform 0.18s;
  border: 1px solid var(--border-subtle);
  user-select: none;
}

.tag-item:hover {
  background: var(--surface);
  color: var(--brand-700);
  border-color: rgba(50, 168, 82, 0.18);
  transform: translateY(-1px);
}

.tag-item.active {
  background: var(--surface);
  color: var(--brand-700);
  border-color: rgba(50, 168, 82, 0.22);
  box-shadow: 0 8px 18px rgba(17, 31, 23, 0.08);
}

.tag-item.active::before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: var(--radius-pill);
  background: var(--brand-500);
}

.tag-item .tag-close {
  font-size: 12px;
  border-radius: 50%;
  padding: 1px;
  transition: all 0.2s;
}
.tag-item .tag-close:hover {
  background: rgba(255, 255, 255, 0.3);
}

.context-menu {
  position: fixed;
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  padding: 6px 0;
  list-style: none;
  min-width: 120px;
  z-index: 9999;
}

.context-menu li {
  padding: 8px 20px;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.18s, color 0.18s;
  color: var(--text-regular);
}

.context-menu li:hover {
  background: var(--brand-50);
  color: var(--brand-700);
}
</style>
