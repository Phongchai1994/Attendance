from database.connection import get_connection


def test_database():
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    current_database(),
                    current_user,
                    version();
                """
            )

            result = cursor.fetchone()

            print("เชื่อมต่อ PostgreSQL สำเร็จ")
            print(f'Database : {result[0]}')
            print(f'User     : {result[1]}')
            print(f'Version  : {result[2]}')

    finally:
        conn.close()


if __name__ == "__main__":
    test_database()