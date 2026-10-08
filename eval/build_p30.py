"""Phase 30: dựng eval/cases_p30.jsonl, bộ ca "hỏi lại khi mơ hồ" vs "trả lời khi một thủ tục rõ ràng". TỰ SOẠN TỪ DB, KHÔNG mở/chép bộ mù (h3/h4/h5/pseudo_real/team).
Đáp án lấy từ SỰ THẬT DỮ LIỆU, không từ đầu ra hệ thống:
  clarify : cụm gốc (1-3 chữ đầu của tên lõi) mà >= 3 thủ tục cấp xã (không tỉnh/ngành dọc) có tên lõi mở đầu bằng cụm đó, không thủ tục nào tên lõi đúng bằng cụm;
            + nhóm viết tay: câu mơ hồ một dòng, chủ đề có nhiều nhóm đối tượng (assert >= 3 thủ tục khác nhau chứa đủ chữ).
  answer  : (a) tên lõi đầy đủ của một thủ tục; (b) cụm 2-3 chữ đầu mà ĐÚNG MỘT thủ tục chứa đủ các chữ (định danh duy nhất); (c) viết tay: câu đời thường một thủ tục rõ.
Mỗi ca được bọc một mẫu câu (xoay vòng). Nửa 'tune' (số thứ tự chẵn) dùng khi chỉnh; nửa 'held' (lẻ) chỉ chạy ở cuối.
Chạy: python run_server.py eval/build_p30.py   rồi   python run_server.py eval/run_p30.py"""
import collections, json, os, random, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [ROOT]
from system3.data import api  # noqa: E402
from system3.data.textutil import fold  # noqa: E402

conn = api.connect()
rows = conn.execute("SELECT proc_id,name,domain,province,agency_levels FROM procedures WHERE status='active'").fetchall()
OK = [r for r in rows if not r["province"] and "Xã/Phường" in (r["agency_levels"] or "") and not any(v in r["domain"] for v in ("Thuế", "Hải quan"))]
DANGLE = re.compile(r"\b(và|của|cho|để|các|tại|đối|với|hoặc|do|là|có)$")


def core(n):
    n = re.sub(r"\([^)]*\)?", " ", n)
    n = re.sub(r"^thủ tục\s+", "", n, flags=re.I)
    return re.sub(r"[,.;“”\"]", " ", n.lower()).split()


C = {r["proc_id"]: core(r["name"]) for r in OK}
T = {p: set(fold(" ".join(w)).split()) for p, w in C.items()}
NAME = {r["proc_id"]: r["name"] for r in OK}
exact = collections.defaultdict(list)
for pid, w in C.items():
    exact[" ".join(w)].append(pid)


def containing(words):
    ws = set(fold(" ".join(words)).split())
    return [p for p, t in T.items() if ws <= t]


WRAP = ["{x}", "cho mình hỏi thủ tục {x}", "em muốn {x}", "{x} làm thế nào ạ", "thủ tục {x} cần giấy tờ gì", "{x} nộp ở đâu", "Tôi cần {x}", "giúp mình {x} với"]
rnd = random.Random(30)
cases = []

# ---- clarify: cụm gốc nhiều nhóm. Danh sách cụm do người soạn chọn (cụm có nghĩa, không phải mảnh âm tiết); DB kiểm: >= 3 tên lõi khác nhau mở đầu bằng cụm, không tên nào bằng đúng cụm
pref = collections.defaultdict(set)
for pid, w in C.items():
    for k in (1, 2, 3, 4):
        if len(w) > k:
            pref[" ".join(w[:k])].add(pid)
