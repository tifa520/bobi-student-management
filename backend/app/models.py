# backend/app/models.py
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Text,
    Boolean, ForeignKey, JSON, UniqueConstraint, Index, func
)
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class TimestampMixin:
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class SoftDeleteMixin:
    """软删除混入类：添加 is_deleted 和 deleted_at 字段"""
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)


class Student(TimestampMixin, Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False)
    gender = Column(String(10), default='')
    birthday = Column(Date, nullable=True)
    age = Column(Integer, nullable=True)
    phone = Column(String(20), unique=True, nullable=False)
    primary_contact_name = Column(String(50), default='')
    primary_contact_relation = Column(String(20), default='')
    primary_contact_phone = Column(String(20), default='')
    secondary_contact_name = Column(String(50), default='')
    secondary_contact_relation = Column(String(20), default='')
    secondary_contact_phone = Column(String(20), default='')
    introducer = Column(String(50), default='')
    note = Column(Text, default='')
    contacts = Column(JSON, default=list)
    total_integral = Column(Integer, default=0)
    is_archived = Column(Boolean, default=False)
    avatar = Column(String(255), nullable=True)
    card_background = Column(String(255), nullable=True)
    # 新增字段
    nation = Column(String(50), nullable=True)
    id_card = Column(String(20), nullable=True)
    school = Column(String(100), nullable=True)

    orders = relationship('Order', back_populates='student', lazy='selectin')
    student_courses = relationship('StudentCourse', back_populates='student', lazy='dynamic')
    attendances = relationship('Attendance', back_populates='student', lazy='dynamic')
    integral_records = relationship('IntegralRecord', back_populates='student', lazy='dynamic')
    gift_exchanges = relationship('GiftExchange', back_populates='student', lazy='dynamic')
    purchases = relationship('Purchase', back_populates='student', lazy='dynamic')
    activity_registrations = relationship('ActivityRegistration', back_populates='student', lazy='dynamic')
    refunds = relationship('Refund', back_populates='student', lazy='dynamic')
    learning_cards = relationship('LearningCard', back_populates='student', lazy='selectin')
    enrollment_histories = relationship('EnrollmentHistory', back_populates='student', lazy='dynamic')
    misc_fees = relationship('MiscFee', back_populates='student', lazy='dynamic')


