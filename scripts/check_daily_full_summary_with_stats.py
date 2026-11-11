from datetime import date
from database.session import SessionLocal
from models.employee import Employee
from services.attendance_service import AttendanceService

def generate_full_summary_with_stats():
    db = SessionLocal()
    try:
        service = AttendanceService(db)
        
        # กำหนดวันที่ต้องการตรวจสอบสรุปผล (สามารถเปลี่ยนวันที่ได้ตามต้องการ)
        target_date = date(2026, 11, 9)
        
        # ดึงรายชื่อพนักงานทั้งหมดในระบบ เรียงตามรหัส
        employees = db.query(Employee).order_by(Employee.employee_code.asc()).all()
        
        summary_stats = {
            "normal": 0,
            "late": 0,
            "leave": 0,
            "absent": 0,
            "other": 0
        }
        
        results_list = []

        for emp in employees:
            try:
                # พยายามประเมินผลรายวันของพนักงานแต่ละคน
                result = service.finalize_daily_attendance(
                    employee_id=emp.id,
                    duty_date=target_date
                )
                
                status_code = result.final_status_code
                
                # นับจำนวนสถิติ
                if "LEAVE" in status_code:
                    summary_stats["leave"] += 1
                elif status_code == "LATE" or "LATE" in status_code:
                    summary_stats["late"] += 1
                elif status_code in ["NORMAL", "NORMAL_OUT", "NIGHT_DUTY_COMPLETE"]:
                    summary_stats["normal"] += 1
                else:
                    summary_stats["other"] += 1

                results_list.append({
                    "code": emp.employee_code,
                    "name": f"{emp.first_name} {emp.last_name}",
                    "shift": result.shift_code or "-",
                    "status_code": status_code,
                    "status_text": result.final_status_text,
                    "in": result.first_in_at.strftime('%H:%M') if result.first_in_at else "-",
                    "out": result.last_out_at.strftime('%H:%M') if result.last_out_at else "-"
                })
                
            except ValueError:
                # เคสที่ไม่มีตารางเวร, ไม่มีสแกนนิ้ว, และไม่ได้ลา (ถือว่าขาดงานในวันนั้น)
                summary_stats["absent"] += 1
                results_list.append({
                    "code": emp.employee_code,
                    "name": f"{emp.first_name} {emp.last_name}",
                    "shift": "-",
                    "status_code": "ABSENT",
                    "status_text": "ไม่มาปฏิบัติงาน / ขาดงาน",
                    "in": "-",
                    "out": "-"
                })

        # แสดงผลรายงานตาราง
        print(f"======================================================================================")
        print(f" รายงานสรุปผลการปฏิบัติงานประจำวันทั้งหมด (รวมคนมา, ลา, และขาด) วันที่: {target_date}")
        print(f"======================================================================================")
        print(f"{'รหัส':<6} | {'ชื่อ-นามสกุล':<22} | {'กะ':<8} | {'สถานะ':<22} | {'เข้า':<6} | {'ออก':<6} | {'รายละเอียด':<15}")
        print("-" * 86)

        for item in results_list:
            print(f"{item['code']:<6} | {item['name']:<22} | {item['shift']:<8} | {item['status_code']:<22} | {item['in']:<6} | {item['out']:<6} | {item['status_text'][:15]:<15}")

        print("======================================================================================")
        print(f" 📊 สรุปยอดรวมประจำวัน:")
        print(f"   - พนักงานทั้งหมดในระบบ : {len(employees)} คน")
        print(f"   - มาปฏิบัติงานปกติ     : {summary_stats['normal']} คน")
        print(f"   - มาสาย               : {summary_stats['late']} คน")
        print(f"   - ลาหยุด (อนุมัติแล้ว)  : {summary_stats['leave']} คน")
        print(f"   - ขาดงาน / ไม่พบข้อมูล : {summary_stats['absent']} คน")
        print(f"======================================================================================")

    finally:
        db.close()

if __name__ == '__main__':
    generate_full_summary_with_stats()