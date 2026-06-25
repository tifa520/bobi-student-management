# backend/app/routers/enroll.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.models import (
    Student, Order, StudentCourse, Course, Class, EnrollSession,
    EnrollmentHistory, IntegralRecord, PaymentLog, Stage
)
from app.schemas import EnrollStep1, EnrollStep2, EnrollStep3Submit
from app.utils import generate_student_uuid, calculate_age, generate_order_no, calculate_payable_amount
from app.services.transaction_service import TransactionService
from app.services.price_service import get_stage_pricing
from dateutil.parser import parse as parse_date
import uuid

router = APIRouter()


def get_or_create_session(request: Request, db: Session) -> EnrollSession:
    session_id = request.headers.get('enroll-session')
    if session_id:
        session = db.query(EnrollSession).filter(
            EnrollSession.id == session_id,
            EnrollSession.expires_at > datetime.now()
        ).first()
        if session:
            return session
    session = EnrollSession(
        id=str(uuid.uuid4()),
        step=1,
        data={},
        expires_at=datetime.now() + timedelta(days=7)
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def create_or_get_student(db: Session, step1_data: dict) -> Student:
    name = step1_data['student_name']
    phone = step1_data['phone']
    student = db.query(Student).filter(
        Student.name == name,
        Student.phone == phone
    ).first()
    if student:
        if student.is_archived:
            student.is_archived = False
        return student
    birth_date = parse_date(step1_data['birth_date']).date() if step1_data.get('birth_date') else None
    age = calculate_age(birth_date) if birth_date else None
    student = Student(
        student_uuid=generate_student_uuid(),
        name=name,
        phone=phone,
        gender=step1_data.get('gender', ''),
        birthday=birth_date,
        age=age,
        introducer=step1_data.get('introducer', ''),
        note=step1_data.get('note', ''),
        primary_contact_name=step1_data.get('primary_contact_name', ''),
        primary_contact_relation=step1_data.get('primary_contact_relation', ''),
        primary_contact_phone=step1_data.get('primary_contact_phone', ''),
        secondary_contact_name=step1_data.get('secondary_contact_name', ''),
        secondary_contact_relation=step1_data.get('secondary_contact_relation', ''),
        secondary_contact_phone=step1_data.get('secondary_contact_phone', ''),
        contacts=step1_data.get('contacts', [])
    )
    db.add(student)
    db.flush()
    return student


@router.post("/step1")
def step1(data: EnrollStep1, request: Request, db: Session = Depends(get_db)):
    session = get_or_create_session(request, db)
    updated_data = dict(session.data) if isinstance(session.data, dict) else {}
    updated_data['step1'] = data.model_dump()
    session.data = updated_data
    session.step = 1
    db.commit()
    return {"code": 0, "session_id": session.id, "message": "保存成功"}


@router.post("/step2")
def step2(data: EnrollStep2, request: Request, db: Session = Depends(get_db)):
    session = get_or_create_session(request, db)
    if 'step1' not in session.data or not session.data['step1']:
        raise HTTPException(400, "请先完成学员信息")

    updated_data = dict(session.data)
    courses_data = []

    for c in data.courses:
        course_dict = c.model_dump()

        # ★ 验证课阶属于该课程
        if c.stage_id:
            stage = db.query(Stage).filter(
                Stage.id == c.stage_id,
                Stage.course_id == c.course_id,
                Stage.is_active == True
            ).first()
            if not stage:
                raise HTTPException(400, f"课程 {c.course_id} 下不存在该课阶")
        else:
            # 如果未选择课阶，自动选择该课程的默认课阶（第一个）
            default_stage = db.query(Stage).filter(
                Stage.course_id == c.course_id,
                Stage.is_active == True
            ).order_by(Stage.sort_order.asc()).first()
            if default_stage:
                course_dict['stage_id'] = default_stage.id

                # 如果未指定班级，尝试从课阶自动分配
                if not c.class_id:
                    auto_class = db.query(Class).filter(
                        Class.course_id == c.course_id,
                        Class.stage_id == default_stage.id,
                        Class.status == 'active'
                    ).order_by(Class.name.asc()).first()
                    if auto_class:
                        course_dict['class_id'] = auto_class.id

        # 处理有效期
        if course_dict.get('validity_days') is not None:
            days = course_dict['validity_days']
            if days and days > 0:
                course_dict['validity_type'] = 'days'
                course_dict['validity_value'] = str(days)
            else:
                course_dict['validity_type'] = None
                course_dict['validity_value'] = None
        course_dict.pop('validity_days', None)

        courses_data.append(course_dict)

    updated_data['step2'] = {"courses": courses_data}
    session.data = updated_data
    session.step = 2
    db.commit()
    return {"code": 0, "message": "保存成功"}


@router.post("/step3/submit")
def step3_submit(data: EnrollStep3Submit, request: Request, db: Session = Depends(get_db)):
    session = get_or_create_session(request, db)
    if 'step1' not in session.data or 'step2' not in session.data:
        raise HTTPException(400, "请先完成前两步")

    step1 = session.data['step1']
    step2 = session.data['step2']
    student = create_or_get_student(db, step1)
    db.flush()

    course_payments = {}
    for cp in (data.course_payments or []):
        course_payments[cp.get('course_id')] = cp.get('paid', 0)

    tx_service = TransactionService(db)
    created_orders = []

    for course_data in step2['courses']:
        course = db.query(Course).get(course_data['course_id'])
        if not course:
            continue

        # ★ 获取课阶信息
        stage_id = course_data.get('stage_id')
        stage = db.query(Stage).get(stage_id) if stage_id else None

        # ★ 确定价格：使用课阶价格
        if stage and stage.unit_price > 0:
            unit_price = stage.unit_price
            price_source = 'stage'
        else:
            unit_price = course.unit_price
            price_source = 'course'

        # ★ 确定班级
        class_id = course_data.get('class_id')
        if class_id:
            cls = db.query(Class).get(class_id)
            if cls and cls.unit_price is not None:
                # 班级有自定义价格，使用班级价格
                unit_price = cls.unit_price
                price_source = 'class'

        total_price = unit_price * course_data['purchase_hours']
        payable, discount = calculate_payable_amount(
            total_price,
            course_data.get('discount_mode', 'none'),
            course_data.get('discount_rate', 0),
            course_data.get('direct_reduction', 0)
        )
        paid = course_payments.get(course.id, payable)
        if paid > payable:
            paid = payable

        order_no = generate_order_no(db)
        validity_type = course_data.get('validity_type')
        validity_value = course_data.get('validity_value')

        order = Order(
            order_no=order_no,
            student_id=student.id,
            course_id=course.id,
            stage_id=stage_id,                           # ★ 新增
            class_id=class_id,
            enroll_type=course_data.get('enroll_type', '新报'),
            purchase_hours=course_data['purchase_hours'],
            unit_price=unit_price,                       # ★ 实际单价
            price_source=price_source,                   # ★ 价格来源
            total_price=total_price,
            discount_mode=course_data.get('discount_mode', 'none'),
            discount_rate=course_data.get('discount_rate', 0),
            direct_reduction=course_data.get('direct_reduction', 0),
            discount_amount=discount,
            payable_amount=payable,
            actual_unit_price=round(payable / course_data['purchase_hours'], 2) if course_data['purchase_hours'] > 0 else 0,
            paid_amount=paid,
            total_paid=paid,
            payment_method=data.payment_method,
            gift_hours=course_data.get('gift_hours', 0),
            gift_note=course_data.get('gift_note', ''),
            validity_type=validity_type,
            validity_value=validity_value,
            leave_limit=course_data.get('leave_limit', '不限制'),
            leave_limit_count=course_data.get('leave_limit_count', 0),
            performance_teacher_id=data.performance_teacher_id,
            is_active=True,
            is_invalid=False,
            remark=''
        )
        db.add(order)
        db.flush()
        created_orders.append(order)

        if paid > 0:
            payment_log = PaymentLog(
                order_id=order.id,
                amount=paid,
                payment_method=data.payment_method,
                payment_type='initial',
                remark=f"订单 {order.order_no} 首次付款",
                occurred_at=datetime.now()
            )
            db.add(payment_log)

        tx_service.record_purchase(order, order.gift_hours)

        sc = db.query(StudentCourse).filter(
            StudentCourse.student_id == student.id,
            StudentCourse.course_id == course.id
        ).first()
        if not sc:
            sc = StudentCourse(
                student_id=student.id,
                course_id=course.id,
                class_id=class_id,
                status='active'
            )
            db.add(sc)
            db.flush()

        if order.class_id:
            history = EnrollmentHistory(
                student_id=student.id,
                course_id=course.id,
                from_class_id=None,
                to_class_id=order.class_id,
                action='assign'
            )
            db.add(history)

        student.is_archived = False

    total_paid = sum(o.total_paid for o in created_orders)
    if total_paid > 0:
        points = int(total_paid * 10)
        if points > 0:
            student.total_integral = (student.total_integral or 0) + points
            integral_record = IntegralRecord(
                student_id=student.id,
                change_amount=points,
                reason="报名缴费",
                remark=f"实付{total_paid}元，赠送{points}积分"
            )
            db.add(integral_record)

    db.delete(session)
    db.commit()
    return {"code": 0, "message": "报名成功", "student_id": student.id}


@router.get("/session")
def get_session(request: Request, db: Session = Depends(get_db)):
    session_id = request.headers.get('enroll-session')
    if not session_id:
        return {"code": 0, "data": None}
    session = db.query(EnrollSession).filter(
        EnrollSession.id == session_id,
        EnrollSession.expires_at > datetime.now()
    ).first()
    if not session:
        return {"code": 0, "data": None}
    return {"code": 0, "data": {"id": session.id, "step": session.step, "data": session.data}}