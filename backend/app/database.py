# backend/app/database.py
"""
数据库配置与连接管理
支持 SQLite WAL 模式、连接池优化、健康检查
"""
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from app.config import DATABASE_URL
import time
import os
from loguru import logger

# 确保 data 目录存在
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# 路径转换
if DATABASE_URL.startswith('sqlite:///./'):
    DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, DATABASE_URL.split('/')[-1])}"
elif DATABASE_URL.startswith('sqlite:///data/'):
    DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, DATABASE_URL.split('/')[-1])}"
elif DATABASE_URL == 'sqlite:///data/app.db':
    DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'app.db')}"

logger.info(f"数据库路径: {DATABASE_URL}")

engine = create_engine(
    DATABASE_URL,
    connect_args={
        'check_same_thread': False,
        'timeout': 60,
        'uri': False
    },
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_use_lifo=True
)


@event.listens_for(engine, 'connect')
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA journal_mode=WAL')
    cursor.execute('PRAGMA synchronous=NORMAL')
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.execute('PRAGMA cache_size=-10000')
    cursor.execute('PRAGMA temp_store=MEMORY')
    cursor.execute('PRAGMA mmap_size=268435456')
    cursor.execute('PRAGMA automatic_index=ON')
    cursor.execute('PRAGMA optimize')
    cursor.close()
    logger.debug("SQLite PRAGMA 设置完成")


@event.listens_for(engine, 'checkout')
def on_checkout(dbapi_conn, connection_record, connection_proxy):
    try:
        cursor = dbapi_conn.cursor()
        cursor.execute('SELECT 1')
        cursor.close()
    except Exception as e:
        logger.warning(f"连接健康检查失败，将回收连接: {e}")
        raise


@event.listens_for(engine, 'checkin')
def on_checkin(dbapi_conn, connection_record):
    try:
        cursor = dbapi_conn.cursor()
        cursor.execute('ROLLBACK')
        cursor.close()
    except Exception:
        pass


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    __abstract__ = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    return SessionLocal()


# ========== ★ init_db 新增 ensure_stages_table ==========
def init_db():
    logger.info("开始初始化数据库...")
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表创建完成")
    ensure_columns()
    ensure_indexes()
    ensure_inventory_batches_table()
    ensure_activity_tables()
    ensure_student_works_table()
    ensure_stages_table()                     # ★ 新增
    ensure_default_roles()
    logger.info("数据库初始化完成")


