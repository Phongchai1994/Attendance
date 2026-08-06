import psycopg2
import traceback
import os
from psycopg2 import Error, Binary
from psycopg2.extensions import connection
from utils import config_env

# ตั้งค่า Connection (ในระบบจริงควรดึงจากไฟล์ .env)
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = "postgres"
DB_PASSWORD = "your_password"
DB_PORT = "5432"




