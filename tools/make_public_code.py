"""Dựng thư mục paper1_vjcs/Code: bản code công khai đi kèm bài 1 (System 3), theo constraints.md D3/D9.

Lấy tệp từ COMMIT (mặc định HEAD) của repo gốc bằng `git show`, không lấy từ working tree (tệp chưa commit không lọt vào).
Chỉ chép theo danh sách cho phép (INCLUDE_*). Biến đổi:
  - kết quả từng câu (*.json trong eval/hard/results/...): bỏ trường văn bản câu hỏi (`q`, `text`);
  - eval/real_v1/collect_real_v1.py: xoá danh sách 17 họ tên người thật (MANUAL_NAMES);
  - sinh labels/*.jsonl từ các bộ đã gán: chỉ mã câu, nguồn (dataset Hugging Face + số dòng), tầng, nhãn, mã thủ tục.
Không chép: văn bản câu hỏi, cache đầu ra model (chứa đầu câu hỏi), tệp Excel gán nhãn, dữ liệu thủ tục đã cào, system4/, docs/, research/.
Cuối cùng quét bản xuất: không còn câu hỏi nào (so 40 ký tự đầu của mọi câu), không còn tên trong MANUAL_NAMES, không có khoá.

    python tools/make_public_code.py [commit]
"""
import json
import os
import re
import shutil
import subprocess
import sys

REPO = r"D:/Claude/System 3/intern-amazing-group_7-merge_sys_3_4"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Code")
COMMIT = sys.argv[1] if len(sys.argv) > 1 else "HEAD"

INCLUDE_PREFIX = ("server/", "retrieval/", "data/", "web/", "knowledge/")
INCLUDE_FILES = {
    "run_server.py", "requirements.txt",
    "eval/answer_adapter.py", "eval/thermal.py", "eval/stamp.py", "eval/run_golden.py", "eval/run_tests.py", "eval/fixture_db.py",
    "eval/hard/README.md", "eval/hard/dev.py", "eval/hard/rag4b.py", "eval/hard/metrics.py", "eval/hard/paced.py", "eval/hard/sem_grid.py",
    "eval/hard/report.py", "eval/hard/final_runs.sh", "eval/hard/final_runs_v4.sh", "eval/hard/regress.sh", "eval/hard/dev595/README.md",
    "eval/real_v1/collect_real_v1.py", "eval/real_v1/real_v1_agree.py", "eval/real_v1/README.md", "eval/real_v1/LOCK.md",
    "eval/real_v2/collect_real_v2.py", "eval/real_v2/build_labeled.py", "eval/real_v2/README.md", "eval/real_v2/LOCK.md",
    "eval/real_v2/relabel/make_relabel.py", "eval/real_v2/relabel/read_relabel.py", "eval/real_v2/relabel/robustness.py",
    "eval/real_v2/relabel/README.md", "eval/real_v2/relabel/agreement.txt", "eval/real_v2/relabel/robustness.txt",
    "eval/real_v2/relabel/relabel_ids.json",
    "eval/real_v4/collect_real_v4.py", "eval/real_v4/make_label_sheet.py", "eval/real_v4/build_labeled.py", "eval/real_v4/README.md",
    "eval/real_v4/RUN_PLAN.md",
}
RESULT_DIRS = ("eval/hard/results/test/", "eval/hard/results/test_v4/", "eval/hard/results/dev/", "eval/hard/results/regress/")
RESULT_OK = (".json", ".txt", ".csv", ".md")
EXCLUDE = {"data/snapshot/procedures.jsonl", "data/snapshot/procedures_v3.jsonl", "data/snapshot/team_corpus.json", "server/COPY_NOTES.md"}
LABEL_SETS = {   # tên tệp nhãn -> (tệp đã gán có văn bản, tệp chưa gán có nguồn)
    "dev_real_v1": ("eval/real_v1/cases_real_v1_labeled.json", None),
    "test1_real_v2": ("eval/real_v2/cases_real_v2_labeled.json", None),
    "test2_real_v4": ("eval/real_v4/cases_real_v4_labeled.json", "eval/real_v4/cases_real_v4.json"),
}
TEXT_KEYS = ("q", "text", "question")


def git(*a) -> bytes:
    return subprocess.run(["git", *a], cwd=REPO, capture_output=True, check=True).stdout


def show(path: str) -> bytes:
    return git("show", f"{COMMIT}:{path}")


