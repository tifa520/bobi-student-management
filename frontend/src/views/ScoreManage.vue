<template>
  <div class="score-manage-modern">
    <!-- 顶部区域：周历 + 个人积分按钮 + 设置按钮 -->
    <div class="top-section">
      <div class="week-calendar-wrapper">
        <div class="week-calendar">
          <div class="week-header">
            <div class="week-days">
              <div
                v-for="day in weekDays"
                :key="day.date"
                class="week-day"
                :class="{ 'is-today': day.isToday, 'is-selected': selectedDate === day.date, 'has-schedule': day.hasSchedule }"
                @click="selectDate(day.date)"
              >
                <div class="day-name">{{ day.dayName }}</div>
                <div class="day-date">{{ day.dayOfMonth }}</div>
                <div class="day-dot" v-if="day.hasSchedule">
                  <span :class="{ 'dot-green': !day.allCompleted, 'dot-gray': day.allCompleted }"></span>
                </div>
                <div v-if="selectedDate === day.date" class="selected-line"></div>
              </div>
            </div>
            <div class="calendar-nav">
              <el-button @click="prevWeek" :icon="ArrowLeft" circle size="small" class="nav-btn" />
              <span class="week-range">{{ weekRange }}</span>
              <el-button @click="nextWeek" :icon="ArrowRight" circle size="small" class="nav-btn" />
              <el-button @click="goToday" size="small" class="today-btn">今天</el-button>
            </div>
          </div>
        </div>
      </div>
      <div class="personal-score-btn"><el-button type="primary" size="large" @click="openPersonalScoreModal"><el-icon><User /></el-icon>个人积分</el-button></div>
      <div class="settings-btn"><el-button size="large" @click="openSettingsModal"><el-icon><Setting /></el-icon>设置</el-button></div>
    </div>

    <div class="three-columns">
      <!-- 左侧：课次列表 -->
      <div class="column left-column">
        <div class="column-header"><span class="column-title">今日课次</span><span class="column-date">{{ selectedDate }}</span></div>
        <div class="session-list" v-loading="sessionsLoading">
          <div v-for="session in todaySessions" :key="session.schedule_id" class="session-item" :class="{ active: selectedSession?.schedule_id === session.schedule_id }" @click="selectSession(session)">
            <div class="session-info-row"><span class="session-time">{{ session.start_time }}</span><span class="session-name">{{ session.class_name }}</span><span class="session-course">{{ session.course_name }}</span><span class="session-teacher">{{ session.teacher_name }}</span></div>
          </div>
          <div v-if="todaySessions.length === 0 && !sessionsLoading" class="empty-tip"><el-icon><Calendar /></el-icon><span>暂无课次</span></div>
        </div>
      </div>

      <!-- 中间：积分操作板块 -->
      <div class="column middle-column">
        <div class="column-header"><span class="column-title">积分操作</span><span v-if="selectedSession" class="session-badge">{{ selectedSession.class_name }}</span></div>
        <div v-if="selectedSession" class="operation-area">
          <div class="student-list-header"><el-input v-model="studentSearch" placeholder="搜索学员" clearable prefix-icon="Search" size="small" style="width:200px" /></div>
          <div class="student-table-wrapper">
            <el-table :data="filteredStudents" v-loading="studentsLoading" border stripe @selection-change="handleSelectionChange">
              <el-table-column type="selection" width="45" />
              <el-table-column label="学员" min-width="160">
                <template #default="{ row }">
                  <div class="student-info-cell">
                    <AppImage :src="row.avatar" :size="28" shape="circle" />
                    <div class="student-name">{{ row.name }}</div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="total_integral" label="当前积分" min-width="100" />
            </el-table>
          </div>
        </div>
        <div v-else class="no-session-tip"><el-icon><Pointer /></el-icon><span>请先选择一个课次</span></div>
        <div class="action-buttons-bottom" v-if="selectedSession">
          <el-button type="success" @click="openBatchModal('reward')" style="flex:1">奖励</el-button>
          <el-button type="danger" @click="openBatchModal('penalty')" style="flex:1">扣分</el-button>
          <el-button type="warning" @click="openBatchModal('exchange')" style="flex:1">兑换</el-button>
        </div>
      </div>

      <!-- 右侧：积分排行榜 + 积分变动明细 -->
      <div class="column right-column">
        <div class="sub-column ranking-section">
          <div class="column-header"><span class="column-title">积分排行榜</span><el-button type="primary" link size="small" @click="refreshRanking"><el-icon><Refresh /></el-icon></el-button></div>
          <div class="ranking-list" v-loading="rankingLoading"><div v-for="(item, index) in rankingList" :key="item.id" class="ranking-item" :class="{ 'top-three': index < 3 }"><div class="rank-num" :class="getRankClass(index + 1)">{{ index + 1 }}</div><div class="rank-info"><span class="rank-name">{{ item.name }}</span><span class="rank-integral">{{ item.total_integral }} 分</span></div><div class="rank-medal" v-if="index === 0">🥇</div><div class="rank-medal" v-else-if="index === 1">🥈</div><div class="rank-medal" v-else-if="index === 2">🥉</div></div><div v-if="rankingList.length === 0 && !rankingLoading" class="empty-tip"><el-icon><Trophy /></el-icon><span>暂无积分数据</span></div></div>
        </div>
        <div class="sub-column detail-section">
          <div class="column-header"><span class="column-title">积分变动明细（今日）</span><el-button type="primary" link size="small" @click="refreshAllDetails"><el-icon><Refresh /></el-icon></el-button></div>
          <div class="detail-list" v-loading="detailLoading"><div v-for="record in allDetails" :key="record.id" class="detail-item"><div class="detail-student">{{ record.student_name }}</div><div class="detail-type"><el-tag :type="getDetailTagType(record)" size="small">{{ getDetailTypeLabel(record) }}</el-tag></div><div class="detail-reason">{{ record.reason }}</div><div class="detail-change" :class="record.change_amount > 0 ? 'text-success' : 'text-danger'">{{ record.change_amount > 0 ? '+' : '' }}{{ record.change_amount }}</div></div><div v-if="allDetails.length === 0 && !detailLoading" class="empty-tip"><el-icon><Document /></el-icon><span>暂无积分变动</span></div></div>
        </div>
      </div>
    </div>

    <!-- 批量操作模态框 -->
    <el-dialog v-model="batchModalVisible" :title="batchModalTitle" width="800px" :close-on-click-modal="false"><div class="batch-modal-content"><div class="modal-desc">确认对以下学员进行积分{{ batchTypeLabel }}：</div><el-table :data="selectedStudentsForBatch" border stripe><el-table-column prop="name" label="学员姓名" width="120" /><el-table-column prop="total_integral" label="当前积分" width="100" /><el-table-column label="积分变动（正整数）" width="150"><template #default="{ row, $index }"><el-input-number v-model="batchForm[$index].scoreChange" :min="1" :step="1" controls-position="right" size="small" style="width:120px" /></template></el-table-column><el-table-column label="变动原因" min-width="180"><template #default="{ row, $index }"><el-select v-model="batchForm[$index].reason" placeholder="请选择" size="small" style="width:140px"><el-option v-for="r in reasonOptions[batchType]" :key="r" :label="r" :value="r" /></el-select></template></el-table-column><el-table-column label="备注" min-width="150"><template #default="{ row, $index }"><el-input v-model="batchForm[$index].remark" placeholder="选填" size="small" /></template></el-table-column></el-table></div><template #footer><el-button @click="batchModalVisible = false">取消</el-button><el-button type="primary" @click="confirmBatch" :loading="batchSubmitting">确认</el-button></template></el-dialog>

    <!-- 个人积分模态框 -->
    <el-dialog v-model="personalScoreModalVisible" title="个人积分操作" width="600px"><div class="personal-score-modal"><div class="student-search-area"><StudentPicker v-model="selectedStudentId" placeholder="搜索学员姓名或手机号" @student-selected="onStudentSelectedForPersonal" /></div><div v-if="selectedStudentForPersonal" class="personal-score-form"><el-descriptions :column="2" border><el-descriptions-item label="学员姓名">{{ selectedStudentForPersonal.name }}</el-descriptions-item><el-descriptions-item label="当前积分" :span="2"><span class="current-score">{{ selectedStudentForPersonal.total_integral }} 分</span></el-descriptions-item></el-descriptions><el-form :model="personalScoreForm" label-width="80px" style="margin-top:20px"><el-form-item label="操作类型"><el-select v-model="personalScoreForm.scoreType" @change="onPersonalScoreTypeChange"><el-option v-for="type in scoreTypes" :key="type.value" :label="type.label" :value="type.value" /></el-select></el-form-item><el-form-item label="积分变动"><el-input-number v-model="personalScoreForm.scoreChange" :min="1" :step="1" :controls="false" /></el-form-item><el-form-item label="变动原因"><el-select v-model="personalScoreForm.reason" placeholder="请选择" style="width:100%"><el-option v-for="r in reasonOptions[personalScoreForm.scoreType]" :key="r" :label="r" :value="r" /></el-select></el-form-item><el-form-item label="备注"><el-input v-model="personalScoreForm.remark" placeholder="选填" /></el-form-item></el-form></div></div><template #footer><el-button @click="personalScoreModalVisible = false">取消</el-button><el-button type="primary" @click="submitPersonalScore" :loading="personalSubmitting">确认</el-button></template></el-dialog>

    <!-- 设置模态框 -->
    <el-dialog v-model="settingsModalVisible" title="积分设置" width="700px"><div class="settings-modal"><el-tabs v-model="settingsTab"><el-tab-pane label="操作类型" name="types"><div class="settings-list"><div v-for="(type, index) in scoreTypes" :key="type.value" class="settings-item"><el-input v-model="type.label" placeholder="类型名称" style="width:200px" /><el-button type="danger" link @click="removeScoreType(index)" style="margin-left:12px">删除</el-button></div><el-button type="primary" link @click="addScoreType" style="margin-top:12px"><el-icon><Plus /></el-icon> 添加操作类型</el-button></div></el-tab-pane><el-tab-pane label="变动原因" name="reasons"><div class="settings-reasons"><div v-for="(type, typeIdx) in scoreTypes" :key="type.value" class="reason-group"><div class="reason-group-title">{{ type.label }}</div><div class="reason-list"><div v-for="(reason, reasonIdx) in reasonOptions[type.value]" :key="reasonIdx" class="reason-item"><el-input v-model="reasonOptions[type.value][reasonIdx]" size="small" style="width:200px" /><el-button type="danger" link @click="removeReason(type.value, reasonIdx)">删除</el-button></div><el-button type="primary" link size="small" @click="addReason(type.value)" class="add-reason-btn"><el-icon><Plus /></el-icon> 添加原因</el-button></div></div></div></el-tab-pane></el-tabs></div><template #footer><el-button @click="settingsModalVisible = false">取消</el-button><el-button type="primary" @click="saveSettings">保存设置</el-button></template></el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight, User, Calendar, Pointer, Refresh, Trophy, Setting, Plus, Document } from '@element-plus/icons-vue'
