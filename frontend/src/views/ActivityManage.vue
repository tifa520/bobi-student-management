<template>
  <div class="activity-manage">
    <!-- 操作栏 -->
    <div class="action-bar">
      <div class="left-actions">
        <el-button type="primary" size="default" @click="createNewActivity">+ 新增活动</el-button>
        <el-button v-if="showArchived" size="default" @click="toggleArchived(false)">返回活动列表</el-button>
      </div>
      <div class="right-actions">
        <el-input
          v-model="filters.keyword"
          placeholder="搜索活动名称"
          clearable
          prefix-icon="Search"
          style="width: 200px"
          size="default"
          @input="handleSearch"
        />
        <el-select
          v-model="filters.status"
          placeholder="活动状态"
          clearable
          size="default"
          style="width: 140px"
          @change="fetchActivities"
        >
          <el-option label="草稿" value="draft" />
          <el-option label="报名中" value="registering" />
          <el-option label="待开始" value="upcoming" />
          <el-option label="进行中" value="ongoing" />
          <el-option label="已结束" value="ended" />
          <el-option label="已取消" value="cancelled" />
        </el-select>
        <el-select
          v-model="filters.activity_type"
          placeholder="活动类型"
          clearable
          size="default"
          style="width: 120px"
          @change="fetchActivities"
        >
          <el-option label="音乐会" value="音乐会" />
          <el-option label="画展" value="画展" />
          <el-option label="比赛" value="比赛" />
          <el-option label="研学" value="研学" />
          <el-option label="试听课" value="试听课" />
          <el-option label="生日会" value="生日会" />
          <el-option label="其他" value="其他" />
        </el-select>
        <el-button type="primary" size="default" @click="fetchActivities">查询</el-button>
        <el-button size="default" @click="resetFilters">重置</el-button>
        <el-button type="info" plain size="default" @click="viewArchived">查看归档</el-button>
      </div>
    </div>

    <!-- 活动卡片网格 -->
    <div class="activity-grid" v-loading="loading">
      <div v-if="activities.length === 0" class="empty-state">
        <el-empty description="暂无活动">
          <el-button type="primary" size="default" @click="createNewActivity">立即创建</el-button>
        </el-empty>
      </div>
      <div
        v-for="item in activities"
        :key="item.id"
        class="activity-card"
        @click="goToDetail(item.id)"
      >
        <!-- 封面图 -->
        <div class="activity-cover">
          <el-image
            v-if="item.cover_image"
            :src="item.cover_image"
            fit="cover"
            class="cover-img"
          />
          <div v-else class="cover-placeholder">
            <el-icon><Picture /></el-icon>
          </div>
          <div class="cover-status" :class="getStatusClass(item.status)">
            {{ getStatusLabel(item.status) }}
          </div>
        </div>

        <!-- 信息区 -->
        <div class="activity-info">
          <div class="info-header">
            <span class="activity-name">{{ item.name }}</span>
            <div class="info-tags">
              <el-tag size="default" type="info">{{ item.activity_type || '其他' }}</el-tag>
              <el-tag size="default" :type="item.is_featured ? 'success' : 'info'">
                {{ item.is_featured ? '推荐' : '普通' }}
              </el-tag>
              <el-tag size="default" v-if="item.is_archived" type="warning">已归档</el-tag>
            </div>
          </div>
          <div class="info-meta">
            <span><el-icon><Calendar /></el-icon> {{ item.start_date || '未设置' }} ~ {{ item.end_date || '未设置' }}</span>
            <span><el-icon><Location /></el-icon> {{ item.location || '未设置' }}</span>
            <span><el-icon><User /></el-icon> {{ item.stats?.registrations || 0 }} 人报名</span>
            <span><el-icon><Money /></el-icon> {{ item.charge_mode === 'free' ? '免费' : item.charge_mode === 'paid' ? '¥'+item.fee : item.points_cost+'积分' }}</span>
          </div>
          <div class="info-footer">
            <div class="registration-info" v-if="item.registration_start || item.registration_end">
              <span>报名：{{ item.registration_start || '未设置' }} ~ {{ item.registration_end || '未设置' }}</span>
            </div>
            <div class="action-buttons" @click.stop>
              <el-button size="default" type="primary" link @click="goToDetail(item.id)">详情</el-button>
              <el-button size="default" type="primary" link @click="goToEdit(item.id)">编辑</el-button>
              <!-- ★★★ 使用方法替代复杂表达式 ★★★ -->
              <el-button v-if="shouldShowPublish(item)" size="default" type="success" link @click="handlePublish(item)">发布</el-button>
              <el-button v-if="shouldShowCancel(item)" size="default" type="danger" link @click="handleCancel(item)">取消</el-button>
              <el-button v-if="shouldShowArchive(item)" size="default" type="info" link @click="handleArchive(item)">归档</el-button>
              <el-button v-if="shouldShowUnarchive(item)" size="default" type="warning" link @click="handleUnarchive(item)">取消归档</el-button>
              <!-- 抽奖按钮 -->
              <el-button
                v-if="shouldShowLottery(item)"
                size="default"
                type="warning"
                link
                @click.stop="openLottery(item)"
              >
                <el-icon><Trophy /></el-icon> 抽奖
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-box" v-if="total > pageSize">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        size="default"
        @current-change="fetchActivities"
      />
    </div>

    <!-- 抽奖模态框 -->
    <el-dialog v-model="lotteryDialogVisible" title="抽奖" width="750px" :close-on-click-modal="false" class="lottery-dialog">
      <div v-if="currentLotteryActivity">
        <div class="lottery-header">
          <span class="activity-name">{{ currentLotteryActivity.name }}</span>
          <div class="lottery-stats">
            <el-tag type="info">可抽次数：{{ lotteryStatus?.remaining_draws || 0 }}</el-tag>
            <el-tag type="success">可中奖次数：{{ lotteryStatus?.remaining_wins || 0 }}</el-tag>
          </div>
        </div>
        <div class="lottery-body">
          <div class="student-select">
            <el-select
              v-model="selectedStudentId"
              placeholder="选择参奖学员"
              filterable
              size="default"
              style="width:100%"
              @change="selectStudent"
            >
              <el-option
                v-for="s in lotteryStudentList"
                :key="s.student_id"
                :label="s.student_name + ' (' + s.student_phone + ')'"
                :value="s.student_id"
              />
            </el-select>
          </div>
          <div v-if="lotteryStatus && selectedStudentId" class="lottery-info">
            <div v-if="lotteryStatus.can_draw" class="lottery-wheel-wrapper">
              <div class="status-info">
                <div>剩余抽奖次数：<strong>{{ lotteryStatus.remaining_draws }}</strong></div>
                <div>剩余可中奖次数：<strong>{{ lotteryStatus.remaining_wins }}</strong></div>
                <div>奖项池：<span v-for="(p, idx) in lotteryStatus.prizes" :key="idx" class="prize-tag">{{ p.name }}({{ p.remaining }})</span></div>
              </div>
              <LotteryWheel
                :prizes="lotteryStatus?.prizes || []"
                :draw-result="drawResult"
                :spinning="lotteryLoading"
                @spin-click="handleSpinClick"
              />
            </div>
            <div v-else class="no-draw">
              <el-empty description="抽奖次数已用完，感谢参与！" :image-size="80" />
            </div>
          </div>
          <div v-else class="no-student">
            <el-empty description="请先选择参奖学员" :image-size="80" />
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Picture, Calendar, Location, User, Money, Trophy } from '@element-plus/icons-vue'
import request from '@/api/request'
import { getActivityList } from '@/api/activity'
import LotteryWheel from '@/components/LotteryWheel.vue'