STEMS = ["gia hạn", "khai báo", "thu hồi", "giao đất", "chuyển đổi", "chứng thực chữ ký", "xét tuyển", "công bố", "cấp giấy phép", "đăng ký lại",
         "phê duyệt", "thông báo", "đề nghị", "thẩm định", "cấp lại giấy chứng nhận", "cho phép", "chứng thực", "tiếp nhận", "thành lập", "giải thể",
         "thanh toán", "sáp nhập", "xóa đăng ký", "sửa đổi bổ sung", "điều chỉnh", "chấm dứt", "tuyển chọn", "ghi vào sổ", "công nhận", "xác nhận",
         "hỗ trợ chi phí", "cấp bản sao", "cấp bằng", "giải quyết hưởng chế độ", "biên phòng", "cho thuê", "trình báo mất", "đăng ký thay đổi",
         "đăng ký chấm dứt", "cho ý kiến", "cấp đổi", "chuyển mục đích", "thay đổi", "công nhận hộ", "cấp lại", "hỗ trợ", "trợ cấp", "đăng ký nhận",
         "đăng ký kết", "cấp giấy xác nhận", "phê duyệt đề", "chế độ chính sách", "đăng ký khai", "tiếp nhận đối tượng", "giải quyết chế độ", "cấp gia hạn"]
for s in STEMS:
    ps = pref.get(s, set())
    n_groups = len({" ".join(C[q]) for q in ps})
    if n_groups < 3 or s in exact:
        print("bỏ cụm", s, "(nhóm:", n_groups, "tên đúng cụm:", s in exact, ")")
        continue
    cases.append(dict(kind="clarify", sub="stem", core=s, n_match=len(containing(s.split()))))

# ---- clarify viết tay: một dòng mơ hồ / chủ đề nhiều nhóm đối tượng
# (câu, chữ nội dung để DB kiểm: TOÀN BỘ chữ nghiệp vụ của câu; phải có >= 3 thủ tục chứa đủ)
HAND_CLARIFY = [("trợ cấp cho người khuyết tật", "trợ cấp khuyết tật"), ("mai táng phí", "mai táng"), ("hỗ trợ người có công", "hỗ trợ có công"), ("liệt sĩ", "liệt sĩ"),
                ("bảo hiểm y tế", "bảo hiểm y tế"), ("trẻ em", "trẻ em"), ("xin giấy phép", "giấy phép"), ("cấp giấy chứng nhận", "cấp giấy chứng nhận"),
                ("đất đai", "đất đai"), ("hỗ trợ hộ nghèo", "hỗ trợ hộ nghèo"), ("người nước ngoài", "nước ngoài"), ("thương binh", "thương binh"),
                ("trợ cấp hàng tháng", "trợ cấp hàng tháng"), ("đăng ký hoạt động", "đăng ký hoạt động"), ("trường học", "trường"), ("tàu thuyền", "tàu thuyền"),
                ("giấy phép xây dựng", "giấy phép xây dựng"), ("nhập cảnh xuất cảnh", "nhập cảnh xuất cảnh"), ("người cao tuổi", "cao tuổi"),
                ("người có công với cách mạng", "có công cách mạng"), ("hỗ trợ giáo dục", "hỗ trợ giáo dục"), ("nhà ở", "nhà ở"),
                ("Mẹ tôi muốn hưởng trợ cấp, làm thế nào?", "trợ cấp"), ("Em muốn xin hỗ trợ cho gia đình người có công", "hỗ trợ có công"), ("Tôi muốn đăng ký thành lập", "đăng ký thành lập"),
                ("Cho hỏi thủ tục đăng ký hợp tác xã", "đăng ký hợp tác xã"), ("Em muốn thay đổi thông tin đăng ký", "thay đổi thông tin đăng ký"), ("Công ty tôi muốn chấm dứt hoạt động", "chấm dứt hoạt động"),
                ("Xin giấy xác nhận", "giấy xác nhận"), ("Tôi muốn xin hỗ trợ", "hỗ trợ"), ("Cần làm giấy tờ cho người nước ngoài", "nước ngoài"), ("Đăng ký cho trẻ em", "đăng ký trẻ em"),
                ("Cho tôi hỏi về bảo hiểm xã hội", "bảo hiểm xã hội"), ("thủ tục liên quan đến đất", "liên quan đất"), ("Hồ sơ xin phép xây dựng", "phép xây dựng"),
                ("Xin cấp lại giấy", "cấp lại giấy"), ("Thủ tục về hộ tịch", "hộ tịch"), ("liên quan đến cư trú", "cư trú"), ("giáo dục mầm non", "giáo dục mầm non"),
                ("điều chỉnh thông tin", "điều chỉnh thông tin"), ("bồi thường thiệt hại", "bồi thường thiệt hại"), ("dân quân tự vệ", "dân quân tự vệ"), ("hoạt động tôn giáo", "tôn giáo"),
                ("hỗ trợ học sinh", "hỗ trợ học sinh"), ("quyền lợi cho người lao động", "lao động"), ("về y tế", "y tế"), ("đăng ký doanh nghiệp", "đăng ký doanh nghiệp")]