import StudentPicker from '@/components/StudentPicker.vue'
import { getAttendanceClasses, getClassStudents } from '@/api/attendance'
import { getScoreRanking, batchSubmitScore, submitScore, getStudentScore, getIntegralRecords } from '@/api/score'
import dayjs from 'dayjs'
import isoWeek from 'dayjs/plugin/isoWeek'

dayjs.extend(isoWeek)

const STORAGE_KEY = 'score_settings'
const defaultScoreTypes = [{ label: '奖励', value: 'reward' }, { label: '扣分', value: 'penalty' }, { label: '兑换', value: 'exchange' }]
const defaultReasonOptions = { reward: ['上课表现优秀', '作业完成优秀', '活动参与', '报名奖励', '续费奖励', '推荐奖励', '其他奖励'], penalty: ['上课迟到', '作业未完成', '违反纪律', '缺勤', '其他扣分'], exchange: ['礼物兑换', '课程兑换', '活动抵扣', '其他兑换'] }
function loadSettings() { try { const saved = localStorage.getItem(STORAGE_KEY); if (saved) { const data = JSON.parse(saved); scoreTypes.value = data.scoreTypes || defaultScoreTypes; reasonOptions.value = data.reasonOptions || defaultReasonOptions } } catch (e) { console.error(e) } }
function saveSettingsToLocal() { localStorage.setItem(STORAGE_KEY, JSON.stringify({ scoreTypes: scoreTypes.value, reasonOptions: reasonOptions.value })) }
const scoreTypes = ref([...defaultScoreTypes])
const reasonOptions = ref(JSON.parse(JSON.stringify(defaultReasonOptions)))

