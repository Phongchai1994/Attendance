import sys
from pathlib import Path

# เพิ่ม Path ให้ Python รู้จักโฟลเดอร์หลักของโปรเจกต์
sys.path.append(str(Path(__file__).resolve().parents[1]))

from database.session import SessionLocal
from models.leave_type import LeaveType
from sqlalchemy import or_  # เพิ่ม import ตัวนี้เข้ามา

def seed_leave_types():
    db = SessionLocal()
    try:
        # 📋 รวมรายการประเภทการลาและสถานะพิเศษทั้งหมดที่ใช้ในระบบเรือนจำ
        leave_types_data = [
            {"leave_code": "SICK", "leave_name": "ลาป่วย", "is_active": True},
            {"leave_code": "PERSONAL", "leave_name": "ลากิจ", "is_active": True},
            {"leave_code": "VACATION", "leave_name": "ลาพักผ่อน", "is_active": True},
            {"leave_code": "MATERNITY", "leave_name": "ลาคลอด", "is_active": True},
            {"leave_code": "ORDINATION", "leave_name": "ลาอุปสมบท", "is_active": True},
            {"leave_code": "STUDY", "leave_name": "ลาศึกษาต่อ", "is_active": True},
            {"leave_code": "OFFICIAL_DUTY", "leave_name": "ไปราชการ", "is_active": True},
            {"leave_code": "ACTING_COMMANDER", "leave_name": "รักษาราชการแทน", "is_active": True},
            {"leave_code": "HOSPITAL_ESCORT", "leave_name": "ควบคุมผู้ต้องขังป่วย รพ.", "is_active": True}
        ]

        print("⏳ กำลังตรวจสอบและตั้งต้นข้อมูลประเภทการลา (Seed Leave Types)...")
        
        added_count = 0
        updated_count = 0
        
        for item in leave_types_data:
            # 💡 เช็คว่ามี รหัส นี้ หรือ ชื่อ นี้ อยู่ในระบบแล้วหรือไม่
            exists = db.query(LeaveType).filter(
                or_(
                    LeaveType.leave_code == item["leave_code"],
                    LeaveType.leave_name == item["leave_name"]
                )
            ).first()
            
            if not exists:
                # ถ้าไม่เคยมีเลย ให้เพิ่มใหม่
                new_leave_type = LeaveType(
                    leave_code=item["leave_code"],
                    leave_name=item["leave_name"],
                    is_active=item["is_active"]
                )
                db.add(new_leave_type)
                added_count += 1
                print(f"✅ เพิ่มใหม่: {item['leave_name']} ({item['leave_code']})")
            else:
                # ถ้ามีแล้ว เช็คว่ารหัสหรือชื่อสะกดผิด/ไม่ตรงกันไหม ถ้าไม่ตรงให้อัปเดตแก้ให้ถูก
                if exists.leave_code != item["leave_code"] or exists.leave_name != item["leave_name"]:
                    print(f"🔄 อัปเดตข้อมูลเก่า: '{exists.leave_name}' ({exists.leave_code}) -> '{item['leave_name']}' ({item['leave_code']})")
                    exists.leave_code = item["leave_code"]
                    exists.leave_name = item["leave_name"]
                    exists.is_active = item["is_active"]
                    updated_count += 1
                else:
                    print(f"⏩ ข้าม: {item['leave_name']} (มีข้อมูลสมบูรณ์อยู่แล้ว)")

        db.commit()
        print("-" * 40)
        print(f"🎉 Seed ข้อมูลเสร็จสิ้น! | เพิ่มใหม่ {added_count} รายการ | อัปเดต {updated_count} รายการ")

    except Exception as e:
        db.rollback()
        print(f"❌ เกิดข้อผิดพลาดในการ Seed ข้อมูล: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_leave_types()