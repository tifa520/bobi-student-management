<!-- src/views/Redirect.vue -->
<template>
  <div></div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const { params, query } = route
const { path } = params

// 替换到目标页面
router.replace({ path: '/' + path, query })
</script>