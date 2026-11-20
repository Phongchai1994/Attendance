
from sqlalchemy import inspect, text
from database.session import engine
from models.base import Base

import models


def check_model_defaults():
    passed = 0
    failed = 0

    print("=" * 70)
    print("DATABASE DEFAULTS CHECK")
    print("=" * 70)

    with engine.connect() as conn:
        conn.execute(text("SET TRANSACTION READ ONLY"))
        inspector = inspect(conn)

        for table in Base.metadata.sorted_tables:
            name = table.name
            schema = table.schema or "public"
            errors = []

            print(f"\nTABLE: {name}")

            columns = {
                col["name"]: col
                for col in inspector.get_columns(
                    name, schema=schema
                )
            }

            # 1. ตรวจสอบการสร้าง ID อัตโนมัติ
            id_column = columns.get("id", {})
            id_default = str(id_column.get("default") or "")

            has_auto_id = (
                "nextval(" in id_default.lower()
                or id_column.get("identity") is not None
            )

            if has_auto_id:
                print("  Auto Increment : OK")
            else:
                errors.append("ID: Auto Increment not found")

            # 2. ตรวจสอบ Server Default ที่ Model กำหนด
            for col in table.columns:
                if col.server_default is None:
                    continue

                expected = str(
                    col.server_default.arg
                ).lower().replace(" ", "")

                actual = str(
                    columns[col.name].get("default") or ""
                ).lower().replace(" ", "")

                if expected == actual:
                    print(f"  Default {col.name}: OK")
                else:
                    errors.append(
                        f"DEFAULT {col.name}: "
                        f"Model={expected}, DB={actual}"
                    )

            # 3. ตรวจสอบพฤติกรรม Foreign Key
            db_fks = {
                tuple(fk["constrained_columns"]): fk
                for fk in inspector.get_foreign_keys(
                    name, schema=schema
                )
            }

            for fk in table.foreign_key_constraints:
                key = tuple(
                    e.parent.name for e in fk.elements
                )

                actual_fk = db_fks.get(key)

                if actual_fk is None:
                    errors.append(f"Missing FK: {key}")
                    continue

                options = actual_fk.get("options") or {}

                for action in ("ondelete", "onupdate"):
                    expected = (
                        getattr(fk, action) or "NO ACTION"
                    ).upper()

                    actual = (
                        options.get(action) or "NO ACTION"
                    ).upper()

                    if expected != actual:
                        errors.append(
                            f"FK {key} {action}: "
                            f"Model={expected}, DB={actual}"
                        )

            # 4. แสดง Check Constraints ที่มีในฐานข้อมูล
            checks = inspector.get_check_constraints(
                name, schema=schema
            )

            print(f"  Check Constraints: {len(checks)}")

            for check in checks:
                print(f"    {check['name']}: {check['sqltext']}")

            # สรุปผล
            if errors:
                failed += 1

                for error in errors:
                    print(f"  ERROR: {error}")

                print("  RESULT: FAIL")

            else:
                passed += 1
                print("  RESULT: PASS")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total Tables : {passed + failed}")
    print(f"Passed       : {passed}")
    print(f"Failed       : {failed}")
    print("=" * 70)


if __name__ == "__main__":
    check_model_defaults()