const selectedDate = ref(dayjs().format('YYYY-MM-DD'))
const weekDays = ref([])
const currentMonday = ref(dayjs().startOf('week').add(1, 'day'))
const weekRange = computed(() => `${currentMonday.value.format('M月D日')} - ${currentMonday.value.add(6, 'day').format('M月D日')}`)
async function loadWeekScheduleStatus() {
  const start = currentMonday.value; const weekDaysTemp = []
  for (let i = 0; i < 7; i++) {
    const d = start.add(i, 'day'); const dateStr = d.format('YYYY-MM-DD'); let hasSchedule = false, allCompleted = true
    try { const res = await getAttendanceClasses(dateStr); const sessions = res.data || []; hasSchedule = sessions.length > 0; allCompleted = sessions.every(s => s.status === 'completed') } catch (e) { console.error(e) }
    weekDaysTemp.push({ date: dateStr, dayName: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][i], dayOfMonth: d.date(), isToday: d.isSame(dayjs(), 'day'), hasSchedule, allCompleted })
  }
  weekDays.value = weekDaysTemp
}
function selectDate(date) {
  selectedDate.value = date
  selectedSession.value = null  // 清空选中的课次
  studentList.value = []        // 清空学员列表
  loadTodaySessions()
  loadAllDetails()
}
function prevWeek() { currentMonday.value = currentMonday.value.subtract(7, 'day'); loadWeekScheduleStatus(); selectedDate.value = currentMonday.value.add(3, 'day').format('YYYY-MM-DD'); loadTodaySessions(); loadAllDetails() }
function nextWeek() { currentMonday.value = currentMonday.value.add(7, 'day'); loadWeekScheduleStatus(); selectedDate.value = currentMonday.value.add(3, 'day').format('YYYY-MM-DD'); loadTodaySessions(); loadAllDetails() }
function goToday() { currentMonday.value = dayjs().startOf('week').add(1, 'day'); loadWeekScheduleStatus(); selectedDate.value = dayjs().format('YYYY-MM-DD'); loadTodaySessions(); loadAllDetails() }

