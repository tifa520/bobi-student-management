<template>
  <div v-if="packages.length" class="package-selector">
    <div class="package-label">选择套餐：</div>
    <el-radio-group v-model="selectedPackageId" @change="onPackageChange">
      <el-radio
        v-for="pkg in packages"
        :key="pkg.id"
        :label="pkg.id"
        :value="pkg.id"
      >
        <div class="package-item">
          <span class="package-name">{{ pkg.name }}</span>
          <span class="package-desc">
            {{ pkg.purchase_hours }}课时
            <template v-if="pkg.gift_hours">+{{ pkg.gift_hours }}赠课</template>
            <template v-if="pkg.discount_mode === 'direct'"> 直减¥{{ pkg.direct_reduction }}</template>
            <template v-else-if="pkg.discount_mode === 'discount'"> {{ pkg.discount_rate }}折</template>
            <template v-if="pkg.validity_days"> 有效期{{ pkg.validity_days }}天</template>
          </span>
        </div>
      </el-radio>
    </el-radio-group>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  courseId: {
    type: Number,
    required: true
  },
  modelValue: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'select'])

const packages = ref([])
const selectedPackageId = ref(null)

async function loadPackages() {
  if (!props.courseId) {
    packages.value = []
    return
  }
  try {
    const { getCoursePackages } = await import('@/api/basic')   // 修改这里
    const res = await getCoursePackages(props.courseId)
    packages.value = res.data || []
    const defaultPkg = packages.value.find(p => p.is_default)
    if (defaultPkg && !selectedPackageId.value) {
      selectedPackageId.value = defaultPkg.id
      onPackageChange(defaultPkg.id)
    }
  } catch (error) {
    console.error('加载套餐失败', error)
  }
}

function onPackageChange(pkgId) {
  const pkg = packages.value.find(p => p.id === pkgId)
  if (pkg) {
    emit('select', pkg)
    emit('update:modelValue', pkg)
  }
}

watch(() => props.courseId, () => {
  selectedPackageId.value = null
  loadPackages()
}, { immediate: true })
</script>

<style scoped>
.package-selector {
  margin: 16px 0;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
}
.package-label {
  font-weight: 500;
  margin-bottom: 8px;
}
.package-item {
  display: flex;
  flex-direction: column;
  line-height: 1.4;
}
.package-name {
  font-weight: 500;
}
.package-desc {
  font-size: 12px;
  color: #606266;
}
</style>