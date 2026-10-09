"""Phase 31: dựng eval/cases_p31.jsonl, bộ ca "tên đầy đủ của họ thủ tục có nhiều dạng THẬT -> hỏi lại" vs "đã rõ -> trả lời". TỰ SOẠN TỪ DB, KHÔNG mở/chép bộ mù (h3-h6/pseudo_real/team).
Đáp án lấy từ SỰ THẬT DỮ LIỆU (bảng families/procedures/procedure_subjects), không từ đầu ra hệ thống:
  Họ "nhiều dạng thật" = họ có >= 3 bản KHÔNG gắn tỉnh, cấp xã, không ngành dọc, tên lõi khác nhau (bỏ "Thủ tục", dấu câu). Bản theo tỉnh và tên gần trùng không tính.
  clarify     : tên đầy đủ / tên lõi của họ đó (bọc mẫu câu, có cả mẫu kèm mục hỏi "cần giấy tờ gì", "lệ phí").
  answer      : (named) tên đầy đủ của TỪNG dạng; (obj) tên chung + đối tượng/từ phân biệt ("cho con", "trong nước", "cho ông nội"); (single) tên đầy đủ thủ tục một dạng;
                (two) họ chỉ có 2 dạng (mặc định + nút "dạng khác", không đổi); (ctx) hội thoại nhiều lượt: lượt trước đã chốt một dạng, lượt cuối hỏi mục;
                (prof) hồ sơ người dùng (Phase 26) thu hẹp về đúng 1 dạng -> trả lời; clarify khi hồ sơ vẫn còn >= 2 dạng hợp hoặc không phân biệt được.
Nửa 'tune' (số thứ tự chẵn) dùng khi chỉnh; 'held' (lẻ) chỉ chạy ở cuối. Chạy: python run_server.py eval/build_p31.py ; python run_server.py eval/run_p31.py [--split tune|held|all]
`--fresh`: sinh thêm lô FRESH (mẫu bọc, họ/đối tượng khác, seed khác) SAU khi chỉnh xong; ghi eval/cases_p31_fresh.jsonl, chạy một lần."""
import collections, json, os, random, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [ROOT]
from system3.data import api  # noqa: E402
from system3.data.textutil import fold  # noqa: E402

FRESH = "--fresh" in sys.argv
conn = api.connect()
VERT = ("Thuế", "Hải quan")
rows = {r["proc_id"]: r for r in conn.execute("SELECT proc_id,name,domain,province,agency_levels FROM procedures WHERE status='active'")}


def ok_row(r):
    return not r["province"] and "Xã/Phường" in (r["agency_levels"] or "") and not any(v in r["domain"] for v in VERT)


def core(name):
    return re.sub(r"^thủ tục\s+", "", name.strip().rstrip("."), flags=re.I).strip()


def nkey(name):
    return " ".join(sorted(set(re.findall(r"[0-9a-z]+", re.sub(r"^thu tuc ", "", fold(name))))))


fams = collections.defaultdict(list)
for pid, h, n, dv in conn.execute("SELECT proc_id,head,n_members,default_variant FROM families"):
    if pid in rows and ok_row(rows[pid]):
        fams[h].append((pid, dv))
REAL, TWO = {}, {}
for h, ms in fams.items():
    seen, vs = set(), []
    for pid, dv in sorted(ms, key=lambda x: (-x[1], len(rows[x[0]]["name"]))):
        k = nkey(rows[pid]["name"])
        if k not in seen:
            seen.add(k)
            vs.append(pid)
    if len(vs) >= 3:
        REAL[h] = vs
    elif len(vs) == 2:
        TWO[h] = vs
subj = api.subjects_of(conn, [p for vs in REAL.values() for p in vs])
print("họ nhiều dạng thật:", {h: len(v) for h, v in REAL.items()}, "| họ 2 dạng:", len(TWO))

WRAP = ["{x}", "cho mình hỏi thủ tục {x}", "em muốn {x}", "{x} làm thế nào ạ", "thủ tục {x} cần giấy tờ gì", "{x} nộp ở đâu", "Tôi cần {x}", "{x} lệ phí bao nhiêu", "{x} mất bao lâu", "giúp mình {x} với"]
WRAP_F = ["mình đang tìm hiểu {x}", "{x} thì làm sao nhỉ", "nhờ tư vấn {x}", "{x}?", "bên mình hướng dẫn {x} giúp với", "tôi muốn biết {x}", "xin hỏi {x} cần chuẩn bị gì", "{x} hết bao nhiêu tiền"]
W = WRAP_F if FRESH else WRAP
rnd = random.Random(32 if FRESH else 31)
cases = []


