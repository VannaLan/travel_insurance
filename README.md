# ✈️ AI 旅平險專員

> 生成式 AI 期末報告｜文件檢索系統（RAG）  
> 作者：謝佳蓉、邱淳湄

以 RAG（Retrieval-Augmented Generation）技術建立的旅行平安保險智慧查詢系統。使用者可以用自然語言提問，系統會從各大保險公司的正式條款中精確擷取相關內容，並生成有來源根據的回答。

---

## 📌 系統架構

```
PDF 條款
   ↓ pdfplumber 解析
原始文字
   ↓ 滑動視窗切塊（400字/chunk，80字 overlap）
Chunks
   ↓ sentence-transformers 本地向量化（免費）
向量
   ↓ FAISS IndexFlatIP 建立索引
向量資料庫
   ↑ 使用者提問（同樣向量化後比對）
Top-K 相關 Chunks
   ↓ 組合 Prompt → Groq llama-3.3-70b（免費）
有來源的精確回答
```

---

## 🚀 快速開始

### 1. Clone 專案

```bash
git clone https://github.com/VannaLan/travel_insurance
cd travel_insurance
```

### 2. 安裝套件

```bash
pip install -r requirements.txt
```

### 3. 取得 Groq API Key 並建立 `.env`

1. 前往 [https://console.groq.com](https://console.groq.com) 免費註冊
2. 左側選單 → **API Keys** → **Create API Key**
3. 複製 `gsk_...` 開頭的金鑰
4. 在專案根目錄建立 `.env` 檔案，填入以下內容：

```
GROQ_API_KEY=你的金鑰貼在這裡
```

> ⚠️ `.env` 已被 `.gitignore` 排除，不會上傳到 GitHub，請勿將金鑰直接寫進程式碼。

### 4. 放入保單 PDF

```
data/raw/
  ├── 富邦產物旅行平安保險_旅-20180703_.pdf
  ├── condition_tp_card.pdf
  ├── V5_(快易保)投保規定_投保人須知_聲明事項.pdf
  ├── overseas_travel_20260401.pdf
  ├── domestic_travel_20260401.pdf
  └── 新光產物全球海外緊急急難救助服務辦法(114年適用)2.pdf
```

> 富邦產險：前三份｜國泰世紀產險：中間兩份｜新光產險：最後一份

### 5. 建立索引

```bash
python src/rag_pipeline.py build
```

> 首次執行會自動下載約 500MB 的中文 Embedding 模型，請耐心等候。

### 6. 啟動聊天介面

```bash
streamlit run src/app.py
```

### 7. 執行驗證分析

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
| 文字向量化（Embedding） | sentence-transformers（本地，免費）|
| 向量資料庫 | FAISS（faiss-cpu）|
| 回答生成 | Groq llama-3.3-70b-versatile（免費）|
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