class Course(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    charge_mode = Column(String(20), default='课时', nullable=True)
    duration = Column(Integer, default=60, nullable=True)
    deduct_hours = Column(Integer, default=1, nullable=True)
    unit_price = Column(Float, default=0.0, nullable=True)

    # ★ 新增：反向关系
    stages = relationship('Stage', back_populates='course', cascade='all, delete-orphan')
    classes = relationship('Class', back_populates='course', lazy='dynamic')
    orders = relationship('Order', back_populates='course', lazy='dynamic')
    student_courses = relationship('StudentCourse', back_populates='course', lazy='dynamic')
    learning_cards = relationship('LearningCard', back_populates='course', lazy='dynamic')
    refunds = relationship('Refund', back_populates='course', lazy='dynamic')
    enrollment_histories = relationship('EnrollmentHistory', back_populates='course', lazy='dynamic')
    packages = relationship('CoursePackage', back_populates='course', cascade='all, delete-orphan')


# ========== ★ 新增：Stage 模型（课阶） ==========
class Stage(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = 'stages'
    __table_args__ = (UniqueConstraint('course_id', 'name', name='uq_stage_course_name'),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    name = Column(String(50), nullable=False)
    description = Column(Text, default='')
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # ★ 新增：阶段级别的收费模式（覆盖课程）
    charge_mode = Column(String(20), default='课时')   # '课时' 或 '按期'

    # 价格相关（课阶级别的价格）
    unit_price = Column(Float, default=0.0)
    duration = Column(Integer, default=60)
    deduct_hours = Column(Integer, default=1)

    # 课阶扩展属性
    target_level = Column(String(50), nullable=True)
    min_age = Column(Integer, nullable=True)
    max_age = Column(Integer, nullable=True)

    # 关系
    course = relationship('Course', back_populates='stages')
    classes = relationship('Class', back_populates='stage')
    packages = relationship('CoursePackage', back_populates='stage')
    orders = relationship('Order', back_populates='stage')



class Teacher(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = 'teachers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    phone = Column(String(20), unique=True)
    role = Column(String(30), default='full_time_teacher')
    is_enabled = Column(Boolean, default=True)
    classes = relationship('Class', back_populates='teacher', lazy='dynamic')
    schedules = relationship('Schedule', back_populates='teacher', lazy='dynamic')


class Classroom(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = 'classrooms'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    is_enabled = Column(Boolean, default=True)
    classes = relationship('Class', back_populates='classroom', lazy='dynamic')
    schedules = relationship('Schedule', back_populates='classroom', lazy='dynamic')


# ========== ★ 修改：Class 模型（增加 stage_id） ==========
class Class(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = 'classes'
    __table_args__ = (
        UniqueConstraint('course_id', 'stage_id', 'name', name='uq_class_course_stage_name'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    stage_id = Column(Integer, ForeignKey('stages.id'), nullable=True)   # ★ 新增
    teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=True)
    classroom_id = Column(Integer, ForeignKey('classrooms.id'), nullable=True)

    # ★ 价格继承：如果班级有自定义价格，使用班级价格；否则使用课阶价格
    unit_price = Column(Float, nullable=True)               # 班级自定义单价（可空）
    duration = Column(Integer, nullable=True)               # 班级自定义时长
    deduct_hours = Column(Integer, nullable=True)           # 班级自定义扣课时

    start_date = Column(Date, nullable=True)
    remark = Column(Text, default='')
    status = Column(String(20), default='active')

    # 关系
    course = relationship('Course', back_populates='classes')
    stage = relationship('Stage', back_populates='classes')      # ★ 新增
    teacher = relationship('Teacher', back_populates='classes')
    classroom = relationship('Classroom', back_populates='classes')
    student_courses = relationship('StudentCourse', back_populates='class_', lazy='dynamic')
    schedules = relationship('Schedule', back_populates='class_', lazy='dynamic')
    attendances = relationship('Attendance', back_populates='class_', lazy='dynamic')
    orders = relationship('Order', back_populates='class_', lazy='dynamic')
    learning_cards = relationship('LearningCard', back_populates='class_', lazy='dynamic')
    enrollment_histories_from = relationship('EnrollmentHistory', foreign_keys='EnrollmentHistory.from_class_id', back_populates='from_class')
    enrollment_histories_to = relationship('EnrollmentHistory', foreign_keys='EnrollmentHistory.to_class_id', back_populates='to_class')


class Order(TimestampMixin, Base):
    __tablename__ = 'orders'
    __table_args__ = (
        Index('idx_order_student_course', 'student_id', 'course_id'),
        Index('idx_order_no', 'order_no'),
        Index('idx_order_stage', 'stage_id'),  # ★ 新增索引
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(20), unique=True, nullable=False)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    stage_id = Column(Integer, ForeignKey('stages.id'), nullable=True)   # ★ 新增
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=True)

    enroll_type = Column(String(20), default='新报')
    purchase_hours = Column(Integer, nullable=False)
    unit_price = Column(Float, default=0.0)                              # ★ 实际单价
    price_source = Column(String(20), default='stage')                  # ★ 价格来源：stage/class/manual

    total_price = Column(Float, default=0.0)
    discount_mode = Column(String(30), default='none')
    discount_rate = Column(Float, default=0.0)
    direct_reduction = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    payable_amount = Column(Float, default=0.0)
    actual_unit_price = Column(Float, default=0.0)
    paid_amount = Column(Float, default=0.0)
    total_paid = Column(Float, default=0.0)
    payment_method = Column(String(20), default='微信')
    gift_hours = Column(Integer, default=0)
    gift_note = Column(String(200), default='')
    validity_type = Column(String(10), nullable=True)
    validity_value = Column(String(50), nullable=True)
    leave_limit = Column(String(20), default='不限制')
    leave_limit_count = Column(Integer, default=0)
    performance_teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=True)
    is_active = Column(Boolean, default=True)
    is_invalid = Column(Boolean, default=False)
    remark = Column(Text, default='')
    parent_order_id = Column(Integer, ForeignKey('orders.id'), nullable=True)

    # 关系
    student = relationship('Student', back_populates='orders')
    course = relationship('Course', back_populates='orders')
    stage = relationship('Stage', back_populates='orders')      # ★ 新增
    class_ = relationship('Class', back_populates='orders')
    parent_order = relationship('Order', remote_side=[id], backref='child_repayments')
    payment_logs = relationship('PaymentLog', back_populates='order', lazy='dynamic')


class StudentCourse(TimestampMixin, Base):
    __tablename__ = 'student_courses'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=True)
    total_purchased = Column(Integer, default=0)
    total_gift = Column(Integer, default=0)
    total_deducted = Column(Integer, default=0)
    total_custom_add = Column(Integer, default=0)
    total_custom_sub = Column(Integer, default=0)
    total_transfer_in = Column(Integer, default=0)
    total_transfer_out = Column(Integer, default=0)
    remaining_hours = Column(Integer, default=0)
    remaining_gift = Column(Integer, default=0)
    remaining_amount = Column(Float, default=0.0)
    status = Column(String(20), default='active')
    suspended_start = Column(Date, nullable=True)
    suspended_end = Column(Date, nullable=True)
    last_refresh_at = Column(DateTime, default=func.now(), onupdate=func.now())
    leave_used = Column(Integer, default=0)

    student = relationship('Student', back_populates='student_courses')
    course = relationship('Course', back_populates='student_courses')
    class_ = relationship('Class', back_populates='student_courses')


class Schedule(TimestampMixin, Base):
    __tablename__ = 'schedules'
    __table_args__ = (
        Index('idx_schedule_date', 'course_date'),
        Index('idx_schedule_class_date', 'class_id', 'course_date')
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False)
    teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=True)
    classroom_id = Column(Integer, ForeignKey('classrooms.id'), nullable=True)
    course_date = Column(Date, nullable=False)
    start_time = Column(String(10), nullable=False)
    duration = Column(Integer, default=60)
    status = Column(String(20), default='scheduled')

    class_ = relationship('Class', back_populates='schedules')
    teacher = relationship('Teacher', back_populates='schedules')
    classroom = relationship('Classroom', back_populates='schedules')
    attendances = relationship('Attendance', back_populates='schedule', lazy='dynamic')


class Attendance(TimestampMixin, Base):
    __tablename__ = 'attendances'
    __table_args__ = (
        Index('idx_attendance_schedule', 'schedule_id'),
        Index('idx_attendance_student_date', 'student_id', 'created_at')
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False)
    schedule_id = Column(Integer, ForeignKey('schedules.id'), nullable=False)
    enrollment_id = Column(Integer, ForeignKey('orders.id'), nullable=True)
    status = Column(String(20), nullable=False)
    deduct_hours = Column(Integer, default=0)
    deduct_amount = Column(Float, default=0.0)
    gift_deduct = Column(Integer, default=0)
    purchased_deduct = Column(Integer, default=0)
    teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=True)
    class_name = Column(String(100), nullable=True)
    remark = Column(Text, default='')

    student = relationship('Student', back_populates='attendances')
    class_ = relationship('Class', back_populates='attendances')
    schedule = relationship('Schedule', back_populates='attendances')


class EnrollmentHistory(TimestampMixin, Base):
    __tablename__ = 'enrollment_histories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    from_class_id = Column(Integer, ForeignKey('classes.id'), nullable=True)
    to_class_id = Column(Integer, ForeignKey('classes.id'), nullable=True)
    action = Column(String(20), nullable=False)

    student = relationship('Student', back_populates='enrollment_histories')
    course = relationship('Course', back_populates='enrollment_histories')
    from_class = relationship('Class', foreign_keys=[from_class_id], back_populates='enrollment_histories_from')
    to_class = relationship('Class', foreign_keys=[to_class_id], back_populates='enrollment_histories_to')


class IntegralRecord(TimestampMixin, Base):
    __tablename__ = 'integral_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    change_amount = Column(Integer, nullable=False)
    reason = Column(String(50), default='')
    remark = Column(Text, default='')

    student = relationship('Student', back_populates='integral_records')


class GiftExchange(TimestampMixin, Base):
    __tablename__ = 'gift_exchanges'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    gift_type = Column(String(20), nullable=False)
    gift_name = Column(String(100), nullable=False)
    activity_name = Column(String(100), default='')
    quantity = Column(Integer, default=1)

    student = relationship('Student', back_populates='gift_exchanges')


class Purchase(TimestampMixin, Base):
    __tablename__ = 'purchases'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    items = Column(JSON, default=list)
    total_amount = Column(Float, default=0.0)
    payment_method = Column(String(20), default='微信')

    student = relationship('Student', back_populates='purchases')


class Activity(TimestampMixin, Base):
    __tablename__ = 'activities'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    activity_type = Column(String(30), default='其他')
    is_free = Column(Boolean, default=True)
    fee = Column(Float, default=0.0)
    content = Column(Text, default='')
    cover_image = Column(String(255), nullable=True)
    banner_image = Column(String(255), nullable=True)
    is_featured = Column(Boolean, default=False)
    featured_order = Column(Integer, default=0)
    prizes = Column(JSON, default=list)
    stats = Column(JSON, default=dict)
    recommend_type = Column(String(20), default='grid')
    pay_option = Column(String(20), default='both')
    registration_start = Column(DateTime, nullable=True)
    registration_end = Column(DateTime, nullable=True)
    max_participants = Column(Integer, default=0)
    location = Column(String(200), nullable=True)
    status = Column(String(20), default='draft')
    charge_mode = Column(String(20), default='free')
    points_cost = Column(Integer, default=0)
    is_archived = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    enable_lottery = Column(Boolean, default=False)
    lottery_times = Column(Integer, default=1)
    max_win_times = Column(Integer, default=1)

    registrations = relationship('ActivityRegistration', back_populates='activity', lazy='dynamic')


class ActivityRegistration(TimestampMixin, Base):
    __tablename__ = 'activity_registrations'
    __table_args__ = (UniqueConstraint('activity_id', 'student_id', name='uq_activity_student'),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_id = Column(Integer, ForeignKey('activities.id'), nullable=False)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    is_attending = Column(String(10), default='待定')
    is_paid = Column(Boolean, default=False)
    paid_amount = Column(Float, default=0.0)
    points_used = Column(Integer, default=0)
    points_refunded = Column(Integer, default=0)
    refund_amount = Column(Float, default=0.0)
    refund_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    cash_payment_method = Column(String(20), default='')
    status = Column(String(20), default='confirmed')
    checked_in_at = Column(DateTime, nullable=True)
    operator_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    cancel_reason = Column(String(200), nullable=True)
    lottery_count = Column(Integer, default=0)
    win_count = Column(Integer, default=0)

    activity = relationship('Activity', back_populates='registrations')
    student = relationship('Student', back_populates='activity_registrations')
    operator = relationship('User')


class Refund(TimestampMixin, Base):
    __tablename__ = 'refunds'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    refund_type = Column(String(20), nullable=False)
    refund_amount = Column(Float, default=0.0)
    refund_method = Column(String(20), default='微信')
    reason = Column(Text, default='')
    remark = Column(Text, default='')

    student = relationship('Student', back_populates='refunds')
    course = relationship('Course', back_populates='refunds')


class ArchivedStudentCourse(TimestampMixin, Base):
    __tablename__ = 'archived_student_courses'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    snapshot_data = Column(JSON, default=dict)
    action = Column(String(20), nullable=False)


class EnrollSession(TimestampMixin, Base):
    __tablename__ = 'enroll_sessions'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    step = Column(Integer, default=1)
    data = Column(JSON, default=dict)
    expires_at = Column(DateTime, nullable=False)


class LearningCard(TimestampMixin, Base):
    __tablename__ = 'learning_cards'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=True)
    remaining_paid_hours = Column(Integer, default=0)
    remaining_gift_hours = Column(Integer, default=0)
    remaining_amount = Column(Float, default=0.0)
    total_leave_quota = Column(Integer, default=0)
    used_leave = Column(Integer, default=0)
    validity_end_date = Column(Date, nullable=True)
    manual_validity_days = Column(Integer, nullable=True)
    status = Column(String(20), default='active')
    suspended_start = Column(Date, nullable=True)
    suspended_end = Column(Date, nullable=True)
    last_refresh_at = Column(DateTime, default=func.now(), onupdate=func.now())

    student = relationship('Student', back_populates='learning_cards')
    course = relationship('Course')
    class_ = relationship('Class')
    transactions = relationship('CardTransaction', cascade='all, delete-orphan')
    validity_logs = relationship('ValidityLog', cascade='all, delete-orphan')


class CardTransaction(Base):
    __tablename__ = 'card_transactions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    card_id = Column(Integer, ForeignKey('learning_cards.id'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=True)
    attendance_id = Column(Integer, ForeignKey('attendances.id'), nullable=True)
    change_type = Column(String(30), nullable=False)
    paid_hours_change = Column(Integer, default=0)
    amount_change = Column(Float, default=0.0)
    gift_hours_change = Column(Integer, default=0)
    leave_change = Column(Integer, default=0)
    reason = Column(String(200), default='')
    occurred_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())

    card = relationship('LearningCard', back_populates='transactions')
    order = relationship('Order')
    attendance = relationship('Attendance')


class ValidityLog(TimestampMixin, Base):
    __tablename__ = 'validity_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    card_id = Column(Integer, ForeignKey('learning_cards.id'), nullable=False)
    change_days = Column(Integer, nullable=False)
    reason = Column(String(200), default='')
    source_type = Column(String(30), nullable=False)
    source_id = Column(Integer, nullable=True)
    occurred_at = Column(DateTime, nullable=False)

    card = relationship('LearningCard', back_populates='validity_logs')


class PaymentLog(TimestampMixin, Base):
    __tablename__ = 'payment_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(20), nullable=False)
    payment_type = Column(String(20), nullable=False)
    remark = Column(String(200), default='')
    occurred_at = Column(DateTime, nullable=False)

    order = relationship('Order', back_populates='payment_logs')


class Item(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    category = Column(String(30), default='其他')
    item_type = Column(String(20), nullable=False)
    points = Column(Integer, default=0)
    sale_price = Column(Float, default=0.0)
    cost_price = Column(Float, default=0.0)
    stock = Column(Integer, default=0)
    unit = Column(String(10), default='个')
    status = Column(String(10), default='上架')
    image_url = Column(String(255), nullable=True)
    remark = Column(Text, default='')
    pay_option = Column(String(20), default='both')


class InventoryBatch(Base):
    __tablename__ = 'inventory_batches'
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey('items.id'), nullable=False)
    batch_no = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)
    remaining_quantity = Column(Integer, nullable=False)
    unit_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    purchase_date = Column(DateTime, nullable=False)
    remark = Column(String(200), default='')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    item = relationship('Item', backref='batches')