def strip_text(obj):
    if isinstance(obj, dict):
        return {k: strip_text(v) for k, v in obj.items() if k not in TEXT_KEYS}
    if isinstance(obj, list):
        return [strip_text(x) for x in obj]
    return obj


def write(rel: str, data: bytes):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(data)


def main():
    files = git("ls-tree", "-r", "--name-only", COMMIT).decode("utf-8").splitlines()
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    n = 0
    for f in files:
        if f in EXCLUDE or "/__pycache__/" in f:
            continue
        keep = f.startswith(INCLUDE_PREFIX) or f in INCLUDE_FILES or (f.startswith(RESULT_DIRS) and f.endswith(RESULT_OK))
        if not keep:
            continue
        data = show(f)
        if f.startswith(RESULT_DIRS) and f.endswith(".json"):
            data = json.dumps(strip_text(json.loads(data.decode("utf-8"))), ensure_ascii=False, indent=1).encode("utf-8")
        if f == "eval/real_v2/relabel/agreement.txt":     # danh sách bất đồng in kèm đầu câu hỏi: chỉ giữ mã câu và nhãn hai lượt
            data = re.sub(r"(?m)^(\s+real_v\d-\d+) \| [^|]* \| ", r"\1 | ", data.decode("utf-8")).encode("utf-8")
        if f == "eval/real_v1/collect_real_v1.py":
            s = data.decode("utf-8")
            s, k = re.subn(r"MANUAL_NAMES = \[.*?\]", "MANUAL_NAMES = []   # bản công khai: đã xoá 17 họ tên người thật tìm được khi đọc tay (không công bố)", s, flags=re.S)
            assert k == 1
            data = s.encode("utf-8")
        write(f, data)
        n += 1
    # nhãn không kèm văn bản
    for name, (lab, src) in LABEL_SETS.items():
        cases = json.loads(show(lab).decode("utf-8"))
        srcmap = {c["id"]: c for c in json.loads(show(src).decode("utf-8"))} if src else {}
        lines = []
        for c in cases:
            s = c.get("source") or srcmap.get(c["id"], {}).get("source")
            st = c.get("stratum") or srcmap.get(c["id"], {}).get("stratum")
            lines.append(json.dumps({"id": c["id"], "source": s, "stratum": st, "beh": c["beh"], "expect_ids": c["expect_ids"]}, ensure_ascii=False))
        write(f"labels/{name}.jsonl", ("\n".join(lines) + "\n").encode("utf-8"))
    extra = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public_extra")
    for root, _, fs in os.walk(extra):
        for f in fs:
            src = os.path.join(root, f)
            write(os.path.relpath(src, extra), open(src, "rb").read())
    sha = git("rev-parse", "--short", COMMIT).decode().strip()
    write("EXPORT.txt", f"exported from {sha} by tools/make_public_code.py\n".encode())
    print("copied", n, "files to", OUT)
    check(files)


def check(files):
    """Quét bản xuất: không còn văn bản câu hỏi, tên người trong danh sách che, khoá."""
    texts = []
    for lab in ("eval/real_v1/cases_real_v1.json", "eval/real_v2/cases_real_v2.json", "eval/real_v4/cases_real_v4.json"):
        for c in json.loads(show(lab).decode("utf-8")):
            t = " ".join((c.get("text") or c.get("q") or "").split())
            if len(t) >= 40:
                texts.append(t[:40])
    names = re.search(r"MANUAL_NAMES = \[(.*?)\]", show("eval/real_v1/collect_real_v1.py").decode("utf-8"), re.S).group(1)
    names = re.findall(r'"([^"]+)"', names)
    bad = []
    for root, _, fs in os.walk(OUT):
        for f in fs:
            p = os.path.join(root, f)
            try:
                s = " ".join(open(p, encoding="utf-8").read().split())
            except UnicodeDecodeError:
                continue
            hit = next((t for t in texts if t in s), None)
            if hit:
                bad.append((p, "question text", hit))
            hn = next((x for x in names if x in s), None)
            if hn:
                bad.append((p, "manual name", "(hidden)"))
            if re.search(r"(?i)(abi\.com\.vn/api|Bearer\s+[A-Za-z0-9]{12,}|ABI_API_KEY\s*=\s*['\"][^'\"]+)", s):
                bad.append((p, "key", ""))
    print("check:", "OK" if not bad else f"{len(bad)} problems")
    for b in bad[:40]:
        print("  ", os.path.relpath(b[0], OUT), b[1], b[2][:30])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
