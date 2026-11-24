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

    
    def upload_employee_to_zk(
        self,
        employee_code,
        employee_name,
        uid=None,
        device_ip="192.168.1.201",
        port=4370,
    ):
        """เพิ่มหรืออัปเดตเจ้าหน้าที่ใน ZKTeco โดยรักษา UID เดิม"""

        from zk import ZK, const

        code = str(employee_code).strip()
        name = str(employee_name).strip()[:20]

        if not code or not name:
            return {
                "status": "error",
                "msg": "รหัสหรือชื่อเจ้าหน้าที่ว่าง",
            }

        zk = ZK(
            self.ip,
            port=self.port,
            timeout=5,
            password=0,
            force_udp=False,
        )

        conn = None
        device_disabled = False
        result = {
            "status": "error",
            "msg": "ยังไม่สามารถส่งข้อมูลได้",
        }

        try:
            conn = zk.connect()

            if conn is None:
                raise RuntimeError(
                    "เชื่อมต่อเครื่องสแกนไม่ได้"
                )

            # ป้องกันการใช้งานเครื่องระหว่างปรับข้อมูล
            conn.disable_device()
            device_disabled = True

            users = conn.get_users() or []

            matched = [
                user for user in users
                if str(user.user_id) == code
            ]

            if len(matched) > 1:
                raise RuntimeError(
                    "พบบัญชีรหัสเดียวกันหลายรายการบนเครื่อง"
                )

            if matched:
                old = matched[0]

                # เก็บข้อมูลสำคัญเดิมของผู้ใช้ไว้
                target_uid = old.uid
                privilege = old.privilege
                password = old.password or ""
                group_id = old.group_id or ""
                card = getattr(old, "card", 0) or 0

                action = "อัปเดต"

            else:
                # เจ้าหน้าที่ใหม่: ใช้ UID ที่ยังไม่ซ้ำ
                max_uid = max(
                    (int(user.uid) for user in users),
                    default=0,
                )

                target_uid = max_uid + 1

                if target_uid > 65535:
                    raise RuntimeError(
                        "ไม่พบ UID ว่างที่รองรับ"
                    )

                privilege = const.USER_DEFAULT
                password = ""
                group_id = ""
                card = 0
                action = "เพิ่ม"

            saved = conn.set_user(
                uid=target_uid,
                name=name,
                privilege=privilege,
                password=password,
                group_id=group_id,
                user_id=code,
                card=card,
            )

            if saved is False:
                raise RuntimeError(
                    "เครื่องสแกนไม่ยอมรับข้อมูลผู้ใช้"
                )

            # อ่านกลับเพื่อยืนยันว่ารหัสผู้ใช้อยู่ในเครื่อง
            users_after = conn.get_users() or []

            verified = any(
                str(user.user_id) == code
                and int(user.uid) == int(target_uid)
                for user in users_after
            )

            if not verified:
                raise RuntimeError(
                    "ส่งข้อมูลแล้วแต่ตรวจสอบผลบนเครื่องไม่ผ่าน"
                )

            result = {
                "status": "success",
                "msg": (
                    f"{action}เจ้าหน้าที่ {code} "
                    f"ในเครื่องสแกนสำเร็จ"
                ),
            }

        except Exception as exc:
            result = {
                "status": "error",
                "msg": str(exc),
            }

        finally:
            if conn is not None:
                if device_disabled:
                    try:
                        conn.enable_device()
                    except Exception as exc:
                        result = {
                            "status": "error",
                            "msg": (
                                "ไม่สามารถเปิดเครื่องสแกน"
                                f"กลับสู่โหมดใช้งาน: {exc}"
                            ),
                        }

                try:
                    conn.disconnect()
                except Exception:
                    pass

        return result