const todaySessions = ref([])
const sessionsLoading = ref(false)
const selectedSession = ref(null)
async function loadTodaySessions() {
  sessionsLoading.value = true
  try { const res = await getAttendanceClasses(selectedDate.value); todaySessions.value = res.data || []; if (todaySessions.value.length > 0 && !selectedSession.value) selectSession(todaySessions.value[0]); else if (todaySessions.value.length === 0) selectedSession.value = null } catch (e) { console.error(e) } finally { sessionsLoading.value = false }
}
async function selectSession(session) { selectedSession.value = session; await loadStudentsForSession(session.schedule_id) }

const studentList = ref([])
const studentsLoading = ref(false)
const studentSearch = ref('')
const selectedStudents = ref([])
const batchModalVisible = ref(false)
const batchType = ref('reward')
const selectedStudentsForBatch = ref([])
const batchForm = ref([])
const batchSubmitting = ref(false)

async function loadStudentsForSession(scheduleId) {
  studentsLoading.value = true
  try {
    const res = await getClassStudents(scheduleId)
    const students = (res.data || []).map(s => ({ student_id: s.student_id, name: s.name, phone: s.phone, avatar: s.avatar, total_integral: s.total_integral || 0 }))
    const promises = students.map(async (student) => { try { const scoreRes = await getStudentScore(student.student_id); student.total_integral = scoreRes.data?.total_integral || 0 } catch (e) { console.error(e) } })
    await Promise.all(promises)
    studentList.value = students
  } catch (e) { studentList.value = [] } finally { studentsLoading.value = false }
}
const filteredStudents = computed(() => { let list = studentList.value; if (studentSearch.value) { const kw = studentSearch.value.toLowerCase(); list = list.filter(s => s.name.toLowerCase().includes(kw) || (s.phone && s.phone.includes(kw))) } return list })
function handleSelectionChange(selection) { selectedStudents.value = selection }
function openBatchModal(type) {
  if (selectedStudents.value.length === 0) { ElMessage.warning('请先选择学员'); return }
  batchType.value = type; selectedStudentsForBatch.value = [...selectedStudents.value]; batchForm.value = selectedStudentsForBatch.value.map(() => ({ scoreChange: 0, reason: '', remark: '' })); batchModalVisible.value = true
}
const batchModalTitle = computed(() => ({ reward: '奖励', penalty: '扣分', exchange: '兑换' }[batchType.value]))
const batchTypeLabel = computed(() => ({ reward: '奖励', penalty: '扣分', exchange: '兑换' }[batchType.value]))
async function confirmBatch() {
  for (let i = 0; i < batchForm.value.length; i++) { const item = batchForm.value[i]; if (item.scoreChange <= 0) { ElMessage.warning(`请为学员 ${selectedStudentsForBatch.value[i].name} 填写正整数的积分变动值`); return } if (!item.reason) { ElMessage.warning(`请为学员 ${selectedStudentsForBatch.value[i].name} 选择变动原因`); return } }
  batchSubmitting.value = true
  try {
    const items = batchForm.value.map((item, idx) => { const student = selectedStudentsForBatch.value[idx]; let changeAmount = item.scoreChange; if (batchType.value === 'penalty' || batchType.value === 'exchange') changeAmount = -Math.abs(changeAmount); return { student_id: student.student_id, change_amount: changeAmount, reason: item.reason, remark: item.remark || '' } })
    await batchSubmitScore({ items })
    ElMessage.success(`成功更新 ${items.length} 位学员的积分`)
    for (let i = 0; i < items.length; i++) { const item = items[i]; const student = studentList.value.find(s => s.student_id === item.student_id); if (student) student.total_integral += item.change_amount }
    batchModalVisible.value = false; await refreshRanking(); await loadAllDetails()
  } catch (e) { ElMessage.error('提交失败') } finally { batchSubmitting.value = false }
}

