<template>
  <div class="student-picker" style="width: 100%">
    <el-select
      v-model="selectedId"
      filterable
      remote
      reserve-keyword
      :placeholder="placeholder"
      :remote-method="debouncedSearch"
      :loading="loading"
      clearable
      value-key="id"
      style="width: 100%"
      @change="handleChange"
      @clear="handleClear"
    >
      <el-option
        v-for="item in options"
        :key="item.id"
        :label="`${item.name}（${item.phone}）`"
        :value="item.id"
      >
        <div class="student-option">
          <AppImage :src="item.avatar" :size="24" class="option-avatar" />
          <span>{{ item.name }}（{{ item.phone }}）</span>
        </div>
      </el-option>
      <template v-if="allowCreate && keyword && !loading && options.length === 0">
        <el-option disabled value="">
          <span>无匹配学员，点击</span>
          <el-button type="primary" link @click.stop="openCreateDrawer">新建学员</el-button>
        </el-option>
      </template>
    </el-select>
    <NewStudentDrawer v-if="allowCreate" v-model:visible="drawerVisible" @student-created="onStudentCreated" />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { searchExistingStudents } from '@/api/enroll'
import NewStudentDrawer from './NewStudentDrawer.vue'
import { debounce } from 'lodash-es'

const props = defineProps({ modelValue: [Number, String], placeholder: { type: String, default: '请输入学员姓名或手机号搜索' }, allowCreate: { type: Boolean, default: false } })
const emit = defineEmits(['update:modelValue', 'student-selected', 'create-student'])
const selectedId = ref(props.modelValue)
const options = ref([])
const loading = ref(false)
const keyword = ref('')
const drawerVisible = ref(false)

watch(() => props.modelValue, (val) => { selectedId.value = val })
watch(selectedId, (val) => emit('update:modelValue', val))

const debouncedSearch = debounce(async (query) => {
  keyword.value = query
  if (!query) { options.value = []; return }
  loading.value = true
  try { const res = await searchExistingStudents(query); options.value = res.data || [] } catch { options.value = [] } finally { loading.value = false }
}, 300)

function handleChange(value) { if (!value || typeof value !== 'number') handleClear(); else { const student = options.value.find(s => s.id === value); if (student) emit('student-selected', student) } }
function handleClear() { emit('student-selected', null) }
function openCreateDrawer() { drawerVisible.value = true }
function onStudentCreated(newStudent) { options.value.push(newStudent); selectedId.value = newStudent.id; emit('student-selected', newStudent); emit('create-student', newStudent); drawerVisible.value = false }
</script>

<style scoped>
.student-picker { width: 100%; }
.student-option { display: flex; align-items: center; gap: 8px; }
.option-avatar { flex-shrink: 0; }
</style>