def ensure_columns():
    """确保必要的列存在（数据库迁移）"""
    conn = engine.connect()
    inspector = inspect(engine)

    def add_column_if_not_exists(table: str, column_def: str):
        try:
            cols = [col['name'] for col in inspector.get_columns(table)]
            col_name = column_def.split()[0]
            if col_name not in cols:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_def}"))
                conn.commit()
                logger.info(f"✅ 表 {table} 已添加列: {column_def}")
        except Exception as e:
            logger.warning(f"⚠️ 添加列 {column_def} 失败: {e}")

    # --- 原有列添加（保持原样）---
    add_column_if_not_exists('students', 'contacts JSON')
    add_column_if_not_exists('students', 'avatar VARCHAR(255)')
    add_column_if_not_exists('students', 'card_background VARCHAR(255)')
    add_column_if_not_exists('attendances', 'gift_deduct INTEGER DEFAULT 0')
    add_column_if_not_exists('attendances', 'purchased_deduct INTEGER DEFAULT 0')
    add_column_if_not_exists('attendances', 'teacher_id INTEGER REFERENCES teachers(id)')
    add_column_if_not_exists('attendances', 'class_name TEXT')
    add_column_if_not_exists('attendances', 'remark TEXT DEFAULT ""')
    add_column_if_not_exists('orders', 'parent_order_id INTEGER REFERENCES orders(id)')
    add_column_if_not_exists('student_courses', 'suspended_start DATE')
    add_column_if_not_exists('student_courses', 'suspended_end DATE')
    add_column_if_not_exists('student_courses', 'leave_used INTEGER DEFAULT 0')
    add_column_if_not_exists('teachers', 'role VARCHAR(30) DEFAULT "full_time_teacher"')
    add_column_if_not_exists('teachers', 'is_enabled BOOLEAN DEFAULT 1')
    add_column_if_not_exists('classes', 'duration INTEGER DEFAULT 60')
    add_column_if_not_exists('classes', 'deduct_hours INTEGER DEFAULT 1')
    add_column_if_not_exists('classes', 'unit_price FLOAT DEFAULT 0.0')
    add_column_if_not_exists('classes', 'start_date DATE')
    add_column_if_not_exists('classes', 'remark TEXT DEFAULT ""')
    add_column_if_not_exists('classes', 'status VARCHAR(20) DEFAULT "active"')
    add_column_if_not_exists('integral_records', 'remark TEXT DEFAULT ""')
    add_column_if_not_exists('users', 'phone VARCHAR(20)')
    add_column_if_not_exists('users', 'avatar VARCHAR(255)')
    add_column_if_not_exists('stages', 'charge_mode VARCHAR(20) DEFAULT "课时"')

    # --- 活动管理相关字段（新增）---
    add_column_if_not_exists('activities', 'registration_start DATETIME')
    add_column_if_not_exists('activities', 'registration_end DATETIME')
    add_column_if_not_exists('activities', 'max_participants INT DEFAULT 0')
    add_column_if_not_exists('activities', 'location VARCHAR(200)')
    add_column_if_not_exists('activities', 'status VARCHAR(20) DEFAULT "draft"')
    add_column_if_not_exists('activities', 'charge_mode VARCHAR(20) DEFAULT "free"')
    add_column_if_not_exists('activities', 'points_cost INT DEFAULT 0')
    add_column_if_not_exists('activities', 'is_archived BOOLEAN DEFAULT 0')
    add_column_if_not_exists('activities', 'created_by INT REFERENCES users(id)')
    add_column_if_not_exists('activities', 'activity_type VARCHAR(30) DEFAULT "其他"')
    add_column_if_not_exists('activity_registrations', 'status VARCHAR(20) DEFAULT "confirmed"')
    add_column_if_not_exists('activity_registrations', 'checked_in_at DATETIME')
    add_column_if_not_exists('activity_registrations', 'operator_id INT REFERENCES users(id)')
    add_column_if_not_exists('activity_registrations', 'cancel_reason VARCHAR(200)')
    add_column_if_not_exists('activity_registrations', 'refund_points INT DEFAULT 0')
    add_column_if_not_exists('activity_registrations', 'updated_at DATETIME DEFAULT CURRENT_TIMESTAMP')
    add_column_if_not_exists('activities', 'enable_lottery BOOLEAN DEFAULT 0')
    add_column_if_not_exists('activities', 'lottery_times INT DEFAULT 1')
    add_column_if_not_exists('activities', 'max_win_times INT DEFAULT 1')
    add_column_if_not_exists('activity_registrations', 'lottery_count INT DEFAULT 0')
    add_column_if_not_exists('activity_registrations', 'win_count INT DEFAULT 0')
    add_column_if_not_exists('learning_cards', 'last_refresh_at DATETIME DEFAULT CURRENT_TIMESTAMP')
    add_column_if_not_exists('students', 'nation VARCHAR(50)')
    add_column_if_not_exists('students', 'id_card VARCHAR(20)')
    add_column_if_not_exists('students', 'school VARCHAR(100)')

    # ★ 新增：课阶相关列
    add_column_if_not_exists('classes', 'stage_id INTEGER REFERENCES stages(id)')
    add_column_if_not_exists('classes', 'duration INTEGER')          # 可空，用于班级自定义
    add_column_if_not_exists('classes', 'deduct_hours INTEGER')      # 可空，用于班级自定义
    add_column_if_not_exists('classes', 'unit_price FLOAT')          # 可空，用于班级自定义
    add_column_if_not_exists('orders', 'stage_id INTEGER REFERENCES stages(id)')
    add_column_if_not_exists('orders', 'unit_price FLOAT DEFAULT 0')
    add_column_if_not_exists('orders', 'price_source VARCHAR(20) DEFAULT "stage"')
    add_column_if_not_exists('course_packages', 'stage_id INTEGER REFERENCES stages(id)')

    conn.close()


