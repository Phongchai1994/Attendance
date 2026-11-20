
from sqlalchemy import text
from database.session import engine


# รายการตรวจสอบความสมบูรณ์ของข้อมูล
CHECKS = {
    "EMPLOYEE_DATE_ORDER": """
        SELECT COUNT(*)
        FROM public.employees
        WHERE first_hired_date > start_date
           OR start_date > resigned_date
           OR first_hired_date > resigned_date
    """,

    "EMPLOYEE_EMPTY_CODE": """
        SELECT COUNT(*)
        FROM public.employees
        WHERE TRIM(employee_code) = ''
    """,

    "EMPLOYEE_EMPTY_NAME": """
        SELECT COUNT(*)
        FROM public.employees
        WHERE TRIM(first_name) = ''
           OR TRIM(last_name) = ''
    """,

    "DUPLICATE_PUNCH_GROUPS": """
        SELECT COUNT(*)
        FROM (
            SELECT employee_id, punched_at, device_id
            FROM public.attendance_punches
            GROUP BY employee_id, punched_at, device_id
            HAVING COUNT(*) > 1
        ) AS duplicates
    """,

    "OVERLAPPING_APPROVED_LEAVES": """
        SELECT COUNT(*)
        FROM public.employee_leaves AS a
        JOIN public.employee_leaves AS b
          ON a.employee_id = b.employee_id
         AND a.leave_date = b.leave_date
         AND a.id < b.id
        WHERE a.approval_status = 'APPROVED'
          AND b.approval_status = 'APPROVED'
          AND (
              a.leave_session = b.leave_session
              OR a.leave_session = 'FULL_DAY'
              OR b.leave_session = 'FULL_DAY'
          )
    """,

    "INVALID_LEAVE_SESSION": """
        SELECT COUNT(*)
        FROM public.employee_leaves
        WHERE leave_session NOT IN (
            'FULL_DAY', 'MORNING', 'AFTERNOON'
        )
    """,

    "INVALID_OFFICIAL_DUTY_DATE": """
        SELECT COUNT(*)
        FROM public.official_duties
        WHERE start_date > end_date
    """,

    "INVALID_ATTENDANCE_MINUTES": """
        SELECT COUNT(*)
        FROM public.attendance_daily_result
        WHERE late_minutes < 0
           OR early_leave_minutes < 0
    """,

    "INVALID_ATTENDANCE_TIME_ORDER": """
        SELECT COUNT(*)
        FROM public.attendance_daily_result
        WHERE first_in_at > last_out_at
    """,

    "INVALID_DEVICE_PORT": """
        SELECT COUNT(*)
        FROM public.devices
        WHERE port < 1 OR port > 65535
    """,
}


def check_data_integrity():
    passed = 0
    warnings = 0

    print("=" * 70)
    print("ATTENDANCE DATA INTEGRITY CHECK")
    print("=" * 70)

    # เปิด Connection สำหรับตรวจสอบแบบอ่านอย่างเดียว
    with engine.connect() as conn:

        conn.execute(text("SET TRANSACTION READ ONLY"))

        for name, query in CHECKS.items():

            count = conn.execute(
                text(query)
            ).scalar_one()

            if count == 0:
                status = "PASS"
                passed += 1
            else:
                status = "REVIEW"
                warnings += 1

            print(f"{name:<38} {count:>8}  {status}")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total Checks : {len(CHECKS)}")
    print(f"Passed       : {passed}")
    print(f"Review       : {warnings}")
    print("=" * 70)


if __name__ == "__main__":
    check_data_integrity()
