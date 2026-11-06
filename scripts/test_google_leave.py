from services.google_leave_service import (
    GoogleLeaveService
)


def test_google_leave():
    service = GoogleLeaveService()

    rows = service.get_rows()

    print(f'พบข้อมูลทั้งหมด {len(rows)} รายการ')
    print()

    for index, row in enumerate(rows, start=1):
        print(f'{index}: {row}')

if __name__ == '__main__':
    test_google_leave()