const router = useRouter()
const loading = ref(false)
const activities = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(12)
const showArchived = ref(false)

// 抽奖相关
const lotteryDialogVisible = ref(false)
const currentLotteryActivity = ref(null)
const selectedStudentId = ref(null)
const lotteryStudentList = ref([])
const lotteryStatus = ref(null)
const lotteryLoading = ref(false)
const drawResult = ref(null)
const wheelRef = ref(null)

const filters = reactive({
  keyword: '',
  status: '',
  activity_type: ''
})

// 状态标签
function getStatusLabel(status) {
  const map = {
    draft: '草稿',
    registering: '报名中',
    upcoming: '待开始',
    ongoing: '进行中',
    ended: '已结束',
    cancelled: '已取消',
    archived: '已归档'
  }
  return map[status] || status
}

function getStatusClass(status) {
  const map = {
    draft: 'status-draft',
    registering: 'status-registering',
    upcoming: 'status-upcoming',
    ongoing: 'status-ongoing',
    ended: 'status-ended',
    cancelled: 'status-cancelled',
    archived: 'status-archived'
  }
  return map[status] || ''
}

// ★★★ 方法替代模板中的复杂表达式 ★★★
function shouldShowPublish(item) {
  return item.status === 'draft'
}
function shouldShowCancel(item) {
  return item.status !== 'cancelled' && item.status !== 'archived' && item.status !== 'ended'
}
function shouldShowArchive(item) {
  return item.status === 'ended' && !item.is_archived
}
function shouldShowUnarchive(item) {
  return item.is_archived
}
function shouldShowLottery(item) {
  return item.enable_lottery && item.status !== 'ended' && item.status !== 'cancelled' && item.status !== 'archived'
}

