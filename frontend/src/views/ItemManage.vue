<template>
  <div class="item-manage">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-right">
        <el-input
          v-model="filters.keyword"
          placeholder="搜索物品名称"
          clearable
          prefix-icon="Search"
          class="search-input"
          @clear="fetchItems"
          @keyup.enter="fetchItems"
        />
        <el-select
          v-model="filters.category"
          placeholder="商品类别"
          clearable
          class="category-select"
          @change="fetchItems"
        >
          <el-option v-for="cat in categoryOptions" :key="cat" :label="cat" :value="cat" />
        </el-select>
        <el-button type="primary" @click="openCreateDialog" class="add-btn">
          <el-icon><Plus /></el-icon> 新增物品
        </el-button>
      </div>
    </div>

    <!-- 卡片网格 -->
    <div class="items-grid" v-loading="loading">
      <div
        v-for="item in items"
        :key="item.id"
        class="item-card"
        :class="{ 'item-disabled': item.status !== '上架' }"
      >
        <!-- 图片区域 -->
        <div class="card-image" @click="editItem(item)">
          <el-image
            v-if="item.image_url"
            :src="item.image_url"
            fit="cover"
            class="item-img"
          />
          <div v-else class="no-image">
            <el-icon><Picture /></el-icon>
            <span>暂无图片</span>
          </div>
          <div class="status-tag" :class="item.status === '上架' ? 'status-on' : 'status-off'">
            {{ item.status }}
          </div>
        </div>

        <!-- 信息区域 -->
        <div class="card-info">
          <div class="card-title">
            <span class="item-name">{{ item.name }}</span>
            <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, item)">
              <el-button type="primary" link class="more-btn">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="records">销售记录</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>

          <div class="card-meta">
            <el-tag size="small" type="info" class="category-tag">{{ item.category }}</el-tag>
            <el-tag 
              size="small" 
              :type="item.pay_option === 'cash' ? 'success' : (item.pay_option === 'points' ? 'warning' : 'primary')"
              class="pay-tag"
            >
              {{ item.pay_option === 'cash' ? '仅现金' : (item.pay_option === 'points' ? '仅积分' : '现金/积分') }}
            </el-tag>
          </div>

          <div class="card-stats">
            <div class="stat-item">
              <span class="stat-label">售价</span>
              <span class="stat-value price">¥{{ item.sale_price }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">库存</span>
              <span class="stat-value stock" :class="{ 'stock-low': item.stock <= 5 && item.stock > 0, 'stock-out': item.stock === 0 }">
                {{ item.stock }}
              </span>
            </div>
            <div class="stat-item">
              <span class="stat-label">成本</span>
              <span class="stat-value cost">¥{{ item.cost_price }}</span>
            </div>
          </div>

          <div class="card-actions">
            <el-button size="small" type="warning" @click="stockIn(item)">
              <el-icon><FolderAdd /></el-icon> 入库
            </el-button>
            <el-button size="small" type="primary" @click="editItem(item)">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="items.length === 0 && !loading" class="empty-state">
        <el-icon><Goods /></el-icon>
        <p>暂无物品数据</p>
        <el-button type="primary" @click="openCreateDialog">立即添加</el-button>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-box" v-if="total > pageSize">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="fetchItems"
      />
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑物品' : '新增物品'" width="550px" class="beauty-dialog">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="90px">
        <el-form-item label="物品名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入物品名称" />
        </el-form-item>
        <el-form-item label="类别" prop="category">
          <el-select v-model="form.category" style="width: 100%">
            <el-option v-for="cat in categoryOptions" :key="cat" :label="cat" :value="cat" />
          </el-select>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="销售价格" prop="sale_price">
              <el-input-number v-model="form.sale_price" :min="0" :precision="2" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="采购成本" prop="cost_price">
              <el-input-number v-model="form.cost_price" :min="0" :precision="2" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="初始库存" prop="stock">
              <el-input-number v-model="form.stock" :min="0" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-radio-group v-model="form.status">
                <el-radio label="上架" value="上架">上架</el-radio>
                <el-radio label="下架" value="下架">下架</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="支付方式" prop="pay_option">
          <el-radio-group v-model="form.pay_option">
            <el-radio label="cash" value="cash">仅现金</el-radio>
            <el-radio label="points" value="points">仅积分</el-radio>
            <el-radio label="both" value="both">现金/积分</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="商品图片">
          <div class="upload-wrapper">
            <el-upload
              :action="uploadUrl"
              :headers="uploadHeaders"
              :on-success="handleImageUploadSuccess"
              :on-error="handleImageUploadError"
              :show-file-list="false"
              :before-upload="beforeImageUpload"
              class="image-upload"
            >
              <el-button type="primary">选择图片</el-button>
            </el-upload>
            <div class="upload-tip">建议使用正方形图片，支持 jpg/png/webp，不超过 2MB</div>
          </div>
          <div v-if="form.image_url" class="image-preview">
            <el-image :src="form.image_url" fit="cover" style="width: 80px; height: 80px; border-radius: 8px" />
            <el-button type="danger" link size="small" @click="removeImage">删除图片</el-button>
          </div>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveItem" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 入库弹窗 -->
    <el-dialog v-model="stockDialogVisible" title="入库" width="450px" class="beauty-dialog">
      <el-form :model="stockForm" label-width="80px">
        <el-form-item label="物品名称">
          <span>{{ currentItem?.name }}</span>
        </el-form-item>
        <el-form-item label="入库数量">
          <el-input-number v-model="stockForm.quantity" :min="1" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="入库单价">
          <el-input-number v-model="stockForm.unit_price" :min="0" :precision="2" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="采购日期">
          <el-date-picker 
            v-model="stockForm.purchase_date" 
            type="date" 
            value-format="YYYY-MM-DD"
            placeholder="选择采购日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="stockForm.remark" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="stockDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmStockIn" :loading="stockLoading">确定入库</el-button>
      </template>
    </el-dialog>

    <!-- 销售记录弹窗 -->
    <el-dialog v-model="salesRecordDialogVisible" title="销售记录" width="850px" class="beauty-dialog sales-record-dialog">
      <el-table :data="salesRecords" border stripe>
        <el-table-column label="学员" width="200">
          <template #default="{ row }">
            <div class="student-cell">
              <AppImage :src="row.student_avatar" :size="36" shape="circle" class="student-avatar" />
              <div class="student-info">
                <div class="student-name">{{ row.student_name }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="物品描述" min-width="200" />
        <el-table-column label="应收金额" width="100" align="center">
          <template #default="{ row }">¥{{ row.amount }}</template>
        </el-table-column>
        <el-table-column label="实收" width="130" align="center">
          <template #default="{ row }">
            <span v-if="row.points_used > 0" class="points-used">{{ row.points_used }}积分</span>
            <span v-if="row.paid_amount > 0" class="cash-paid">¥{{ row.paid_amount }}</span>
            <span v-if="row.points_used === 0 && row.paid_amount === 0">-</span>
          </template>
        </el-table-column>
        <el-table-column label="支付方式" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="getPaymentTagType(row.payment_method)" size="small">
              {{ formatPaymentMethod(row.payment_method) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="paid_at" label="销售时间" width="170" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Picture, Goods, MoreFilled, Edit, FolderAdd, Delete } from '@element-plus/icons-vue'
import request from '@/api/request'
import { DEFAULT_AVATAR_SVG } from '@/utils/constants'

const items = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(12)
const total = ref(0)
const filters = reactive({ keyword: '', category: '' })
const categoryOptions = ref(['教材', '教具', '礼品', '办公用品', '其他'])

const dialogVisible = ref(false)
const editing = ref(false)
const saving = ref(false)
const formRef = ref(null)
const form = reactive({
  id: null,
  name: '',
  category: '其他',
  sale_price: 0,
  cost_price: 0,
  stock: 0,
  unit: '个',
  status: '上架',
  remark: '',
  pay_option: 'both',
  image_url: ''
})

const rules = {
  name: [{ required: true, message: '请输入物品名称', trigger: 'blur' }]
}

const uploadUrl = '/api/upload/item-image'
const uploadHeaders = computed(() => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }))

const stockDialogVisible = ref(false)
const stockForm = reactive({ quantity: 1, unit_price: 0, remark: '', purchase_date: '' })
const currentItem = ref(null)
const stockLoading = ref(false)

const salesRecordDialogVisible = ref(false)
const salesRecords = ref([])

function formatPaymentMethod(method) {
  if (method === '积分') return '积分支付'
  if (method === 'wechat') return '微信支付'
  if (method === 'alipay') return '支付宝'
  if (method === 'cash') return '现金'
  return method || '-'
}

function getPaymentTagType(method) {
  if (method === '积分') return 'warning'
  if (method === 'wechat' || method === 'alipay') return 'primary'
  if (method === 'cash') return 'success'
  return 'info'
}

async function loadCategories() {
  try {
    const res = await request.get('/item-categories')
    if (res.code === 0 && res.data && res.data.length) {
      categoryOptions.value = res.data
    }
  } catch (e) {}
}

async function fetchItems() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
      keyword: filters.keyword || undefined,
      category: filters.category || undefined
    }
    const res = await request.get('/items', { params })
    items.value = res.data?.items || []
    total.value = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  editing.value = false
  Object.assign(form, {
    id: null, name: '', category: categoryOptions.value[0] || '其他',
    sale_price: 0, cost_price: 0, stock: 0, unit: '个',
    status: '上架', remark: '', pay_option: 'both', image_url: ''
  })
  dialogVisible.value = true
}

