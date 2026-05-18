"""
驗證分析腳本
比較系統回答的正確性，並產生分析報告。
"""

import json
import csv
from pathlib import Path
from datetime import datetime
import sys
sys.path.insert(0, str(Path(__file__).parent))
from rag_pipeline import load_index, retrieve, generate_answer

# ─── 測試問題集 ──────────────────────────────────────
# 依照報告要求設計，涵蓋：語意歧義、多層條件、除外責任
TEST_QUESTIONS = [
    {
        "id": "Q01",
        "category": "班機延誤",
        "question": "出發班機延誤幾小時才符合理賠條件？",
        "note": "測試：語意歧義（出發 vs 回程）"
    },
    {
        "id": "Q02",
        "category": "班機延誤",
        "question": "回程班機延誤的理賠條件和出發班機延誤一樣嗎？",
        "note": "測試：語意歧義辨別能力"
    },
    {
        "id": "Q03",
        "category": "醫療理賠",
        "question": "在日本住院超過 3 天，理賠金額是否會加成？",
        "note": "測試：多層條件（特定國家 + 住院天數）"
    },
    {
        "id": "Q04",
        "category": "醫療理賠",
        "question": "旅遊期間突發疾病的門診費用可以理賠嗎？",
        "note": "測試：基本醫療理賠範圍"
    },
    {
        "id": "Q05",
        "category": "除外責任",
        "question": "哪些情況下保險公司不予理賠？",
        "note": "測試：除外責任清單擷取能力"
    },
    {
        "id": "Q06",
        "category": "除外責任",
        "question": "從事極限運動（如滑雪、跳傘）受傷可以理賠嗎？",
        "note": "測試：特殊活動的除外責任"
    },
    {
        "id": "Q07",
        "category": "行李",
        "question": "行李箱被航空公司損壞，可以理賠多少？",
        "note": "測試：財物損失上限"
    },
    {
        "id": "Q08",
        "category": "行李",
        "question": "行李延誤到達目的地，可以申請理賠嗎？",
        "note": "測試：行李延誤 vs 行李遺失的區別"
    },
    {
        "id": "Q09",
        "category": "身故理賠",
        "question": "在旅途中因意外身故，受益人可以領多少保險金？",
        "note": "測試：主約身故理賠金額"
    },
    {
        "id": "Q10",
        "category": "理賠程序",
        "question": "發生事故後，需要在幾天內通知保險公司？",
        "note": "測試：程序性規定的擷取"
    },
]


def run_evaluation():
    """執行所有測試問題，記錄回答與檢索結果。"""
    print("=" * 60)
    print("🧪 開始驗證分析")
    print("=" * 60)

    index, metadata = load_index()
    results = []

    for q in TEST_QUESTIONS:
        print(f"\n[{q['id']}] {q['question']}")
        print(f"     分類：{q['category']} | {q['note']}")

        chunks = retrieve(q["question"], index, metadata)
        answer = generate_answer(q["question"], chunks)

        result = {
            "id":          q["id"],
            "category":    q["category"],
            "question":    q["question"],
            "note":        q["note"],
            "answer":      answer,
            "sources_used": [
                {"source": c["source"], "chunk_id": c["chunk_id"], "score": round(c["score"], 4)}
                for c in chunks
            ],
            "top_score":   round(chunks[0]["score"], 4) if chunks else 0,
            "timestamp":   datetime.now().isoformat(),
        }
        results.append(result)
        print(f"     ✅ 回答長度：{len(answer)} 字 | 最高相似度：{result['top_score']}")

    # 存成 JSON
    out_path = Path("data/evaluation_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 存成 CSV（方便對照 NotebookLM）
    csv_path = Path("data/evaluation_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "category", "question", "note",
            "answer", "top_score", "timestamp"
        ])
        writer.writeheader()
        for r in results:
            writer.writerow({k: r[k] for k in writer.fieldnames})

    print(f"\n\n📊 結果已儲存：")
    print(f"   {out_path}")
    print(f"   {csv_path}")
    print(f"\n下一步：將 CSV 的問題輸入 NotebookLM，比對回答差異。")

    return results


if __name__ == "__main__":
    run_evaluation()
