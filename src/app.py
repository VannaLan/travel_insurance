"""
AI 旅平險專員 ─ Streamlit 聊天介面
執行：streamlit run src/app.py
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rag_pipeline import load_index, retrieve, generate_answer, INDEX_PATH

# ─── 頁面設定 ────────────────────────────────────────
st.set_page_config(
    page_title="AI 旅平險專員",
    page_icon="✈️",
    layout="centered",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; }
    .source-badge {
        background: #e8f4fd; border-radius: 6px;
        padding: 4px 10px; font-size: 0.75rem; color: #1a73e8;
        display: inline-block; margin: 2px;
    }
    .score-bar { color: #888; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# ─── 標題 ────────────────────────────────────────────
st.title("✈️ AI 旅平險專員")
st.caption("根據各大保險公司條款，精確回答您的旅平險問題")

# ─── 索引狀態檢查 ─────────────────────────────────────
if not INDEX_PATH.exists():
    st.error("⚠️ 尚未建立索引！請先執行：`python src/rag_pipeline.py build`")
    st.stop()

# ─── 載入索引（快取）────────────────────────────────
@st.cache_resource
def get_index():
    return load_index()

index, metadata = get_index()

# 統計資訊
sources = list(set(m["source"] for m in metadata))
st.info(f"📚 已載入 **{len(sources)}** 份保單條款 | 共 **{len(metadata)}** 個段落")
st.caption("保單來源：" + "、".join(sources))

st.divider()

# ─── 範例問題 ─────────────────────────────────────────
st.markdown("**💡 範例問題（點擊即可提問）**")
examples = [
    "出發班機延誤幾小時才可以理賠？",
    "在日本住院 5 天可以理賠多少？",
    "什麼情況屬於除外責任，不予理賠？",
    "行李遺失的理賠上限是多少？",
    "旅遊不便險和旅平險有什麼差異？",
]
cols = st.columns(2)
for i, ex in enumerate(examples):
    if cols[i % 2].button(ex, use_container_width=True):
        st.session_state["pending_query"] = ex

# ─── 對話記錄 ─────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "sources" in msg:
            with st.expander("📎 參考條款來源", expanded=False):
                for s in msg["sources"]:
                    st.markdown(
                        f'<span class="source-badge">📄 {s["source"]}</span>'
                        f'<span class="score-bar"> 相似度: {s["score"]:.3f}</span>',
                        unsafe_allow_html=True
                    )
                    st.caption(s["text"][:200] + "...")

# ─── 輸入框 ──────────────────────────────────────────
query = st.chat_input("請輸入您的旅平險問題...")

# 處理範例問題點擊
if "pending_query" in st.session_state:
    query = st.session_state.pop("pending_query")

if query:
    # 顯示使用者訊息
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # 生成回答
    with st.chat_message("assistant"):
        with st.spinner("🔍 查詢保單條款中..."):
            chunks = retrieve(query, index, metadata)
            answer = generate_answer(query, chunks)

        st.markdown(answer)

        # 顯示來源
        with st.expander("📎 參考條款來源", expanded=False):
            for s in chunks:
                st.markdown(
                    f'<span class="source-badge">📄 {s["source"]}</span>'
                    f'<span class="score-bar"> 相似度: {s["score"]:.3f}</span>',
                    unsafe_allow_html=True
                )
                st.caption(s["text"][:200] + "...")

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": chunks,
    })
