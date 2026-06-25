<template>
  <div class="right-content">
    <div class="attendance-header">
      <el-tabs v-model="localRightTab" class="right-tabs" @tab-click="onRightTabClick">
        <el-tab-pane v-if="showPendingTab" name="pending" label="待考勤" />
        <el-tab-pane name="present" label="出勤" />
        <el-tab-pane name="absent" label="缺勤" />
      </el-tabs>
    </div>

    <div class="temp-enroll-btn-wrapper">
      <el-button class="temp-enroll-btn" @click="emit('open-temp-enroll')">临时插班</el-button>
    </div>

    <!-- 子页签 -->
    <div class="sub-tabs" v-if="localRightTab === 'pending'">
      <el-tabs v-model="localSubTabPending" class="sub-tab-tabs" @tab-click="onSubTabClick">
        <el-tab-pane :label="`待考勤 (${subPendingCount})`" name="pending" />
        <el-tab-pane label="请假待确认" name="leave_confirm" />
        <el-tab-pane label="预约体验" name="trial" />
      </el-tabs>
    </div>
    <div class="sub-tabs" v-else-if="localRightTab === 'present'">
      <el-tabs v-model="localSubTabPresent" class="sub-tab-tabs" @tab-click="onSubTabClick">
        <el-tab-pane :label="`出勤 (${subPresentCount})`" name="present" />
        <el-tab-pane :label="`迟到 (${subLateCount})`" name="late" />
        <el-tab-pane :label="`临时插班 (${subTempCount})`" name="temp" />
        <el-tab-pane label="预约体验" name="trial" />
      </el-tabs>
    </div>
    <div class="sub-tabs" v-else-if="localRightTab === 'absent'">
      <el-tabs v-model="localSubTabAbsent" class="sub-tab-tabs" @tab-click="onSubTabClick">
        <el-tab-pane :label="`请假 (${subLeaveCount})`" name="leave" />
        <el-tab-pane :label="`未到 (${subAbsentCount})`" name="absent" />
        <el-tab-pane label="预约未到" name="trial_absent" />
      </el-tabs>
    </div>

    <div class="search-bar">
      <el-input v-model="localSearchKeyword" placeholder="请输入学员姓名或联系方式" clearable size="large" style="width:100%" />
    </div>

    <div class="student-table-wrapper">
      <el-table :data="paginatedFilteredList" v-loading="studentLoading" border stripe @selection-change="onSelectionChange" class="student-table">
        <!-- 待考勤页签 -->
        <template v-if="localRightTab === 'pending' && localSubTabPending === 'pending'">
          <el-table-column type="selection" width="45" />
          <el-table-column label="学员信息" min-width="180">
            <template #default="{ row }">
              <div class="student-info-cell">
                <AppImage :src="row.avatar" :size="28" shape="circle" />
                <div class="student-name-detail">
                  <div class="student-name">{{ row.name }}</div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="剩余课时" min-width="100"><template #default="{ row }">{{ row.remaining_hours }}课时</template></el-table-column>
          <el-table-column label="请假/限制次数" min-width="120"><template #default="{ row }">{{ row.leave_display || '-' }}</template></el-table-column>
        </template>

        <!-- 出勤页签 -->
        <template v-if="localRightTab === 'present' && (localSubTabPresent === 'present' || localSubTabPresent === 'late' || localSubTabPresent === 'temp')">
          <el-table-column label="学员信息" min-width="180">
            <template #default="{ row }">
              <div class="student-info-cell">
                <AppImage :src="row.avatar" :size="28" shape="circle" />
                <div class="student-name-detail">
                  <div class="student-name">{{ row.name }}</div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="扣课时数" min-width="100"><template #default="{ row }"><span v-if="row.status === '请假' || row.status === '未到'">0</span><span v-else-if="row.deduct_hours !== undefined && row.deduct_hours !== null">{{ row.deduct_hours }}</span><span v-else>-</span></template></el-table-column>
          <el-table-column label="备注" min-width="150"><template #default="{ row }">{{ row.remark || '-' }}</template></el-table-column>
          <el-table-column label="操作" width="80" fixed="right"><template #default="{ row }"><el-button v-if="row.attendance_id" link type="primary" size="small" @click="emit('edit-attendance', row)"><el-icon><Edit /></el-icon></el-button></template></el-table-column>
        </template>

        <!-- 缺勤页签 -->
        <template v-if="localRightTab === 'absent' && (localSubTabAbsent === 'leave' || localSubTabAbsent === 'absent')">
          <el-table-column label="学员信息" min-width="180">
            <template #default="{ row }">
              <div class="student-info-cell">
                <AppImage :src="row.avatar" :size="32" class="student-avatar" />
                <div class="student-name-detail">
                  <div class="student-name">{{ row.name }}</div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="扣课时数" min-width="100"><template><span>0</span></template></el-table-column>
          <el-table-column label="备注" min-width="150"><template #default="{ row }">{{ row.remark || '-' }}</template></el-table-column>
          <el-table-column label="操作" width="80" fixed="right"><template #default="{ row }"><el-button v-if="row.attendance_id" link type="primary" size="small" @click="emit('edit-attendance', row)"><el-icon><Edit /></el-icon></el-button></template></el-table-column>
        </template>

        <template v-if="(localRightTab === 'pending' && localSubTabPending !== 'pending') || (localRightTab === 'present' && localSubTabPresent === 'trial') || (localRightTab === 'absent' && localSubTabAbsent === 'trial_absent')">
          <el-table-column><template><div class="placeholder-tip">功能开发中，敬请期待</div></template></el-table-column>
        </template>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Edit } from '@element-plus/icons-vue'
