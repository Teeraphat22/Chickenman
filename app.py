"""MilkLab RAG Chatbot (S3).

Run locally: streamlit run app.py
Deploy: push to GitHub then Actions deploys to HuggingFace Space

นักศึกษาต้องเติม TODO 5 จุด ใน Session 3 Lab 2.2
"""

import os

import streamlit as st


@st.cache_resource
def load_index():
    """TODO 1+2+3: โหลด menu_kb.md, split เป็น chunk, encode ด้วย sentence-transformers,
    สร้าง faiss index. Cache เพราะโหลด model ครั้งแรกใช้เวลา 30 วินาที

    Returns: (model, index, chunks_list)
    """
    raise NotImplementedError("Implement in Session 3 Lab 2.2 (TODO 1-3)")


def retrieve_top_k(query: str, model, index, chunks: list[str], k: int = 3) -> list[str]:
    """TODO 4: encode query, search index, return top-k chunks"""
    raise NotImplementedError("Implement in Session 3 Lab 2.2 (TODO 4)")


def generate_answer(query: str, context_chunks: list[str]) -> str:
    """TODO 5: ส่ง query + context ไป Gemini, return answer

    Hint: build prompt that says "ตอบจากข้อมูลต่อไปนี้เท่านั้น ถ้าไม่มีใน context ให้บอกว่าไม่รู้"
    """
    raise NotImplementedError("Implement in Session 3 Lab 2.2 (TODO 5)")


def main():
    st.set_page_config(page_title="MilkLab° RAG", page_icon="🥛")
    st.title("MilkLab° RAG Chatbot")
    st.caption("ถามอะไรเกี่ยวกับ MilkLab ได้ ตอบจาก menu_kb.md")

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

    if prompt := st.chat_input("ถามอะไรเกี่ยวกับ MilkLab"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("กำลังค้นข้อมูล..."):
                context = retrieve_top_k(prompt, model, index, chunks)
                answer = generate_answer(prompt, context)
            st.write(answer)
            with st.expander("Source chunks"):
                for i, c in enumerate(context, 1):
                    st.markdown(f"**[{i}]** {c}")
        st.session_state.messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()