def ensure_indexes():
    """创建必要的数据库索引以优化查询性能"""
    conn = engine.connect()

    indexes = [
        # 学员相关
        "CREATE INDEX IF NOT EXISTS idx_students_phone ON students(phone)",
        "CREATE INDEX IF NOT EXISTS idx_students_name ON students(name)",
        "CREATE INDEX IF NOT EXISTS idx_students_archived ON students(is_archived)",
        "CREATE INDEX IF NOT EXISTS idx_students_birthday ON students(birthday)",

        # 订单相关
        "CREATE INDEX IF NOT EXISTS idx_orders_student_id ON orders(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_orders_course_id ON orders(course_id)",
        "CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_order_no ON orders(order_no)",
        "CREATE INDEX IF NOT EXISTS idx_orders_student_course_active ON orders(student_id, course_id, is_active, is_invalid)",
        "CREATE INDEX IF NOT EXISTS idx_orders_student_course_type ON orders(student_id, course_id, enroll_type)",
        "CREATE INDEX IF NOT EXISTS idx_orders_stage_id ON orders(stage_id)",  # ★ 新增

        # 排课
        "CREATE INDEX IF NOT EXISTS idx_schedules_class_id_date ON schedules(class_id, course_date)",
        "CREATE INDEX IF NOT EXISTS idx_schedules_course_date ON schedules(course_date)",
        "CREATE INDEX IF NOT EXISTS idx_schedules_classroom_date ON schedules(classroom_id, course_date)",
        "CREATE INDEX IF NOT EXISTS idx_schedules_status_date ON schedules(status, course_date)",

        # 考勤
        "CREATE INDEX IF NOT EXISTS idx_attendances_schedule_id ON attendances(schedule_id)",
        "CREATE INDEX IF NOT EXISTS idx_attendances_student_id ON attendances(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_attendances_schedule_student ON attendances(schedule_id, student_id)",
        "CREATE INDEX IF NOT EXISTS idx_attendances_class_created ON attendances(class_id, created_at)",

        # 学员课程
        "CREATE INDEX IF NOT EXISTS idx_student_courses_student_id ON student_courses(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_student_courses_class_id ON student_courses(class_id)",

        # 学习卡片
        "CREATE INDEX IF NOT EXISTS idx_learning_cards_student ON learning_cards(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_learning_cards_status ON learning_cards(status)",
        "CREATE INDEX IF NOT EXISTS idx_learning_cards_class ON learning_cards(class_id, status)",
        "CREATE INDEX IF NOT EXISTS idx_learning_cards_course ON learning_cards(course_id)",

        # 流水
        "CREATE INDEX IF NOT EXISTS idx_card_transactions_card ON card_transactions(card_id)",
        "CREATE INDEX IF NOT EXISTS idx_card_transactions_card_occurred ON card_transactions(card_id, occurred_at)",
        "CREATE INDEX IF NOT EXISTS idx_card_transactions_type_date ON card_transactions(change_type, occurred_at)",
        "CREATE INDEX IF NOT EXISTS idx_card_transactions_card_change_occurred ON card_transactions(card_id, change_type, occurred_at)",
        "CREATE INDEX IF NOT EXISTS idx_card_transactions_order ON card_transactions(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_card_transactions_attendance ON card_transactions(attendance_id)",
        "CREATE INDEX IF NOT EXISTS idx_card_transactions_occurred ON card_transactions(occurred_at)",
        "CREATE INDEX IF NOT EXISTS idx_validity_logs_occurred ON validity_logs(occurred_at)",

        # 有效期日志
        "CREATE INDEX IF NOT EXISTS idx_validity_logs_card ON validity_logs(card_id)",
        "CREATE INDEX IF NOT EXISTS idx_validity_logs_card_source ON validity_logs(card_id, source_type, source_id)",

        # 支付日志
        "CREATE INDEX IF NOT EXISTS idx_payment_logs_order ON payment_logs(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_payment_logs_occurred ON payment_logs(occurred_at)",

        # 积分记录
        "CREATE INDEX IF NOT EXISTS idx_integral_records_student ON integral_records(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_integral_records_student_date ON integral_records(student_id, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_integral_records_created ON integral_records(created_at)",

        # 杂费
        "CREATE INDEX IF NOT EXISTS idx_misc_fees_student ON misc_fees(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_misc_fees_created ON misc_fees(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_misc_fees_type ON misc_fees(fee_type)",

        # 活动
        "CREATE INDEX IF NOT EXISTS idx_activities_featured ON activities(is_featured)",
        "CREATE INDEX IF NOT EXISTS idx_activities_dates ON activities(start_date, end_date)",
        "CREATE INDEX IF NOT EXISTS idx_activities_status ON activities(status)",
        "CREATE INDEX IF NOT EXISTS idx_activities_archived ON activities(is_archived)",
        "CREATE INDEX IF NOT EXISTS idx_activity_registrations_activity ON activity_registrations(activity_id)",
        "CREATE INDEX IF NOT EXISTS idx_activity_registrations_student ON activity_registrations(student_id)",
        "CREATE INDEX IF NOT EXISTS idx_activity_registrations_status ON activity_registrations(status)",

        # 班级
        "CREATE INDEX IF NOT EXISTS idx_classes_course ON classes(course_id)",
        "CREATE INDEX IF NOT EXISTS idx_classes_teacher ON classes(teacher_id)",
        "CREATE INDEX IF NOT EXISTS idx_classes_status ON classes(status)",
        "CREATE INDEX IF NOT EXISTS idx_classes_stage ON classes(stage_id)",  # ★ 新增

        # 课程
        "CREATE INDEX IF NOT EXISTS idx_courses_name ON courses(name)",

        # 教师
        "CREATE INDEX IF NOT EXISTS idx_teachers_enabled ON teachers(is_enabled)",

        # 教室
        "CREATE INDEX IF NOT EXISTS idx_classrooms_enabled ON classrooms(is_enabled)",

        # 物品
        "CREATE INDEX IF NOT EXISTS idx_items_status ON items(status)",
        "CREATE INDEX IF NOT EXISTS idx_items_category ON items(category)",

        # 物品批次
        "CREATE INDEX IF NOT EXISTS idx_inventory_batches_item ON inventory_batches(item_id)",
        "CREATE INDEX IF NOT EXISTS idx_inventory_batches_purchase ON inventory_batches(purchase_date)",
        "CREATE INDEX IF NOT EXISTS idx_inventory_batches_remaining ON inventory_batches(remaining_quantity)",
        "CREATE INDEX IF NOT EXISTS idx_inventory_transactions_batch ON inventory_transactions(batch_id)",
        "CREATE INDEX IF NOT EXISTS idx_inventory_transactions_item ON inventory_transactions(item_id)",
        "CREATE INDEX IF NOT EXISTS idx_inventory_transactions_type ON inventory_transactions(transaction_type)",

        # 系统配置
        "CREATE INDEX IF NOT EXISTS idx_system_configs_key ON system_configs(key)",

        # 教师薪酬
        "CREATE INDEX IF NOT EXISTS idx_teacher_salaries_teacher_month ON teacher_salaries(teacher_id, settlement_month)",

        # 奖品
        "CREATE INDEX IF NOT EXISTS idx_prizes_name ON prizes(name)",
        "CREATE INDEX IF NOT EXISTS idx_prize_winners_activity ON prize_winners(activity_id)",
        "CREATE INDEX IF NOT EXISTS idx_prize_winners_status ON prize_winners(status)",

        # ★ 课阶
        "CREATE INDEX IF NOT EXISTS idx_stages_course_id ON stages(course_id)",
        "CREATE INDEX IF NOT EXISTS idx_stages_sort_order ON stages(sort_order)",
        "CREATE INDEX IF NOT EXISTS idx_stages_is_active ON stages(is_active)",
    ]

    for sql in indexes:
        try:
            conn.execute(text(sql))
            conn.commit()
        except Exception as e:
            logger.warning(f"⚠️ 创建索引失败: {sql[:50]}... 错误: {e}")

    conn.close()
    logger.info("✅ 所有索引创建/更新完成")


