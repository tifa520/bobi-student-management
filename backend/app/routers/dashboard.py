# backend/app/routers/dashboard.py
"""
工作台数据统计接口
包含：基础统计、学员概况、收入概况、剩余课时、课程表等
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import date, datetime, timedelta
from app.database import get_db
from app.models import (
    Student, LearningCard, Order, Attendance, Schedule, Class,
    StudentCourse, Teacher, Course, MiscFee
)
from loguru import logger

router = APIRouter(prefix="/dashboard", tags=["工作台"])


# ===================================================================
# 1. 基础统计（保留原有接口）
# ===================================================================

@router.get("/statistics")
def get_statistics(db: Session = Depends(get_db)):
    """
    获取工作台基础统计数据
    包含：学员统计、课时统计、金额统计、欠费统计
    """
    now = datetime.now()
    start_of_month = datetime(now.year, now.month, 1)
    start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)

    # ---- 学员统计 ----
    total_students = db.query(Student).filter(Student.is_archived == False).count()
    new_this_month = db.query(Student).filter(
        Student.created_at >= start_of_month,
        Student.is_archived == False
    ).count()
    new_last_month = db.query(Student).filter(
        Student.created_at >= start_of_last_month,
        Student.created_at < start_of_month,
        Student.is_archived == False
    ).count()
    lost = db.query(StudentCourse).filter(
        StudentCourse.status == 'graduated',
        StudentCourse.updated_at >= start_of_month
    ).count()
    renewed = db.query(Order).filter(
        Order.enroll_type == '续报',
        Order.created_at >= start_of_month
    ).count()

    # ---- 课时统计 ----
    remaining_hours = db.query(func.sum(LearningCard.remaining_paid_hours)).scalar() or 0
    remaining_gift = db.query(func.sum(LearningCard.remaining_gift_hours)).scalar() or 0
    consumed_this_month = db.query(func.sum(Attendance.deduct_hours)).filter(
        Attendance.created_at >= start_of_month
    ).scalar() or 0
    consumed_last_month = db.query(func.sum(Attendance.deduct_hours)).filter(
        Attendance.created_at >= start_of_last_month,
        Attendance.created_at < start_of_month
    ).scalar() or 0

    # ---- 金额统计 ----
    remaining_amount = db.query(func.sum(LearningCard.remaining_amount)).scalar() or 0
    amount_this_month = db.query(func.sum(Attendance.deduct_amount)).filter(
        Attendance.created_at >= start_of_month
    ).scalar() or 0
    amount_last_month = db.query(func.sum(Attendance.deduct_amount)).filter(
        Attendance.created_at >= start_of_last_month,
        Attendance.created_at < start_of_month
    ).scalar() or 0

    # ---- 尾款欠费 ----
    orders = db.query(Order).filter(
        Order.is_active == True,
        Order.is_invalid == False,
        Order.enroll_type != '尾款补费'
    ).all()
    total_arrears = 0
    arrears_count = 0
    for o in orders:
        arrears = o.payable_amount - o.total_paid
        if arrears > 0:
            total_arrears += arrears
            arrears_count += 1

    excess_hours_count = db.query(LearningCard).filter(
        LearningCard.remaining_paid_hours <= 0,
        LearningCard.status == 'active'
    ).count()

    return {
        "code": 0,
        "data": {
            "students": {
                "total": total_students,
                "newThisMonth": new_this_month,
                "newLastMonth": new_last_month,
                "lost": lost,
                "renewedThisMonth": renewed
            },
            "hours": {
                "remaining": remaining_hours,
                "consumedThisMonth": consumed_this_month,
                "consumedLastMonth": consumed_last_month,
                "remainingGift": remaining_gift
            },
            "amount": {
                "remainingAmount": round(remaining_amount, 2),
                "consumedAmountThisMonth": round(amount_this_month, 2),
                "consumedAmountLastMonth": round(amount_last_month, 2)
            },
            "arrears": {
                "totalArrears": round(total_arrears, 2),
                "arrearsCount": arrears_count,
                "arrearsAmount": round(total_arrears, 2),
                "excessHoursCount": excess_hours_count,
                "excessHoursAmount": 0.0
            }
        }
    }


# ===================================================================
# 2. 学员概况
# ===================================================================

@router.get("/student-overview")
def get_student_overview(db: Session = Depends(get_db)):
    """
    获取学员概况数据
    包含：在学/历史/预约学员、性别分布、本月新增/流失、课程人数分布
    """
    now = datetime.now()
    start_of_month = datetime(now.year, now.month, 1)

    # ---- 在学学员 ----
    active_students = db.query(Student).filter(Student.is_archived == False).count()

    # ---- 历史学员 ----
    history_students = db.query(Student).filter(Student.is_archived == True).count()

    # ---- 预约学员（统计 activity_registrations 中 is_attending='待定' 的学员） ----
    from app.models import ActivityRegistration
    reserved_students = db.query(ActivityRegistration.student_id).filter(
        ActivityRegistration.is_attending == '待定'
    ).distinct().count()

    # ---- 性别分布 ----
    male_count = db.query(Student).filter(
        Student.is_archived == False,
        Student.gender == '男'
    ).count()
    female_count = db.query(Student).filter(
        Student.is_archived == False,
        Student.gender == '女'
    ).count()
    unknown_gender = db.query(Student).filter(
        Student.is_archived == False,
        Student.gender.notin_(['男', '女'])
    ).count()

    # ---- 本月新增 ----
    new_this_month = db.query(Student).filter(
        Student.is_archived == False,
        Student.created_at >= start_of_month
    ).count()

    # ---- 本月流失 ----
    lost_this_month = db.query(Student).filter(
        Student.is_archived == True,
        Student.updated_at >= start_of_month
    ).count()

    # ---- 各课程人数分布 ----
    course_distribution = db.query(
        Course.name.label('name'),
        func.count(LearningCard.id).label('value')
    ).join(LearningCard, Course.id == LearningCard.course_id).filter(
        LearningCard.status.in_(['active', 'suspended'])
    ).group_by(Course.id, Course.name).order_by(func.count(LearningCard.id).desc()).limit(10).all()

    return {
        "code": 0,
        "data": {
            "active": active_students,
            "history": history_students,
            "reserved": reserved_students,
            "gender": {
                "male": male_count,
                "female": female_count,
                "unknown": unknown_gender
            },
            "new_this_month": new_this_month,
            "lost_this_month": lost_this_month,
            "course_distribution": [
                {"name": d.name, "value": d.value} for d in course_distribution
            ]
        }
    }


# ===================================================================
# 3. 收入概况
# ===================================================================

@router.get("/income-overview")
def get_income_overview(
    period: str = Query('week', description="today/week/month/month_last/year"),
    db: Session = Depends(get_db)
):
    """
    获取收入概况数据
    支持按周期切换：本周/本月/上月/本年
    """
    now = datetime.now()
    today = now.date()

    # ---- 计算时间范围 ----
    period_map = {
        'today': (today, '今日'),           # 新增
        'week': (today - timedelta(days=7), '本周'),
        'month': (today.replace(day=1), '本月'),
        'month_last': ((today.replace(day=1) - timedelta(days=1)).replace(day=1), '上月'),
        'year': (today.replace(month=1, day=1), '本年')
    }
    start_date, period_label = period_map.get(period, period_map['week'])
    end_date = today

    logger.debug(f"收入概况查询: {period_label}, {start_date} ~ {end_date}")

    # ---- 报名订单统计 ----
    orders_query = db.query(Order).filter(
        Order.is_active == True,
        Order.is_invalid == False,
        Order.enroll_type != '尾款补费',
        Order.created_at >= start_date,
        Order.created_at <= end_date
    )
    order_count = orders_query.count()
    order_amount = db.query(func.sum(Order.payable_amount)).filter(
        Order.is_active == True,
        Order.is_invalid == False,
        Order.enroll_type != '尾款补费',
        Order.created_at >= start_date,
        Order.created_at <= end_date
    ).scalar() or 0

    # ---- 报名课程分布（按金额） ----
    course_amount_dist = db.query(
        Course.name.label('name'),
        func.sum(Order.payable_amount).label('value')
    ).join(Course, Order.course_id == Course.id).filter(
        Order.is_active == True,
        Order.is_invalid == False,
        Order.enroll_type != '尾款补费',
        Order.created_at >= start_date,
        Order.created_at <= end_date
    ).group_by(Course.id, Course.name).order_by(func.sum(Order.payable_amount).desc()).limit(10).all()

    # ---- 报名课程分布（按人数） ----
    course_count_dist = db.query(
        Course.name.label('name'),
        func.count(Order.id).label('value')
    ).join(Course, Order.course_id == Course.id).filter(
        Order.is_active == True,
        Order.is_invalid == False,
        Order.enroll_type != '尾款补费',
        Order.created_at >= start_date,
        Order.created_at <= end_date
    ).group_by(Course.id, Course.name).order_by(func.count(Order.id).desc()).limit(10).all()

    # ---- 杂费收入（活动 + 商品销售） ----
    misc_fees_query = db.query(MiscFee).filter(
        MiscFee.amount > 0,
        MiscFee.status == 'paid',
        MiscFee.created_at >= start_date,
        MiscFee.created_at <= end_date
    )
    activity_income = db.query(func.sum(MiscFee.amount)).filter(
        MiscFee.fee_type == 'activity',
        MiscFee.amount > 0,
        MiscFee.status == 'paid',
        MiscFee.created_at >= start_date,
        MiscFee.created_at <= end_date
    ).scalar() or 0

    item_income = db.query(func.sum(MiscFee.amount)).filter(
        MiscFee.fee_type == 'item_sale',
        MiscFee.amount > 0,
        MiscFee.status == 'paid',
        MiscFee.created_at >= start_date,
        MiscFee.created_at <= end_date
    ).scalar() or 0

    # ---- 课时总收入 ----
    hours_income = db.query(func.sum(Attendance.deduct_amount)).filter(
        Attendance.created_at >= start_date,
        Attendance.created_at <= end_date
    ).scalar() or 0

    # ---- 课时收入课程分布 ----
    hours_course_dist = db.query(
        Course.name.label('name'),
        func.sum(Attendance.deduct_amount).label('value')
    ).join(Class, Attendance.class_id == Class.id).join(
        Course, Class.course_id == Course.id
    ).filter(
        Attendance.created_at >= start_date,
        Attendance.created_at <= end_date
    ).group_by(Course.id, Course.name).order_by(func.sum(Attendance.deduct_amount).desc()).limit(10).all()

    # ---- 尾款欠费总金额 ----
    arrears_total = db.query(
        func.sum(Order.payable_amount - Order.total_paid)
    ).filter(
        Order.is_active == True,
        Order.is_invalid == False,
        Order.enroll_type != '尾款补费',
        Order.payable_amount > Order.total_paid
    ).scalar() or 0

    return {
        "code": 0,
        "data": {
            "period_label": period_label,
            "new_order_count": order_count,
            "new_order_amount": float(order_amount),
            "course_amount_distribution": [
                {"name": d.name, "value": float(d.value)} for d in course_amount_dist
            ],
            "course_count_distribution": [
                {"name": d.name, "value": d.value} for d in course_count_dist
            ],
            "activity_income": float(activity_income),
            "item_income": float(item_income),
            "hours_income": float(hours_income),
            "hours_course_distribution": [
                {"name": d.name, "value": float(d.value)} for d in hours_course_dist
            ],
            "arrears_total": float(arrears_total)
        }
    }


# ===================================================================
# 4. 剩余课时概况
# ===================================================================

@router.get("/hours-overview")
def get_hours_overview(db: Session = Depends(get_db)):
    """
    获取剩余课时概况数据
    包含：剩余总课时、剩余课消总金额、课程分布（课时/金额）
    """
    # ---- 剩余总课时 ----
    remaining_hours = db.query(func.sum(LearningCard.remaining_paid_hours)).filter(
        LearningCard.status.in_(['active', 'suspended'])
    ).scalar() or 0

    # ---- 剩余课消总金额 ----
    remaining_amount = db.query(func.sum(LearningCard.remaining_amount)).filter(
        LearningCard.status.in_(['active', 'suspended'])
    ).scalar() or 0

    # ---- 剩余课时课程分布 ----
    hours_course_dist = db.query(
        Course.name.label('name'),
        func.sum(LearningCard.remaining_paid_hours).label('value')
    ).join(Course, LearningCard.course_id == Course.id).filter(
        LearningCard.status.in_(['active', 'suspended'])
    ).group_by(Course.id, Course.name).order_by(
        func.sum(LearningCard.remaining_paid_hours).desc()
    ).limit(10).all()

    # ---- 剩余课消金额课程分布 ----
    amount_course_dist = db.query(
        Course.name.label('name'),
        func.sum(LearningCard.remaining_amount).label('value')
    ).join(Course, LearningCard.course_id == Course.id).filter(
        LearningCard.status.in_(['active', 'suspended'])
    ).group_by(Course.id, Course.name).order_by(
        func.sum(LearningCard.remaining_amount).desc()
    ).limit(10).all()

    return {
        "code": 0,
        "data": {
            "remaining_hours": int(remaining_hours),
            "remaining_amount": float(remaining_amount),
            "hours_course_distribution": [
                {"name": d.name, "value": int(d.value)} for d in hours_course_dist
            ],
            "amount_course_distribution": [
                {"name": d.name, "value": float(d.value)} for d in amount_course_dist
            ]
        }
    }


# ===================================================================
# 5. 课程表（保留原有接口）
# ===================================================================

@router.get("/today-schedule")
def get_today_schedule(db: Session = Depends(get_db)):
    """获取今日课程表"""
    today = date.today()
    schedules = db.query(Schedule).filter(
        Schedule.course_date == today,
        Schedule.status != 'cancelled'
    ).order_by(Schedule.start_time).all()

    result = []
    for s in schedules:
        class_obj = db.query(Class).get(s.class_id)
        teacher = db.query(Teacher).get(s.teacher_id) if s.teacher_id else (
            class_obj.teacher if class_obj else None
        )
        result.append({
            "time": s.start_time,
            "class_name": class_obj.name if class_obj else '',
            "course_name": class_obj.course.name if class_obj and class_obj.course else '',
            "teacher_name": teacher.name if teacher else '',
            "duration": s.duration
        })
    return {"code": 0, "data": result}


@router.get("/month-schedule")
def get_month_schedule(
    year: int = Query(...),
    month: int = Query(...),
    db: Session = Depends(get_db)
):
    """获取指定月份有排课的日期列表"""
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    dates = db.query(Schedule.course_date).filter(
        Schedule.course_date >= start_date,
        Schedule.course_date < end_date,
        Schedule.status != 'cancelled'
    ).distinct().all()
    return {"code": 0, "data": [str(d[0]) for d in dates]}


@router.get("/week-course-amount")
def get_week_course_amount(db: Session = Depends(get_db)):
    """获取本周各课程的课时消耗金额"""
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=7)

    results = db.query(
        Class.course_id,
        func.sum(Attendance.deduct_amount).label('amount')
    ).join(Schedule, Attendance.schedule_id == Schedule.id).join(
        Class, Schedule.class_id == Class.id
    ).filter(
        Attendance.created_at >= start_of_week,
        Attendance.created_at < end_of_week
    ).group_by(Class.course_id).all()

    data = []
    for r in results:
        course = db.query(Course).get(r.course_id)
        if course:
            data.append({"name": course.name, "amount": round(r.amount, 2)})
    return {"code": 0, "data": data}


@router.get("/week-attendance-rate")
def get_week_attendance_rate(db: Session = Depends(get_db)):
    """获取本周每天的考勤率"""
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    rates = []

    for i in range(7):
        day = start_of_week + timedelta(days=i)
        schedules = db.query(Schedule).filter(
            Schedule.course_date == day,
            Schedule.status != 'cancelled'
        ).all()

        if not schedules:
            rates.append({"date": day.isoformat(), "rate": 0})
            continue

        total_students = 0
        attended = 0
        for s in schedules:
            class_students = db.query(LearningCard).filter(
                LearningCard.class_id == s.class_id,
                LearningCard.status == 'active'
            ).count()
            total_students += class_students
            attended_count = db.query(Attendance).filter(
                Attendance.schedule_id == s.id,
                Attendance.status.in_(['出勤', '迟到'])
            ).count()
            attended += attended_count

        rate = round((attended / total_students * 100) if total_students > 0 else 0, 2)
        rates.append({"date": day.isoformat(), "rate": rate})

    return {"code": 0, "data": rates}