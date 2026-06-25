<template>
  <div class="item-sale-exchange">
    <div class="two-columns">
      <!-- 左侧：购买结算区 -->
      <div class="cart-section">
        <div class="section-header">
          <span class="section-title">购买结算</span>
          <span class="section-subtitle">已选商品</span>
        </div>

        <div class="cart-items" v-if="cartItems.length > 0">
          <div v-for="(item, index) in cartItems" :key="item.id" class="cart-item">
            <div class="cart-item-info">
              <div class="cart-item-name">{{ item.name }}</div>
              <div class="cart-item-price">¥{{ item.sale_price }} × {{ item.quantity }}</div>
            </div>
            <div class="cart-item-actions">
              <span class="cart-item-total">¥{{ (item.sale_price * item.quantity).toFixed(2) }}</span>
              <el-button type="danger" link size="small" @click="removeFromCart(index)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
        <div v-else class="cart-empty">
          <el-icon><ShoppingCart /></el-icon>
          <p>暂未选择商品</p>
          <span>点击右侧商品卡片添加</span>
        </div>

        <div class="cart-summary" v-if="cartItems.length > 0">
          <div class="summary-row">
            <span>商品总数</span>
            <span>{{ totalQuantity }} 件</span>
          </div>
          <div class="summary-row">
            <span>应付总额</span>
            <span class="total-price">¥{{ totalAmount.toFixed(2) }}</span>
          </div>

          <el-divider />

          <!-- 学员选择 -->
          <div class="student-select">
            <div class="select-label">购买学员：</div>
            <StudentPicker
              v-model="selectedStudentId"
              placeholder="请选择学员"
              @student-selected="onStudentSelected"
              style="width: 100%"
            />
          </div>
          <div v-if="selectedStudent" class="student-info-row">
            <el-icon><User /></el-icon>
            <span>{{ selectedStudent.name }}</span>
            <el-icon><Coin /></el-icon>
            <span>{{ studentIntegral }} 积分</span>
          </div>

          <!-- 动态支付方式列表（修复布局） -->
          <div class="payment-methods">
            <div class="select-label">支付方式：</div>
            <div v-for="(method, idx) in paymentMethods" :key="idx" class="payment-method-item">
              <el-select v-model="method.name" placeholder="支付方式" size="small" class="method-select" @change="onPaymentMethodChange(method, idx)">
                <el-option
                  v-for="opt in paymentMethodOptions"
                  :key="opt"
                  :label="opt"
                  :value="opt"
                />
              </el-select>
              <div class="method-input-wrapper">
                <template v-if="method.type === 'points'">
                  <el-input-number
                    v-model="method.points"
                    :min="0"
                    :step="10"
                    controls-position="right"
                    size="small"
                    class="method-input-number"
                    @change="onPointsChange(method, idx)"
                  />
                  <span class="unit">积分 (≈ ¥{{ ((method.points || 0) / exchangeRate).toFixed(2) }})</span>
                </template>
                <template v-else>
                  <el-input-number
                    v-model="method.amount"
                    :min="0"
                    :precision="2"
                    :step="0.01"
                    controls-position="right"
                    size="small"
                    class="method-input-number"
                    @change="onAmountChange(method, idx)"
                  />
                  <span class="unit">元</span>
                </template>
              </div>
              <el-button
                type="danger"
                link
                size="small"
                class="method-delete-btn"
                @click="removePaymentMethod(idx)"
                v-if="paymentMethods.length > 1"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
            <el-button type="primary" link size="small" @click="addPaymentMethod" class="add-payment-btn">
              <el-icon><Plus /></el-icon> 添加支付方式
            </el-button>
            <div v-if="paymentTotalError" class="payment-error">{{ paymentTotalError }}</div>
          </div>

          <el-button
            type="primary"
            size="large"
            class="confirm-btn"
            :loading="purchasing"
            :disabled="!canSubmit"
            @click="confirmPurchase"
          >
            确认购买 ({{ totalQuantity }}件)
          </el-button>
        </div>
      </div>

      <!-- 右侧：商品列表区（与之前相同，省略） -->
      <div class="goods-section">
        <div class="section-header">
          <span class="section-title">商品列表</span>
          <el-select
            v-model="categoryFilter"
            placeholder="全部分类"
            clearable
            size="small"
            style="width: 120px"
            @change="filterGoods"
          >
            <el-option v-for="cat in categoryOptions" :key="cat" :label="cat" :value="cat" />
          </el-select>
        </div>
        <div class="goods-grid" v-loading="loadingItems">
          <div
            v-for="item in filteredGoods"
            :key="item.id"
            class="goods-card"
            :class="{
              disabled: item.stock <= 0 || item.status !== '上架',
              selected: isInCart(item.id)
            }"
            @click="addToCart(item)"
          >
            <div class="card-image">
              <el-image v-if="item.image_url" :src="item.image_url" fit="cover" class="goods-img" />
              <div v-else class="no-image"><el-icon><Picture /></el-icon></div>
              <div v-if="isInCart(item.id)" class="selected-badge"><el-icon><Check /></el-icon></div>
              <div v-if="item.stock <= 0" class="sold-out-tag">缺货</div>
            </div>
            <div class="card-info">
              <div class="goods-name">{{ item.name }}</div>
              <div class="goods-price-row">
                <span class="goods-price">¥{{ item.sale_price }}</span>
                <span class="goods-stock">库存:{{ item.stock }}</span>
              </div>
              <div class="goods-category"><el-tag size="small" type="info">{{ item.category }}</el-tag></div>
            </div>
          </div>
          <div v-if="filteredGoods.length === 0 && !loadingItems" class="empty-tip">
            <el-icon><Goods /></el-icon><span>暂无商品</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Picture,
  Goods,
  User,
  Coin,
  Delete,
  ShoppingCart,
  Check,
  Plus,
  Close
} from '@element-plus/icons-vue'
import request from '@/api/request'
import StudentPicker from '@/components/StudentPicker.vue'