const allDetails = ref([])
const detailLoading = ref(false)
function getDetailTypeLabel(record) { if (record.change_amount > 0) return '奖励'; if (record.change_amount < 0) return record.reason?.includes('礼物') || record.reason?.includes('兑换') ? '兑换' : '扣分'; return '' }
function getDetailTagType(record) { if (record.change_amount > 0) return 'success'; if (record.change_amount < 0) return (record.reason?.includes('礼物') || record.reason?.includes('兑换')) ? 'warning' : 'danger'; return 'info' }
async function fetchAllDetails() {
  detailLoading.value = true; const today = dayjs().format('YYYY-MM-DD'); let allRecords = []
  try { for (let page = 1; page <= 3; page++) { const res = await getIntegralRecords({ start_date: today, end_date: today, page: page, page_size: 100 }); const records = res.data?.items || []; if (records.length === 0) break; allRecords = [...allRecords, ...records] } const unique = new Map(); for (const r of allRecords) if (!unique.has(r.id)) unique.set(r.id, r); allDetails.value = Array.from(unique.values()).sort((a, b) => new Date(b.created_at) - new Date(a.created_at)) } catch (e) { allDetails.value = [] } finally { detailLoading.value = false } }
async function loadAllDetails() { await fetchAllDetails() }
function refreshAllDetails() { loadAllDetails() }