class InventoryTransaction(Base):
    __tablename__ = 'inventory_transactions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey('items.id'), nullable=False)
    batch_id = Column(Integer, ForeignKey('inventory_batches.id'), nullable=True)
    transaction_type = Column(String(20), nullable=False)
    quantity = Column(Integer, nullable=False)
    before_stock = Column(Integer, nullable=False)
    after_stock = Column(Integer, nullable=False)
    unit_price = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    cost_of_goods_sold = Column(Float, default=0.0)
    payment_method = Column(String(50), default='')
    related_id = Column(Integer, nullable=True)
    remark = Column(String(200), default='')
    created_at = Column(DateTime, default=func.now())

    item = relationship('Item', backref='inventory_transactions')
    batch = relationship('InventoryBatch', backref='transactions')


class MiscFee(TimestampMixin, Base):
    __tablename__ = 'misc_fees'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    fee_type = Column(String(20), nullable=False)
    source_id = Column(Integer, nullable=False)
    description = Column(String(200), nullable=False)
    amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0.0)
    points_used = Column(Integer, default=0)
    exchange_rate = Column(Integer, default=10)
    status = Column(String(20), default='pending')
    payment_method = Column(String(20), default='')
    paid_at = Column(DateTime, nullable=True)

    student = relationship('Student', back_populates='misc_fees')


