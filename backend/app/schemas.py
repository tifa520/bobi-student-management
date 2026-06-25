# backend/app/schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime


class StudentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    phone: str = Field(..., min_length=11, max_length=20)
    gender: Optional[str] = ''
    birth_date: Optional[str] = None
    introducer: Optional[str] = ''
    note: Optional[str] = ''
    primary_contact_name: Optional[str] = ''
    primary_contact_relation: Optional[str] = ''
    primary_contact_phone: Optional[str] = ''
    secondary_contact_name: Optional[str] = ''
    secondary_contact_relation: Optional[str] = ''
    secondary_contact_phone: Optional[str] = ''
    contacts: Optional[List[dict]] = None


class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    introducer: Optional[str] = None
    note: Optional[str] = None
    primary_contact_name: Optional[str] = None
    primary_contact_relation: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    secondary_contact_name: Optional[str] = None
    secondary_contact_relation: Optional[str] = None
    secondary_contact_phone: Optional[str] = None
    contacts: Optional[list] = None
    card_background: Optional[str] = None
    # ★ 新增字段
    nation: Optional[str] = None
    id_card: Optional[str] = None
    school: Optional[str] = None


class EnrollStep1(BaseModel):
    student_name: str = Field(..., max_length=50)
    phone: str = Field(..., max_length=20)
    gender: Optional[str] = ''
    birth_date: Optional[str] = None
    introducer: Optional[str] = ''
    note: Optional[str] = ''
    primary_contact_name: Optional[str] = ''
    primary_contact_relation: Optional[str] = ''
    primary_contact_phone: Optional[str] = ''
    secondary_contact_name: Optional[str] = ''
    secondary_contact_relation: Optional[str] = ''
    secondary_contact_phone: Optional[str] = ''


# ========== ★ 修改：CourseItem（支持 stage_id） ==========
class CourseItem(BaseModel):
    course_id: int
    stage_id: Optional[int] = None          # ★ 新增
    enroll_type: str = '新报'
    purchase_hours: int = Field(..., ge=1)
    validity_days: Optional[int] = Field(None, ge=1, le=3650)
    validity_type: Optional[str] = None
    validity_value: Optional[str] = None
    discount_mode: str = 'none'
    discount_rate: float = Field(0.0, ge=0, le=10)
    direct_reduction: float = Field(0.0, ge=0)
    class_id: Optional[int] = None
    leave_limit: str = '不限制'
    leave_limit_count: int = Field(0, ge=0)
    gift_hours: int = Field(0, ge=0)
    gift_note: str = ''


class EnrollStep2(BaseModel):
    courses: List[CourseItem]


class EnrollStep3Submit(BaseModel):
    payment_method: str
    paid_amount: float = Field(..., ge=0)
    performance_teacher_id: Optional[int] = None
    course_payments: Optional[List[dict]] = None


class AttendanceSubmit(BaseModel):
    attendance_list: List[dict]
    schedule_id: int
    leave_deduct: Optional[int] = 0


class TransferClassRequest(BaseModel):
    student_id: int
    from_schedule_id: int
    to_class_id: int
    to_schedule_id: int


class ScoreChange(BaseModel):
    student_id: int
    change_amount: int
    reason: str = Field(..., max_length=50)


class GiftExchangeCreate(BaseModel):
    student_id: int
    gift_type: str = Field(..., max_length=20)
    gift_name: str = Field(..., max_length=100)
    activity_name: Optional[str] = Field('', max_length=100)
    quantity: int = Field(1, ge=1)


class PurchaseCreate(BaseModel):
    student_id: int
    items: List[dict]
    total_amount: float = Field(..., ge=0)
    payment_method: str = '微信'


class ActivityCreate(BaseModel):
    name: str = Field(..., max_length=100)
    activity_date: Optional[str] = None
    activity_type: str = '全体'
    is_free: bool = True
    fee: float = Field(0.0, ge=0)
    content: str = ''


class ActivityRegister(BaseModel):
    student_id: int
    is_attending: str = '待定'
    payment_type: Optional[str] = 'cash'
    cash_payment_method: Optional[str] = ''
    payments: Optional[List[dict]] = []


class BatchRepayItem(BaseModel):
    order_id: int
    amount: float = Field(..., gt=0)


