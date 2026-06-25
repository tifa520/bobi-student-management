<template>
  <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
    <el-form-item label="规则名称" prop="rule_name">
      <el-input v-model="form.rule_name" placeholder="例如：全职教师阶梯课酬" />
    </el-form-item>

    <el-form-item label="适用类型" prop="applicable_type">
      <el-radio-group v-model="form.applicable_type" @change="onApplicableTypeChange">
        <el-radio label="teacher" value="teacher">教师</el-radio>
        <el-radio label="course" value="course">课程</el-radio>
        <el-radio label="class" value="class">班级</el-radio>
      </el-radio-group>
    </el-form-item>

    <el-form-item label="适用对象" prop="applicable_id">
      <el-select v-model="form.applicable_id" placeholder="请选择" filterable style="width: 100%">
        <el-option
          v-for="item in applicableOptions"
          :key="item.id"
          :label="item.name"
          :value="item.id"
        />
      </el-select>
    </el-form-item>

    <el-form-item label="计薪标准" prop="calculation_type">
      <el-radio-group v-model="form.calculation_type">
        <el-radio label="class_count" value="class_count">上课次数</el-radio>
        <el-radio label="attendance_count" value="attendance_count">出勤人次</el-radio>
        <el-radio label="consumed_hours" value="consumed_hours">消耗课时数</el-radio>
        <el-radio label="consumed_amount" value="consumed_amount">消耗课时金额</el-radio>
      </el-radio-group>
    </el-form-item>

    <el-form-item label="提成方式" prop="commission_type">
      <el-radio-group v-model="form.commission_type" @change="onCommissionTypeChange">
        <el-radio label="fixed" value="fixed">固定比例/单价</el-radio>
        <el-radio label="tiered" value="tiered">阶梯比例/单价</el-radio>
      </el-radio-group>
    </el-form-item>

    <template v-if="form.commission_type === 'fixed'">
      <el-form-item label="计薪单位">
        <el-radio-group v-model="fixedType">
          <el-radio label="ratio" value="ratio">比例 (%)</el-radio>
          <el-radio label="unit_price" value="unit_price">单价 (元)</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="固定值" v-if="fixedType === 'ratio'">
        <el-input-number v-model="form.fixed_ratio" :min="0" :max="100" :precision="2" controls-position="right" style="width: 200px" />
        <span style="margin-left: 8px">%</span>
      </el-form-item>
      <el-form-item label="固定单价" v-else>
        <el-input-number v-model="form.fixed_unit_price" :min="0" :precision="2" controls-position="right" style="width: 200px" />
        <span style="margin-left: 8px">元</span>
      </el-form-item>
    </template>

    <template v-if="form.commission_type === 'tiered'">
      <el-divider content-position="left">阶梯设置</el-divider>
      <el-table :data="tiers" border style="width: 100%">
        <!-- 保持原样 -->
        <el-table-column label="区间下限" width="120">
          <template #default="{ row, $index }">
            <el-input-number v-model="row.min_value" :min="0" :precision="0" controls-position="right" size="small" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column label="区间上限" width="120">
          <template #default="{ row, $index }">
            <el-input-number v-model="row.max_value" :min="row.min_value + 1" :precision="0" controls-position="right" size="small" style="width: 100%" placeholder="空则无穷" />
          </template>
        </el-table-column>
        <el-table-column label="计算方式" width="100">
          <template #default="{ row }">
            <el-select v-model="row.calc_type" size="small">
              <el-option label="比例" value="ratio" />
              <el-option label="单价" value="unit_price" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="值" width="140">
          <template #default="{ row }">
            <el-input-number v-if="row.calc_type === 'ratio'" v-model="row.ratio" :min="0" :max="100" :precision="2" controls-position="right" size="small" style="width: 100%" />
            <el-input-number v-else v-model="row.unit_price" :min="0" :precision="2" controls-position="right" size="small" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column label="按人次" width="80">
          <template #default="{ row }">
            <el-checkbox v-model="row.is_per_person" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="60">
          <template #default="{ $index }">
            <el-button type="danger" link size="small" @click="removeTier($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-button type="primary" link size="small" @click="addTier" style="margin-top: 12px">+ 添加阶梯</el-button>
    </template>

    <el-form-item label="是否启用">
      <el-switch v-model="form.is_enabled" />
    </el-form-item>
    <el-form-item label="备注">
      <el-input v-model="form.remark" type="textarea" :rows="2" />
    </el-form-item>

    <el-form-item>
      <el-button type="primary" @click="submit" :loading="submitting">保存</el-button>
      <el-button @click="$emit('cancel')">取消</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { createSalaryRule, updateSalaryRule } from '@/api/salary'
