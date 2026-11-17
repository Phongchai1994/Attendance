from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import select
from zk import ZK, const
from models.attendance_punch import AttendancePunch
from models.employee import Employee

BANGKOK_TZ = ZoneInfo('Asia/Bangkok')

class ZKSyncService:
    def __init__(self, db_session, device_ip='192.168.1.201', device_port = 4370):
        self.db = db_session
        self.ip = device_ip
        self.port = device_port

    def sync_attendance_logs(self) -> dict:
        '''
        เชื่อมต่อกับเครื่อง ZK ดึง log การสแกนทั้งหมด และบันทึกลง PostgreSQL
        โดยกรองข้อมูลไม่ให้ซ้ำ 
        '''

        zk = ZK(self.ip, self.port, timeout=5, password=0, force_udp=False)
        conn = None
        stats = {"total_fetched": 0, "saved": 0, "skipped": 0, "error": None}

        try:
            # 1. เชื่อมต่อเครื่องสแกน
            conn = zk.connect()
            if not conn:
                stats['error'] = 'ไม่สามารถเชื่อมต่อเครื่องสแกนได้'
                return False

            # เปิดใช้งานเครื่อง (disable device ช่วงดึงข้อมูลเพื่อความเสถียร ตามข้อกำหนดของ pyzk)
            conn.disable_device()

            # 2. ดึงข้อมูล Log ทั้งหมดจากเครื่อง
            zk_attendance = conn.get_attendance()
            if not zk_attendance:
                conn.enable_device()
                return stats

            stats['total_fetched'] = len(zk_attendance)

            # ดึงข้อมูลพนักงานทั้งหมดมาทำ mapping เชื่อมโยงจาก legacy_user_id หรือ employee_code ของ zk กับฐานข้อมูล
            employees = self.db.scalars(select(Employee)).all()
            # สมมติว่าใช้ employee_code หรือ lagacy_user_id เทียบกับ user_id ของเครื่อง zk
            emp_map = {str(emp.employee_code): emp.id for emp in employees}

            for attend in zk_attendance:
                # attend.user_id คือรหัสพนักงานในเครื่อง zk, attend.timestamp คือเวลาสแกน
                zk_user_id = str(attend.user_id)
                punch_time = attend.timestamp

                # แปลงเวลาให้เป็น timezone กรุงเทพ
                if punch_time.tzinfo is None:
                    punch_time = punch_time.replace(tzinfo=BANGKOK_TZ)
                else:
                    punch_time = punch_time.astimezone(BANGKOK_TZ)

                # หาว่า employee_id ในระบบเราคือใคร
                employee_id = emp_map.get(zk_user_id)
                if not employee_id:
                    # ถ้าไม่พบพนักงานคนนี้ในระบบ ข้ามไปก่อน
                    stats['skipped'] += 1
                    continue

                # 3. ตรวจสอบว่ามีข้อมูล punch นี้ในฐานข้อมุลหรือยัง (ป้องกันการบันทึกซ้ำ)
                existing_punch = self.db.scalar(
                    select(AttendancePunch).where(
                        AttendancePunch.employee_id == employee_id,
                        AttendancePunch.punched_at == punch_time
                    )
                )

                if existing_punch is None:
                    # สร้างรายการ punch ใหม่ลง postgreSQL
                    new_punch = AttendancePunch(
                        employee_id=employee_id,
                        device_id=1,
                        punched_at=punch_time,
                        source='ZKTeco_Device',
                        raw_check_type=str(attend.status)
                    )
                    self.db.add(new_punch)
                    stats['saved'] += 1
                else:
                    stats['skipped'] += 1

            self.db.commit()
            conn.enable_device()
            return stats

        except Exception as e:
            if conn:
                try:
                    conn.enable_device()
                except:
                    pass

            self.db.rollback()
            stats['error'] = str(e)
            return stats

    def upload_employee_to_zk(self, employee_code, employee_name, uid=None, device_ip="192.168.1.201", port=4370):
        """ส่งข้อมูลพนักงาน 1 คนไปยังเครื่องสแกนนิ้ว"""
        from zk import ZK, const
        
        target_ip = getattr(self, 'device_ip', getattr(self, 'ip', getattr(self, 'ip_address', device_ip)))
        target_port = getattr(self, 'port', port)
        
        zk = ZK(target_ip, port=target_port, timeout=5)
        conn = None
        try:
            conn = zk.connect()
            
            # ดึงรายชื่อผู้ใช้ทั้งหมดในเครื่องมาก่อน เพื่อหาว่ามีพนักงานคนนี้อยู่แล้วหรือไม่
            users = conn.get_users()
            existing_user = next((u for u in users if u.user_id == str(employee_code)), None)
            
            short_name = employee_name[:20]
            
            if existing_user:
                # ถ้ามีอยู่แล้ว ให้อัปเดตข้อมูล (ใช้ uid เดิมของเครื่อง)
                conn.set_user(
                    uid=existing_user.uid,
                    name=short_name,
                    privilege=const.USER_DEFAULT,
                    password=existing_user.password,
                    group_id=existing_user.group_id,
                    user_id=str(employee_code)
                )
                return {"status": "success", "msg": f"อัปเดตข้อมูล {employee_name} ในเครื่องสแกนสำเร็จ"}
            else:
                # ถ้าเป็นคนใหม่ ให้เครื่องสแกนหา uid ว่างให้เอง (รันเลขต่อจากคนล่าสุด)
                # ปกติ uid ของเครื่อง ZK จะต้องเป็นตัวเลขรันไปเรื่อยๆ (1, 2, 3...)
                max_uid = max([u.uid for u in users]) if users else 0
                new_uid = max_uid + 1
                
                conn.set_user(
                    uid=new_uid,
                    name=short_name,
                    privilege=const.USER_DEFAULT,
                    password='',
                    group_id='',
                    user_id=str(employee_code)
                )
                return {"status": "success", "msg": f"เพิ่มข้อมูล {employee_name} ไปยังเครื่องสแกนสำเร็จ"}
                
        except Exception as e:
            return {"status": "error", "msg": str(e)}
        finally:
            if conn:
                conn.disconnect()