from app.services.cache_service import cached, cache

@router.get("/courses/list")
@cached(ttl=600, key_prefix="courses_list")  # 缓存10分钟
def get_course_list_simple(db: Session = Depends(get_db)):
    """课程列表 - 低频变化，适合缓存"""
    courses = db.query(Course).all()
    return {"code": 0, "data": [{"id": c.id, "name": c.name, "unit_price": c.unit_price} for c in courses]}

@router.get("/teachers/enabled")
@cached(ttl=600, key_prefix="teachers_enabled")
def get_enabled_teachers(db: Session = Depends(get_db)):
    """启用的教师列表"""
    teachers = db.query(Teacher).filter(Teacher.is_enabled == True).order_by(Teacher.name).all()
    return {"code": 0, "data": [{"id": t.id, "name": t.name} for t in teachers]}

@router.get("/classrooms/enabled")
@cached(ttl=600, key_prefix="classrooms_enabled")
def get_enabled_classrooms(db: Session = Depends(get_db)):
    """启用的教室列表"""
    rooms = db.query(Classroom).filter(Classroom.is_enabled == True).order_by(Classroom.name).all()
    return {"code": 0, "data": [{"id": r.id, "name": r.name} for r in rooms]}


# 在修改数据后清除缓存
@router.post("/courses")
def create_course(name: str = Query(...), ...):
    # ... 创建课程
    # 清除缓存
    cache.clear_pattern("courses_list*")
    return {"code": 0, "data": {"id": c.id}}

@router.put("/courses/{course_id}")
def update_course(course_id: int, ...):
    # ... 更新课程
    # 清除缓存
    cache.clear_pattern("courses_list*")
    return {"code": 0, "message": "更新成功"}

@router.delete("/courses/{course_id}")
def delete_course(course_id: int, ...):
    # ... 删除课程
    # 清除缓存
    cache.clear_pattern("courses_list*")
    return {"code": 0, "message": "已删除"}