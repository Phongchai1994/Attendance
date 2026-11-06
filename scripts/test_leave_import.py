from database.session import SessionLocal
from services.leave_import_service import LeaveImportService

def test_import():
    db = SessionLocal()
    try:
        service = LeaveImportService(db=db)
        stats = service.sync_leaves_from_sheet()
        
        print("\n--------------------------------")
        print("ผลการนำเข้าข้อมูลการลาจาก Google Sheets")
        print("--------------------------------")
        print(f"อ่านข้อมูลจาก Sheet ได้     : {stats['total_rows']} แถว")
        print(f"บันทึกลงฐานข้อมูลใหม่ (Insert) : {stats['inserted']} วัน")
        print(f"อัปเดตข้อมูล (Update)          : {stats['updated']} วัน")
        print(f"ข้ามเนื่องจากซ้ำ (Skipped)     : {stats['skipped']} วัน")
        print(f"พบข้อผิดพลาด (Errors)          : {stats['errors']} รายการ")
        print("--------------------------------\n")

    finally:
        db.close()


if __name__ == '__main__':
    test_import()