class Role(TimestampMixin, Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    permissions = Column(JSON, default=list)

    users = relationship('User', back_populates='role')


class User(TimestampMixin, Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    avatar = Column(String(255), nullable=True)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    is_enabled = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)

    role = relationship('Role', back_populates='users')
    sessions = relationship('UserSession', back_populates='user')


class UserSession(TimestampMixin, Base):
    __tablename__ = 'user_sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)

    user = relationship('User', back_populates='sessions')


class SystemConfig(Base):
    __tablename__ = 'system_configs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(String(200))
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class CardTransactionBackup(Base):
    __tablename__ = 'card_transactions_backup'
    id = Column(Integer, primary_key=True, autoincrement=True)
    original_id = Column(Integer, nullable=False)
    card_id = Column(Integer, nullable=False)
    order_id = Column(Integer, nullable=True)
    attendance_id = Column(Integer, nullable=True)
    change_type = Column(String(30), nullable=False)
    paid_hours_change = Column(Integer, default=0)
    amount_change = Column(Float, default=0.0)
    gift_hours_change = Column(Integer, default=0)
    leave_change = Column(Integer, default=0)
    reason = Column(String(200), default='')
    occurred_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False)
    backup_at = Column(DateTime, default=func.now())
    backup_by = Column(String(50), default='system')
    backup_reason = Column(String(200), default='')


