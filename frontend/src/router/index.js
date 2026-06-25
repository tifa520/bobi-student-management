// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useTagsViewStore } from '@/stores/tagsView'
import Layout from '@/layouts/index.vue'

const routes = [
  // ========== 登录页（独立，不包含在 Layout 中） ==========
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' }
  },
  // ========== 重定向页（用于刷新标签页） ==========
  {
    path: '/redirect/:path(.*)',
    name: 'Redirect',
    component: () => import('@/views/Redirect.vue')
  },
  // ========== 所有受保护页面（包含在 Layout 中） ==========
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      // -------- 个人中心 --------
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue'),
        meta: { title: '个人中心', requiresAuth: true }
      },
      // -------- 工作台 --------
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '工作台', affix: true }
      },
      // -------- 教务模块 --------
      {
        path: 'enroll',
        name: 'Enrollment',
        component: () => import('@/views/Enrollment.vue'),
        meta: { title: '学员报名' }
      },
      {
        path: 'students',
        name: 'StudentList',
        component: () => import('@/views/StudentList.vue'),
        meta: { title: '在学学员' }
      },
      {
        path: 'students/:id',
        name: 'StudentDetail',
        component: () => import('@/views/StudentDetail.vue'),
        meta: { title: '学员详情' }
      },
      {
        path: 'history-students',
        name: 'HistoryStudents',
        component: () => import('@/views/HistoryStudents.vue'),
        meta: { title: '历史学员' }
      },
      {
        path: 'attendance',
        name: 'Attendance',
        component: () => import('@/views/Attendance.vue'),
        meta: { title: '学员考勤' }
      },
      {
        path: 'scores',
        name: 'ScoreManage',
        component: () => import('@/views/ScoreManage.vue'),
        meta: { title: '积分管理' }
      },
      // -------- 管理模块 --------
      {
        path: 'teachers',
        name: 'TeacherManage',
        component: () => import('@/views/TeacherManage.vue'),
        meta: { title: '教师管理' }
      },
      {
        path: 'salary',
        name: 'SalaryManage',
        component: () => import('@/views/salary/SalaryManage.vue'),
        meta: { title: '课酬提成' }
      },
      {
        path: 'classes',
        name: 'ClassList',
        component: () => import('@/views/ClassList.vue'),
        meta: { title: '班级管理' }
      },
      {
        path: 'classes/:id',
        name: 'ClassDetail',
        component: () => import('@/views/ClassDetail.vue'),
        meta: { title: '班级详情' }
      },
      {
        path: 'courses',
        name: 'CourseManage',
        component: () => import('@/views/CourseManage.vue'),
        meta: { title: '课程管理' }
      },
      {
        path: 'packages',
        name: 'PackageManage',
        component: () => import('@/views/PackageManage.vue'),
        meta: { title: '套餐管理' }
      },
      {
        path: 'classrooms',
        name: 'ClassroomManage',
        component: () => import('@/views/ClassroomManage.vue'),
        meta: { title: '教室管理' }
      },
      {
        path: 'items-manage',
        name: 'ItemManage',
        component: () => import('@/views/ItemManage.vue'),
        meta: { title: '物品管理' }
      },
      {
        path: 'item-sale-exchange',
        name: 'ItemSaleExchange',
        component: () => import('@/views/ItemSaleExchange.vue'),
        meta: { title: '销售兑换' }
      },
      {
        path: 'activities',
        name: 'ActivityManage',
        component: () => import('@/views/ActivityManage.vue'),
        meta: { title: '活动管理' }
      },
      {
        path: 'activities/new',
        name: 'ActivityNew',
        component: () => import('@/views/ActivityNew.vue'),
        meta: { title: '新建活动' }
      },
      {
        path: 'activities/edit',
        name: 'ActivityEdit',
        component: () => import('@/views/ActivityNew.vue'),
        meta: { title: '编辑活动' }
      },
      {
        path: 'activities/detail',
        name: 'ActivityDetail',
        component: () => import('@/views/ActivityDetail.vue'),
        meta: { title: '活动详情' }
      },
      // -------- 统计模块 --------
      {
        path: 'stats/enroll',
        name: 'StatsEnroll',
        component: () => import('@/views/stats/StatsEnroll.vue'),
        meta: { title: '报名统计' }
      },
      {
        path: 'stats/payment',
        name: 'StatsPayment',
        component: () => import('@/views/stats/StatsPayment.vue'),
        meta: { title: '收费统计' }
      },
      {
        path: 'stats/hours',
        name: 'StatsHours',
        component: () => import('@/views/stats/StatsHours.vue'),
        meta: { title: '课时统计' }
      },
      {
        path: 'stats/items',
        name: 'StatsItems',
        component: () => import('@/views/stats/StatsItems.vue'),
        meta: { title: '物品统计' }
      },
      {
        path: 'stats/fees',
        name: 'StatsFees',
        component: () => import('@/views/stats/StatsFees.vue'),
        meta: { title: '杂费统计' }
      },
      {
        path: 'stats/refund',
        name: 'StatsRefund',
        component: () => import('@/views/stats/StatsRefund.vue'),
        meta: { title: '退费统计' }
      },
      // -------- 记录模块 --------
      {
        path: 'orders',
        name: 'OrderList',
        component: () => import('@/views/OrderList.vue'),
        meta: { title: '报名记录' }
      },
      {
        path: 'sales-orders',
        name: 'SalesOrderList',
        component: () => import('@/views/SalesOrderList.vue'),
        meta: { title: '销售订单' }
      },
      {
        path: 'course-records',
        name: 'CourseRecord',
        component: () => import('@/views/CourseRecord.vue'),
        meta: { title: '课消记录' }
      },
      {
        path: 'score-records',
        name: 'ScoreRecord',
        component: () => import('@/views/ScoreRecord.vue'),
        meta: { title: '积分记录' }
      },
      {
        path: 'fees-records',
        name: 'MiscFeeRecord',
        component: () => import('@/views/MiscFeeRecord.vue'),
        meta: { title: '杂费记录' }
      },
      {
        path: 'inventory-records',
        name: 'InventoryRecord',
        component: () => import('@/views/InventoryRecord.vue'),
        meta: { title: '库存记录' }
      },
      // -------- 设置模块 --------
      {
        path: 'settings/payment-methods',
        name: 'PaymentMethods',
        component: () => import('@/views/settings/PaymentMethods.vue'),
        meta: { title: '支付方式' }
      },
      {
        path: 'settings/background',
        name: 'BackgroundSetting',
        component: () => import('@/views/settings/BackgroundSetting.vue'),
        meta: { title: '背景设置' }
      },
      {
        path: 'settings/item-categories',
        name: 'ItemCategories',
        component: () => import('@/views/settings/ItemCategories.vue'),
        meta: { title: '商品类别' }
      },
      {
        path: 'settings/exchange-rate',
        name: 'ExchangeRate',
        component: () => import('@/views/settings/ExchangeRate.vue'),
        meta: { title: '积分汇率' }
      }
    ]
  },
  // ========== 404 重定向 ==========
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// ========== 路由守卫 ==========
router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('access_token')

  // 未登录跳转登录页
  if (to.path !== '/login' && !token) {
    next('/login')
    return
  }

  // 已登录访问登录页跳转工作台
  if (to.path === '/login' && token) {
    next('/dashboard')
    return
  }

  // 检查用户信息（简单验证）
  if (token && to.path !== '/login') {
    try {
      // 可以在这里验证 token 有效性
      // await request.get('/auth/me')
      next()
    } catch {
      localStorage.clear()
      next('/login')
    }
  } else {
    next()
  }
})

// ========== 路由后置守卫：自动添加标签页 ==========
router.afterEach((to) => {
  // 排除登录页和重定向页
  if (to.path !== '/login' && to.name !== 'Redirect') {
    const tagsStore = useTagsViewStore()
    tagsStore.addView(to)
  }
})

export default router