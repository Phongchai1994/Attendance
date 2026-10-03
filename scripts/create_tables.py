from database.session import engine
from models.base import Base

import models

def create_tables():
    print('กำลังสร้างตาราง')

    Base.metadata.create_all(bind=engine)

    print('สร้างตารางสำเร็จ')

if __name__ == '__main__':
    create_tables()