function editItem(item) {
  editing.value = true
  Object.assign(form, item)
  dialogVisible.value = true
}

function handleCommand(cmd, item) {
  if (cmd === 'records') viewSalesRecords(item)
  else if (cmd === 'delete') deleteItem(item)
}

function beforeImageUpload(file) {
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isImage) { ElMessage.error('只能上传图片文件'); return false }
  if (!isLt2M) { ElMessage.error('图片大小不能超过 2MB'); return false }
  return true
}

function handleImageUploadSuccess(res) {
  if (res.code === 0 && res.data?.url) {
    form.image_url = res.data.url
    ElMessage.success('图片上传成功')
  } else {
    ElMessage.error(res.message || '上传失败')
  }
}

function handleImageUploadError() { ElMessage.error('上传失败') }
function removeImage() { form.image_url = '' }

async function saveItem() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const submitData = { ...form, item_type: 'sale' }
    if (editing.value) {
      await request.put(`/items/${form.id}`, submitData)
      ElMessage.success('更新成功')
    } else {
      await request.post('/items', submitData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchItems()
  } finally { saving.value = false }
}

async function deleteItem(item) {
  try {
    await ElMessageBox.confirm(`确认删除 "${item.name}"？`, '提示', { type: 'warning' })
    await request.delete(`/items/${item.id}`)
    ElMessage.success('已删除')
    fetchItems()
  } catch {}
}