// 商品列表
const saleItems = ref([])
const loadingItems = ref(false)
const categoryFilter = ref('')
const categoryOptions = ref([])

// 购物车
const cartItems = ref([])

// 学员信息
const selectedStudentId = ref(null)
const selectedStudent = ref(null)
const studentIntegral = ref(0)
const maxAvailablePoints = ref(0)

// 支付方式动态列表
const paymentMethods = ref([
  { name: '现金', amount: 0, type: 'cash' }
])
const paymentMethodOptions = ref(['现金', '微信支付', '支付宝', '银行转账', '积分'])
const exchangeRate = ref(10)
const paymentTotalError = ref('')
const purchasing = ref(false)

// 计算属性
const totalQuantity = computed(() => {
  return cartItems.value.reduce((sum, item) => sum + item.quantity, 0)
})

const totalAmount = computed(() => {
  return cartItems.value.reduce((sum, item) => sum + item.sale_price * item.quantity, 0)
})

const filteredGoods = computed(() => {
  if (!categoryFilter.value) return saleItems.value
  return saleItems.value.filter(item => item.category === categoryFilter.value)
})

const currentPaidTotal = computed(() => {
  let total = 0
  for (const method of paymentMethods.value) {
    if (method.type === 'points') {
      total += (method.points || 0) / exchangeRate.value
    } else {
      total += method.amount || 0
    }
  }
  return total
})

const remainingAmount = computed(() => {
  return Math.max(0, totalAmount.value - currentPaidTotal.value)
})

const canSubmit = computed(() => {
  if (cartItems.value.length === 0) return false
  if (!selectedStudentId.value) return false
  const diff = Math.abs(currentPaidTotal.value - totalAmount.value)
  if (diff > 0.01) return false
  let totalPointsUsed = 0
  for (const method of paymentMethods.value) {
    if (method.type === 'points') {
      totalPointsUsed += method.points || 0
    }
  }
  if (totalPointsUsed > maxAvailablePoints.value) return false
  return true
})

function isInCart(itemId) {
  return cartItems.value.some(item => item.id === itemId)
}

function addToCart(item) {
  if (item.stock <= 0 || item.status !== '上架') {
    ElMessage.warning('该商品库存不足或已下架')
    return
  }
  const existing = cartItems.value.find(cartItem => cartItem.id === item.id)
  if (existing) {
    if (existing.quantity + 1 > item.stock) {
      ElMessage.warning(`库存不足，当前库存 ${item.stock}`)
      return
    }
    existing.quantity++
  } else {
    cartItems.value.push({
      id: item.id,
      name: item.name,
      sale_price: item.sale_price,
      quantity: 1,
      stock: item.stock
    })
  }
  resetPaymentMethods()
}

