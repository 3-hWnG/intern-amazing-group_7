#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ragas_runner.py — Nối hệ thống vào RAGAS (Paper 31).

Gom đúng 4 cột RAGAS cần, từ golden set + output thật của hệ thống:
    question      ← câu hỏi golden
    answer        ← câu trả lời hệ thống (qua answer_adapter / /chat)
    contexts      ← ngữ cảnh hệ thống LẤY VỀ (từ trace/plan)
    ground_truth  ← đáp án chuẩn trong golden

Chạy:
    # bước 1: dựng dataset 4 cột (gọi hệ thống):
    python ragas_runner.py --golden cases_golden_dev.jsonl --build ragas_dataset.json
    # bước 2: chấm bằng RAGAS (cần ragas + 1 LLM giám khảo):
    python ragas_runner.py --score ragas_dataset.json

QUAN TRỌNG (xem tài liệu PHẦN 5.3):
  - RAGAS mặc định gọi OpenAI. Nhóm chạy on-prem (bảo mật dữ liệu dân, Paper 05)
    => trỏ giám khảo sang LLM local (Qwen qua Ollama). Xem hàm make_local_judge().
  - RAGAS là LLM-as-judge => KHÔNG thay kiểm số cứng. Lỗi bịa SỐ TIỀN vẫn phải
    kiểm bằng luật (forbidden_facts + verifier). Báo cả hai loại số.