class TokenBlacklist(Base):
    __tablename__ = 'token_blacklist'
    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    token_type = Column(String(20), default='access')
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, default=func.now())
    revoked_by = Column(String(50), default='system')
    reason = Column(String(200), default='')


class SalesOrder(Base):
    __tablename__ = 'sales_orders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(20), unique=True, nullable=False)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    total_amount = Column(Float, default=0.0)
    paid_amount = Column(Float, default=0.0)
    used_points = Column(Integer, default=0)
    status = Column(String(20), default='paid')
    payment_details = Column(JSON, default=list)
    remark = Column(Text, default='')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    student = relationship('Student', backref='sales_orders')
    items = relationship('SalesOrderItem', back_populates='order', cascade='all, delete-orphan')


class SalesOrderItem(Base):
    __tablename__ = 'sales_order_items'
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('sales_orders.id'), nullable=False)
    item_id = Column(Integer, ForeignKey('items.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, default=0.0)
    subtotal = Column(Float, default=0.0)

    order = relationship('SalesOrder', back_populates='items')
    item = relationship('Item')


class SalaryRule(TimestampMixin, Base):
    __tablename__ = 'salary_rules'
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_name = Column(String(100), nullable=False)
    applicable_type = Column(String(20), nullable=False)
    applicable_id = Column(Integer, nullable=False)
    calculation_type = Column(String(20), nullable=False)
    commission_type = Column(String(20), nullable=False)
    fixed_ratio = Column(Float, default=0.0)
    fixed_unit_price = Column(Float, default=0.0)
    is_enabled = Column(Boolean, default=True)
    remark = Column(Text, default='')

    tiers = relationship('SalaryRuleTier', back_populates='rule', cascade='all, delete-orphan')


class SalaryRuleTier(Base):
    __tablename__ = 'salary_rule_tiers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(Integer, ForeignKey('salary_rules.id'), nullable=False)
    min_value = Column(Float, nullable=False, default=0)
    max_value = Column(Float, nullable=True)
    unit_price = Column(Float, nullable=False, default=0.0)
    ratio = Column(Float, nullable=True)
    is_per_person = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    rule = relationship('SalaryRule', back_populates='tiers')


class TeacherSalary(TimestampMixin, Base):
    __tablename__ = 'teacher_salaries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=False)
    settlement_month = Column(String(7), nullable=False)
    total_classes = Column(Integer, default=0)
    total_attendance_count = Column(Integer, default=0)
    total_consumed_hours = Column(Integer, default=0)
    total_consumed_amount = Column(Float, default=0.0)
    base_amount = Column(Float, default=0.0)
    adjust_amount = Column(Float, default=0.0)
    final_amount = Column(Float, default=0.0)
    status = Column(String(20), default='calculated')
    remark = Column(Text, default='')
    paid_at = Column(DateTime, nullable=True)
    payment_method = Column(String(50), nullable=True)

    teacher = relationship('Teacher', backref='salaries')
    details = relationship('TeacherSalaryDetail', back_populates='salary', cascade='all, delete-orphan')
    adjustments = relationship('TeacherSalaryAdjustment', back_populates='salary', cascade='all, delete-orphan')


class TeacherSalaryDetail(Base):
    __tablename__ = 'teacher_salary_details'
    id = Column(Integer, primary_key=True, autoincrement=True)
    salary_id = Column(Integer, ForeignKey('teacher_salaries.id'), nullable=False)
    rule_id = Column(Integer, ForeignKey('salary_rules.id'), nullable=True)
    rule_name = Column(String(100), nullable=False)
    target_type = Column(String(20), nullable=False)
    target_id = Column(Integer, nullable=False)
    target_name = Column(String(100), nullable=False)
    calculation_type = Column(String(30), nullable=False)
    calculated_value = Column(Float, default=0.0)
    unit_price = Column(Float, default=0.0)
    calculated_amount = Column(Float, default=0.0)

    salary = relationship('TeacherSalary', back_populates='details')
    rule = relationship('SalaryRule')


class TeacherSalaryAdjustment(Base):
    __tablename__ = 'teacher_salary_adjustments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    salary_id = Column(Integer, ForeignKey('teacher_salaries.id'), nullable=False)
    adjust_amount = Column(Float, nullable=False)
    reason = Column(String(200), nullable=False)
    operator_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    operator_name = Column(String(50))
    created_at = Column(DateTime, default=func.now())

    salary = relationship('TeacherSalary', back_populates='adjustments')
    operator = relationship('User')


# ========== ★ 修改：CoursePackage 模型（增加 stage_id） ==========
class CoursePackage(TimestampMixin, Base):
    __tablename__ = 'course_packages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    stage_id = Column(Integer, ForeignKey('stages.id'), nullable=True)   # ★ 新增
    name = Column(String(50), nullable=False)
    purchase_hours = Column(Integer, nullable=False)
    gift_hours = Column(Integer, default=0)
    discount_mode = Column(String(30), default='none')
    discount_rate = Column(Float, default=0.0)
    direct_reduction = Column(Float, default=0.0)
    validity_days = Column(Integer, nullable=True)
    leave_limit = Column(String(20), default='不限制')
    leave_limit_count = Column(Integer, default=0)
    sort_order = Column(Integer, default=0)
    is_default = Column(Boolean, default=False)
    remark = Column(Text, default='')

    course = relationship('Course', back_populates='packages')
    stage = relationship('Stage', back_populates='packages')    # ★ 新增


class PrizeWinner(Base):
    __tablename__ = 'prize_winners'
    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_id = Column(Integer, ForeignKey('activities.id'), nullable=False)
    registration_id = Column(Integer, ForeignKey('activity_registrations.id'), nullable=False)
    prize_id = Column(Integer, nullable=True)
    prize_name = Column(String(100), nullable=False)
    prize_level = Column(String(20), nullable=True)
    status = Column(String(20), default='pending')
    delivered_at = Column(DateTime, nullable=True)
    delivery_method = Column(String(30), nullable=True)
    delivery_info = Column(String(200), nullable=True)
    operator_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    activity = relationship('Activity')
    registration = relationship('ActivityRegistration')
    operator = relationship('User')


class StudentWork(Base):
    __tablename__ = 'student_works'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(20), nullable=False)
    original_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    size = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    student = relationship('Student', backref='works')