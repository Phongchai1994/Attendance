
from sqlalchemy import inspect, select
from database.session import engine, SessionLocal
from models.base import Base

# โหลด Models ทั้งหมดเข้าสู่ Metadata
import models


def check_model_schema():
    inspector = inspect(engine)

    # ดึงรายชื่อตารางจากฐานข้อมูล
    db_tables = set(
        inspector.get_table_names(schema="public")
    )

    # ดึงรายชื่อตารางจาก SQLAlchemy Models
    model_tables = {
        table.name: table
        for table in Base.metadata.sorted_tables
    }

    passed = 0
    failed = 0

    print("=" * 70)
    print("DATABASE / SQLALCHEMY SCHEMA CHECK")
    print("=" * 70)

    for table_name, table in sorted(model_tables.items()):

        print(f"\nTABLE: {table_name}")

        if table_name not in db_tables:
            print("  ERROR: Table not found")
            failed += 1
            continue

        # เปรียบเทียบชื่อคอลัมน์
        db_columns = {
            col["name"]
            for col in inspector.get_columns(
                table_name,
                schema="public",
            )
        }

        model_columns = {
            col.name for col in table.columns
        }

        missing = sorted(model_columns - db_columns)
        extra = sorted(db_columns - model_columns)

        print(f"  Missing in DB : {missing}")
        print(f"  Extra in DB   : {extra}")

        db = SessionLocal()

        try:
            # ทดสอบอ่านข้อมูลผ่าน Model
            mapper = next(
                mapper
                for mapper in Base.registry.mappers
                if mapper.local_table is table
            )

            db.execute(
                select(mapper.class_).limit(1)
            ).first()

            print("  ORM SELECT    : OK")

            if not missing and not extra:
                print("  RESULT        : PASS")
                passed += 1
            else:
                print("  RESULT        : FAIL")
                failed += 1

        except Exception as e:
            db.rollback()
            print(f"  ORM ERROR     : {e}")
            failed += 1

        finally:
            db.close()

    extra_tables = sorted(
        db_tables - set(model_tables)
    )

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Database Tables : {len(db_tables)}")
    print(f"Model Tables    : {len(model_tables)}")
    print(f"Passed          : {passed}")
    print(f"Failed          : {failed}")
    print(f"Extra Tables    : {extra_tables}")
    print("=" * 70)


if __name__ == "__main__":
    check_model_schema()