import { getTeacherList, getCourseListSimple, getClassList } from '@/api/basic'

const props = defineProps({
  rule: { type: Object, default: null }
})
const emit = defineEmits(['success', 'cancel'])

const formRef = ref(null)
const submitting = ref(false)
const fixedType = ref('ratio')
const tiers = ref([])
const applicableOptions = ref([])

const form = reactive({
  id: null,
  rule_name: '',
  applicable_type: 'teacher',
  applicable_id: null,
  calculation_type: 'class_count',
  commission_type: 'fixed',
  fixed_ratio: 0,
  fixed_unit_price: 0,
  is_enabled: true,
  remark: ''
})

const rules = {
  rule_name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  applicable_id: [{ required: true, message: '请选择适用对象', trigger: 'change' }]
}

watch(() => props.rule, (val) => {
  if (val) {
    Object.assign(form, val)
    if (val.commission_type === 'fixed') {
      fixedType.value = val.fixed_ratio > 0 ? 'ratio' : 'unit_price'
    } else {
      tiers.value = val.tiers?.map(t => ({
        ...t,
        calc_type: t.ratio ? 'ratio' : 'unit_price'
      })) || []
    }
  } else {
    resetForm()
  }
}, { immediate: true })

watch(() => form.applicable_type, async () => {
  await loadApplicableOptions()
  form.applicable_id = null
})

async function loadApplicableOptions() {
  if (form.applicable_type === 'teacher') {
    const res = await getTeacherList()
    applicableOptions.value = res.data || []
  } else if (form.applicable_type === 'course') {
    const res = await getCourseListSimple()
    applicableOptions.value = res.data || []
  } else {
    const res = await getClassList({ page_size: 100 })
    applicableOptions.value = res.data?.items || []
  }
}

function onApplicableTypeChange() {
  loadApplicableOptions()
}

function onCommissionTypeChange() {
  if (form.commission_type === 'tiered' && tiers.value.length === 0) {
    addTier()
  }
}

function addTier() {
  tiers.value.push({ min_value: 0, max_value: null, unit_price: 0, ratio: null, calc_type: 'ratio', is_per_person: false })
}

function removeTier(index) {
  tiers.value.splice(index, 1)
}

function resetForm() {
  form.id = null
  form.rule_name = ''
  form.applicable_type = 'teacher'
  form.applicable_id = null
  form.calculation_type = 'class_count'
  form.commission_type = 'fixed'
  form.fixed_ratio = 0
  form.fixed_unit_price = 0
  form.is_enabled = true
  form.remark = ''
  fixedType.value = 'ratio'
  tiers.value = []
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const submitData = {
      rule_name: form.rule_name,
      applicable_type: form.applicable_type,
      applicable_id: form.applicable_id,
      calculation_type: form.calculation_type,
      commission_type: form.commission_type,
      fixed_ratio: form.commission_type === 'fixed' && fixedType.value === 'ratio' ? form.fixed_ratio : 0,
      fixed_unit_price: form.commission_type === 'fixed' && fixedType.value === 'unit_price' ? form.fixed_unit_price : 0,
      is_enabled: form.is_enabled,
      remark: form.remark,
      tiers: form.commission_type === 'tiered' ? tiers.value.map(t => ({
        min_value: t.min_value,
        max_value: t.max_value || null,
        unit_price: t.calc_type === 'unit_price' ? t.unit_price : 0,
        ratio: t.calc_type === 'ratio' ? t.ratio : null,
        is_per_person: t.is_per_person || false
      })) : []
    }
    if (form.id) {
      await updateSalaryRule(form.id, submitData)
      ElMessage.success('更新成功')
    } else {
      await createSalaryRule(submitData)
      ElMessage.success('创建成功')
    }
    emit('success')
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}
</script>