function stockIn(item) {
  currentItem.value = item
  stockForm.quantity = 1
  stockForm.unit_price = 0
  stockForm.remark = ''
  stockDialogVisible.value = true
}

async function confirmStockIn() {
  if (!stockForm.quantity || stockForm.quantity <= 0) {
    ElMessage.warning('请输入入库数量')
    return
  }
  stockLoading.value = true
  try {
    await request.post(`/items/${currentItem.value.id}/stock-in`, null, {
      params: { 
        quantity: stockForm.quantity, 
        unit_price: stockForm.unit_price, 
        remark: stockForm.remark,
        purchase_date: stockForm.purchase_date || undefined
      }
    })
    ElMessage.success('入库成功')
    stockDialogVisible.value = false
    fetchItems()
  } finally { 
    stockLoading.value = false 
  }
}

async function viewSalesRecords(item) {
  try {
    const res = await request.get('/misc-fees', { params: { fee_type: 'item_sale', page_size: 100 } })
    const allRecords = res.data?.items || []
    const recordsWithAvatar = await Promise.all(
      allRecords.filter(r => r.description && r.description.includes(item.name))
        .map(async (record) => {
          if (record.student_id) {
            try {
              const studentRes = await request.get(`/student/student/${record.student_id}`)
              record.student_avatar = studentRes.data?.avatar || ''
            } catch (e) {
              record.student_avatar = ''
            }
          }
          return record
        })
    )
    salesRecords.value = recordsWithAvatar
    salesRecordDialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载销售记录失败')
  }
}

