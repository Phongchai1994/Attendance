from database.session import SessionLocal
from services.zk_sync_service import ZKSyncService

def test_zk_sync():
    print('กำลังเริ่มเชื่อมต่อเครื่องสแกน ZKTeco ...')

    # เปิด session
    db = SessionLocal()
    try:
        device_ip = '192.168.1.201'

        sync_service = ZKSyncService(db,device_ip=device_ip)

        result = sync_service.sync_attendance_logs()

        print("\n--------------------------------------------")
        print(" ผลการซิงค์ข้อมูลจากเครื่อง ZK")
        print("--------------------------------------------")
        if result["error"]:
            print(f"เกิดข้อผิดพลาด: {result['error']}")
        else:
            print(f"ดึงข้อมูลทั้งหมดจากเครื่อง : {result['total_fetched']} รายการ")
            print(f"บันทึกใหม่ลงฐานข้อมูล     : {result['saved']} รายการ")
            print(f"ข้าม (ข้อมูลซ้ำ/ไม่พบชื่อ)  : {result['skipped']} รายการ")
        print("--------------------------------------------")

    finally:
        db.close()


if __name__ == '__main__':
    test_zk_sync()