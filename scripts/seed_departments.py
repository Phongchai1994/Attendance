from database.session import SessionLocal
from models.department import Department


def seed_departments():
    db = SessionLocal()

    try:
        department = [
            Department(
                department_code="ADMIN",
                department_name="ฝ่ายบริหารทั่วไป",
            ),
            Department(
                department_code="CONTROL",
                department_name="ฝ่ายควบคุมผู้ต้องขัง",
            ),
            Department(
                department_code="PENAL",
                department_name="ฝ่ายทัณฑปฏิบัติ",
            ),
        ]

        db.add_all(department)
        db.commit()

        print('เพิ่มข้อมูลหน่วยงานสำเร็จ')

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_departments()