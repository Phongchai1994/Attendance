
"""บริการจัดการข้อมูลเจ้าหน้าที่ แยก SQLAlchemy ออกจาก PyQt6 GUI"""

from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from database.session import SessionLocal
from models.department import Department
from models.employee import Employee


class EmployeeValidationError(ValueError):
    """ข้อมูลเจ้าหน้าที่ไม่ผ่านการตรวจสอบ"""


def _clean_text(value, field, max_length, required=False):
    text = str(value or "").strip()

    if required and not text:
        raise EmployeeValidationError(f"กรุณากรอก{field}")

    if len(text) > max_length:
        raise EmployeeValidationError(
            f"{field}ยาวเกิน {max_length} ตัวอักษร"
        )

    return text or None


def _parse_date(value, field):
    if value is None or value == "":
        return None

    if isinstance(value, date):
        return value

    try:
        return date.fromisoformat(str(value))
    except (ValueError, TypeError):
        raise EmployeeValidationError(
            f"{field}ไม่ถูกต้อง"
        ) from None


def _serialize(employee):
    """แปลงข้อมูล ORM เป็น Dict เพื่อส่งกลับ GUI"""

    dep = employee.department

    return {
        "id": employee.id,
        "employee_code": employee.employee_code,
        "title": employee.title or "",
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "position_name": employee.position_name or "",
        "position_level": employee.position_level or "",
        "department_id": employee.department_id,
        "department_name": (
            dep.department_name if dep else ""
        ),
        "card_no": employee.card_no or "",
        "legacy_user_id": employee.legacy_user_id,
        "first_hired_date": (
            employee.first_hired_date.isoformat()
            if employee.first_hired_date else None
        ),
        "start_date": (
            employee.start_date.isoformat()
            if employee.start_date else None
        ),
        "resigned_date": (
            employee.resigned_date.isoformat()
            if employee.resigned_date else None
        ),
        "is_active": employee.is_active,
    }


def load_employee_snapshot():
    """อ่านข้อมูลเจ้าหน้าที่และสังกัดโดยไม่แก้ไขฐานข้อมูล"""

    with SessionLocal() as db:
        employees = db.scalars(
            select(Employee)
            .options(joinedload(Employee.department))
            .order_by(Employee.employee_code)
        ).all()

        departments = db.scalars(
            select(Department)
            .order_by(Department.department_name)
        ).all()

        return {
            "employees": [
                _serialize(emp)
                for emp in employees
            ],
            "departments": [
                {
                    "id": dep.id,
                    "name": dep.department_name,
                    "is_active": dep.is_active,
                }
                for dep in departments
            ],
        }


