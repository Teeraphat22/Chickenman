# MilkLab° Solopreneur Starter (Course 69-1)

Template repo สำหรับวิชา 31-407-106-406 : AI for Solopreneurs

## เริ่มต้น

1. **Use this template** then Create a new repository (ตั้งชื่อ `milklab-<ชื่อ>`)
2. เปิด **Codespaces** จาก repo ใหม่
3. ตั้ง user-level Codespaces secret `GOOGLE_API_KEY` (ดู Quickstart)
4. รัน `python scripts/verify_setup.py` ใน terminal

## ไฟล์หลัก

| ไฟล์ | Session | คำอธิบาย |
|---|---|---|
| `caption_generator.py` | S1 | สร้างแคปชั่นให้โพสต์ MilkLab |
| `sales_logger.py` | S2 | บันทึกยอดขายลง Google Sheets |
| `agent_harness.py` | S2 | รับคำสั่งภาษาไทย เรียก tool |
| `app.py` | S3 | Streamlit RAG chatbot |

## เครื่องมือ

- Python 3.11
- Gemini API (google-genai)
- Streamlit (S3)
- gspread (S2)

## ดูคอร์ส

[course-691-stsw](https://github.com/<owner>/course-691-stsw) (link จะ update ตอนสร้าง public repo)
