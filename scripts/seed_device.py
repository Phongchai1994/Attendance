from database.session import SessionLocal
from models.device import Device


def seed_device():
    db = SessionLocal()

    try:
        existing = (
            db.query(Device)
            .filter(Device.device_code == "DEV01")
            .first()
        )

        if existing:
            print('มี DEV01 อยู่แล้ว')
            return

        device = Device(
            device_code = "DEV01",
            device_name='เครื่องสแกนหน้าประตูเจ้าหน้าที่',
            ip_address='192.168.1.201',
            port=4370,
            location_name='ประตูทางเข้าเจ้าหน้าที่',
            device_type='ZKTeco MB360',
        )

        db.add(device)
        db.commit()

        print('เพื่อเครื่องสแกนสำเร็จ')

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

if __name__ == "__main__":
    seed_device()