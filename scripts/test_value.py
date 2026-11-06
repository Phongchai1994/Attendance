from dotenv import load_dotenv
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BASE_DIR/'.env')


def read_val():
    sheet_url = os.getenv(
        "GOOGLE_LEAVE_SHEET_URL",
        "",
    ).strip()

    worksheet_name = os.getenv(
        "GOOGLE_LEAVE_WORKSHEET",
        "",
    ).strip()

    print(sheet_url)
    print(worksheet_name)
    print(BASE_DIR)
    print(load_dotenv)


if __name__ == '__main__':
    read_val()