const rankingList = ref([])
const rankingLoading = ref(false)
async function refreshRanking() { rankingLoading.value = true; try { const res = await getScoreRanking(); rankingList.value = (res.data || []).slice(0, 10) } catch (e) { console.error(e) } finally { rankingLoading.value = false } }
function getRankClass(rank) { if (rank === 1) return 'rank-1'; if (rank === 2) return 'rank-2'; if (rank === 3) return 'rank-3'; return '' }

const personalScoreModalVisible = ref(false)
const selectedStudentId = ref(null)
const selectedStudentForPersonal = ref(null)
const personalSubmitting = ref(false)
const personalScoreForm = reactive({ scoreType: 'reward', scoreChange: 0, reason: '', remark: '' })
function openPersonalScoreModal() { selectedStudentId.value = null; selectedStudentForPersonal.value = null; personalScoreForm.scoreType = 'reward'; personalScoreForm.scoreChange = 0; personalScoreForm.reason = ''; personalScoreForm.remark = ''; personalScoreModalVisible.value = true }
async function onStudentSelectedForPersonal(student) { if (!student) { selectedStudentForPersonal.value = null; return } try { const res = await getStudentScore(student.id); selectedStudentForPersonal.value = { ...student, total_integral: res.data?.total_integral || 0 } } catch (e) { ElMessage.error('获取学员积分失败') } }
function onPersonalScoreTypeChange() { personalScoreForm.scoreChange = 0; personalScoreForm.reason = '' }
async function submitPersonalScore() {
  if (!selectedStudentForPersonal.value) { ElMessage.warning('请选择学员'); return }
  if (personalScoreForm.scoreChange <= 0) { ElMessage.warning('积分变动必须为正整数'); return }
  if (!personalScoreForm.reason) { ElMessage.warning('请选择变动原因'); return }
  let changeAmount = personalScoreForm.scoreChange; if (personalScoreForm.scoreType === 'penalty' || personalScoreForm.scoreType === 'exchange') changeAmount = -Math.abs(changeAmount)
  personalSubmitting.value = true
  try {
    await submitScore([{ student_id: selectedStudentForPersonal.value.id, change_amount: changeAmount, reason: personalScoreForm.reason, remark: personalScoreForm.remark }])
    ElMessage.success('积分更新成功'); personalScoreModalVisible.value = false; if (selectedSession.value) await loadStudentsForSession(selectedSession.value.schedule_id); await refreshRanking(); await loadAllDetails()
  } catch (e) { ElMessage.error('更新失败') } finally { personalSubmitting.value = false }
}

const settingsModalVisible = ref(false)
const settingsTab = ref('types')
function openSettingsModal() { settingsModalVisible.value = true }
function addScoreType() { const newValue = `type_${Date.now()}`; scoreTypes.value.push({ label: '新类型', value: newValue }); if (!reasonOptions.value[newValue]) reasonOptions.value[newValue] = [] }
function removeScoreType(index) { const type = scoreTypes.value[index]; if (type.value === 'reward' || type.value === 'penalty' || type.value === 'exchange') { ElMessage.warning('默认类型不能删除'); return }; scoreTypes.value.splice(index, 1); delete reasonOptions.value[type.value] }
function addReason(typeValue) { if (!reasonOptions.value[typeValue]) reasonOptions.value[typeValue] = []; reasonOptions.value[typeValue].push('新原因') }
function removeReason(typeValue, index) { reasonOptions.value[typeValue].splice(index, 1) }
function saveSettings() { saveSettingsToLocal(); ElMessage.success('设置已保存'); settingsModalVisible.value = false }

