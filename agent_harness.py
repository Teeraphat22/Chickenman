"""MilkLab Agent Harness (S2).

Usage:
    python agent_harness.py --cmd "บันทึกขายนมหมี 2 ขวด ขวดละ 65"

รับคำสั่งภาษาไทย ส่งให้ Gemini พร้อม tool schema parse response เป็น tool call
เรียก tool จริง print trace log

นักศึกษาต้องเติม TODO ใน 3 จุด ใน Session 2 Lab 2.3
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv
from google import genai


TOOL_SCHEMA = [
    {
        "name": "log_sale",
        "description": "บันทึกการขายลง Google Sheets และส่ง notification",
        "parameters": {
            "type": "object",
            "properties": {
                "menu": {"type": "string", "description": "ชื่อเมนู"},
                "qty": {"type": "integer", "description": "จำนวนที่ขาย"},
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
]


def parse_command(cmd: str, api_key: str | None = None) -> dict:
    """TODO 1: ส่ง cmd ไป Gemini พร้อม TOOL_SCHEMA ขอให้ตอบเป็น JSON {tool, args}

    Returns dict {"tool": <name>, "args": <dict>}
    Raises RuntimeError ถ้า parse ไม่ได้
    """
    raise NotImplementedError("Implement in Session 2 Lab 2.3 (TODO 1)")


def dispatch_tool(tool_call: dict) -> str:
    """TODO 2: เรียก tool ตาม tool_call["tool"] ด้วย args จริง

    Returns: ข้อความสรุปผลที่ tool คืน
    """
    raise NotImplementedError("Implement in Session 2 Lab 2.3 (TODO 2)")


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--cmd", required=True, help="คำสั่งภาษาไทย")
    args = parser.parse_args()

    print(f"[USER] {args.cmd}")

    # TODO 3: เรียก parse_command then dispatch_tool then print trace ตาม format ใน session-2.md
    tool_call = parse_command(args.cmd)
    print(f"[LLM]  tool={tool_call['tool']} args={tool_call['args']}")

    result = dispatch_tool(tool_call)
    print(f"[TOOL] {tool_call['tool']} {result}")
    print(f"[USER] ← {result}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