onMounted(async () => {
  await loadCategories()
  await fetchItems()
})
</script>

<style scoped>
.item-manage {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  overflow-y: auto;
  padding: 0 0 var(--space-4);
}

.page-header {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xs);
}

.header-right { display: flex; gap: var(--space-3); align-items: center; flex-wrap: wrap; }

.search-input { width: 240px; }
.category-select { width: 140px; }

.items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-4);
}

.item-card {
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-xs);
}

.item-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.card-image {
  position: relative;
  aspect-ratio: 1 / 1;
  background: linear-gradient(135deg, var(--surface-soft) 0%, var(--gray-100) 100%);
  cursor: pointer;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.item-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.no-image {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--text-placeholder);
}

.no-image .el-icon { font-size: 36px; }
.no-image span { font-size: 11px; }

.status-tag {
  position: absolute;
  top: 8px;
  left: 8px;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
}

.status-on { background: var(--brand-500); color: var(--surface); }
.status-off { background: var(--danger); color: var(--surface); }

.card-info { padding: 12px; }

.card-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-2);
}

.item-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.more-btn { opacity: 0.5; padding: 0; }

.card-meta {
  display: flex;
  gap: 6px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.category-tag, .pay-tag { font-size: 10px; height: 20px; line-height: 18px; }

.card-stats {
  display: flex;
  justify-content: space-around;
  padding: 8px 0;
  border-top: 1px solid var(--border-light);
  border-bottom: 1px solid var(--border-light);
  margin-bottom: 10px;
}

.stat-item { text-align: center; flex: 1; }

.stat-label {
  display: block;
  font-size: 10px;
  color: var(--text-placeholder);
  margin-bottom: 2px;
}

.stat-value { font-size: 14px; font-weight: 700; }
.stat-value.price { color: var(--danger); }
.stat-value.stock { color: var(--success); }
.stat-value.stock-low { color: var(--warning); }
.stat-value.stock-out { color: var(--danger); }

.card-actions { display: flex; gap: var(--space-2); }
.card-actions .el-button { flex: 1; border-radius: var(--radius-pill); font-size: 12px; height: var(--control-height); }

.empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px var(--space-4);
  background: var(--surface);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  color: var(--text-placeholder);
  gap: var(--space-3);
}

.pagination-box {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  padding-top: var(--space-3);
}

/* 弹窗 */
.beauty-dialog :deep(.el-dialog__header) { border-bottom: 1px solid var(--border-light); padding: 16px 20px; }
.beauty-dialog :deep(.el-dialog__title) { font-size: 16px; font-weight: 700; }
.beauty-dialog :deep(.el-dialog__body) { padding: 20px; }
.beauty-dialog :deep(.el-dialog__footer) { border-top: 1px solid var(--border-light); padding: 16px 20px; }

.upload-wrapper { display: flex; flex-direction: column; gap: var(--space-2); }
.image-upload { display: inline-block; }
.upload-tip { font-size: 12px; color: var(--text-secondary); line-height: 1.4; margin: 0; }
.image-preview { margin-top: var(--space-3); display: flex; align-items: center; gap: var(--space-3); }

/* 销售记录 */
.student-cell { display: flex; align-items: center; gap: var(--space-3); }
.student-avatar { flex-shrink: 0; background: var(--brand-500); color: var(--surface); }
.student-info { display: flex; flex-direction: column; }
.student-name { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.points-used { color: var(--warning); font-weight: 600; }
.cash-paid { color: var(--danger); font-weight: 600; }

.sales-record-dialog :deep(.el-table th) { background-color: var(--surface-soft); }

@media (max-width: 768px) {
  .item-manage { padding: var(--space-3); }
  .items-grid { grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: var(--space-3); }
  .item-name { font-size: 13px; }
}
</style>