watch(selectedDate, () => { loadTodaySessions(); loadAllDetails() })
watch(selectedSession, () => { if (selectedSession.value) loadAllDetails() })
onMounted(() => { loadSettings(); loadWeekScheduleStatus(); loadTodaySessions(); refreshRanking(); loadAllDetails() })
</script>

<style scoped>
/* 整体布局 */
.score-manage-modern {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 0;
  overflow: hidden;
}

/* 顶部区域 */
.top-section {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--surface);
  padding: 16px 20px;
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  flex-shrink: 0;
}

/* 周历容器 */
.week-calendar-wrapper {
  flex: 1;
}

.week-calendar {
  background: white;
  border-radius: var(--radius-md);
}

/* 周历头部：星期行 + 导航按钮在同一行 */
.week-header {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.week-days {
  display: flex;
  gap: 12px;
}

/* 圆形周历单元 */
.week-day {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  text-align: center;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, var(--surface-soft) 0%, var(--gray-200) 100%);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.week-day:hover {
  background: linear-gradient(135deg, var(--brand-500) 0%, var(--brand-600) 50%, var(--brand-800) 100%);
  transform: translateY(-4px) scale(1.05);
  box-shadow: 0 8px 16px rgba(54, 180, 89, 0.3);
}

.week-day:hover .day-name,
.week-day:hover .day-date {
  color: white;
}

.week-day.is-selected {
  background: linear-gradient(135deg, var(--brand-500) 0%, var(--brand-600) 50%, var(--brand-800) 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(54, 180, 89, 0.25);
}

.week-day.is-selected .day-name,
.week-day.is-selected .day-date {
  color: white;
}

.week-day.is-today .day-date {
  color: var(--brand-500);
  font-weight: 600;
}

.week-day.is-selected.is-today .day-date {
  color: white;
}

.day-name {
  font-size: 12px;
  color: var(--text-placeholder);
  margin-bottom: 4px;
  transition: color 0.2s;
}

.day-date {
  font-size: 18px;
  font-weight: 500;
  margin: 0;
  color: var(--text-primary);
  transition: color 0.2s;
}

/* 状态点 - 使用 margin 定位，不用 absolute */
.day-dot {
  margin-top: 4px;
  height: 6px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.dot-green {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--brand-500);
}

.dot-gray {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--gray-4);
}

.selected-line {
  display: none;
}

/* 圆形按钮样式，覆盖外部 .el-button--small 的椭圆效果 */
.nav-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  padding: 0;
  background: var(--surface-soft);
  border: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.nav-btn:hover {
  background: var(--primary-bg);
  color: var(--brand-500);
}

.calendar-nav {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.week-range {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.today-btn {
  background: var(--primary-bg);
  color: var(--brand-500);
  border: none;
  border-radius: var(--radius-pill);
  height: 32px;
  padding: 0 12px;
}

.personal-score-btn,
.settings-btn {
  flex-shrink: 0;
}

/* 三列布局 */
.three-columns {
  flex: 1;
  display: flex;
  gap: 16px;
  min-height: 0;
}

.column {
  background: var(--surface);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.left-column { width: 30%; }
.middle-column { width: 40%; }
.right-column { width: 30%; }

/* 右侧上下分区：排行榜60%，明细40% */
.right-column {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.sub-column {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: inherit;
  border-radius: inherit;
}
.ranking-section {
  flex: 6;  /* 60% */
  min-height: 0;
}
.detail-section {
  flex: 4;  /* 40% */
  min-height: 0;
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}
.column-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}
.session-badge {
  font-size: 13px;
  color: var(--brand-500);
  background: var(--primary-bg);
  padding: 4px 12px;
  border-radius: 20px;
}

/* 左侧课次列表 */
.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}
.session-item {
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid var(--border-color);
}
.session-item:hover {
  background: var(--surface-soft);
  border-color: var(--brand-500);
}
.session-item.active {
  background: var(--primary-bg);
  border-color: var(--brand-500);
}
.session-info-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: nowrap;
}
.session-time {
  font-size: 14px;
  font-weight: 500;
  color: var(--brand-500);
  min-width: 60px;
}
.session-name {
  font-weight: 500;
  min-width: 100px;
}
.session-course {
  color: var(--text-secondary);
  min-width: 80px;
}
.session-teacher {
  color: var(--text-placeholder);
  font-size: 13px;
}

/* 中间操作区 */
.operation-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 16px;
}
.student-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.student-table-wrapper {
  flex: 1;
  overflow-y: auto;
}
.action-buttons-bottom {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  border-top: 1px solid var(--border-color);
  background: var(--surface);
  flex-shrink: 0;
}
.no-session-tip {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--text-placeholder);
}
.no-session-tip .el-icon {
  font-size: 48px;
}