// 获取活动列表
async function fetchActivities() {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
      activity_type: filters.activity_type || undefined,
      is_archived: showArchived.value || undefined
    }
    const res = await getActivityList(params)
    activities.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e) {
    ElMessage.error('加载活动列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索防抖
let searchTimer = null
function handleSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    fetchActivities()
  }, 300)
}

// 重置筛选
function resetFilters() {
  filters.keyword = ''
  filters.status = ''
  filters.activity_type = ''
  currentPage.value = 1
  fetchActivities()
}

// 查看归档
function viewArchived() {
  showArchived.value = true
  currentPage.value = 1
  fetchActivities()
}

function toggleArchived(val) {
  showArchived.value = val
  currentPage.value = 1
  fetchActivities()
}

// 路由跳转
function createNewActivity() {
  router.push('/activities/new')
}

function goToDetail(id) {
  router.push(`/activities/detail?id=${id}`)
}

function goToEdit(id) {
  router.push(`/activities/edit?id=${id}`)
}

// 活动操作
async function handlePublish(item) {
  try {
    await ElMessageBox.confirm(`确认发布活动"${item.name}"？`, '提示', { type: 'info' })
    await request.post(`/activity/activities/${item.id}/publish`)
    ElMessage.success('发布成功')
    fetchActivities()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('发布失败')
  }
}

async function handleCancel(item) {
  try {
    await ElMessageBox.confirm(
      `确认取消活动"${item.name}"？所有已缴费报名将自动退费。`,
      '警告',
      { type: 'warning', confirmButtonText: '确认取消', cancelButtonText: '取消' }
    )
    await request.post(`/activity/activities/${item.id}/cancel`)
    ElMessage.success('已取消活动')
    fetchActivities()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('操作失败')
  }
}

async function handleArchive(item) {
  try {
    await ElMessageBox.confirm(`确认归档活动"${item.name}"？`, '提示', { type: 'info' })
    await request.post(`/activity/activities/${item.id}/archive`)
    ElMessage.success('已归档')
    fetchActivities()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('归档失败')
  }
}

async function handleUnarchive(item) {
  try {
    await request.post(`/activity/activities/${item.id}/unarchive`)
    ElMessage.success('已取消归档')
    fetchActivities()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}


// 执行抽奖（点击转盘时调用）
async function handleSpinClick() {
  if (!selectedStudentId.value) {
    ElMessage.warning('请先选择学员')
    return
  }
  if (lotteryLoading.value) return
  if (!lotteryStatus.value || !lotteryStatus.value.can_draw) {
    ElMessage.warning('抽奖次数已用完')
    return
  }

  lotteryLoading.value = true
  drawResult.value = null
  try {
    // ★★★ 直接发送整数，而不是对象 ★★★
    const res = await request.post(`/activity/activities/${currentLotteryActivity.value.id}/lottery/draw`, 
      selectedStudentId.value
    )
    const data = res.data
    if (data.win) {
      drawResult.value = {
        win: true,
        prize: { name: data.prize_name, level: data.prize_level },
        prize_index: currentLotteryActivity.value.prizes.findIndex(p => p.name === data.prize_name)
      }
    } else {
      drawResult.value = { win: false, prize: null }
    }
    await selectStudent(selectedStudentId.value)
    await fetchActivities()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '抽奖失败')
  } finally {
    lotteryLoading.value = false
  }
}


// 打开抽奖模态框时重置状态
async function openLottery(activity) {
  currentLotteryActivity.value = activity
  lotteryDialogVisible.value = true
  selectedStudentId.value = null
  lotteryStudentList.value = []
  lotteryStatus.value = null
  drawResult.value = null
  lotteryLoading.value = false
  await loadLotteryStudents(activity.id)
}

