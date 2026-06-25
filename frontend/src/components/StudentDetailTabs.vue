<template>
  <div class="student-detail-tabs">
    <div class="vertical-tabs">
      <div 
        v-for="tab in tabs" 
        :key="tab.name" 
        class="tab-item" 
        :class="{ active: activeTab === tab.name }" 
        @click="activeTab = tab.name"
      >
        {{ tab.label }}
      </div>
    </div>

    <div class="tab-content">
      <!-- 课程账户 Tab -->
      <div v-if="activeTab === 'courses'" class="courses-content">
        <div class="course-cards" v-if="courses.length > 0">
          <CourseAccountCard
            v-for="course in courses"
            :key="course.course_id"
            :course="course"
            :student-id="studentId"
            @renew="$emit('renew', course)"
            @refund="$emit('refund', course)"
            @graduate="$emit('graduate', course)"
            @suspend="$emit('suspend', course)"
            @transfer-hours="$emit('transfer-hours', course)"
            @adjust-hours="$emit('adjust-hours', course)"
            @gift-hours="$emit('gift-hours', course)"
            @transfer-class="$emit('transfer-class', course)"
            @drop-class="$emit('drop-class', course)"
            @assign-class="$emit('assign-class', course)"
            @repay="$emit('repay', course)"
            @refresh="handleCourseRefresh"
          />
        </div>
        <el-empty v-else description="暂无课程记录" />
      </div>

      <!-- 基本信息 Tab -->
      <div v-if="activeTab === 'info'">
        <StudentInfoTab 
          ref="infoTabRef"
          :student="student" 
          :student-id="studentId"
          @update:success="handleInfoUpdateSuccess"
        />
      </div>

      <!-- 积分 Tab -->
      <div v-if="activeTab === 'integral'">
        <StudentIntegralTab 
          :student-id="studentId"
          @update:success="handleIntegralUpdateSuccess"
        />
      </div>

      <!-- 订单 Tab -->
      <div v-if="activeTab === 'orders'" class="orders-content">
        <OrderTimeline :orders="orders" />
      </div>

      <!-- 课消 Tab -->
      <div v-if="activeTab === 'records'" class="records-content">
        <CourseRecordTab :student-id="studentId" />
      </div>

      <!-- 变更记录 Tab -->
      <div v-if="activeTab === 'changes'" class="changes-content">
        <ChangeTimeline :student-id="studentId" />
      </div>

      <!-- 作品 Tab -->
      <div v-if="activeTab === 'works'" class="works-content">
        <StudentWorksTab :student-id="studentId" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import CourseAccountCard from './CourseAccountCard.vue'
import StudentInfoTab from './StudentInfoTab.vue'
import StudentIntegralTab from './StudentIntegralTab.vue'
import OrderTimeline from './OrderTimeline.vue'
import CourseRecordTab from '@/views/CourseRecordTab.vue'
import ChangeTimeline from './ChangeTimeline.vue'
import StudentWorksTab from './StudentWorksTab.vue'

const props = defineProps({
  studentId: {
    type: Number,
    required: true
  },
  student: {
    type: Object,
    default: () => ({})
  },
  courses: {
    type: Array,
    default: () => []
  },
  orders: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits([
  'renew', 'refund', 'graduate', 'suspend',
  'transfer-hours', 'adjust-hours', 'gift-hours',
  'transfer-class', 'drop-class', 'assign-class', 'repay',
  'refresh'
])

// 选项卡配置
const tabs = [
  { name: 'courses', label: '课程账户' },
  { name: 'info', label: '基本信息' },
  { name: 'integral', label: '积分' },
  { name: 'orders', label: '订单' },
  { name: 'records', label: '课消' },
  { name: 'changes', label: '变更' },
  { name: 'works', label: '作品' }
]

// 当前激活的选项卡
const activeTab = ref('courses')

// 组件引用
const infoTabRef = ref(null)

// 保存选项卡状态到 sessionStorage
const STORAGE_KEY = `student_tab_${props.studentId}`

function saveTabState() {
  sessionStorage.setItem(STORAGE_KEY, activeTab.value)
}

function restoreTabState() {
  const saved = sessionStorage.getItem(STORAGE_KEY)
  if (saved && tabs.some(t => t.name === saved)) {
    activeTab.value = saved
  } else {
    activeTab.value = 'courses'
  }
}

// 监听选项卡变化，保存状态
watch(activeTab, () => {
  saveTabState()
})

// 组件挂载时恢复状态
onMounted(() => {
  restoreTabState()
})

// ========== 事件处理 ==========

/**
 * 基本信息保存成功后的处理
 */
async function handleInfoUpdateSuccess() {
  // 刷新父组件数据（学员信息、课程信息等）
  emit('refresh')
  
  // 刷新当前基本信息表单的数据
  setTimeout(() => {
    if (infoTabRef.value && typeof infoTabRef.value.refreshFormData === 'function') {
      infoTabRef.value.refreshFormData()
    }
    if (infoTabRef.value && typeof infoTabRef.value.refreshStudentInfo === 'function') {
      infoTabRef.value.refreshStudentInfo()
    }
  }, 100)
}

/**
 * 积分更新成功后的处理
 */
function handleIntegralUpdateSuccess() {
  emit('refresh')
}

/**
 * 课程卡片刷新（如修改有效期后）
 */
function handleCourseRefresh() {
  emit('refresh')
}

// 暴露刷新方法给父组件
defineExpose({
  refreshInfoTab: () => {
    if (infoTabRef.value && typeof infoTabRef.value.refreshStudentInfo === 'function') {
      infoTabRef.value.refreshStudentInfo()
    }
  }
})
</script>

<style scoped>
/* 样式保持不变 */
.student-detail-tabs {
  display: flex;
  height: 100%;
  min-height: 0;
}

.vertical-tabs {
  width: 90px;
  background: transparent;
  border-right: 1px solid var(--border-color);
  flex-shrink: 0;
}

.tab-item {
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  cursor: pointer;
  border-bottom: 1px solid var(--border-color);
  position: relative;
  transition: all 0.2s ease;
}

.tab-item:hover {
  background-color: var(--primary-bg);
  color: var(--primary-color);
}

.tab-item.active {
  background-color: var(--primary-bg);
  color: var(--primary-color);
  font-weight: 500;
}

.tab-item.active::after {
  content: '';
  position: absolute;
  right: 0;
  top: 0;
  width: 4px;
  height: 100%;
  background-color: var(--primary-color);
}

.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  min-width: 0;
}

.courses-content,
.orders-content,
.records-content,
.changes-content {
  width: 100%;
}

.course-cards {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>