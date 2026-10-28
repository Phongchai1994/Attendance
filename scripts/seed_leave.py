from datetime import date

from database.session import SessionLocal
from models.employee import Employee
from models.employee_leave import EmployeeLeave
from models.leave_type import LeaveType

from sqlalchemy import inspect

def show_object(obj):
    if obj is None:
        print('ไม่พบข้อมูล')
        return

    mapper = inspect(obj).mapper

    for column in mapper.columns:
        print(f'{column.key} = {getattr(obj, column.key)}')


def seed_leave():
    db = SessionLocal()

    try:
        employee = (
            db.query(Employee)
            .filter(Employee.employee_code == '0001')
            .first()
        )

        print(f'=== employee ===')
        show_object(employee)

        if employee is None:
            print('ไม่พบพนักงาน 0001')
            return

        leave_type = (
            db.query(LeaveType)
            .filter(LeaveType.leave_code == 'PERSONAL')
            .first()
        )

        print(f'=== leave_type ===')
        show_object(leave_type)

        if leave_type is None:
            print('ไม่พบประเภทการลา PERSONAL')
            return

        leave_date = date(2026, 10, 15)

        existing = (
            db.query(EmployeeLeave)
            .filter(
                EmployeeLeave.employee_id == employee.id,
                EmployeeLeave.leave_date == leave_date,
            )
            .first()
        )

        print(f'=== existing ===')
        show_object(existing)

        if existing:
            print('มีข้อมูลการลาของวันนี้แล้ว')
            return

        leave = EmployeeLeave(
            employee_id=employee.id,
            leave_type_id=leave_type.id,
            leave_date=leave_date,
            leave_session='MORNING',
            approval_status='APPROVED',
            source='TEST',
            note='ทดสอบลาเช้าครึ่งวัน',
        )

        db.add(leave)
        db.commit()

        print('เพื่มข้อมูลการลาสำเร็จ')

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

if __name__ == '__main__':
    seed_leave()