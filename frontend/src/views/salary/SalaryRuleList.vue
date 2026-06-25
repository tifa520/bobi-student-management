<template>
  <div class="salary-rule-list">
    <div class="action-bar">
      <el-button type="primary" @click="openCreateDrawer">+ 新增规则</el-button>
      <el-select v-model="filterType" placeholder="适用类型" clearable style="width: 150px" @change="fetchRules">
        <el-option label="教师" value="teacher" />
        <el-option label="课程" value="course" />
        <el-option label="班级" value="class" />
      </el-select>
    </div>

    <el-table :data="rules" v-loading="loading" border stripe>
      <el-table-column prop="rule_name" label="规则名称" min-width="150" />
      <el-table-column label="适用对象" min-width="120">
        <template #default="{ row }">
          <span v-if="row.applicable_type === 'teacher'">教师</span>
          <span v-else-if="row.applicable_type === 'course'">课程</span>
          <span v-else>班级</span>
        </template>
      </el-table-column>
      <el-table-column label="计薪标准" width="120">
        <template #default="{ row }">
          <span v-if="row.calculation_type === 'class_count'">上课次数</span>
          <span v-else-if="row.calculation_type === 'attendance_count'">出勤人次</span>
          <span v-else-if="row.calculation_type === 'consumed_hours'">消耗课时</span>
          <span v-else>消耗金额</span>
        </template>
      </el-table-column>
      <el-table-column label="提成方式" width="120">
        <template #default="{ row }">
          <span v-if="row.commission_type === 'fixed'">固定</span>
          <span v-else>阶梯</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_enabled ? 'success' : 'danger'">{{ row.is_enabled ? '启用' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="editRule(row)">编辑</el-button>
          <el-button type="danger" link size="small" @click="deleteRule(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-drawer v-model="drawerVisible" :title="editing ? '编辑规则' : '新增规则'" size="60%">
      <RuleForm ref="ruleFormRef" :rule="currentRule" @success="onFormSuccess" @cancel="drawerVisible = false" />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSalaryRules, deleteSalaryRule } from '@/api/salary'
import RuleForm from '@/components/salary/RuleForm.vue'

const rules = ref([])
const loading = ref(false)
const filterType = ref('')
const drawerVisible = ref(false)
const editing = ref(false)
const currentRule = ref(null)
const ruleFormRef = ref(null)

async function fetchRules() {
  loading.value = true
  try {
    const res = await getSalaryRules({ applicable_type: filterType.value || undefined })
    rules.value = res.data || []
  } catch (error) {
    ElMessage.error('加载规则失败')
  } finally {
    loading.value = false
  }
}

function openCreateDrawer() {
  editing.value = false
  currentRule.value = null
  drawerVisible.value = true
}

function editRule(rule) {
  editing.value = true
  currentRule.value = { ...rule }
  drawerVisible.value = true
}

async function deleteRule(rule) {
  await ElMessageBox.confirm(`确认删除规则“${rule.rule_name}”？`, '提示', { type: 'warning' })
  await deleteSalaryRule(rule.id)
  ElMessage.success('删除成功')
  await fetchRules()
}

function onFormSuccess() {
  drawerVisible.value = false
  fetchRules()
}

defineExpose({ fetchRules })

onMounted(() => {
  fetchRules()
})
</script>

<style scoped>
.salary-rule-list {
  padding: 20px;
}
.action-bar {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
}
</style>