from database.session import SessionLocal
from models.department import Department

def seed_departments():
    db = SessionLocal()
    
    try:
        # รายชื่อแผนก/สังกัดทั้งหมดในเรือนจำจังหวัดจันทบุรี
        departments_data = [
            "ฝ่ายบริหารทั่วไป",
            "ส่วนควบคุมผู้ต้องขัง",
            "ส่วนทัณฑปฏิบัติ",
            "ส่วนสวัสดิการและสงเคราะห์ผู้ต้องขัง",
            "ส่วนพัฒนาผู้ต้องขัง",
            "เรือนจำชั่วคราวทุ่งพลงใต้"
        ]
        
        print("กำลังเตรียมข้อมูลแผนก/สังกัด...")
        
        added_count = 0
        for dept_name in departments_data:
            # เช็คว่ามีแผนกนี้ในฐานข้อมูลหรือยัง เพื่อป้องกันการเพิ่มซ้ำ
            existing = db.query(Department).filter(Department.department_name == dept_name).first()
            
            if not existing:
                new_dept = Department(department_name=dept_name)
                db.add(new_dept)
                added_count += 1
                print(f"  [+] เพิ่ม: {dept_name}")
            else:
                print(f"  [-] มีอยู่แล้ว: {dept_name}")
        
        if added_count > 0:
            db.commit()
            print(f"\nบันทึกข้อมูลแผนกสำเร็จ จำนวน {added_count} รายการ")
        else:
            print("\nไม่มีข้อมูลแผนกใหม่ที่ต้องเพิ่ม")
            
    except Exception as e:
        db.rollback()
        print(f"เกิดข้อผิดพลาด: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_departments()