class BatchRepay(BaseModel):
    items: List[BatchRepayItem]


class RefundCreate(BaseModel):
    student_id: int
    course_id: int
    refund_type: str
    refund_amount: float = Field(..., ge=0)
    refund_method: str = '微信'
    reason: str = ''
    remark: str = ''


# ========== ★ 修改：ClassCreate / ClassUpdate（支持 stage_id） ==========
class ClassCreate(BaseModel):
    name: str = Field(..., max_length=50)
    course_id: int
    stage_id: Optional[int] = None          # ★ 新增
    teacher_id: Optional[int] = None
    classroom_id: Optional[int] = None
    duration: Optional[int] = Field(60, ge=1, le=480)
    deduct_hours: Optional[int] = Field(1, ge=1)
    unit_price: Optional[float] = Field(None, ge=0)   # ★ 可空，空则继承课阶
    start_date: Optional[str] = None
    remark: Optional[str] = ''


class ClassUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    course_id: Optional[int] = None
    stage_id: Optional[int] = None          # ★ 新增
    teacher_id: Optional[int] = None
    classroom_id: Optional[int] = None
    duration: Optional[int] = Field(None, ge=1, le=480)
    deduct_hours: Optional[int] = Field(None, ge=1)
    unit_price: Optional[float] = Field(None, ge=0)
    start_date: Optional[str] = None
    remark: Optional[str] = None
    status: Optional[str] = None


# ========== ★ 新增：课阶相关 Schema ==========
class StageCreate(BaseModel):
    name: str = Field(..., max_length=50)
    charge_mode: str = Field('课时', max_length=20)
    description: Optional[str] = ''
    sort_order: int = Field(0, ge=0)
    is_active: bool = True
    unit_price: float = Field(0.0, ge=0)
    duration: int = Field(60, ge=1, le=480)
    deduct_hours: int = Field(1, ge=1)
    target_level: Optional[str] = None
    min_age: Optional[int] = Field(None, ge=0)
    max_age: Optional[int] = Field(None, ge=0)


class StageUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    charge_mode: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    unit_price: Optional[float] = Field(None, ge=0)
    duration: Optional[int] = Field(None, ge=1, le=480)
    deduct_hours: Optional[int] = Field(None, ge=1)
    target_level: Optional[str] = None
    min_age: Optional[int] = Field(None, ge=0)
    max_age: Optional[int] = Field(None, ge=0)


class StageResponse(BaseModel):
    id: int
    course_id: int
    name: str
    charge_mode: str
    description: str
    sort_order: int
    is_active: bool
    unit_price: float
    duration: int
    deduct_hours: int
    target_level: Optional[str]
    min_age: Optional[int]
    max_age: Optional[int]
    created_at: str
    updated_at: str


# ========== ★ 新增：创建课程时携带阶段列表 ==========
class CourseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    stages: List[StageCreate] = []   # ★ 前端直接传入课阶列表


class CourseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    stages: Optional[List[StageCreate]] = None   # ★ 全量替换课阶

class CourseResponse(BaseModel):
    id: int
    name: str
    stages: List[StageResponse] = []   # ★ 嵌套返回课阶
    

# ========== ★ 修改：PackageCreate（支持 stage_id） ==========
class PackageCreate(BaseModel):
    course_id: int
    stage_id: Optional[int] = None          # ★ 新增
    name: str
    purchase_hours: int
    gift_hours: int = 0
    discount_mode: str = 'none'
    discount_rate: float = 0.0
    direct_reduction: float = 0.0
    validity_days: Optional[int] = None
    leave_limit: str = '不限制'
    leave_limit_count: int = 0
    sort_order: int = 0
    is_default: bool = False
    remark: str = ''


class PackageUpdate(BaseModel):
    name: Optional[str] = None
    stage_id: Optional[int] = None          # ★ 新增
    purchase_hours: Optional[int] = None
    gift_hours: Optional[int] = None
    discount_mode: Optional[str] = None
    discount_rate: Optional[float] = None
    direct_reduction: Optional[float] = None
    validity_days: Optional[int] = None
    leave_limit: Optional[str] = None
    leave_limit_count: Optional[int] = None
    sort_order: Optional[int] = None
    is_default: Optional[bool] = None
    remark: Optional[str] = None