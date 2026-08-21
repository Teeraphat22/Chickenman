"""Chickenman Agent Harness (S2)."""

import argparse
import json
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from google import genai
from google.genai import types

from sales_logger import append_to_sheet, send_notification
import gspread
from google.oauth2.service_account import Credentials


TOOL_SCHEMA = [
    {
        "name": "log_sale",
        "description": "บันทึกการขายลง Google Sheets และส่ง notification",
        "parameters": {
            "type": "object",
            "properties": {
                "menu": {"type": "string", "description": "ชื่อเมนู"},
                "qty": {"type": "integer", "description": "จำนวนที่ขาย (ไม้/ห่อ)"},
                "price": {"type": "number", "description": "ราคาต่อหน่วย"},
            },
            "required": ["menu", "qty", "price"],
        },
    },
    {
        "name": "query_sales",
        "description": "ดูยอดขายของวันที่ระบุ",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "วันที่ format YYYY-MM-DD"},
            },
            "required": ["date"],
        },
    },
    {
        "name": "send_alert",
        "description": "ส่ง message แจ้งเตือนผ่าน Bot",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
            },
            "required": ["message"],
        },
    },
    {
        "name": "query_inventory",
        "description": "เช็คจำนวนวัตถุดิบ/เมนูคงเหลือในสต็อก",
        "parameters": {
            "type": "object",
            "properties": {
                "item": {"type": "string", "description": "ชื่อเมนูหรือวัตถุดิบที่ต้องการเช็คสต็อก"},
            },
            "required": ["item"],
        },
    },
]

ALLOWED_TOOLS = ["log_sale", "query_sales", "send_alert", "query_inventory"]

TRACE_LOG_FILE = "agent_trace.log"

# สต็อกจำลอง (ไม้/ห่อ) - ในระบบจริงควรดึงจาก Google Sheet แยกต่างหาก
INVENTORY = {
    "ไก่ย่างไม้เล็ก": 40,
    "อกไก่ไม้ใหญ่": 20,
    "หมูนมสด": 35,
    "หมูชิ้น": 35,
    "ตับไก่": 25,
    "ตูดไก่": 25,
    "หนังไก่": 30,
    "แหนมหมู": 15,
    "ไส้อั่วเผ็ดน้อย": 20,
    "ไส้อั่วเผ็ดมาก": 20,
    "ส้มย่าง": 15,
    "แจ่วพลิกดับ": 10,
    "ข้าวเหนียวห่อเล็ก": 50,
    "ข้าวเหนียวห่อใหญ่": 30,
    "ปลาหมึก": 10,
    "ไส้กรอกหมูกระเทียม": 20,
    "ไส้กรอกหมูวุ้นเส้น": 20,
    "ไส้กรอกอีสานหมู": 15,
    "ปีกไก่": 25,
    "หัวใจไก่": 20,
    "ไส้หมู": 20,
    "หมูแดดเดียว": 15,
}


def parse_command(cmd: str, api_key: str | None = None) -> dict:
    """ส่ง cmd ไป Gemini พร้อม TOOL_SCHEMA ขอให้ตอบเป็น tool call จริง (function calling)"""
    api_key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("ไม่พบ GOOGLE_API_KEY")

    client = genai.Client(api_key=api_key)
    tool = types.Tool(function_declarations=TOOL_SCHEMA)
    config = types.GenerateContentConfig(tools=[tool])

    instruction = (
        "คุณคือระบบสกัดข้อมูล (extractor) เท่านั้น หน้าที่ของคุณคือดึงค่าตามที่ผู้ใช้พิมพ์ "
        "ให้ตรงกับคำสั่งเป๊ะที่สุด แล้วเรียก tool ที่เหมาะสมเสมอ "
        "ห้ามปฏิเสธการเรียก tool ไม่ว่าค่าที่ผู้ใช้ให้มาจะดูสมเหตุสมผลหรือไม่ก็ตาม "
        "(เช่น จำนวนติดลบ ราคาติดลบ ชื่อเมนูว่าง) "
        "ระบบอื่นจะเป็นผู้ตรวจสอบความถูกต้องเอง ไม่ใช่หน้าที่ของคุณ "
        "ห้ามแก้ไข ปรับปรุง หรือสะกดชื่อเมนูใหม่ ให้ใช้คำที่ผู้ใช้พิมพ์มาตรงตัว\n\n"
        f"คำสั่ง: {cmd}"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=instruction,
        config=config,
    )

    try:
        parts = response.candidates[0].content.parts
    except (IndexError, AttributeError) as e:
        raise RuntimeError(f"Gemini ไม่ตอบผลลัพธ์ที่ใช้ได้: {e}")

    for part in parts:
        if part.function_call:
            fn = part.function_call
            args = dict(fn.args)
            if "qty" in args and isinstance(args["qty"], float):
                args["qty"] = int(args["qty"])
            return {"tool": fn.name, "args": args}

    raise RuntimeError(f"Gemini ไม่ได้เรียก tool ใดๆ: {response.text}")