"""
import argparse, json, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_PROC_TEXT_CACHE = None

def _proc_text_index():
    """proc_id -> 1 đoạn văn bản MÔ TẢ THẬT (tên + lệ phí + thời hạn + checklist rút gọn),
    dùng làm `contexts` cho RAGAS. KHÔNG dùng bare proc_id ("1.001714") làm context -- RAGAS
    Faithfulness so câu trả lời (câu chữ) với contexts (câu chữ); nếu contexts chỉ là mã số,
    giám khảo LLM không thấy câu trả lời khớp gì cả -> chấm sai thành "bịa", dù bot không bịa.
    (Lỗi này tự phát hiện khi chạy --score thật lần đầu: faithfulness tụt xuống 0,08 giả tạo.)"""
    global _PROC_TEXT_CACHE
    if _PROC_TEXT_CACHE is not None:
        return _PROC_TEXT_CACHE
    idx = {}
    snap = HERE.parent.parent / "data" / "snapshot" / "procedures.jsonl"
    try:
        for line in open(snap, encoding="utf-8"):
            p = json.loads(line)
            fees = p.get("fees") or []
            fee_txt = "; ".join(f"{f.get('amount_value', 0)} {f.get('amount_text', '')}".strip() for f in fees) or "(không rõ)"
            ck = p.get("checklist") or []
            ck_txt = "; ".join(str(c.get("name") or c) for c in ck[:6]) if ck else "(không rõ)"
            idx[p["proc_id"]] = (
                f"{p.get('name', '')}. Lệ phí: {fee_txt}. Thời hạn giải quyết: {p.get('processing_time_text', '(không rõ)')}. "
                f"Hồ sơ cần: {ck_txt}. Cơ quan: {p.get('agency_levels', '')}."
            )
    except Exception as e:
        print(f"  [cảnh báo] không đọc được procedures.jsonl để dựng context thật ({e})", file=sys.stderr)
    _PROC_TEXT_CACHE = idx
    return idx

# ---------- bước 1: gom 4 cột từ hệ thống ----------
def call_system(question):
    """Trả (answer, contexts[list[str]], behavior). Thử answer_adapter của repo; lỗi thì None."""
    try:
        # answer_adapter nằm ở eval/ (một cấp trên eval/golden/) -> thêm vào sys.path trước khi import
        EVAL_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if EVAL_PARENT not in sys.path:
            sys.path.insert(0, EVAL_PARENT)
        import answer_adapter  # type: ignore
        res = answer_adapter.adapter([{"role": "user", "text": question}])
        # answer_adapter.adapter() trả "answer_text" (KHÔNG phải "answer"/"text") -- xem eval/answer_adapter.py::adapter
        answer = res.get("answer_text") or ""
        # ngữ cảnh: candidates (proc_id) nằm trong từng task của res["tasks"] -> map sang văn bản thật
        pidx = _proc_text_index()
        ctx = []
        for t in (res.get("tasks") or []):
            for c in (t.get("candidates") or []):
                pid = c.get("proc_id") if isinstance(c, dict) else str(c)
                ctx.append(pidx.get(pid, pid))  # nếu không tra được text thì fallback về chính proc_id
        return answer, ctx, res.get("behavior")
    except Exception as e:
        print(f"  [cảnh báo] không gọi được answer_adapter ({e}); để trống answer/contexts.", file=sys.stderr)
        return "", [], None

def build(golden_path, out_path):
    rows = [json.loads(l) for l in open(golden_path, encoding="utf-8")]
    # RAGAS Faithfulness/Relevance chỉ có nghĩa với ca behavior=answer (golden kỳ vọng VÀ hệ thống thật cũng trả answer)
    rows = [r for r in rows if r.get("expected_behavior") == "answer"]
    data = {"question": [], "answer": [], "contexts": [], "ground_truth": [],
            "id": [], "domain": [], "archetype": [], "forbidden_facts": []}
    skipped_behavior = []  # golden kỳ vọng "answer" nhưng hệ thống thật trả khác -> KHÔNG đưa vào RAGAS
    for r in rows:
        ans, ctx, beh = call_system(r["question"])
        if beh is not None and beh != "answer":
            # Hệ thống từ chối/hỏi lại dù golden kỳ vọng trả lời -> đây là lỗi HÀNH VI (tầng C), không
            # phải lỗi SINH (tầng B). Đưa câu "chưa hỗ trợ được..." vào RAGAS sẽ bị giám khảo chấm sai
            # thành "lạc đề" (answer_relevancy~0), lẫn 2 loại lỗi khác nhau vào 1 số -- tách riêng ra.
            skipped_behavior.append({"id": r["id"], "question": r["question"], "actual_behavior": beh})
            continue
        if not ctx:
            ctx = r.get("golden_contexts") or [""]
        data["question"].append(r["question"])
        data["answer"].append(ans)
        data["contexts"].append(ctx)
        data["ground_truth"].append(r.get("ground_truth", ""))
        data["id"].append(r["id"])
        data["domain"].append(r.get("domain", ""))
        data["archetype"].append(r.get("archetype"))
        data["forbidden_facts"].append(r.get("forbidden_facts", []))
    json.dump(data, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Đã gom {len(data['question'])} ca (golden kỳ vọng answer VÀ hệ thống thật cũng trả answer) -> {out_path}")
    if skipped_behavior:
        print(f"[Tách riêng, KHÔNG đưa vào RAGAS] {len(skipped_behavior)} ca golden kỳ vọng answer nhưng hệ "
              f"thống thật trả hành vi khác (xem cột 'actual_behavior' trong file *_behavior_mismatch.json) "
              f"-- đây là lỗi Behavioral Accuracy (tầng C), chấm riêng, không gộp vào Faithfulness/Relevancy.")
        mism_path = str(Path(out_path).with_name(Path(out_path).stem + "_behavior_mismatch.json"))
        json.dump(skipped_behavior, open(mism_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"  đã lưu: {mism_path}")

    # kiểm BỊA SỐ bằng luật (độc lập RAGAS, chắc chắn hơn):
    bia = [data["id"][i] for i in range(len(data["question"]))
           if any(f and f in (data["answer"][i] or "") for f in data["forbidden_facts"][i])]
    print(f"[Kiểm luật] Bịa số (chứa forbidden_facts): {len(bia)}/{len(data['question'])} "
          f"{'-> ' + ', '.join(bia[:8]) if bia else '(sạch)'}")

# ---------- bước 2: chấm bằng RAGAS ----------
def make_local_judge():
    """Cấu hình giám khảo LLM chạy local (Ollama). Chỉnh model theo máy."""
    try:
        from langchain_community.chat_models import ChatOllama
        from langchain_community.embeddings import OllamaEmbeddings
        llm = ChatOllama(model="qwen2.5:7b", temperature=0)
        emb = OllamaEmbeddings(model="bge-m3")  # khớp embedding Friendly Engine
        return llm, emb
    except Exception as e:
        print(f"  [cảnh báo] chưa cấu hình được LLM local ({e}); RAGAS sẽ thử giám khảo mặc định.", file=sys.stderr)
        return None, None

def score(dataset_path, limit=None, workers=2, timeout=180):
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
    except Exception as e:
        sys.exit(f"Chưa cài RAGAS: pip install ragas datasets langchain-community  ({e})")
    raw = json.load(open(dataset_path, encoding="utf-8"))
    if limit is not None and limit > 0:
        raw = {k: v[:limit] for k, v in raw.items()}
        print(f"Đang chấm RAGAS trên tập mẫu {limit} ca đầu tiên...")
    else:
        print(f"Đang chấm RAGAS trên toàn bộ {len(raw['question'])} ca...")
    ds = Dataset.from_dict({k: raw[k] for k in ["question", "answer", "contexts", "ground_truth"]})
    llm, emb = make_local_judge()
    kw = {}
    if llm is not None:
        kw = {"llm": llm, "embeddings": emb}
    # QUAN TRỌNG (phát hiện 2026-10-13, chạy thật lần đầu với mặc định max_workers=16): Ollama local
    # xử lý TUẦN TỰ trên 1 GPU, không song song được 16 luồng như RAGAS mặc định giả định -> hàng loạt
    # job timeout -> metric trả None cho phần lớn ca (vd context_precision chỉ đo được 1/20 ca, coi
    # mean trên 1 ca là "đạt 100%" là SAI, không phải hệ thống tốt mà là dữ liệu gần như không đo được).
    # Hạ max_workers xuống thấp (mặc định 2) + tăng timeout mỗi job (mặc định 180s) để số đo đầy đủ hơn.
    try:
        from ragas.run_config import RunConfig
        kw["run_config"] = RunConfig(max_workers=workers, timeout=timeout)
        print(f"(RunConfig: max_workers={workers}, timeout={timeout}s -- giảm song song để khớp Ollama chạy tuần tự trên 1 GPU)")
    except Exception as e:
        print(f"  [cảnh báo] không cấu hình được RunConfig ({e}); dùng mặc định của ragas (dễ timeout với Ollama local).", file=sys.stderr)
    res = evaluate(ds, metrics=[faithfulness, answer_relevancy, context_precision, context_recall], **kw)
    print("\n=== RAGAS (toàn bộ) ===")
    print(res)
    # cắt lát theo domain để biết lĩnh vực nào yếu
    try:
        df = res.to_pandas()
        df["domain"] = raw["domain"]
        if "id" in raw:
            df["id"] = raw["id"]
        out_score_path = Path(dataset_path).parent / f"{Path(dataset_path).stem}_score{f'_limit{limit}' if limit else ''}.json"
        df.to_json(out_score_path, orient="records", force_ascii=False, indent=2)
        print(f"Đã lưu chi tiết điểm RAGAS -> {out_score_path}")
        # LUÔN báo kèm n đo được / tổng ca cho từng chỉ số -- một mean tính trên 1-2 ca "null hết"
        # trông y hệt mean tính trên cả bộ, phải tự in ra mới biết số có đáng tin hay không.
        print("\n=== Số ca thật sự đo được cho mỗi chỉ số (RAGAS trả None khi job timeout/lỗi) ===")
        for col in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
            if col in df.columns:
                n_ok = df[col].notna().sum()
                print(f"  {col:20s} n_đo_được = {n_ok}/{len(df)}" + ("  <-- QUÁ ÍT, đừng trích số này vào báo cáo" if n_ok < len(df) * 0.8 else ""))
        print("\n=== Theo domain (faithfulness / answer_relevancy / context_recall) ===")
        cols = [c for c in ["faithfulness", "answer_relevancy", "context_recall"] if c in df.columns]
        print(df.groupby("domain")[cols].mean().round(3).to_string())
    except Exception as e:
        print(f"(bỏ qua cắt lát domain: {e})")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden")
    ap.add_argument("--build")
    ap.add_argument("--score")
    ap.add_argument("--limit", type=int, default=None, help="Giới hạn số ca chấm (vd: --limit 20)")
    ap.add_argument("--workers", type=int, default=2, help="Số luồng song song gọi LLM giám khảo (Ollama 1 GPU chạy tuần tự -> để thấp, mặc định 2)")
    ap.add_argument("--timeout", type=int, default=180, help="Timeout (giây) mỗi job chấm (mặc định 180, tăng nếu vẫn thấy None nhiều)")
    a = ap.parse_args()
    if a.build:
        if not a.golden:
            sys.exit("--build cần --golden <file.jsonl>")
        build(a.golden, a.build)
    elif a.score:
        score(a.score, limit=a.limit, workers=a.workers, timeout=a.timeout)
    else:
        ap.print_help()