for s, kw in HAND_CLARIFY:
    n = len(containing(kw.split()))
    if n < 3:                    # chủ đề phải thật sự nằm trong >= 3 thủ tục, không thì bỏ (không có đáp án clarify theo dữ liệu)
        print("bỏ ca viết tay (chỉ", n, "thủ tục):", s)
        continue
    cases.append(dict(kind="clarify", sub="hand", core=s, n_match=n))

# ---- answer (a) tên lõi đầy đủ, (b) cụm đầu định danh duy nhất
full = sorted(pid for pid in C if len(exact[" ".join(C[pid])]) == 1 and 3 <= len(C[pid]) <= 14)
rnd.shuffle(full)
for pid in full[:40]:
    cases.append(dict(kind="answer", sub="full", core=" ".join(C[pid]), ids=[pid]))
BOUND = {"và", "cho", "của", "đối", "với", "tại", "trong", "do", "khi", "đã", "trên", "từ", "ở", "theo", "hoặc", "để"}
# (a2) tên lõi đầy đủ của thủ tục nằm TRONG nhóm một cụm gốc nhiều nhóm (anh em cùng mở đầu): rủi ro hỏi thừa cao nhất
sib = sorted({q for st in STEMS for q in pref.get(st, set()) if len(exact[" ".join(C[q])]) == 1 and 3 <= len(C[q]) <= 14} - set(full[:40]))
rnd.shuffle(sib)
for pid in sib[:30]:
    cases.append(dict(kind="answer", sub="sibling", core=" ".join(C[pid]), ids=[pid]))
uniq = []
for pid, w in sorted(C.items()):
    for k in (2, 3, 4):
        if len(w) > k + 1 and w[k] in BOUND and containing(w[:k]) == [pid] and not DANGLE.search(" ".join(w[:k])):     # cụm kết thúc ở ranh giới tự nhiên (không phải mảnh âm tiết)
            uniq.append((pid, " ".join(w[:k])))
            break
rnd.shuffle(uniq)
for pid, s in uniq[:36]:
    cases.append(dict(kind="answer", sub="unique", core=s, ids=[pid]))

# ---- answer viết tay: đời thường, một thủ tục rõ (đáp án = proc_id đã kiểm tên trong DB)
HAND_ANSWER = [("em muốn làm khai tử cho ông nội", "1.000656"), ("tách hộ khẩu cần giấy tờ gì", "1.010038"), ("khai báo tạm vắng ở đâu", "1.003677"),
               ("đăng ký kết hôn lệ phí bao nhiêu", "1.000894"), ("chứng thực di chúc", "2.001019"), ("gia hạn tạm trú", "1.002755"),
               ("hòa giải tranh chấp đất đai", "1.012812"), ("đăng ký khai sinh cho con", "1.001193")]
for q, pid in HAND_ANSWER:
    assert pid in NAME, (q, pid)
    cases.append(dict(kind="answer", sub="hand", core=None, question=q, ids=[pid]))

