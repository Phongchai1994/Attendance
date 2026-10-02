from database.session import SessionLocal
from models.department import Department
from models.employee import Employee


def seed_employee():
    db = SessionLocal()

    try:
        department = (
            db.query(Department)
            .filter(Department.department_code == "ADMIN")
            .first()
        )

        if department is None:
            print("ไม่พบหน่วยงาน")
            return

        employee = Employee(
            employee_code="0001",
            title="นาย",
            first_name="สมชาย",
            last_name="ใจดี",
            position_name="เจ้าพนักงานราชทัณฑ์",
            position_level="ชำนาญงาน",
            department_id=department.id,
            legacy_user_id=1,
        )

        db.add(employee)
        db.commit()

        print('เพิ่มพนักงานสำเร็จ')

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

if __name__ == "__main__":
    seed_employee()



