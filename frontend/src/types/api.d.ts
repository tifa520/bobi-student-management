/**
 * API 响应类型定义
 */

// 通用响应结构
export interface ApiResponse<T = any> {
  code: number
  data: T
  message?: string
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page?: number
  page_size?: number
}

// ========== 学员相关 ==========

export interface Student {
  id: number
  name: string
  phone: string
  gender: string
  age: number | null
  birthday: string | null
  total_integral: number
  avatar: string
  is_archived: boolean
  created_at: string
  updated_at: string
}

export interface StudentCourse {
  course_id: number
  course_name: string
  class_id: number | null
  class_name: string
  remaining_hours: number
  remaining_gift: number
  remaining_amount: number
  total_purchased: number
  total_gift: number
  validity_display: string
  status: string
}

// ========== 订单相关 ==========

export interface Order {
  id: number
  order_no: string
  student_id: number
  student_name: string
  course_id: number
  course_name: string
  enroll_type: string
  purchase_hours: number
  payable_amount: number
  total_paid: number
  arrears: number
  payment_method: string
  created_at: string
  is_invalid: boolean
}

// ========== 物品相关 ==========

export interface Item {
  id: number
  name: string
  category: string
  item_type: 'sale' | 'gift'
  sale_price: number
  cost_price: number
  stock: number
  unit: string
  status: '上架' | '下架'
  image_url: string | null
  pay_option: 'cash' | 'points' | 'both'
  remark: string
  created_at: string
}

export interface InventoryBatch {
  id: number
  batch_no: string
  quantity: number
  remaining_quantity: number
  unit_cost: number
  total_cost: number
  purchase_date: string
  remark: string
}

// ========== 系统设置 ==========

export type PaymentMethod = string
export type ItemCategory = string
export type ExchangeRate = number