<template>
  <div class="salary-manage">
    <el-tabs v-model="activeTab" @tab-click="handleTabClick">
      <el-tab-pane label="课酬规则" name="rules">
        <SalaryRuleList ref="ruleListRef" />
      </el-tab-pane>
      <el-tab-pane label="教师薪酬" name="salary">
        <TeacherSalaryList ref="salaryListRef" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import SalaryRuleList from './SalaryRuleList.vue'
import TeacherSalaryList from './TeacherSalaryList.vue'

const activeTab = ref('rules')
const ruleListRef = ref(null)
const salaryListRef = ref(null)

const handleTabClick = () => {
  // 切换页签时刷新对应列表
  if (activeTab.value === 'rules' && ruleListRef.value) {
    ruleListRef.value.fetchRules()
  } else if (activeTab.value === 'salary' && salaryListRef.value) {
    salaryListRef.value.fetchSalaries()
  }
}
</script>

<style scoped>
.salary-manage {
  padding: 0;
  height: 100%;
  background: var(--surface);
}
</style>