function removeFromCart(index) {
  cartItems.value.splice(index, 1)
  resetPaymentMethods()
}

function resetPaymentMethods() {
  paymentMethods.value = [
    { name: '现金', amount: totalAmount.value, type: 'cash', points: 0 }
  ]
  paymentTotalError.value = ''
}

function onAmountChange(method, index) {
  if (method.amount < 0) method.amount = 0
  if (method.amount > totalAmount.value) method.amount = totalAmount.value
  autoDistributeRemaining()
  validatePaymentTotal()
}

function onPointsChange(method, index) {
  if (method.points < 0) method.points = 0
  let totalPointsUsed = 0
  for (const m of paymentMethods.value) {
    if (m.type === 'points') {
      totalPointsUsed += m.points || 0
    }
  }
  if (totalPointsUsed > maxAvailablePoints.value) {
    method.points = Math.max(0, maxAvailablePoints.value - (totalPointsUsed - method.points))
  }
  autoDistributeRemaining()
  validatePaymentTotal()
}

function autoDistributeRemaining() {
  const filledMethods = []
  const emptyMethods = []
  for (let i = 0; i < paymentMethods.value.length; i++) {
    const m = paymentMethods.value[i]
    if (m.type === 'points') {
      if (m.points && m.points > 0) {
        filledMethods.push(i)
      } else {
        emptyMethods.push(i)
      }
    } else {
      if (m.amount && m.amount > 0) {
        filledMethods.push(i)
      } else {
        emptyMethods.push(i)
      }
    }
  }
  let paid = 0
  for (const idx of filledMethods) {
    const m = paymentMethods.value[idx]
    if (m.type === 'points') {
      paid += (m.points || 0) / exchangeRate.value
    } else {
      paid += m.amount || 0
    }
  }
  const remaining = totalAmount.value - paid
  if (remaining <= 0.01) {
    for (const idx of emptyMethods) {
      const m = paymentMethods.value[idx]
      if (m.type === 'points') {
        m.points = 0
      } else {
        m.amount = 0
      }
    }
    return
  }
  if (emptyMethods.length === 1) {
    const idx = emptyMethods[0]
    const m = paymentMethods.value[idx]
    if (m.type === 'points') {
      let needPoints = Math.ceil(remaining * exchangeRate.value)
      let totalPointsUsed = 0
      for (const pm of paymentMethods.value) {
        if (pm.type === 'points') {
          totalPointsUsed += pm.points || 0
        }
      }
      const availablePoints = maxAvailablePoints.value - (totalPointsUsed - (m.points || 0))
      m.points = Math.min(needPoints, availablePoints)
    } else {
      m.amount = remaining
    }
  }
  validatePaymentTotal()
}

function onPaymentMethodChange(method, index) {
  if (method.name === '积分') {
    method.type = 'points'
    method.amount = 0
    method.points = 0
  } else {
    method.type = 'cash'
    method.amount = 0
    method.points = 0
  }
  nextTick(() => {
    autoDistributeRemaining()
    validatePaymentTotal()
  })
}

function addPaymentMethod() {
  const defaultName = paymentMethodOptions.value.find(opt => opt !== '积分') || '现金'
  paymentMethods.value.push({
    name: defaultName,
    amount: 0,
    type: defaultName === '积分' ? 'points' : 'cash',
    points: 0
  })
  nextTick(() => {
    autoDistributeRemaining()
    validatePaymentTotal()
  })
}

function removePaymentMethod(idx) {
  if (paymentMethods.value.length <= 1) {
    ElMessage.warning('至少保留一种支付方式')
    return
  }
  paymentMethods.value.splice(idx, 1)
  nextTick(() => {
    autoDistributeRemaining()
    validatePaymentTotal()
  })
}