// 无需导入 DEFAULT_AVATAR_SVG，AppImage 内部处理

const props = defineProps({
  studentList: { type: Array, default: () => [] },
  studentLoading: { type: Boolean, default: false },
  rightTab: { type: String, default: 'pending' },
  subTabPending: { type: String, default: 'pending' },
  subTabPresent: { type: String, default: 'present' },
  subTabAbsent: { type: String, default: 'leave' },
  searchKeyword: { type: String, default: '' },
  paginatedFilteredList: { type: Array, default: () => [] },
  selectedStudents: { type: Array, default: () => [] }
})

const emit = defineEmits([
  'update:rightTab', 'update:subTabPending', 'update:subTabPresent', 'update:subTabAbsent',
  'update:searchKeyword', 'selection-change', 'edit-attendance', 'open-temp-enroll'
])

const localRightTab = computed({ get: () => props.rightTab, set: (val) => emit('update:rightTab', val) })
const localSubTabPending = computed({ get: () => props.subTabPending, set: (val) => emit('update:subTabPending', val) })
const localSubTabPresent = computed({ get: () => props.subTabPresent, set: (val) => emit('update:subTabPresent', val) })
const localSubTabAbsent = computed({ get: () => props.subTabAbsent, set: (val) => emit('update:subTabAbsent', val) })
const localSearchKeyword = computed({ get: () => props.searchKeyword, set: (val) => emit('update:searchKeyword', val) })

const subPendingCount = computed(() => props.studentList.filter(s => !s.attendance_id || s.status === '未考勤').length)
const subPresentCount = computed(() => props.studentList.filter(s => s.status === '出勤').length)
const subLateCount = computed(() => props.studentList.filter(s => s.status === '迟到').length)
const subTempCount = computed(() => props.studentList.filter(s => s.is_temporary === true).length)
const subLeaveCount = computed(() => props.studentList.filter(s => s.status === '请假').length)
const subAbsentCount = computed(() => props.studentList.filter(s => s.status === '未到').length)
const showPendingTab = computed(() => subPendingCount.value > 0)

function onSelectionChange(selection) { emit('selection-change', selection) }
function onRightTabClick() { emit('update:searchKeyword', '') }
function onSubTabClick() { emit('update:searchKeyword', '') }
</script>

<style scoped>
.right-content { flex: 1; display: flex; flex-direction: column; padding: 0 var(--spacing-4); }
.right-tabs :deep(.el-tabs__header) { height: 60px; margin: 0; width: 100%; }
.right-tabs :deep(.el-tabs__nav) { display: flex; width: 100%; }
.right-tabs :deep(.el-tabs__item) { flex: 1; text-align: center; height: 60px; line-height: 60px; }
.temp-enroll-btn-wrapper { margin: var(--spacing-5) 0; }
.temp-enroll-btn { width: 88px; background: transparent; border-color: var(--primary); color: var(--primary); }
.temp-enroll-btn:hover { background: var(--primary); color: var(--bg-white); }
.sub-tabs { margin-bottom: var(--spacing-3); }
.sub-tab-tabs :deep(.el-tabs__nav) { display: flex; width: 100%; }
.sub-tab-tabs :deep(.el-tabs__item) { flex: 1; text-align: center; font-size: 14px; height: 36px; line-height: 36px; }
.sub-tab-tabs :deep(.el-tabs__item.is-active) { color: var(--primary); font-weight: 500; }
.search-bar { margin-bottom: var(--spacing-3); }
.search-bar :deep(.el-input__wrapper) { height: 40px; }
.student-table-wrapper { flex: 1; overflow-y: auto; }
.student-table { width: 100%; }
.student-info-cell { display: flex; align-items: center; gap: 10px; }
.student-avatar { flex-shrink: 0; }
.student-name { font-weight: 500; }
.placeholder-tip { text-align: center; padding: 40px; color: var(--text-tertiary); }
</style>