async function loadLotteryStudents(activityId) {
  try {
    const res = await request.get(`/activity/activities/${activityId}/registrations`)
    lotteryStudentList.value = res.data || []
  } catch (e) {
    ElMessage.error('加载报名学员失败')
  }
}

// 选择学员后获取状态
async function selectStudent(studentId) {
  selectedStudentId.value = studentId
  lotteryLoading.value = true
  try {
    const res = await request.get(`/activity/activities/${currentLotteryActivity.value.id}/lottery/status`, {
      params: { student_id: studentId }
    })
    lotteryStatus.value = res.data
  } catch (e) {
    ElMessage.error('获取抽奖状态失败')
  } finally {
    lotteryLoading.value = false
  }
}

async function handleSpinEnd(result) {
  if (result.win) {
    ElMessage.success(`🎉 恭喜获得 ${result.prize.name}！`)
    await selectStudent(selectedStudentId.value)
    await fetchActivities()
  } else {
    ElMessage.info('未中奖，再接再厉！')
    await selectStudent(selectedStudentId.value)
  }
}

onMounted(() => {
  fetchActivities()
})
</script>

<style scoped>
.activity-manage {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  overflow-y: auto;
  padding: 0 0 var(--space-4);
}

.action-bar {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
}

.left-actions { display: flex; gap: var(--space-3); }
.right-actions { display: flex; gap: var(--space-3); flex-wrap: wrap; }

.activity-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: var(--space-4);
}

.activity-card {
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-xs);
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.2s;
  display: flex;
  flex-direction: column;
}

.activity-card:hover {
  box-shadow: 0 4px 16px rgba(54, 180, 89, 0.1);
  transform: translateY(-2px);
}

.activity-cover {
  width: 100%;
  height: 160px;
  position: relative;
  background: var(--surface-soft);
  flex-shrink: 0;
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: var(--text-placeholder);
  font-size: 32px;
}

.cover-status {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 2px 10px;
  border-radius: var(--radius-pill);
  font-size: 11px;
  font-weight: 600;
  color: var(--surface);
}

.status-draft { background: var(--gray-400); }
.status-registering { background: var(--info); }
.status-upcoming { background: var(--warning); }
.status-ongoing { background: var(--success); }
.status-ended { background: var(--gray-500); }
.status-cancelled { background: var(--danger); }
.status-archived { background: var(--gray-500); }

.activity-info {
  padding: var(--space-4);
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}

.activity-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.4;
}

.info-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.info-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px var(--space-5);
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: var(--space-2);
}

.info-meta .el-icon { margin-right: 4px; }

.info-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: var(--text-placeholder);
  border-top: 1px solid var(--border-light);
  padding-top: 10px;
  margin-top: auto;
}

.registration-info { font-size: 12px; color: var(--text-placeholder); }

.action-buttons { display: flex; gap: 4px; flex-wrap: wrap; }

.empty-state {
  grid-column: 1 / -1;
  padding: 60px var(--space-4);
  text-align: center;
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
}

.pagination-box {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  padding: var(--space-4);
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
}

/* 抽奖模态框 */
.lottery-dialog :deep(.el-dialog__body) { padding-top: 16px; }

.lottery-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  padding: 12px var(--space-4);
  background: var(--surface-soft);
  border-radius: var(--radius-md);
}

.lottery-header .activity-name { font-size: 16px; font-weight: 700; }

.lottery-stats { display: flex; gap: var(--space-3); }

.lottery-body { min-height: 400px; }

.student-select { margin-bottom: var(--space-4); }

.status-info {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
  padding: var(--space-3);
  background: var(--surface-green);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-4);
}

.status-info strong { color: var(--brand-600); }

.prize-tag {
  display: inline-block;
  background: var(--brand-50);
  padding: 2px 10px;
  border-radius: var(--radius-pill);
  margin: 0 4px;
  font-size: 12px;
  color: var(--text-primary);
}

.lottery-wheel-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.no-draw, .no-student { padding: 40px 0; }

@media (max-width: 768px) {
  .activity-grid { grid-template-columns: 1fr; }
  .action-bar { flex-direction: column; align-items: stretch; }
  .right-actions { flex-wrap: wrap; }
  .right-actions .el-input,
  .right-actions .el-select { flex: 1; min-width: 120px; }
  .activity-cover { height: 120px; }
  .lottery-stats { flex-wrap: wrap; }
}
</style>
