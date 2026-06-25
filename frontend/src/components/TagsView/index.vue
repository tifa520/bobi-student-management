<template>
  <div class="tags-view">
    <div class="tags-scroll" ref="scrollContainer">
      <div
        v-for="view in visitedViews"
        :key="view.key"
        class="tag-item"
        :class="{ active: activeView === view.key }"
        @click="switchView(view.key)"
        @contextmenu.prevent="openContextMenu($event, view)"
      >
        <span v-if="view.affix" class="tag-pin">📌</span>
        <span class="tag-title">{{ view.title }}</span>
        <el-icon
          v-if="!view.affix"
          class="tag-close"
          @click.stop="closeView(view.key)"
        >
          <Close />
        </el-icon>
      </div>
    </div>

    <div class="tags-actions">
      <div class="action-divider"></div>
      <el-dropdown trigger="click" @command="handleAction">
        <div class="tags-more-btn">
          <el-icon><MoreFilled /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="refresh">
              <el-icon><RefreshRight /></el-icon>
              刷新当前页
            </el-dropdown-item>
            <el-dropdown-item command="closeOther" divided>
              <el-icon><Close /></el-icon>
              关闭其他
            </el-dropdown-item>
            <el-dropdown-item command="closeAll">
              <el-icon><Delete /></el-icon>
              关闭全部
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <!-- 右键菜单 -->
    <ul
      v-show="contextMenuVisible"
      class="context-menu"
      :style="{ left: contextMenuX + 'px', top: contextMenuY + 'px' }"
      @click.stop
    >
      <li @click="handleRefresh">
        <el-icon><RefreshRight /></el-icon>
        <span>刷新</span>
      </li>
      <li v-if="!contextMenuTarget?.affix" @click="handleCloseCurrent">
        <el-icon><Close /></el-icon>
        <span>关闭</span>
      </li>
      <li @click="handleCloseOther">
        <el-icon><Minus /></el-icon>
        <span>关闭其他</span>
      </li>
      <li @click="handleCloseAll">
        <el-icon><Delete /></el-icon>
        <span>关闭所有</span>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  Close,
  MoreFilled,
  RefreshRight,
  Delete,
  Minus
} from '@element-plus/icons-vue'
import { useTagsViewStore } from '@/stores/tagsView'

const route = useRoute()
const tagsStore = useTagsViewStore()

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

function handleAction(command) {
  const currentView = visitedViews.value.find(v => v.key === activeView.value)
  if (!currentView) return

  switch (command) {
    case 'refresh':
      tagsStore.refreshView(currentView.key)
      break
    case 'closeOther':
      tagsStore.closeOtherViews(currentView.key)
      break
    case 'closeAll':
      tagsStore.closeAllViews()
      break
  }
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

watch(activeView, () => {
  scrollToActiveTab()
})

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
  background:
    linear-gradient(180deg,
      rgba(255, 255, 255, 0.7),
      rgba(255, 255, 255, 0.55));
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  padding: 0 12px 0 16px;
  overflow: hidden;
  flex-shrink: 0;
  width: 100%;
  box-sizing: border-box;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  position: relative;
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
  padding: 6px 0;
}

.tags-scroll::-webkit-scrollbar {
  display: none;
}

.tag-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 12px 0 14px;
  height: 32px;
  border-radius: var(--radius-pill);
  font-size: 13px;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.75);
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: all 0.2s var(--ease-soft);
  border: 1px solid var(--border-subtle);
  user-select: none;
  font-weight: 500;
  position: relative;
}

.tag-item:hover {
  background: var(--surface);
  color: var(--brand-700);
  border-color: rgba(30, 168, 82, 0.25);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(17, 31, 23, 0.06);
}

.tag-item.active {
  background: linear-gradient(135deg,
    rgba(30, 168, 82, 0.12),
    rgba(30, 168, 82, 0.06));
  color: var(--brand-700);
  border-color: rgba(30, 168, 82, 0.3);
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(30, 168, 82, 0.1);
}

.tag-item.active::before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--brand-400), var(--brand-600));
  flex-shrink: 0;
  margin-right: 2px;
}

.tag-pin {
  font-size: 12px;
  opacity: 0.6;
}

.tag-title {
  line-height: 1;
}

.tag-close {
  font-size: 12px;
  border-radius: 50%;
  padding: 2px;
  color: var(--text-placeholder);
  transition: all 0.2s;
  opacity: 0.7;
}

.tag-item:hover .tag-close {
  opacity: 1;
}

.tag-close:hover {
  background: rgba(239, 68, 68, 0.12);
  color: var(--danger-color);
}

.tags-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  margin-left: 8px;
}

.action-divider {
  width: 1px;
  height: 20px;
  background: linear-gradient(180deg, transparent, var(--border-light), transparent);
}

.tags-more-btn {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s var(--ease-soft);
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid var(--border-subtle);
}

.tags-more-btn:hover {
  color: var(--brand-700);
  background: var(--surface-green);
  border-color: rgba(30, 168, 82, 0.2);
  transform: translateY(-1px);
}

.tags-more-btn :deep(.el-icon) {
  font-size: 16px;
}

.context-menu {
  position: fixed;
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  padding: 6px 0;
  list-style: none;
  min-width: 140px;
  z-index: 9999;
  margin: 0;
}

.context-menu li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 16px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.18s;
  color: var(--text-regular);
}

.context-menu li:hover {
  background: var(--brand-50);
  color: var(--brand-700);
}

.context-menu li .el-icon {
  font-size: 15px;
  flex-shrink: 0;
}
</style>
