<template>
  <div class="lottery-wheel" ref="wheelContainer">
    <canvas ref="canvas" :width="canvasSize" :height="canvasSize"></canvas>
    <div class="pointer" @click="spin">抽奖</div>
    <div v-if="resultText" class="result">{{ resultText }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  prizes: { type: Array, default: () => [] },
  spinning: Boolean,
  // 由父组件传入中奖结果，格式：{ win: true, prize: { name, level }, prize_index: 0 }
  drawResult: { type: Object, default: null }
})
const emit = defineEmits(['spin-click'])

const canvas = ref(null)
const canvasSize = 300
const ctx = ref(null)
const currentAngle = ref(0)
const isSpinning = ref(false)
const resultText = ref('')

// 绘制转盘
function drawWheel(angle = currentAngle.value) {
  if (!canvas.value) return
  const c = canvas.value.getContext('2d')
  ctx.value = c
  const centerX = canvasSize / 2
  const centerY = canvasSize / 2
  const radius = canvasSize / 2 - 10
  const total = props.prizes.reduce((sum, p) => sum + (p.remaining || 0), 0) || 1
  
  c.clearRect(0, 0, canvasSize, canvasSize)
  let startAngle = angle
  props.prizes.forEach((prize, i) => {
    const sliceAngle = ((prize.remaining || 0) / total) * Math.PI * 2
    const endAngle = startAngle + sliceAngle
    c.beginPath()
    c.moveTo(centerX, centerY)
    c.arc(centerX, centerY, radius, startAngle, endAngle)
    c.closePath()
    c.fillStyle = `hsl(${i * 360 / props.prizes.length}, 70%, 50%)`
    c.fill()
    c.stroke()
    // 文字
    const textAngle = startAngle + sliceAngle / 2
    const textRadius = radius * 0.6
    const x = centerX + Math.cos(textAngle) * textRadius
    const y = centerY + Math.sin(textAngle) * textRadius
    c.fillStyle = '#fff'
    c.font = '14px sans-serif'
    c.textAlign = 'center'
    c.textBaseline = 'middle'
    c.fillText(prize.name, x, y)
    startAngle = endAngle
  })
}

// 旋转动画（外部调用，传入目标角度）
function spinTo(targetAngle, callback) {
  if (isSpinning.value) return
  isSpinning.value = true
  resultText.value = ''
  const startAngle = currentAngle.value
  const duration = 3000
  const startTime = performance.now()
  
  function animate(time) {
    const elapsed = time - startTime
    const progress = Math.min(elapsed / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    const angle = startAngle + (targetAngle - startAngle) * eased
    currentAngle.value = angle
    drawWheel(angle)
    if (progress < 1) {
      requestAnimationFrame(animate)
    } else {
      currentAngle.value = targetAngle
      isSpinning.value = false
      if (callback) callback()
    }
  }
  requestAnimationFrame(animate)
}

// 点击抽奖
function spin() {
  if (isSpinning.value || props.spinning) return
  if (!props.prizes.length) {
    ElMessage.warning('暂无奖项可抽')
    return
  }
  // 通知父组件执行抽奖
  emit('spin-click')
}

// 监听外部中奖结果，驱动转盘
watch(() => props.drawResult, (newResult) => {
  if (!newResult) return
  // 计算目标角度：让指针指向获奖扇区中心
  const total = props.prizes.reduce((sum, p) => sum + (p.remaining || 0), 0) || 1
  let prizeIndex = newResult.prize_index
  if (prizeIndex === undefined && newResult.prize) {
    // 根据奖品名称查找索引
    prizeIndex = props.prizes.findIndex(p => p.name === newResult.prize.name)
  }
  if (prizeIndex === -1) prizeIndex = 0
  // 计算该扇区中心角度
  let angle = 0
  for (let i = 0; i < prizeIndex; i++) {
    const slice = (props.prizes[i].remaining || 0) / total * Math.PI * 2
    angle += slice
  }
  angle += ((props.prizes[prizeIndex].remaining || 0) / total) * Math.PI
  // 添加额外的旋转圈数
  const extraSpins = 5 + Math.random() * 5
  const targetAngle = angle + extraSpins * Math.PI * 2
  // 执行动画
  spinTo(targetAngle, () => {
    if (newResult.win) {
      resultText.value = `🎉 恭喜获得 ${newResult.prize.name}！`
    } else {
      resultText.value = '😅 未中奖，再接再厉！'
    }
  })
}, { deep: true })

onMounted(() => {
  drawWheel()
})

// 当奖品变化时重绘
watch(() => props.prizes, () => drawWheel(), { deep: true })
</script>

<style scoped>
.lottery-wheel {
  position: relative;
  width: 300px;
  height: 300px;
  margin: 0 auto;
}
.lottery-wheel canvas {
  width: 100%;
  height: 100%;
}
.pointer {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 60px;
  height: 60px;
  background: #f56c6c;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: bold;
  cursor: pointer;
  border: 3px solid #fff;
  box-shadow: 0 2px 12px rgba(0,0,0,0.3);
}
.pointer:hover {
  background: #e84545;
}
.result {
  text-align: center;
  font-size: 18px;
  font-weight: 600;
  margin-top: 16px;
  color: #36b459;
}
</style>