"""Mục 3.3 của kế hoạch: bộ test lớn dùng chung, sinh từ KHUÔN câu hỏi theo chủ đề áp lên bản ghi của một dataset.
Chạy: python run_server.py eval/build_template_set.py [--n 40] [--seed 13]   -> eval/golden/template_thu-tuc.jsonl (cùng định dạng golden)
Chấm: PYTHONIOENCODING=utf-8 S3_USE_LLM=0 python run_server.py eval/run_golden.py template_thu-tuc --by type

Mở rộng sang dataset khác: viết một hàm `records_xxx()` trả list {id, title, domain, has:{field: bool}} rồi dùng lại TOPICS.
Hiện chỉ có bộ nối cho dataset thủ tục (DB System 3). Dataset người dùng tải lên ở System 4 chưa nối: chưa có đáp án chuẩn kiểm được.

Giới hạn (ghi vào báo cáo): câu dùng nguyên tên thủ tục nên DỄ hơn câu người dân gõ thật; đây là bộ kiểm hồi quy và so sánh
giữa các chủ đề, không phải số chính thức. Chọn bản ghi cấp xã, không gắn tỉnh, không ngành dọc (thuế, hải quan bị từ chối theo thiết kế), có tên duy nhất và là họ một dạng (không gây hỏi lại).
Không sinh chủ đề "áp dụng/điều kiện" vì chưa có đáp án chuẩn tự động. Chủ đề "liệt kê" chấm qua `orchestrator._list_request` (adapter bỏ qua orchestrator): có trả danh sách không, và bao nhiêu mục đúng lĩnh vực (hệ thống chưa có truy vấn SQL, chỉ liệt kê các thủ tục gần câu hỏi nhất).
"""
import argparse, collections, json, random, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from data import api  # noqa: E402
sys.path.insert(0, str(HERE.parent / "server"))
from policy.policy import _vertical  # noqa: E402  (cùng quy tắc "ngành dọc" với hệ thống thật)

# type -> (trường chuẩn của bộ chấm, trường chunk cần có dữ liệu, các khuôn câu). {n} = tên thủ tục
TOPICS = {
    "explain":    (["explanation"], ["explanation"], ["{n} là gì?", "Giải thích giúp mình thủ tục {n}."]),
    "components": (["components"], ["components"], ["{n} cần giấy tờ gì?", "Hồ sơ {n} gồm những gì?"]),
    "fees":       (["fees"], ["fees"], ["{n} mất bao nhiêu tiền?", "Lệ phí {n} là bao nhiêu?"]),
    "time":       (["processing_time"], ["processing_time"], ["{n} bao lâu thì có kết quả?", "Thời hạn giải quyết {n} là bao lâu?"]),
    "address":    (["address"], ["address"], ["{n} nộp hồ sơ ở đâu?", "Nơi nộp hồ sơ {n}?"]),
    "online":     (["online"], ["online"], ["{n} nộp trực tuyến được không?", "Có làm {n} qua mạng được không?"]),
    "steps":      (["steps"], ["steps"], ["{n} gồm những bước nào?", "Trình tự thực hiện {n}?"]),
    "legal":      (["meta"], ["legal_basis"], ["Căn cứ pháp lý của {n} là gì?", "{n} dựa trên văn bản nào?"]),
    "multi_field": (["components", "processing_time"], ["components", "processing_time"],
                    ["{n} cần giấy tờ gì và bao lâu có kết quả?", "Cho mình hỏi hồ sơ {n} gồm gì và thời hạn giải quyết?"]),
}


def candidates(conn):
    """Bản ghi họ một dạng, tên duy nhất, đủ ngắn; kèm tập trường có dữ liệu thật."""
    rows = conn.execute("""select p.proc_id, p.name, p.domain from procedures p join families f on f.proc_id = p.proc_id
                           where f.n_members = 1 and length(p.name) <= 120 and p.province is null and p.agency_levels like '%Xã/Phường%'
                             and (select count(*) from procedures q where q.name = p.name) = 1""").fetchall()
    out = []
    for r in rows:
        if _vertical(r[2]):          # thuế, hải quan...: ngoài phạm vi theo thiết kế, đáp án đúng là từ chối
            continue
        has = {x[0] for x in conn.execute("select field from field_chunks where proc_id=? and status='present'", (r[0],))}
        out.append(dict(id=r[0], title=r[1], domain=r[2], has=has))
    return out


def case(cid, typ, q, tasks, beh="answer"):
    return dict(id=cid, domain="thu-tuc", type=typ, turns=[{"role": "user", "text": q}], question=q, source="template", status="synthetic",
                expected=dict(behavior=beh, tasks=tasks))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--seed", type=int, default=13)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    recs = candidates(api.connect())
    out = []
    for typ, (fields, need, tmpls) in TOPICS.items():
        pool = [r for r in recs if all(x in r["has"] for x in need)]
        for i, r in enumerate(rng.sample(pool, min(a.n, len(pool)))):
            q = tmpls[i % len(tmpls)].format(n=r["title"].rstrip(".?"))
            out.append(case(f"tpl-{typ}-{i+1:02d}", typ, q, [dict(proc_ids=[r["id"]], fields=fields)]))
    by = collections.defaultdict(list)       # so sánh: hai thủ tục cùng lĩnh vực
    for r in recs:
        by[r["domain"]].append(r)
    pairs = [rng.sample(v, 2) for v in by.values() if len(v) >= 2]
    rng.shuffle(pairs)
    CMP = [("compare-so-sanh", "So sánh {x} và {y}."), ("compare-khac-gi", "{x} khác gì so với {y}?")]
    for i, (x, y) in enumerate(pairs[:a.n]):
        typ, tm = CMP[i % 2]
        out.append(case(f"tpl-compare-{i+1:02d}", typ, tm.format(x=x["title"].rstrip(".?"), y=y["title"].rstrip(".?")),
                        [dict(proc_ids=[x["id"]], fields=[]), dict(proc_ids=[y["id"]], fields=[])]))
    doms = [d for d, v in by.items() if len(v) >= 3]
    for i, d in enumerate(rng.sample(doms, min(a.n, len(doms)))):
        c = case(f"tpl-list-{i+1:02d}", "list", f"Liệt kê các thủ tục thuộc lĩnh vực {d}.", [], "answer")
        c["expected"]["list_domain"] = d
        out.append(c)
    p = HERE / "golden" / "template_thu-tuc.jsonl"
    p.parent.mkdir(exist_ok=True)
    with p.open("w", encoding="utf-8", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(out)} ca:", dict(collections.Counter(r["type"] for r in out)), "-> eval/golden/template_thu-tuc.jsonl")


if __name__ == "__main__":
    main()
