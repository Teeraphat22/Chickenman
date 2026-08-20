"""MilkLab Sales Logger (S2).

Usage:
    python sales_logger.py --menu "นมหมีฮอกไกโด" --qty 2 --price 65

Reads GOOGLE_SHEETS_CREDENTIALS and TELEGRAM_BOT_TOKEN (or LINE_CHANNEL_TOKEN) from env.
Appends row [timestamp, menu, qty, price, total] to a Google Sheet,
then sends a notification via Telegram or LINE bot.

นักศึกษาต้องเติม TODO ใน 4 จุดด้านล่างใน Session 2 Lab 1.3
"""

import json
import gspread
import argparse
import os
import sys
from datetime import datetime
from google.oauth2.service_account import Credentials


def append_to_sheet(menu: str, qty: int, price: float) -> dict:
    """Append a row to Google Sheet."""
    if not menu.strip():
        raise RuntimeError("menu ต้องไม่ว่าง")

    if qty <= 0:
        raise RuntimeError("qty ต้องมากกว่า 0")

    if price < 0:
        raise RuntimeError("price ต้องไม่ติดลบ")

    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_CHICKENMAN")
    sheet_id = os.environ.get("GOOGLE_SHEET_ID_CHICKENMAN")

    if not creds_json:
        raise RuntimeError("ไม่พบ GOOGLE_SHEETS_CREDENTIALS_CHICKENMAN")

    if not sheet_id:
        raise RuntimeError("ไม่พบ GOOGLE_SHEET_ID_CHICKENMAN")


    credentials_info = json.loads(creds_json)

    scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

    creds = Credentials.from_service_account_info(
            credentials_info,
            scopes=scopes
        )

    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(sheet_id)

    worksheet = spreadsheet.worksheet("Sheet1")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total = qty * price

    worksheet.append_row([
            timestamp,
            menu,
            qty,
            price,
            total
        ])

    return {
            "timestamp": timestamp,
            "menu": menu,
            "qty": qty,
            "price": price,
            "total": total
        }

def send_notification(message: str) -> str:

    import requests

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        raise RuntimeError("ไม่พบ TELEGRAM_BOT_TOKEN หรือ TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": chat_id,
            "text": message
        }
    )

    if response.status_code != 200:
        raise RuntimeError(response.text)

    return "telegram"


def main() -> int:
    parser = argparse.ArgumentParser(description="MilkLab Sales Logger")
    parser.add_argument("--menu", required=True, help="ชื่อเมนู")
    parser.add_argument("--qty", type=int, required=True, help="จำนวนขวด")
    parser.add_argument("--price", type=float,
                        required=True, help="ราคาต่อขวด")
    args = parser.parse_args()

    try:
        # TODO 3: เรียก append_to_sheet แล้ว extract total
        row = append_to_sheet(args.menu, args.qty, args.price)
        total = row["total"]
    except Exception as exc:
        print(f"[ERROR] บันทึก Sheet ล้มเหลว: {exc}", file=sys.stderr)
        print("[HINT] ตรวจ GOOGLE_SHEETS_CREDENTIALS และ share Sheet กับ service account email", file=sys.stderr)
        return 1

    try:
        # TODO 4: เรียก send_notification ด้วย message ที่บอกยอดที่บันทึก
        provider = send_notification(
            f"บันทึก {args.menu} x{args.qty} = {total} บาท")
    except Exception as exc:
        print(
            f"[WARN] บันทึก Sheet สำเร็จแต่ส่งแจ้งเตือนล้มเหลว: {exc}", file=sys.stderr)
        return 0

    print(f"[OK] บันทึกและแจ้งเตือนผ่าน {provider} เรียบร้อย ยอด {total} บาท")
    return 0


if __name__ == "__main__":
    sys.exit(main())