function validatePaymentTotal() {
  let totalPaid = 0
  let totalPointsUsed = 0
  for (const method of paymentMethods.value) {
    if (method.type === 'points') {
      totalPaid += (method.points || 0) / exchangeRate.value
      totalPointsUsed += method.points || 0
    } else {
      totalPaid += method.amount || 0
    }
  }
  const diff = Math.abs(totalPaid - totalAmount.value)
  if (diff > 0.01) {
    paymentTotalError.value = `支付总额 ${totalPaid.toFixed(2)} 与应付总额 ${totalAmount.value.toFixed(2)} 不相等`
    return false
  }
  if (totalPointsUsed > maxAvailablePoints.value) {
    paymentTotalError.value = `所需积分 ${totalPointsUsed} 超过学员可用积分 ${maxAvailablePoints.value}`
    return false
  }
  paymentTotalError.value = ''
  return true
}

watch(totalAmount, () => {
  resetPaymentMethods()
})

watch(studentIntegral, (newVal) => {
  maxAvailablePoints.value = newVal
  autoDistributeRemaining()
  validatePaymentTotal()
})

async function onStudentSelected(student) {
  if (student && student.id) {
    selectedStudent.value = student
    selectedStudentId.value = student.id
    await fetchStudentIntegral(student.id)
  } else {
    selectedStudent.value = null
    selectedStudentId.value = null
    studentIntegral.value = 0
    maxAvailablePoints.value = 0
  }
  resetPaymentMethods()
}

async function fetchStudentIntegral(studentId) {
  try {
    const res = await request.get(`/score/student/${studentId}`)
    studentIntegral.value = res.data?.total_integral || 0
    maxAvailablePoints.value = studentIntegral.value
  } catch {
    studentIntegral.value = 0
    maxAvailablePoints.value = 0
  }
}

async function confirmPurchase() {
  if (!validatePaymentTotal()) {
    ElMessage.warning(paymentTotalError.value)
    return
  }
  if (cartItems.value.length === 0) {
    ElMessage.warning('请先选择商品')
    return
  }
  if (!selectedStudentId.value) {
    ElMessage.warning('请选择购买学员')
    return
  }

  // 构建 payments 数组 —— 符合后端 PaymentItem 模型
  const payments = paymentMethods.value.map(method => ({
    type: method.type,
    amount: method.type === 'cash' ? (method.amount || 0) : 0,
    points: method.type === 'points' ? (method.points || 0) : 0,
    method: method.name || '其他'
  }));

  const orderData = {
    student_id: Number(selectedStudentId.value),
    items: cartItems.value.map(item => ({
      item_id: item.id,
      quantity: item.quantity
    })),
    payments
  };

  purchasing.value = true;
  try {
    const res = await request.post('/sales/order', orderData);
    if (res.code === 0) {
      ElMessage.success(`订单 ${res.data.order_no} 创建成功`);
      cartItems.value = [];
      selectedStudentId.value = null;
      selectedStudent.value = null;
      studentIntegral.value = 0;
      maxAvailablePoints.value = 0;
      resetPaymentMethods();
      await loadItems();
    } else {
      ElMessage.error(res.message || '创建订单失败');
    }
  } catch (error) {
    console.error(error);
    ElMessage.error(error.response?.data?.detail || '创建订单失败');
  } finally {
    purchasing.value = false;
  }
}

async function loadCategories() {
  try {
    const res = await request.get('/item-categories')
    if (res.code === 0 && res.data && res.data.length) {
      categoryOptions.value = res.data
    }
  } catch (e) {
    console.error('加载商品类别失败', e)
  }
}

async function loadExchangeRate() {
  try {
    const res = await request.get('/exchange-rate')
    if (res.code === 0 && res.data) {
      exchangeRate.value = res.data
    }
  } catch (e) {
    console.error('加载积分汇率失败', e)
    exchangeRate.value = 10
  }
}

async function loadPaymentMethodOptions() {
  try {
    const res = await request.get('/payment-methods')
    if (res.code === 0 && res.data && res.data.length) {
      paymentMethodOptions.value = res.data
    }
  } catch (e) {
    console.error('加载支付方式选项失败', e)
  }
}

async function loadItems() {
  loadingItems.value = true
  try {
    const res = await request.get('/items', {
      params: { page_size: 100, item_type: 'sale', status: '上架' }
    })
    const items = res.data?.items || []
    saleItems.value = items.map(item => ({ ...item, loading: false }))
  } catch (e) {
    ElMessage.error('加载商品列表失败')
  } finally {
    loadingItems.value = false
  }
}

