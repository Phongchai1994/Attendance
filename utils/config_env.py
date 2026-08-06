import os
import sys 
from dotenv import load_dotenv

def get_project_root():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.abspath(os.path.join(current_dir, '..'))
    
def find_env_file(start_path):
    '''ค้นหาไฟล์ .env ในทุกโฟล์เดอร์ย่อย'''
    # Floder ที่ไม่ต้องการ
    ignore_dirs = {'.git', '.venv', '.vscode', '__pycache__'}

    for dirpath, dirnames, filenames in os.walk(start_path):
        # ลบโฟล์เดอร์ที่ไม่ต้องการออกจากลิตส์ ของ dirnames
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]

        # ถ้าเจอไฟล์ .env ในโฟลเดอร์ที่กำลังสแกนอยู่ ให้ส่งคืน path นั้นทันที
        if '.env' in filenames:
            return os.path.join(dirpath, '.env')
        
    return None # คืนค่า None ถ้าแสกนจนจบแล้วไม่เจอเลย

def load_project_env():
    root_dir = get_project_root()

    env_path = find_env_file(root_dir)

    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f'Loaded .env จาก: {env_path}')
    else:
        print(f'Warning: ไม่พบไฟล์ .env ที่ตำแหน่ง {env_path}')

load_project_env()