# ---- bọc câu hỏi, gán nửa tune/held
out, cnt_k = [], collections.Counter()
for c in cases:
    n = cnt_k[c["kind"]]
    cnt_k[c["kind"]] += 1
    q = c.pop("question", None) or (c["core"] if c["core"][0].isupper() else WRAP[(n * 3 + (1 if c["kind"] == "answer" else 0)) % len(WRAP)].format(x=c["core"]))     # câu viết hoa đầu = câu đủ ý, không bọc
    exp = {"behavior": "clarify"} if c["kind"] == "clarify" else {"behavior": "answer", "acceptable": c["ids"]}
    out.append({"id": f"p30-{c['kind'][0]}-{n:03d}", "split": "tune" if n % 2 == 0 else "held", "kind": c["kind"], "sub": c["sub"],
                "question": q, "expected": exp, "n_match": c.get("n_match")})
# ---- FRESH: lô viết SAU khi chỉnh xong, chưa từng chạy trước phần chỉnh (split 'fresh'); mẫu bọc khác, cụm/chủ đề khác, seed khác
WRAP2 = ["{x} thì phải làm sao", "cho em hỏi về {x}", "tôi đang tìm hiểu {x}", "{x}?", "nhờ tư vấn {x} với", "mình cần biết về {x}"]
rnd2 = random.Random(31)
used = {o["question"] for o in out}
F_STEMS = ["giải quyết hưởng", "cấp giấy", "giải quyết", "thực hiện", "trình báo", "cho thuê nhà", "giải thể trường", "gia hạn giấy phép", "cấp lại giấy",
           "đăng ký thay đổi", "chấp thuận", "chấm dứt hoạt động", "công bố mở", "đăng ký phương tiện", "cấp giấy xác nhận", "thôi", "điều chỉnh thông tin"]
F_HAND = [("nuôi con nuôi", "con nuôi"), ("khen thưởng", "khen thưởng"), ("thủy sản", "thủy sản"), ("thủy lợi", "thủy lợi"), ("rừng", "rừng"), ("đường bộ", "đường bộ"),
          ("an ninh trật tự", "an ninh trật tự"), ("giấy phép lao động", "giấy phép lao động"), ("quân nhân", "quân nhân"), ("thiên tai", "thiên tai"),
          ("đăng ký xe", "phương tiện"), ("chế độ cho cựu chiến binh", "cựu chiến binh"), ("tai nạn lao động", "tai nạn lao động"), ("học bổng", "học")]
fc, fa = [], []
for st in F_STEMS:
    ps = pref.get(st, set())
    if len({" ".join(C[q]) for q in ps}) >= 3 and st not in exact:
        fc.append((st, len(containing(st.split()))))
    else:
        print("fresh: bỏ cụm", st)
for st, kw in F_HAND:
    n = len(containing(kw.split()))
    if n >= 3:
        fc.append((st, n))
    else:
        print("fresh: bỏ chủ đề", st, n)
pool_full = [pid for pid in full if " ".join(C[pid]) not in used and pid not in full[:40]]
rnd2.shuffle(pool_full)
fa += [("full", " ".join(C[pid]), [pid]) for pid in pool_full[:12]]
sib_left = [pid for pid in sib if pid not in sib[:30]]
rnd2.shuffle(sib_left)
fa += [("sibling", " ".join(C[pid]), [pid]) for pid in sib_left[:12]]
uq_left = [(pid, st) for pid, st in uniq if (pid, st) not in uniq[:36]]
rnd2.shuffle(uq_left)
fa += [("unique", st, [pid]) for pid, st in uq_left[:10]]
for i, (st, n) in enumerate(fc):
    out.append({"id": f"p30-fc-{i:03d}", "split": "fresh", "kind": "clarify", "sub": "fresh", "question": WRAP2[i % len(WRAP2)].format(x=st), "expected": {"behavior": "clarify"}, "n_match": n})
for i, (sub, core_, ids) in enumerate(fa):
    out.append({"id": f"p30-fa-{i:03d}", "split": "fresh", "kind": "answer", "sub": "fresh-" + sub, "question": WRAP2[(i + 2) % len(WRAP2)].format(x=core_), "expected": {"behavior": "answer", "acceptable": ids}, "n_match": None})
with open(os.path.join(HERE, "cases_p30.jsonl"), "w", encoding="utf-8") as f:
    for o in out:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")
print(len(out), dict(collections.Counter((o["kind"], o["split"]) for o in out)))
