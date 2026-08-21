"""Chickenman RAG Chatbot (S3).

Run locally: streamlit run app.py
Deploy: push to GitHub then Actions deploys to HuggingFace Space
"""

import os
import streamlit as st
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from google import genai


@st.cache_resource
def load_index():
    """TODO 1+2+3: โหลด chickenman_kb.md, split เป็น chunk, encode ด้วย sentence-transformers,
    สร้าง faiss index. Cache เพราะโหลด model ครั้งแรกใช้เวลา 30 วินาที
    Returns: (model, index, chunks_list)
    """
    with open("chickenman_kb.md", "r", encoding="utf-8") as f:
        text = f.read()

    raw_sections = text.split("\n## ")
    chunks = []
    for i, sec in enumerate(raw_sections):
        sec = sec.strip()
        if not sec:
            continue
        if i > 0:
            sec = "## " + sec
        chunks.append(sec)

    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    embeddings = model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    return model, index, chunks


def retrieve_top_k(query: str, model, index, chunks: list[str], k: int = 3) -> list[str]:
    """TODO 4: encode query, search index, return top-k chunks"""
    q_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
    scores, idxs = index.search(q_emb, k)
    return [chunks[i] for i in idxs[0]]


def generate_answer(query: str, context_chunks: list[str]) -> str:
    """TODO 5: ส่ง query + context ไป Gemini, return answer"""
    try:
        api_key = st.secrets.get("GOOGLE_API_KEY")
    except Exception:
        api_key = None
    api_key = api_key or os.environ.get("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)

    context = "\n\n---\n\n".join(context_chunks)
    prompt = f"""คุณคือผู้ช่วยตอบคำถามลูกค้าร้าน Chickenman (ร้านปิ้งย่าง)

กฎเหล็กที่ต้องทำตามเป๊ะ:
1. ตอบจากข้อมูลด้านล่างนี้เท่านั้น ห้ามใช้ความรู้ทั่วไปหรือแต่งเพิ่มโดยเด็ดขาด
2. ถ้าคำถามถามถึงเมนู/ข้อมูลที่ไม่ปรากฏอยู่ในข้อมูลด้านล่างนี้ ให้ตอบว่า "ไม่พบข้อมูลนี้ในระบบค่ะ"
   ห้ามสร้างชื่อเมนู ส่วนผสม หรือรายละเอียดใดๆ ที่ไม่ได้ระบุไว้ในข้อมูลโดยเด็ดขาด
3. ก่อนตอบ ให้ตรวจสอบก่อนว่าสิ่งที่จะพูดถึงมีระบุไว้ในข้อมูลด้านล่างจริงหรือไม่

ข้อมูล:
{context}

คำถาม: {query}

คำตอบ:"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text


def main():
    st.set_page_config(page_title="Chickenman RAG", page_icon="🐔")
    st.title("Chickenman RAG Chatbot")
    st.caption("ถามอะไรเกี่ยวกับ Chickenman ได้ ตอบจาก chickenman_kb.md")

    try:
        model, index, chunks = load_index()
    except NotImplementedError as exc:
        st.error(f"TODO not implemented: {exc}")
        st.stop()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("ถามอะไรเกี่ยวกับ Chickenman"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("กำลังค้นข้อมูล..."):
                context = retrieve_top_k(prompt, model, index, chunks)
                answer = generate_answer(prompt, context)
            st.write(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()