
from sqlalchemy import inspect, UniqueConstraint
from database.session import engine
from models.base import Base

# โหลด Models ทั้งหมด
import models


def normalize_type(column_type):
    """แปลงชนิดข้อมูลให้อยู่ในรูปแบบเดียวกัน"""
    return str(
        column_type.compile(dialect=engine.dialect)
    ).upper().strip()


def check_model_constraints():
    inspector = inspect(engine)

    passed = 0
    failed = 0

    print("=" * 70)
    print("DATABASE CONSTRAINTS CHECK")
    print("=" * 70)

    for table in Base.metadata.sorted_tables:
        errors = []
        name = table.name
        schema = table.schema or "public"

        print(f"\nTABLE: {name}")

        # 1. ตรวจสอบชนิดข้อมูลและ Nullable
        db_columns = {
            col["name"]: col
            for col in inspector.get_columns(
                name, schema=schema
            )
        }

        for col in table.columns:
            if col.name not in db_columns:
                errors.append(
                    f"Missing column: {col.name}"
                )
                continue

            actual = db_columns[col.name]

            model_type = normalize_type(col.type)
            db_type = normalize_type(actual["type"])

            if model_type != db_type:
                errors.append(
                    f"TYPE {col.name}: "
                    f"Model={model_type}, DB={db_type}"
                )

            if col.nullable != actual["nullable"]:
                errors.append(
                    f"NULLABLE {col.name}: "
                    f"Model={col.nullable}, "
                    f"DB={actual['nullable']}"
                )

        # 2. ตรวจสอบ Primary Key
        model_pk = tuple(
            col.name for col in table.primary_key.columns
        )

        db_pk = tuple(
            inspector.get_pk_constraint(
                name, schema=schema
            ).get("constrained_columns") or []
        )

        if model_pk != db_pk:
            errors.append(
                f"PRIMARY KEY: Model={model_pk}, DB={db_pk}"
            )

        # 3. ตรวจสอบ Foreign Key
        model_fks = {
            (
                tuple(e.parent.name for e in fk.elements),
                fk.referred_table.schema or schema,
                fk.referred_table.name,
                tuple(e.column.name for e in fk.elements),
            )
            for fk in table.foreign_key_constraints
        }

        db_fks = {
            (
                tuple(fk["constrained_columns"]),
                fk["referred_schema"] or schema,
                fk["referred_table"],
                tuple(fk["referred_columns"]),
            )
            for fk in inspector.get_foreign_keys(
                name, schema=schema
            )
        }

        for fk in sorted(model_fks - db_fks):
            errors.append(f"Missing FOREIGN KEY: {fk}")

        for fk in sorted(db_fks - model_fks):
            errors.append(f"Extra FOREIGN KEY: {fk}")

        # 4. ตรวจสอบ Unique Constraint และ Index
        db_unique = {
            tuple(item["column_names"])
            for item in inspector.get_unique_constraints(
                name, schema=schema
            )
        }

        db_indexes = {
            (
                tuple(idx["column_names"]),
                bool(idx["unique"]),
            )
            for idx in inspector.get_indexes(
                name, schema=schema
            )
            if all(idx["column_names"])
        }

        unique_columns = db_unique | {
            columns
            for columns, unique in db_indexes
            if unique
        }

        for constraint in table.constraints:
            if isinstance(constraint, UniqueConstraint):
                columns = tuple(
                    col.name for col in constraint.columns
                )

                if columns not in unique_columns:
                    errors.append(
                        f"Missing UNIQUE: {columns}"
                    )

        # ตรวจสอบ Index ที่ Model กำหนด
        for idx in table.indexes:
            signature = (
                tuple(col.name for col in idx.columns),
                bool(idx.unique),
            )

            if signature not in db_indexes:
                errors.append(
                    f"Missing INDEX: {idx.name} {signature}"
                )

        # 5. สรุปผลรายตาราง
        if errors:
            failed += 1
            for error in errors:
                print(f"  ERROR: {error}")

            print("  RESULT: FAIL")
        else:
            passed += 1
            print("  Data Types   : OK")
            print("  Nullable     : OK")
            print("  Primary Key  : OK")
            print("  Foreign Keys : OK")
            print("  Unique       : OK")
            print("  Indexes      : OK")
            print("  RESULT       : PASS")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total Tables : {passed + failed}")
    print(f"Passed       : {passed}")
    print(f"Failed       : {failed}")
    print("=" * 70)


if __name__ == "__main__":
    check_model_constraints()