/* 积分排行榜列表 */
.ranking-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}
.ranking-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  margin-bottom: 8px;
  border-radius: 8px;
  background: var(--surface-soft);
}
.ranking-item.top-three {
  background: linear-gradient(135deg, rgba(217, 150, 40, 0.14), var(--surface));
  border: 1px solid rgba(217, 150, 40, 0.42);
}
.rank-num {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-weight: 600;
  background: var(--gray-200);
  color: var(--text-secondary);
}
.rank-num.rank-1 {
  background: linear-gradient(135deg, var(--warning), rgba(217, 150, 40, 0.82));
  color: white;
}
.rank-num.rank-2 {
  background: linear-gradient(135deg, var(--gray-300), var(--gray-400));
  color: white;
}
.rank-num.rank-3 {
  background: linear-gradient(135deg, rgba(217, 150, 40, 0.78), var(--brand-800));
  color: white;
}
.rank-info {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.rank-name {
  font-weight: 500;
}
.rank-integral {
  color: var(--brand-500);
  font-weight: 600;
}
.rank-medal {
  font-size: 20px;
}

/* 积分变动明细列表 */
.detail-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}
.detail-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-light);
  font-size: 13px;
}
.detail-student {
  width: 100px;
  font-weight: 500;
  color: var(--text-primary);
}
.detail-type {
  width: 70px;
}
.detail-reason {
  flex: 1;
  color: var(--text-secondary);
}
.detail-change {
  width: 70px;
  text-align: right;
  font-weight: 500;
}

/* 模态框通用 */
.batch-modal-content {
  max-height: 500px;
  overflow-y: auto;
}
.modal-desc {
  margin-bottom: 16px;
  font-size: 14px;
  color: var(--text-secondary);
}
.current-score {
  font-size: 16px;
  font-weight: 600;
  color: var(--brand-500);
}
.settings-modal {
  max-height: 500px;
  overflow-y: auto;
}
.settings-list {
  padding: 12px;
}
.settings-item {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}
.settings-reasons {
  padding: 12px;
}
.reason-group {
  margin-bottom: 20px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 12px;
}
.reason-group-title {
  font-weight: 600;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
}
.reason-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.reason-item {
  display: flex;
  align-items: center;
  gap: 12px;
}
.add-reason-btn {
  font-size: 14px;
}
.empty-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--text-placeholder);
  gap: 8px;
}
.empty-tip .el-icon {
  font-size: 36px;
}
.text-success {
  color: var(--success);
}
.text-danger {
  color: var(--danger);
}
.student-info-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}
.student-avatar {
  flex-shrink: 0;
}
.student-name-detail {
  display: flex;
  flex-direction: column;
}
.student-name {
  font-weight: 500;
}
.student-phone {
  font-size: 12px;
  color: var(--text-secondary);
}
.rank-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.rank-avatar {
  flex-shrink: 0;
}
</style>