def save_employee(payload):
    """เพิ่มหรือแก้ไขเจ้าหน้าที่ด้วย Transaction เดียว"""

    employee_id = payload.get("id")

    if employee_id is not None:
        try:
            employee_id = int(employee_id)
        except (ValueError, TypeError):
            raise EmployeeValidationError(
                "รหัส ID ภายในไม่ถูกต้อง"
            ) from None

    cleaned = {
        "employee_code": _clean_text(
            payload.get("employee_code"),
            "รหัสเจ้าหน้าที่",
            30,
            True,
        ),
        "title": _clean_text(
            payload.get("title"),
            "คำนำหน้า",
            30,
        ),
        "first_name": _clean_text(
            payload.get("first_name"),
            "ชื่อ",
            100,
            True,
        ),
        "last_name": _clean_text(
            payload.get("last_name"),
            "นามสกุล",
            100,
            True,
        ),
        "position_name": _clean_text(
            payload.get("position_name"),
            "ตำแหน่ง",
            150,
        ),
        "position_level": _clean_text(
            payload.get("position_level"),
            "ระดับ",
            100,
        ),
        "card_no": _clean_text(
            payload.get("card_no"),
            "หมายเลขบัตร",
            50,
        ),
    }

    # ตรวจสอบหน่วยงาน
    dep_id = payload.get("department_id")

    if dep_id is not None and dep_id != "":
        try:
            dep_id = int(dep_id)
        except (TypeError, ValueError):
            raise EmployeeValidationError(
                "หน่วยงานไม่ถูกต้อง"
            ) from None
    else:
        dep_id = None

    cleaned["department_id"] = dep_id

    # ตรวจสอบ Legacy User ID
    raw_legacy_id = payload.get("legacy_user_id")

    if raw_legacy_id not in (None, ""):
        try:
            legacy_id = int(raw_legacy_id)
        except (ValueError, TypeError):
            raise EmployeeValidationError(
                "Legacy User ID ต้องเป็นตัวเลข"
            ) from None

        if not 0 <= legacy_id <= 9223372036854775807:
            raise EmployeeValidationError(
                "Legacy User ID อยู่นอกช่วง BIGINT"
            )
    else:
        legacy_id = None

    cleaned["legacy_user_id"] = legacy_id

    # ตรวจสอบวันที่
    first_hired = _parse_date(
        payload.get("first_hired_date"),
        "วันบรรจุครั้งแรก",
    )

    started = _parse_date(
        payload.get("start_date"),
        "วันเริ่มงาน",
    )

    resigned = _parse_date(
        payload.get("resigned_date"),
        "วันสิ้นสุดงาน",
    )

    if first_hired and started and first_hired > started:
        raise EmployeeValidationError(
            "วันบรรจุครั้งแรกต้องไม่หลังวันเริ่มงานที่เรือนจำ"
        )

    if resigned and first_hired and resigned < first_hired:
        raise EmployeeValidationError(
            "วันสิ้นสุดงานต้องไม่ก่อนวันบรรจุครั้งแรก"
        )

    if resigned and started and resigned < started:
        raise EmployeeValidationError(
            "วันสิ้นสุดงานต้องไม่ก่อนวันเริ่มงานที่เรือนจำ"
        )

    cleaned.update({
        "first_hired_date": first_hired,
        "start_date": started,
        "resigned_date": resigned,
    })

    with SessionLocal() as db:
        try:
            if employee_id is None:
                # สร้างรายการใหม่ แต่ยังไม่ INSERT
                employee = Employee(is_active=True)
            else:
                employee = db.get(Employee, employee_id)

                if employee.employee_code != cleaned["employee_code"]:
                    raise EmployeeValidationError(
                        "ไม่อนุญาตให้เปลี่ยนรหัสเจ้าหน้าที่ในขั้นตอนนี้ "
                        "เพราะรหัสเชื่อมโยงกับเครื่องสแกน"
                    )

                if employee is None:
                    raise EmployeeValidationError(
                        "ไม่พบเจ้าหน้าที่ที่ต้องการแก้ไข"
                    )

            # ตรวจสอบรหัสเจ้าหน้าที่ซ้ำ
            duplicate_query = select(Employee.id).where(
                Employee.employee_code
                == cleaned["employee_code"]
            )

            if employee_id is not None:
                duplicate_query = duplicate_query.where(
                    Employee.id != employee_id
                )

            duplicate = db.scalar(
                duplicate_query.limit(1)
            )

            if duplicate is not None:
                raise EmployeeValidationError(
                    "รหัสเจ้าหน้าที่นี้ถูกใช้งานแล้ว"
                )

            # ตรวจสอบว่าสังกัดมีอยู่จริง
            if (
                dep_id is not None
                and db.get(Department, dep_id) is None
            ):
                raise EmployeeValidationError(
                    "ไม่พบหน่วยงานที่เลือก"
                )

            # ตรวจสอบ Legacy User ID ซ้ำ
            if legacy_id is not None:
                legacy_query = select(Employee.id).where(
                    Employee.legacy_user_id == legacy_id
                )

                if employee_id is not None:
                    legacy_query = legacy_query.where(
                        Employee.id != employee_id
                    )

                duplicate_legacy = db.scalar(
                    legacy_query.limit(1)
                )

                if duplicate_legacy is not None:
                    raise EmployeeValidationError(
                        "Legacy User ID นี้ถูกใช้งานแล้ว"
                    )

            # นำข้อมูลไปกำหนดให้ Model
            for field, value in cleaned.items():
                setattr(employee, field, value)

            if employee_id is None:
                db.add(employee)

            db.flush()

            saved_id = employee.id

            db.commit()

            return {"id": saved_id}

        except IntegrityError as exc:
            db.rollback()
            raise EmployeeValidationError(
                "บันทึกไม่สำเร็จ: "
                "รหัสเจ้าหน้าที่หรือ Legacy User ID ซ้ำ"
            ) from exc

        except Exception:
            db.rollback()
            raise


def set_employee_active(employee_id, active):
    """ปิดหรือเปิดใช้งาน โดยไม่ลบประวัติเดิม"""

    with SessionLocal() as db:
        try:
            employee = db.get(
                Employee,
                int(employee_id),
            )

            if employee is None:
                raise EmployeeValidationError(
                    "ไม่พบเจ้าหน้าที่"
                )

            employee.is_active = bool(active)
            db.commit()

            return {
                "id": employee.id,
                "is_active": bool(active),
            }

        except Exception:
            db.rollback()
            raise


def sync_employee_to_zk(employee_id):
    """ส่งข้อมูลเจ้าหน้าที่ที่บันทึกแล้วไปเครื่องสแกน"""

    # Import ภายในฟังก์ชัน เพื่อไม่ให้การโหลด GUI
    # ขึ้นอยู่กับการเชื่อมต่อเครื่องสแกน
    from services.zk_sync_service import ZKSyncService

    with SessionLocal() as db:
        employee = db.get(Employee, int(employee_id))

        if employee is None:
            raise EmployeeValidationError(
                "ไม่พบเจ้าหน้าที่ที่จะส่งไปเครื่องสแกน"
            )

        if not employee.is_active:
            return {
                "id": employee.id,
                "status": "skipped",
                "msg": "เจ้าหน้าที่ปิดใช้งาน จึงไม่ส่งข้อมูล",
            }

        full_name = (
            f"{employee.first_name} "
            f"{employee.last_name}"
        ).strip()

        service = ZKSyncService(db)

        result = service.upload_employee_to_zk(
            employee_code=employee.employee_code,
            employee_name=full_name,
        )

        result["id"] = employee.id
        return result
