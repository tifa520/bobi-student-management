<template>
  <div class="inventory-record-page">
    <el-tabs v-model="activeTab" class="record-tabs" @tab-click="handleTabClick">
      <el-tab-pane name="purchase">
        <template #label>
          <span :class="{ 'tab-active': activeTab === 'purchase' }">入库记录</span>
        </template>
      </el-tab-pane>
      <el-tab-pane name="sale">
        <template #label>
          <span :class="{ 'tab-active': activeTab === 'sale' }">出库记录</span>
        </template>
      </el-tab-pane>
    </el-tabs>

    <div class="filter-bar">
      <el-select
        v-model="filters.item_id"
        placeholder="选择物品"
        clearable
        filterable
        style="width: 200px"
        @change="handleFilterChange"
      >
        <el-option
          v-for="item in items"
          :key="item.id"
          :label="item.name"
          :value="item.id"
        />
      </el-select>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
        style="width: 280px"
        @change="handleFilterChange"
      />
      <el-button type="primary" @click="handleSearch">查询</el-button>
      <el-button @click="resetFilters">重置</el-button>
    </div>

    <!-- 入库记录表格 -->
    <div v-if="activeTab === 'purchase'" class="table-wrapper" v-loading="loading">
      <el-table :data="records" border stripe>
        <el-table-column prop="created_at" label="入库时间" width="160" />
        <el-table-column label="商品图片" width="60" align="center">
          <template #default="{ row }">
            <el-image
              v-if="row.item_image"
              :src="row.item_image"
              fit="cover"
              style="width:40px; height:40px; border-radius:4px; cursor:pointer;"
              :preview-src-list="[row.item_image]"
              :z-index="99999"
              preview-teleported
            />
            <div v-else style="width:40px; height:40px; background:#f5f7fa; border-radius:4px;"></div>
          </template>
        </el-table-column>
        <el-table-column prop="item_name" label="物品名称" min-width="150" />
        <el-table-column prop="batch_no" label="批次号" width="160" />
        <el-table-column label="入库数量" width="100" align="center">
          <template #default="{ row }">
            <span class="text-success">+{{ row.quantity }}</span>
          </template>
        </el-table-column>
        <el-table-column label="入库单价" width="100" align="right">
          <template #default="{ row }">￥{{ row.unit_price }}</template>
        </el-table-column>
        <el-table-column label="入库金额" width="120" align="right">
          <template #default="{ row }">￥{{ row.total_amount }}</template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="150" />
      </el-table>
      <div v-if="records.length === 0 && !loading" class="empty-state">
        <el-icon><Document /></el-icon>
        <span>暂无入库记录</span>
      </div>
    </div>

    <!-- 出库记录表格 -->
    <div v-if="activeTab === 'sale'" class="table-wrapper" v-loading="loading">
      <el-table :data="records" border stripe>
        <el-table-column prop="created_at" label="出库时间" width="160" />
        <el-table-column label="商品图片" width="60" align="center">
          <template #default="{ row }">
            <el-image
              v-if="row.item_image"
              :src="row.item_image"
              fit="cover"
              style="width:40px; height:40px; border-radius:4px; cursor:pointer;"
              :preview-src-list="[row.item_image]"
              :z-index="99999"
              preview-teleported
            />
            <div v-else style="width:40px; height:40px; background:#f5f7fa; border-radius:4px;"></div>
          </template>
        </el-table-column>
        <el-table-column prop="item_name" label="物品名称" min-width="150" />
        <el-table-column prop="batch_no" label="批次号" width="160" />
        <el-table-column label="出库数量" width="100" align="center">
          <template #default="{ row }">
            <span class="text-danger">{{ row.quantity }}</span>
          </template>
        </el-table-column>
        <el-table-column label="销售单价" width="100" align="right">
          <template #default="{ row }">￥{{ row.unit_price }}</template>
        </el-table-column>
        <el-table-column label="销售金额" width="120" align="right">
          <template #default="{ row }">￥{{ row.total_amount }}</template>
        </el-table-column>
        <el-table-column label="销售成本" width="120" align="right">
          <template #default="{ row }">￥{{ row.cost_of_goods_sold }}</template>
        </el-table-column>
        <el-table-column label="毛利" width="100" align="right">
          <template #default="{ row }">
            <span :class="getProfitClass(row.total_amount, row.cost_of_goods_sold)">
              ￥{{ (row.total_amount - row.cost_of_goods_sold).toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="出库方式" width="100">
          <template #default="{ row }">
            <el-tag :type="getPaymentTypeTag(row.payment_method)" size="small">
              {{ getPaymentTypeLabel(row.payment_method) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="150" />
      </el-table>
      <div v-if="records.length === 0 && !loading" class="empty-state">
        <el-icon><Document /></el-icon>
        <span>暂无出库记录</span>
      </div>
    </div>

    <div class="pagination-box" v-if="total > pageSize">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="fetchRecords"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Document } from '@element-plus/icons-vue'
import request from '@/api/request'

const activeTab = ref('purchase')
const loading = ref(false)
const records = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const items = ref([])

const filters = reactive({
  item_id: null
})
const dateRange = ref(null)

// 加载物品列表
async function loadItems() {
  try {
    const res = await request.get('/items', { params: { page_size: 100, item_type: 'sale' } })
    items.value = res.data?.items || []
  } catch (e) {
    console.error('加载物品列表失败', e)
  }
}

// 获取记录
async function fetchRecords() {
  loading.value = true
  try {
    const transactionType = activeTab.value === 'purchase' ? 'purchase' : 'sale'
    const params = {
      page: page.value,
      page_size: pageSize.value,
      transaction_type: transactionType,
      item_id: filters.item_id || undefined,
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1]
    }
    const res = await request.get('/inventory/records', { params })
    records.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e) {
    console.error('加载记录失败', e)
    ElMessage.error('加载记录失败')
  } finally {
    loading.value = false
  }
}

// 筛选变化时重置页码
function handleFilterChange() {
  page.value = 1
  fetchRecords()
}

function handleSearch() {
  page.value = 1
  fetchRecords()
}

// 重置筛选条件
function resetFilters() {
  filters.item_id = null
  dateRange.value = null
  page.value = 1
  fetchRecords()
}

// 切换页签
function handleTabClick() {
  page.value = 1
  fetchRecords()
}

// 获取利润样式类
function getProfitClass(amount, cost) {
  const profit = amount - cost
  if (profit > 0) return 'text-success'
  if (profit < 0) return 'text-danger'
  return ''
}

// 获取支付方式标签类型
function getPaymentTypeTag(method) {
  const map = {
    'wechat': 'success',
    'alipay': 'primary',
    'cash': 'warning',
    'points': 'danger',
    'mix': 'info'
  }
  return map[method] || 'info'
}

// 获取支付方式显示文本
function getPaymentTypeLabel(method) {
  const map = {
    'wechat': '微信支付',
    'alipay': '支付宝',
    'cash': '现金',
    'points': '积分抵扣',
    'mix': '组合支付'
  }
  return map[method] || method || '-'
}

// 监听 activeTab 变化，重新获取数据
watch(activeTab, () => {
  page.value = 1
  fetchRecords()
})

onMounted(async () => {
  await loadItems()
  await fetchRecords()
})
</script>

<style scoped>
.inventory-record-page {
  padding: 20px;
  background: var(--app-bg);
  min-height: 100%;
}

.record-tabs {
  background: var(--surface);
  padding: 0 20px;
  border-radius: 12px 12px 0 0;
  margin-bottom: 0;
}

.record-tabs :deep(.el-tabs__header) {
  margin: 0;
}

.tab-active {
  color: var(--brand-500);
  font-weight: 500;
}

.filter-bar {
  background: var(--surface);
  padding: 16px 20px;
  border-radius: 0 0 12px 12px;
  margin-bottom: 20px;
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.table-wrapper {
  background: var(--surface);
  border-radius: 12px;
  padding: 0;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.pagination-box {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  background: var(--surface);
  padding: 16px 20px;
  border-radius: 12px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--text-placeholder);
  gap: 12px;
}

.empty-state .el-icon {
  font-size: 48px;
}

.text-success {
  color: var(--success);
}

.text-danger {
  color: var(--danger);
}
</style>