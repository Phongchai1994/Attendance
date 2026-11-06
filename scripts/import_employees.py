import pandas as pd
from database.session import SessionLocal
from models.employee import Employee
from models.department import Department

def import_employees_from_excel(file_path: str):
    db = SessionLocal()
    try:
        print(f"กำลังอ่านข้อมูลจากไฟล์: {file_path}")
        # อ่านไฟล์ Excel
        df = pd.read_excel(file_path)
        
        # แปลงค่าว่าง (NaN/NaT) ใน pandas ให้เป็น None เพื่อให้ PostgreSQL รับได้
        df = df.where(pd.notnull(df), None)

        added_count = 0
        updated_count = 0

        for index, row in df.iterrows():
            emp_code = str(row.get('employee_code', '')).strip()
            
            # ถ้าไม่มีรหัสพนักงาน ให้ข้ามแถวนั้นไป
            if not emp_code or emp_code == 'None':
                continue

            # เตรียมข้อมูล
            title = row.get('title')
            first_name = row.get('first_name')
            last_name = row.get('last_name')
            pos_name = row.get('position_name')
            pos_level = row.get('position_level')
            dept_id = row.get('department_id')
            
            # จัดการค่าตัวเลข/ตัวหนังสือ
            card_no = str(row.get('card_no')).strip() if row.get('card_no') is not None else None
            if card_no == 'None' or card_no == 'nan': card_no = None
            
            legacy_id = str(row.get('legacy_user_id')).strip() if row.get('legacy_user_id') is not None else None
            if legacy_id == 'None' or legacy_id == 'nan': legacy_id = None
            
            # จัดการวันที่
            hired_date = row.get('hired_date')
            if hired_date and pd.notna(hired_date):
                if hasattr(hired_date, 'date'):
                    hired_date = hired_date.date()
            else:
                hired_date = None

            # จัดการสถานะ (ค่าเริ่มต้นคือ True)
            is_active_val = row.get('is_active')
            is_active = bool(is_active_val) if is_active_val is not None else True

            # ค้นหาว่ามีพนักงานรหัสนี้ในระบบหรือยัง
            existing_emp = db.query(Employee).filter(Employee.employee_code == emp_code).first()

            if existing_emp:
                # อัปเดตข้อมูล
                existing_emp.title = title
                existing_emp.first_name = first_name
                existing_emp.last_name = last_name
                existing_emp.position_name = pos_name
                existing_emp.position_level = pos_level
                existing_emp.department_id = dept_id
                existing_emp.card_no = card_no
                existing_emp.legacy_user_id = legacy_id
                existing_emp.hired_date = hired_date
                existing_emp.is_active = is_active
                updated_count += 1
            else:
                # เพิ่มพนักงานใหม่
                new_emp = Employee(
                    employee_code=emp_code,
                    title=title,
                    first_name=first_name,
                    last_name=last_name,
                    position_name=pos_name,
                    position_level=pos_level,
                    department_id=dept_id,
                    card_no=card_no,
                    legacy_user_id=legacy_id,
                    hired_date=hired_date,
                    is_active=is_active
                )
                db.add(new_emp)
                added_count += 1

        # บันทึกลงฐานข้อมูล
        db.commit()
        print("-" * 40)
        print("🎉 นำเข้าข้อมูลพนักงานสำเร็จ!")
        print(f"เพิ่มพนักงานใหม่ : {added_count} รายการ")
        print(f"อัปเดตข้อมูลเดิม  : {updated_count} รายการ")
        print("-" * 40)

    except Exception as e:
        db.rollback()
        print(f"❌ เกิดข้อผิดพลาด: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # ระบุชื่อไฟล์ Excel ของคุณตรงนี้ (เอาไฟล์ไปวางในโฟลเดอร์เดียวกับโปรเจกต์)
    EXCEL_FILE_NAME = "employee_import_template.xlsx" 
    import_employees_from_excel(EXCEL_FILE_NAME)