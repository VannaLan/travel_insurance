"""
AI 旅平險專員 - RAG Pipeline
"""
import os, json
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path
from typing import List, Dict
import pdfplumber
import numpy as np

DATA_DIR   = Path("data/raw")
CHUNK_DIR  = Path("data/chunks")
INDEX_PATH = Path("data/faiss.index")
META_PATH  = Path("data/metadata.json")
CHUNK_SIZE    = 400
CHUNK_OVERLAP = 80
TOP_K         = 4
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

def parse_pdf(pdf_path):
    texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    rows = [" | ".join([cell or "" for cell in row]) for row in table]
                    texts.append("\n".join(rows))
            text = page.extract_text()
            if text:
                texts.append(text)
    return "\n\n".join(texts)

def load_all_pdfs():
    docs = []
    for pdf_file in DATA_DIR.glob("*.pdf"):
        print(f"  📄 解析: {pdf_file.name}")
        docs.append({"source": pdf_file.stem, "text": parse_pdf(pdf_file)})
    return docs

def chunk_text(text, source):
    chunks, start, idx = [], 0, 0
    while start < len(text):
        chunks.append({"source": source, "chunk_id": idx, "text": text[start:start+CHUNK_SIZE].strip()})
        start += CHUNK_SIZE - CHUNK_OVERLAP
        idx += 1
    return chunks

def build_chunks(docs):
    all_chunks = []
    for doc in docs:
        chunks = chunk_text(doc["text"], doc["source"])
        all_chunks.extend(chunks)
        print(f"  ✂️  {doc['source']}: {len(chunks)} chunks")
    return all_chunks

_embedder = None
def get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        print(f"  📦 載入模型（首次執行會下載約 500MB，請稍候...）")
        _embedder = SentenceTransformer(EMBED_MODEL)
        print("  ✅ 模型載入完成")
    return _embedder

def embed_texts(texts):
    return np.array(get_embedder().encode(texts, show_progress_bar=False, normalize_embeddings=True), dtype="float32")

def build_index(chunks):
    import faiss
    print("\n🔢 向量化中（本地執行，不需要 API）...")
    texts = [c["text"] for c in chunks]
    vectors_list = []
    for i in range(0, len(texts), 64):
        vectors_list.append(embed_texts(texts[i:i+64]))
        print(f"  ✅ {min(i+64, len(texts))}/{len(texts)} 完成")
    all_vectors = np.vstack(vectors_list)
    index = faiss.IndexFlatIP(all_vectors.shape[1])
    index.add(all_vectors)
    faiss.write_index(index, str(INDEX_PATH))
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"\n💾 索引已儲存：{INDEX_PATH}（共 {index.ntotal} 個向量）")

def load_index():
    import faiss
    index = faiss.read_index(str(INDEX_PATH))
    with open(META_PATH, encoding="utf-8") as f:
        metadata = json.load(f)
    return index, metadata

def retrieve(query, index, metadata, top_k=TOP_K):
    scores, indices = index.search(embed_texts([query]), top_k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        chunk = metadata[idx].copy()
        chunk["score"] = float(score)
        results.append(chunk)
    return results

SYSTEM_PROMPT = """你是一位專業的台灣旅遊平安保險專員 AI。
回答規則：
1. 只能根據【參考條款】中的內容回答，不可自行捏造。
2. 每個重要陳述後，必須標註來源，格式：【來源：XX保險_第N段】
3. 若條款中沒有相關資訊，直接說「根據現有條款，無法找到相關規定」。
4. 回答要清晰、分點，適合一般民眾理解。"""

def generate_answer(query, retrieved_chunks):
    from groq import Groq
    context = "\n\n---\n\n".join(
        f"【條款片段 {i+1}｜來源：{c['source']}｜段落 {c['chunk_id']}】\n{c['text']}"
        for i, c in enumerate(retrieved_chunks)
    )
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"【參考條款】\n{context}\n\n【用戶問題】\n{query}\n\n請根據以上條款內容回答問題，並標註來源。"},
        ],
        temperature=0.1,
    )
    return response.choices[0].message.content

def build_pipeline():
    print("=" * 50)
    print("🚀 開始建立 AI 旅平險專員索引（免費版）")
    print("=" * 50)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHUNK_DIR.mkdir(parents=True, exist_ok=True)
    print("\n📂 STEP 1: 解析 PDF...")
    docs = load_all_pdfs()
    if not docs:
        print("❌ 錯誤：data/raw/ 資料夾中沒有 PDF 檔案！")
        return
    print(f"\n✂️  STEP 2: 切塊（chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}）...")
    chunks = build_chunks(docs)
    print(f"   總計 {len(chunks)} 個 chunks")
    print("\n🔢 STEP 3: 向量化 & 建立 FAISS 索引...")
    build_index(chunks)
    print("\n✅ 索引建立完成！可以開始提問了。")

def ask(query):
    index, metadata = load_index()
    return generate_answer(query, retrieve(query, index, metadata))

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        build_pipeline()
