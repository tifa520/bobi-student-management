<template>
  <el-dialog v-model="visible" :title="title" width="500px" @close="handleClose">
    <!-- 红色提示语（顶部） -->
    <div v-if="!isGift" class="warning-tip">
      减少课时将扣除<strong>付费课时</strong>，如需扣除赠送课时请使用“增减赠送课时”按钮。
    </div>

    <el-form :model="form" label-width="110px">
      <el-form-item label="课程">
        <el-select
          v-model="form.course_id"
          placeholder="请选择课程"
          @change="onCourseChange"
          :style="{ width: '100%' }"
        >
          <el-option
            v-for="c in courseList"
            :key="c.course_id"
            :label="c.course_name"
            :value="c.course_id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="当前剩余">
        <span>{{ remainingHours }} 课时</span>
      </el-form-item>

      <el-form-item label="操作类型">
        <el-radio-group v-model="form.changeType" name="adjust_hours_type">
          <el-radio label="add" value="add">增加课时</el-radio>
          <el-radio label="sub" value="sub">减少课时</el-radio>
        </el-radio-group>
      </el-form-item>

      <template v-if="form.changeType === 'add'">
        <el-form-item label="增加课时数">
          <el-input-number v-model="form.hours" :min="1" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="原因">
          <el-input v-model="form.reason" placeholder="请输入原因" />
        </el-form-item>
      </template>

      <template v-else>
        <el-form-item label="算作教师业绩">
          <el-radio-group v-model="form.performance" name="performance_type">
            <el-radio label="yes" value="yes">是</el-radio>
            <el-radio label="no" value="no">否</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="form.performance === 'yes'" label="课消归属时间">
          <el-date-picker
            v-model="form.occurrence_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item v-if="form.performance === 'yes'" label="教师">
          <el-select v-model="form.teacher_id" placeholder="选择教师" clearable style="width: 100%">
            <el-option v-for="t in teachers" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="减少课时数">
          <el-input-number
            v-model="form.hours"
            :min="1"
            controls-position="right"
            style="width: 100%"
          />
          <span style="margin-left: 8px; color: #909399;">
            减少后剩余{{ Math.max(0, remainingHours - form.hours) }}课时
          </span>
        </el-form-item>

        <el-form-item label="原因">
          <el-input v-model="form.reason" placeholder="请输入原因" />
        </el-form-item>
      </template>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="handleConfirm" :loading="submitting">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { adjustHours, giftHours, getStudentCourses } from '@/api/student'
import { getEnabledTeachers } from '@/api/basic'
import dayjs from 'dayjs'

const props = defineProps({
  visible: Boolean,
  studentId: Number,
  courseId: Number,        // 初始选中的课程ID（可选）
  remainingHours: Number,  // 当前选中课程的剩余课时
  isGift: { type: Boolean, default: false }  // 是否为赠送课时操作
})
const emit = defineEmits(['update:visible', 'success'])

const visible = ref(props.visible)
const submitting = ref(false)
const courseList = ref([])   // 存储课程列表 { course_id, course_name }
const teachers = ref([])

const form = reactive({
  course_id: null,
  changeType: 'sub',
  hours: 1,
  reason: '',
  performance: 'no',
  occurrence_date: dayjs().format('YYYY-MM-DD'),
  teacher_id: null
})

const title = computed(() => props.isGift ? '增减赠送课时' : '增减付费课时')

// 监听弹窗显示，初始化数据
watch(() => props.visible, async (val) => {
  visible.value = val
  if (val) {
    // 加载教师列表（用于业绩归属）
    const teacherRes = await getEnabledTeachers()
    teachers.value = teacherRes.data || []

    // 加载该学员的课程列表（显示课程名称）
    if (props.studentId) {
      const res = await getStudentCourses(props.studentId)
      courseList.value = (res.data || []).map(c => ({
        course_id: c.course_id,
        course_name: c.course_name
      }))
    }

    // 初始化表单
    form.course_id = props.courseId || (courseList.value[0]?.course_id || null)
    form.changeType = 'sub'
    form.hours = 1
    form.reason = ''
    form.performance = 'no'
    form.occurrence_date = dayjs().format('YYYY-MM-DD')
    form.teacher_id = null
  }
})
watch(visible, (val) => emit('update:visible', val))

function onCourseChange(courseId) {
  // 可在此处更新剩余课时，但剩余课时已由父组件传入，这里不需要额外操作
}

async function handleConfirm() {
  if (!form.course_id) {
    ElMessage.warning('请选择课程')
    return
  }
  if (!form.hours || form.hours <= 0) {
    ElMessage.warning('请输入有效的课时数')
    return
  }
  if (form.changeType === 'sub' && form.hours > props.remainingHours) {
    ElMessage.warning('减少课时数不能超过剩余课时')
    return
  }
  submitting.value = true
  try {
    const hours = form.changeType === 'add' ? form.hours : -form.hours
    if (props.isGift) {
      await giftHours(props.studentId, {
        course_id: form.course_id,
        change_hours: hours,
        reason: form.reason,
        occurrence_date: form.occurrence_date,
        performance: form.performance === 'yes',
        teacher_id: form.teacher_id || null
      })
    } else {
      await adjustHours(props.studentId, {
        course_id: form.course_id,
        change_hours: hours,
        reason: form.reason,
        occurrence_date: form.occurrence_date,
        performance: form.performance === 'yes',
        teacher_id: form.teacher_id || null
      })
    }
    ElMessage.success('操作成功')
    visible.value = false
    emit('success')
  } catch (err) {
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

function handleClose() {
  visible.value = false
}
</script>

<style scoped>
.warning-tip {
  color: #f56c6c;
  font-size: 13px;
  margin-bottom: 16px;
  padding: 8px 12px;
  background-color: #fef0f0;
  border-radius: 4px;
  line-height: 1.5;
}

/* 统一输入框、下拉框、按钮高度为 40px */
:deep(.el-input__wrapper),
:deep(.el-select .el-input__wrapper),
:deep(.el-date-editor .el-input__wrapper),
:deep(.el-input-number .el-input__wrapper) {
  height: 40px;
  min-height: 40px;
}

:deep(.el-input__inner),
:deep(.el-select__input) {
  line-height: 40px;
  height: 40px;
}

:deep(.el-button) {
  height: 40px;
  line-height: 40px;
}

:deep(.el-input-number .el-input-number__decrease),
:deep(.el-input-number .el-input-number__increase) {
  display: none;
}
</style>