def names_of(h):
    d = core(rows[REAL[h][0]]["name"]).lower().replace("“", "").replace("”", "")
    out = [d]
    if d.startswith("đăng ký "):
        out.append(d[len("đăng ký "):])        # tên lõi ngắn: "khai sinh", "kết hôn"
    return out


# ---- clarify: tên đầy đủ / lõi của họ nhiều dạng thật
for h in sorted(REAL):
    for nm in names_of(h):
        for wi in range(len(W)):
            cases.append(dict(kind="clarify", sub="full" if nm == names_of(h)[0] else "core", q=W[wi].format(x=nm), head=h, ids=REAL[h], wrap=wi))
# ---- answer: từng dạng được gọi đúng tên (tên đầy đủ của dạng)
for h in sorted(REAL):
    for pid in REAL[h][1:]:        # bản đầu (mặc định) có tên = tên chung của họ: đó là ca clarify, không phải ca 'gọi đúng tên dạng'
        nm = core(rows[pid]["name"]).lower().replace("“", "").replace("”", "")
        for wi in rnd.sample(range(len(W)), 2):
            cases.append(dict(kind="answer", sub="named", q=W[wi].format(x=nm), head=h, ids=[pid], wrap=wi))
# ---- answer: tên chung + đối tượng / từ phân biệt (đối tượng "con", "ông nội"... KHÔNG chọn dạng cụ thể: đáp án là dạng mặc định, chấp nhận mọi dạng của họ)
OBJ = {"đăng ký khai sinh": ["cho con", "cho cháu", "cho bé nhà em", "trong nước"], "đăng ký kết hôn": ["trong nước", "cho hai vợ chồng em"],
       "đăng ký khai tử": ["cho ông nội", "cho bố tôi", "cho bà ngoại"], "đăng ký nhận cha, mẹ, con": ["cho con tôi", "trong nước"],
       "cấp bằng tổ quốc ghi công": ["cho ông nội tôi", "cho bố tôi"]}
for h in sorted(REAL):
    nm = names_of(h)[0]
    for ob in OBJ.get(nm, ["cho con", "cho ông nội"]):
        pat = rnd.choice(["{x} {o}", "em muốn {x} {o}", "{x} {o} cần giấy tờ gì"])
        cases.append(dict(kind="answer", sub="obj", q=pat.format(x=nm, o=ob), head=h, ids=REAL[h], wrap=-1))
# ---- answer: thủ tục một dạng (full name) và họ 2 dạng
singles = sorted(pid for pid, r in rows.items() if ok_row(r) and pid in {p for ms in fams.values() for p, _ in ms if len(ms) == 1} and 3 <= len(core(r["name"]).split()) <= 12)
rnd.shuffle(singles)
for i, pid in enumerate(singles[:50]):
    cases.append(dict(kind="answer", sub="single", q=W[i % len(W)].format(x=core(rows[pid]["name"]).lower()), head=None, ids=[pid], wrap=i % len(W)))
tw = sorted(TWO)
rnd.shuffle(tw)
for i, h in enumerate(tw[:14]):
    cases.append(dict(kind="answer", sub="two", q=W[(i * 3) % len(W)].format(x=core(rows[TWO[h][0]]["name"]).lower()), head=h, ids=TWO[h], wrap=(i * 3) % len(W)))
# ---- answer: hội thoại nhiều lượt, lượt trước đã chốt một dạng; lượt cuối hỏi mục -> trả lời đúng dạng đó
FOLLOW = ["còn lệ phí?", "mất mấy ngày", "nộp ở đâu vậy", "cần giấy tờ gì", "thời gian giải quyết bao lâu"]
for h in sorted(REAL):
    for pid in rnd.sample(REAL[h], min(3, len(REAL[h]))):
        nm = core(rows[pid]["name"])
        turns = [{"role": "user", "text": nm}, {"role": "assistant", "text": f"Về «{rows[pid]['name']}»: bạn cần chuẩn bị hồ sơ theo quy định, nộp tại UBND cấp xã. Bạn muốn hỏi thêm gì không?"}, {"role": "user", "text": rnd.choice(FOLLOW)}]
        cases.append(dict(kind="answer", sub="ctx", q=turns[-1]["text"], head=h, ids=[pid], turns=turns, wrap=-1))
