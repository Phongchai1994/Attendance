import os
from pathlib import Path

import gspread
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BASE_DIR / ".env")


class GoogleLeaveService:
    def __init__(self):
        self.credentials_file = (
            BASE_DIR
            / "credentials"
            / "google_service_account.json"
        )

        self.sheet_url = os.getenv(
            "GOOGLE_LEAVE_SHEET_URL",
            "",
        ).strip()

        self.worksheet_name = os.getenv(
            "GOOGLE_LEAVE_WORKSHEET",
            "",
        ).strip()

    def _validate_config(self):
        if not self.credentials_file.exists():
            raise FileNotFoundError(
                "ไม่พบไฟล์ Service Account: "
                f"{self.credentials_file}"
            )

        if not self.sheet_url:
            raise ValueError(
                "ไม่พบ GOOGLE_LEAVE_SHEET_URL "
                "ในไฟล์ .env"
            )

        if not self.worksheet_name:
            raise ValueError(
                "ไม่ได้กำหนดชื่อ Worksheet"
            )

    def get_rows(self) -> list[dict]:
        self._validate_config()

        client = gspread.service_account(
            filename=str(self.credentials_file)
        )

        spreadsheet = client.open_by_url(
            self.sheet_url
        )

        worksheet = spreadsheet.worksheet(
            self.worksheet_name
        )

        records = worksheet.get_all_records(
            numericise_ignore=["all"]
        )

        return records