"""Thí nghiệm: LLM có xác nhận được 'ứng viên đầu có đúng việc người dùng muốn không' (yes/no ngắn)?"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [ROOT, os.path.join(ROOT, "system3", "server")]
from system3.data import api
from system3.retrieval import Index, resolve
from core.llm import chat_json

SYS = ("Bạn kiểm tra kết quả tra cứu. Cho câu hỏi của người dùng và MỘT thủ tục tìm được. "
       "Trả lời match=true nếu thủ tục đúng là việc người dùng muốn làm/hỏi (cùng loại việc và cùng đối tượng). "
       "match=false nếu khác việc (ví dụ: cấp mới/làm mới khác với trình báo mất; đăng ký lại khác đăng ký lần đầu khi người dùng không nói 'lại'; "
       "chỉ trùng vài từ), hoặc người dùng hỏi chuyện không liên quan thủ tục hành chính.")
SCHEMA = {"type": "object", "properties": {"match": {"type": "boolean"}}, "required": ["match"]}

idx = Index(api.connect())
cases = [json.loads(l) for l in open(os.path.join(HERE, "cases.jsonl"), encoding="utf-8")]
tp = fp = tn = fn = 0
lat = []
for c in cases:
    r = resolve(idx, c["turns"])
    for s in r.segments:
        if not (s.proc_id and s.hits and s.uncertain):
            continue
        top = s.hits[0]
        exp = {p for t in c["expected"]["tasks"] for p in t["acceptable_proc_ids"]}
        truth = top.proc_id in exp and c["category"] != "out_of_scope"
        q = s.text
        t0 = time.perf_counter()
        out = chat_json(SYS, f"Câu hỏi: {q}\nThủ tục tìm được: {top.name[:160]}", schema=SCHEMA, think=False)
        lat.append(time.perf_counter() - t0)
        pred = bool(out.get("match"))
        if truth and pred: tp += 1
        elif truth and not pred: fn += 1; print("FN", q[:70], "|", top.name[:70])
        elif not truth and pred: fp += 1; print("FP", q[:70], "|", top.name[:70])
        else: tn += 1
print(dict(tp=tp, fp=fp, tn=tn, fn=fn, n=len(lat), avg_s=round(sum(lat) / max(1, len(lat)), 2)))