# ---- hồ sơ người dùng: mỗi (họ, đối tượng) -> số dạng "hợp" (dạng không khai đối tượng = chưa biết, giữ) -> 1: answer; 2..n-1 hoặc cả họ: clarify
pi = 0
for h in sorted(REAL):
    allsub = sorted({s for p in REAL[h] for s in subj[p]})
    for s in allsub:
        hit = [p for p in REAL[h] if not subj[p] or s in subj[p]]
        nm = names_of(h)[0]
        q = W[pi % len(W)].format(x=nm)
        pi += 1
        if len(hit) == 1:
            cases.append(dict(kind="answer", sub="prof", q=q, head=h, ids=hit, profile=s, wrap=pi % len(W)))
        elif 2 <= len(hit) < len(REAL[h]):
            cases.append(dict(kind="clarify", sub="prof-shrink", q=q, head=h, ids=hit, profile=s, wrap=pi % len(W)))
        else:
            cases.append(dict(kind="clarify", sub="prof-none", q=q, head=h, ids=REAL[h], profile=s, wrap=pi % len(W)))

# ---- FRESH: câu viết tay SAU khi chỉnh xong (không dùng khi chỉnh): gõ không dấu/viết tắt, mục hỏi lạ, đối tượng/từ phân biệt chưa từng dùng ở nửa tune/held
if FRESH:
    H = {"ks": "dang ky khai sinh", "kh": "dang ky ket hon", "kt": "dang ky khai tu", "ncm": "dang ky nhan cha me con", "bq": "cap bang to quoc ghi cong"}
    for q, h in [("dk khai sinh", "ks"), ("dang ky ket hon can giay to gi", "kh"), ("làm khai tử", "kt"), ("thủ tục khai sinh", "ks"), ("hồ sơ khai sinh gồm những gì", "ks"), ("xin hướng dẫn đăng ký kết hôn", "kh"),
                 ("đăng ký nhận cha mẹ con online được không", "ncm"), ("bằng tổ quốc ghi công", "bq"), ("Cấp Bằng Tổ quốc ghi công thời hạn bao lâu", "bq"), ("đăng ký khai tử thời gian giải quyết", "kt"),
                 ("khai sinh nộp hồ sơ ở đâu", "ks"), ("đăng ký kết hôn có mất phí không", "kh"), ("ĐĂNG KÝ KHAI SINH", "ks"), ("mình cần đăng ký kết hôn, thủ tục thế nào?", "kh")]:
        cases.append(dict(kind="clarify", sub="hand", q=q, head=H[h], ids=REAL[H[h]], wrap=-1))
    for q, h, ids in [("đăng ký khai sinh cho cháu ngoại", "ks", REAL[H["ks"]]), ("đăng ký kết hôn cho em gái tôi", "kh", REAL[H["kh"]]), ("đăng ký khai tử cho chồng tôi", "kt", REAL[H["kt"]]),
                      ("khai sinh lưu động cần gì", "ks", ["1.003583"]), ("đăng ký kết hôn người nước ngoài ở khu vực biên giới", "kh", ["1.000094", "2.000806"]),
                      ("khai sinh có yếu tố nước ngoài lệ phí bao nhiêu", "ks", ["2.000528", "1.000110", "1.001695", "1.000893"]), ("đăng ký khai sinh quá hạn", "ks", REAL[H["ks"]]),
                      ("đăng ký kết hôn lưu động", "kh", ["1.000593"]), ("khai tử cho người nước ngoài ở biên giới", "kt", ["1.004827", "1.001766"]), ("đăng ký nhận cha, mẹ, con có yếu tố nước ngoài", "ncm", ["2.000779", "1.000080"]),
                      ("đăng ký khai sinh kèm nhận cha mẹ con", "ks", ["1.000689", "1.001695"]), ("em muốn đăng ký khai sinh cho con trai mới sinh", "ks", REAL[H["ks"]])]:
        cases.append(dict(kind="answer", sub="hand", q=q, head=H[h], ids=ids, wrap=-1))
out, cnt = [], collections.Counter()
for c in cases:
    k = (c["kind"], c["sub"])
    n = cnt[k]
    cnt[k] += 1
    split = "fresh" if FRESH else ("tune" if n % 2 == 0 else "held")
    e = {"behavior": "clarify", "family": c["ids"]} if c["kind"] == "clarify" else {"behavior": "answer", "acceptable": c["ids"]}
    o = {"id": f"p31{'f' if FRESH else ''}-{c['kind'][0]}-{c['sub']}-{n:03d}", "split": split, "kind": c["kind"], "sub": c["sub"], "question": c["q"], "head": c["head"], "expected": e}
    if c.get("turns"):
        o["turns"] = c["turns"]
    if c.get("profile"):
        o["profile_subject"] = c["profile"]
    out.append(o)
fn = "cases_p31_fresh.jsonl" if FRESH else "cases_p31.jsonl"
with open(os.path.join(HERE, fn), "w", encoding="utf-8") as f:
    for o in out:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")
print(fn, len(out), dict(collections.Counter((o["kind"], o["sub"], o["split"]) for o in out)))