function filterGoods() {}

onMounted(async () => {
  await loadExchangeRate()
  await loadCategories()
  await loadPaymentMethodOptions()
  await loadItems()
})
</script>

<style scoped>
/* 全局样式（与之前相同，增加支付方式布局修复） */
.item-sale-exchange {
  height: 100%;
  padding: 20px;
  background: var(--app-bg);
  overflow: hidden;
  box-sizing: border-box;
  font-size: 14px;
}
.two-columns {
  display: flex;
  gap: 20px;
  height: 100%;
}
/* 左侧结算区 */
.cart-section {
  width: 40%;
  background: var(--surface);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}
.section-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-light);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  font-size: 14px;
}
.section-title { font-weight: 600; color: var(--text-primary); }
.section-subtitle { color: var(--text-placeholder); }
.cart-items {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}
.cart-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: var(--surface-soft);
  border-radius: 12px;
  margin-bottom: 8px;
  font-size: 14px;
}
.cart-item-info {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cart-item-name { font-weight: 500; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cart-item-price { font-size: 12px; color: var(--text-placeholder); }
.cart-item-actions { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }
.cart-item-total { font-weight: 600; color: var(--danger); white-space: nowrap; }
.cart-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--text-placeholder);
  gap: 10px;
  font-size: 14px;
}
.cart-summary {
  padding: 16px;
  border-top: 1px solid var(--border-light);
  background: var(--surface);
  flex-shrink: 0;
}
.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 14px;
}
.total-price { font-size: 18px; font-weight: 700; color: var(--danger); }
.student-select { margin: 12px 0; }
.select-label { font-size: 14px; margin-bottom: 6px; color: var(--text-secondary); }
.student-info-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 12px;
  background: var(--surface-green);
  border-radius: 10px;
  font-size: 14px;
  color: var(--brand-500);
  margin: 12px 0;
  flex-wrap: wrap;
}
/* 支付方式区域布局修复 */
.payment-methods {
  margin: 16px 0;
}
.payment-method-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.method-select {
  width: 120px;
  flex-shrink: 0;
}
.method-input-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 180px;
}
.method-input-number {
  width: 140px;
}
.unit {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
}
.method-delete-btn {
  flex-shrink: 0;
  margin-left: auto;
}
.add-payment-btn {
  margin-top: 6px;
}
.payment-error {
  color: var(--danger);
  font-size: 12px;
  margin-top: 8px;
  padding-left: 8px;
}
.confirm-btn {
  width: 100%;
  margin-top: 16px;
  height: 44px;
  border-radius: 22px;
  font-size: 14px;
}
/* 右侧商品区（与之前相同） */
.goods-section {
  width: 60%;
  background: var(--surface);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}
.goods-grid {
  flex: 1;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
  padding: 16px;
}
.goods-card {
  background: var(--surface);
  border-radius: 12px;
  border: 1px solid var(--border-light);
  cursor: pointer;
  transition: all 0.2s ease;
  height: 280px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.goods-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-color: var(--brand-500); }
.goods-card.selected { border-color: var(--brand-500); background: var(--surface-green); }
.goods-card.disabled { opacity: 0.6; cursor: not-allowed; }
.card-image {
  position: relative;
  height: 150px;
  background: var(--surface-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}
.goods-img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.2s; }
.no-image .el-icon { font-size: 32px; color: var(--text-placeholder); }
.selected-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 22px;
  height: 22px;
  background: var(--brand-500);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--surface);
  font-size: 12px;
}
.sold-out-tag {
  position: absolute;
  top: 6px;
  left: 6px;
  background: rgba(0,0,0,0.65);
  color: var(--surface);
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 12px;
}
.card-info {
  padding: 10px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.goods-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.goods-price-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 14px;
}
.goods-price { font-weight: 700; color: var(--danger); }
.goods-stock { font-size: 12px; color: var(--text-secondary); }
.goods-category { margin-top: auto; }
.empty-tip {
  grid-column: 1/-1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 50px 20px;
  color: var(--text-placeholder);
  gap: 12px;
  font-size: 14px;
}
@media (max-width: 900px) {
  .two-columns { flex-direction: column; }
  .cart-section, .goods-section { width: 100%; height: 50%; }
  .goods-grid { max-height: 300px; }
}
</style>