def ensure_inventory_batches_table():
    """确保库存批次表存在（用于 FIFO 成本管理）"""
    conn = engine.connect()
    try:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS inventory_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL REFERENCES items(id),
                batch_no VARCHAR(50) NOT NULL,
                quantity INTEGER NOT NULL,
                remaining_quantity INTEGER NOT NULL,
                unit_cost FLOAT DEFAULT 0,
                total_cost FLOAT DEFAULT 0,
                purchase_date DATETIME NOT NULL,
                remark VARCHAR(200) DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()

        try:
            conn.execute(text("ALTER TABLE inventory_transactions ADD COLUMN batch_id INTEGER REFERENCES inventory_batches(id)"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE inventory_transactions ADD COLUMN cost_of_goods_sold FLOAT DEFAULT 0"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE inventory_transactions ADD COLUMN payment_method VARCHAR(50) DEFAULT ''"))
            conn.commit()
        except Exception:
            pass

        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inventory_batches_item ON inventory_batches(item_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inventory_batches_purchase ON inventory_batches(purchase_date)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inventory_batches_remaining ON inventory_batches(remaining_quantity)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inventory_transactions_batch ON inventory_transactions(batch_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inventory_transactions_item_type ON inventory_transactions(item_id, transaction_type)"))
        conn.commit()

        logger.info("✅ 库存批次表初始化完成")
    except Exception as e:
        logger.warning(f"⚠️ 库存批次表创建警告: {e}")
    finally:
        conn.close()


def ensure_activity_tables():
    """确保活动管理相关表存在（奖品库、中奖记录），并添加缺失的列（如成本字段）"""
    conn = engine.connect()
    try:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS prizes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                type VARCHAR(20) DEFAULT 'physical',
                level VARCHAR(20),
                image_url VARCHAR(255),
                stock INT DEFAULT 0,
                remaining INT DEFAULT 0,
                value FLOAT DEFAULT 0,
                cost FLOAT DEFAULT 0,
                remark VARCHAR(200) DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()

        try:
            conn.execute(text("ALTER TABLE prizes ADD COLUMN cost FLOAT DEFAULT 0.0"))
            conn.commit()
            logger.info("✅ prizes 表已添加 cost 列")
        except Exception as e:
            if "duplicate column name" not in str(e).lower():
                logger.warning(f"⚠️ 添加 cost 列时出现异常: {e}")

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS prize_winners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INT NOT NULL,
                registration_id INT NOT NULL,
                prize_id INT,
                prize_name VARCHAR(100) NOT NULL,
                prize_level VARCHAR(20),
                status VARCHAR(20) DEFAULT 'pending',
                delivered_at DATETIME,
                delivery_method VARCHAR(30),
                delivery_info VARCHAR(200),
                operator_id INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (activity_id) REFERENCES activities(id),
                FOREIGN KEY (registration_id) REFERENCES activity_registrations(id),
                FOREIGN KEY (operator_id) REFERENCES users(id)
            )
        """))
        conn.commit()

        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prizes_name ON prizes(name)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prize_winners_activity ON prize_winners(activity_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prize_winners_status ON prize_winners(status)"))
            conn.commit()
            logger.info("✅ 奖品管理相关索引创建完成")
        except Exception as e:
            logger.warning(f"⚠️ 创建索引失败: {e}")

        logger.info("✅ 活动管理相关表（prizes, prize_winners）初始化完成")
    except Exception as e:
        logger.error(f"❌ 活动管理表创建失败: {e}")
    finally:
        conn.close()


def ensure_student_works_table():
    """确保学员作品表存在"""
    conn = engine.connect()
    try:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS student_works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                type VARCHAR(20) NOT NULL,
                original_url VARCHAR(500) NOT NULL,
                thumbnail_url VARCHAR(500),
                size INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_student_works_student_id ON student_works(student_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_student_works_created_at ON student_works(created_at)"))
        conn.commit()
        logger.info("✅ student_works 表初始化完成")
    except Exception as e:
        logger.warning(f"⚠️ student_works 表创建警告: {e}")
    finally:
        conn.close()


# ========== ★ 新增：ensure_stages_table ==========
def ensure_stages_table():
    """确保课阶表存在，并为已有课程创建默认课阶"""
    conn = engine.connect()
    try:
        # 1. 创建表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS stages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
                name VARCHAR(50) NOT NULL,
                description TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                unit_price FLOAT DEFAULT 0.0,
                duration INTEGER DEFAULT 60,
                deduct_hours INTEGER DEFAULT 1,
                target_level VARCHAR(50),
                min_age INTEGER,
                max_age INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(course_id, name)
            )
        """))
        conn.commit()

        # 2. 创建索引
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_stages_course_id ON stages(course_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_stages_sort_order ON stages(sort_order)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_stages_is_active ON stages(is_active)"))
        conn.commit()
        logger.info("✅ stages 表初始化完成")

        # 3. 数据迁移：为已有课程创建默认课阶
        result = conn.execute(text("""
            SELECT c.id, c.name, c.unit_price, c.duration, c.deduct_hours
            FROM courses c
            WHERE NOT EXISTS (SELECT 1 FROM stages s WHERE s.course_id = c.id)
        """))
        courses = result.fetchall()

        for course in courses:
            conn.execute(text("""
                INSERT INTO stages (course_id, name, description, unit_price, duration, deduct_hours, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """), (
                course[0],
                f"{course[1]} 默认课阶",
                "系统自动创建的默认课阶",
                course[2] or 0.0,
                course[3] or 60,
                course[4] or 1,
                1
            ))
        conn.commit()
        if len(courses) > 0:
            logger.info(f"✅ 为 {len(courses)} 个课程创建了默认课阶")

    except Exception as e:
        logger.warning(f"⚠️ stages 表初始化警告: {e}")
    finally:
        conn.close()


def ensure_default_roles():
    """确保默认角色存在"""
    from app.models import Role
    db = SessionLocal()
    try:
        roles = [
            {"id": 1, "name": "超级管理员", "permissions": ["*"]},
            {"id": 2, "name": "管理员", "permissions": ["*"]},
            {"id": 3, "name": "教师", "permissions": ["teacher"]},
            {"id": 4, "name": "前台", "permissions": ["reception"]},
        ]
        for r in roles:
            exists = db.query(Role).filter(Role.id == r["id"]).first()
            if not exists:
                role = Role(id=r["id"], name=r["name"], permissions=r["permissions"])
                db.add(role)
        db.commit()
        logger.info("✅ 默认角色初始化完成")
    except Exception as e:
        logger.warning(f"⚠️ 初始化角色失败: {e}")
    finally:
        db.close()


def init_system_configs(db: Session):
    from app.models import SystemConfig
    defaults = [
        ('payment_methods', '["微信支付", "支付宝", "现金", "银行转账"]', '支付方式列表'),
        ('item_categories', '["教材", "教具", "礼品", "办公用品", "其他"]', '商品类别列表'),
        ('exchange_rate', '10', '积分兑换汇率（1元 = ? 积分）'),
        ('login_bg_url', '', '登录页背景图片URL'),
    ]
    for key, value, desc in defaults:
        exists = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if not exists:
            config = SystemConfig(key=key, value=value, description=desc)
            db.add(config)
    db.commit()
    logger.info("✅ 系统配置初始化完成")


def get_database_size() -> dict:
    import os
    db_path = DATABASE_URL.replace('sqlite:///', '')
    if db_path.startswith('./'):
        db_path = db_path[2:]
    if os.path.exists(db_path):
        size_bytes = os.path.getsize(db_path)
        size_mb = size_bytes / (1024 * 1024)
        return {
            "path": db_path,
            "size_bytes": size_bytes,
            "size_mb": round(size_mb, 2),
            "exists": True
        }
    return {"path": db_path, "exists": False, "size_mb": 0}


def vacuum_database():
    conn = engine.connect()
    try:
        conn.execute(text("VACUUM"))
        conn.commit()
        logger.info("✅ 数据库 VACUUM 完成")
    except Exception as e:
        logger.error(f"❌ 数据库 VACUUM 失败: {e}")
    finally:
        conn.close()