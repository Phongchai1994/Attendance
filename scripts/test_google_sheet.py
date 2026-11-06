from pathlib import Path
import gspread

# โฟลเดอร์หลักของโปรเจคต์ Attendance
BASE_DIR = Path(__file__).resolve().parents[1]

# ตำแหน่ง Service Account JSON
CREDENTIALS_FILE = (
    BASE_DIR / 'credentials' / 'google_service_account.json'
)

# ใส่ URL ของ Google Sheets ที่มีอยู่แล้ว
SHEET_URL = 'https://docs.google.com/spreadsheets/d/1b_A4kzGt2K0RatJIcwcya7Eo9_OL6ohlSNjnlk2f6gQ/edit?gid=1882703421#gid=1882703421'

# ชื่อแท็บใน Google Sheets
WORKSHEET_NAME = 'ลาพักผ่อน'

def get_google_sheet_data():
    # ยืนยันตัวตน
    client = gspread.service_account(
        filename=str(CREDENTIALS_FILE)
    )

    # เปิดไฟล์ Google Sheets
    spreadsheet = client.open_by_url(SHEET_URL)

    # เลือกแท็บ
    worksheet = spreadsheet.worksheet(WORKSHEET_NAME)

    # อ่านทุกแถวโดยใช้แถวแรกเป็นชื่อคอลัมน์
    # เก็บข้อมูลเป็นข้อความ เพื่อรักษาเลข 0 นำหน้า
    records = worksheet.get_all_records(
        numericise_ignore=['all']
    )

    return records

def main():
    try:
        data = get_google_sheet_data()

        print(f'พบข้อมูลทั้งหมด {len(data)} รายการ')

        for index, row in enumerate(data, start=1):
            print(f'{index}: {row}')

    except Exception as error:
        print(f'เกิดข้อผิดพลาด: {error}')


if __name__ == '__main__':
    main()


