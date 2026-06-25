<template>
  <div
    class="app-image"
    :style="{
      width: size + 'px',
      height: size + 'px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0,
      borderRadius: shape === 'circle' ? '50%' : shape === 'round' ? '8px' : '0',
      overflow: 'hidden',
      backgroundColor: '#f0f2f5'
    }"
  >
    <img
      :src="src || DEFAULT_AVATAR_SVG"
      :alt="alt"
      style="width:100%; height:100%; object-fit:cover;"
      @error="handleError"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { DEFAULT_AVATAR_SVG } from '@/utils/constants'

const props = defineProps({
  src: { type: String, default: '' },
  size: { type: Number, default: 40 },
  shape: { type: String, default: 'circle' },
  className: { type: String, default: '' },
  alt: { type: String, default: '头像' }
})

const fallbackSrc = DEFAULT_AVATAR_SVG
const hasError = ref(false)

watch(() => props.src, () => {
  hasError.value = false
})

const displaySrc = computed(() => {
  if (hasError.value) return fallbackSrc
  if (!props.src) return fallbackSrc
  return props.src
})

const wrapperStyle = computed(() => ({
  width: `${props.size}px`,
  height: `${props.size}px`,
  borderRadius: props.shape === 'circle' ? '50%' : props.shape === 'round' ? '8px' : '0',
  overflow: 'hidden',
  flexShrink: 0,
  display: 'inline-block'
}))

const handleError = () => {
  hasError.value = true
}
</script>

<style scoped>
.app-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
</style>