# ✈️ AI 旅平險專員

> 生成式 AI 期末報告｜文件檢索系統（RAG）  
> 作者：朱政安（Zheng-An Zhu）

以 RAG（Retrieval-Augmented Generation）技術建立的旅行平安保險智慧查詢系統。使用者可以用自然語言提問，系統會從各大保險公司的正式條款中精確擷取相關內容，並生成有來源根據的回答。

---

## 📌 系統架構

```
PDF 條款
   ↓ pdfplumber 解析
原始文字
   ↓ 滑動視窗切塊（400字/chunk，80字 overlap）
Chunks
   ↓ OpenAI text-embedding-3-small 向量化
向量
   ↓ FAISS IndexFlatIP 建立索引
向量資料庫
   ↑ 使用者提問（同樣向量化後比對）
Top-K 相關 Chunks
   ↓ 組合 Prompt → GPT-4o-mini
有來源的精確回答
```

---

## 🚀 快速開始

### 1. 環境設定

```bash
git clone https://github.com/<your-username>/travel-insurance-rag
cd travel-insurance-rag

pip install -r requirements.txt

# 設定 OpenAI API Key
export OPENAI_API_KEY="sk-..."
```

### 2. 放入保單 PDF

```
data/raw/
  ├── 富邦旅平險條款.pdf
  ├── 國泰旅平險條款.pdf
  └── 新光旅平險條款.pdf
```

### 3. 建立索引

```bash
python src/rag_pipeline.py build
```

### 4. 啟動聊天介面

```bash
streamlit run src/app.py
```

### 5. 執行驗證分析

```bash
python src/evaluate.py
# 結果存在 data/evaluation_results.csv
```

---

## 📂 專案結構

```
travel-insurance-rag/
├── data/
│   ├── raw/              # 原始 PDF 條款（請自行下載）
│   ├── faiss.index       # 向量索引（build 後自動產生）
│   ├── metadata.json     # Chunk 元資料
│   └── evaluation_results.csv  # 驗證結果
├── src/
│   ├── rag_pipeline.py   # 核心 RAG 邏輯
│   ├── app.py            # Streamlit 聊天 UI
│   └── evaluate.py       # 驗證分析腳本
├── requirements.txt
└── README.md
```

---

## 🤖 AI 工具鏈紀錄

| 任務 | 使用工具 |
|------|----------|
| 程式碼撰寫與架構設計 | Claude Sonnet（claude.ai）|
| PDF 解析 | pdfplumber |
| 文字向量化（Embedding） | OpenAI text-embedding-3-small |
| 向量資料庫 | FAISS（faiss-cpu）|
| 回答生成 | OpenAI GPT-4o-mini |
| 聊天介面 | Streamlit |
| 輔助 IDE | VS Code |
| 系統環境 | Python 3.11, macOS / Ubuntu |

---

## 📊 評分重點：驗證分析方法

本系統設計 10 道測試問題（`src/evaluate.py`），涵蓋：

- **語意歧義測試**：出發班機延誤 vs 回程班機延誤
- **多層條件測試**：特定國家 + 住院天數 → 加成計算
- **除外責任測試**：極限運動、酒駕等不予理賠情境
- **程序性規定測試**：通知期限、申請文件

### 正確性驗證方式

1. 人工比對條款原文（Ground Truth）
2. 計算 Top-1 相似度分數（`score` 欄位）作為檢索品質指標
3. 與 NotebookLM 回答進行逐題比對（詳見報告附錄）

> ⚠️ 最終效能不重要，分析才重要。重點在於理解系統在哪類問題上表現好/差，以及原因為何。

---

## ⚠️ 注意事項

- 本系統僅供學術研究用途
- 實際投保決策請以各保險公司正式條款為準
- API 金鑰請勿上傳至 GitHub（使用 `.env` 或環境變數）