# ---------- Tool implementations ----------
def _tool_log_sale(args):
    menu = args.get("menu")
    qty = args.get("qty")
    price = args.get("price")

    if not menu or not str(menu).strip():
        raise ValueError("ชื่อเมนูห้ามว่าง")
    if not isinstance(qty, int) or qty <= 0:
        raise ValueError("qty ต้องเป็นจำนวนเต็มมากกว่า 0")
    if not isinstance(price, (int, float)) or price < 0:
        raise ValueError("price ห้ามติดลบ")

    row = append_to_sheet(menu, qty, price)
    msg = f"บันทึกขาย {row['menu']} จำนวน {row['qty']} ราคา {row['price']} รวม {row['total']} บาท"
    send_notification(msg)
    return msg


def _tool_query_sales(args):
    date = args.get("date")
    if not date or not str(date).strip():
        raise ValueError("date ห้ามว่าง")

    creds = Credentials.from_service_account_info(
        json.loads(os.environ["GOOGLE_SHEETS_CREDENTIALS_CHICKENMAN"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
    )
    gc = gspread.authorize(creds)
    sheet_id = os.environ["GOOGLE_SHEET_ID_CHICKENMAN"]
    worksheet = gc.open_by_key(sheet_id).worksheet("Sheet1")
    records = worksheet.get_all_records()

    matched = [r for r in records if str(r.get("timestamp", "")).startswith(date)]
    if not matched:
        return f"ไม่พบยอดขายวันที่ {date}"

    total = sum(float(r.get("total", 0)) for r in matched)
    return f"วันที่ {date} มี {len(matched)} รายการ รวม {total} บาท"


def _tool_send_alert(args):
    message = args.get("message")
    if not message or not str(message).strip():
        raise ValueError("message ห้ามว่าง")
    send_notification(message)
    return f"ส่งแจ้งเตือนแล้ว: {message}"


def _tool_query_inventory(args):
    item = args.get("item")
    if not item or not str(item).strip():
        raise ValueError("item ห้ามว่าง")

    stock = INVENTORY.get(item)
    if stock is None:
        return f"ไม่พบเมนู '{item}' ในระบบสต็อก"

    if stock <= 5:
        return f"{item} เหลือ {stock} ไม้/ห่อ (สต็อกใกล้หมด ควรเติมด่วน)"
    return f"{item} เหลือ {stock} ไม้/ห่อ"


TOOL_FUNCS = {
    "log_sale": _tool_log_sale,
    "query_sales": _tool_query_sales,
    "send_alert": _tool_send_alert,
    "query_inventory": _tool_query_inventory,
}


def dispatch_tool(tool_call: dict) -> str:
    """เรียก tool ตาม tool_call["tool"] ด้วย args จริง — whitelist + validate ก่อน execute"""
    name = tool_call.get("tool")
    args = tool_call.get("args", {})

    if name not in ALLOWED_TOOLS:
        raise ValueError(f"Tool ไม่ได้รับอนุญาต: {name}")

    func = TOOL_FUNCS[name]
    return func(args)


def log_trace(event_type: str, content) -> None:
    """บันทึก event ลง agent_trace.log"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not isinstance(content, str):
        content = json.dumps(content, ensure_ascii=False)
    line = f"{timestamp} | {event_type} | {content}\n"
    with open(TRACE_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--cmd", required=True, help="คำสั่งภาษาไทย")
    args = parser.parse_args()

    print(f"[USER] {args.cmd}")
    log_trace("user_input", args.cmd)

    try:
        tool_call = parse_command(args.cmd)
        print(f"[LLM]  tool={tool_call['tool']} args={tool_call['args']}")
        log_trace("llm_response", tool_call)

        result = dispatch_tool(tool_call)
        print(f"[TOOL] {tool_call['tool']} {result}")
        print(f"[USER] ← {result}")
        log_trace("tool_result", result)
        return 0

    except Exception as e:
        print(f"[TOOL-ERROR] {e}")
        print(f"[USER] ← ล้มเหลว: {e}")
        log_trace("tool_error", str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
