"""Bộ kiểm tổng quát hoá truy hồi, SINH TỰ ĐỘNG từ DB (không dùng cases.jsonl).
Chạy: cd eval && PYTHONPATH=.. S3_USE_LLM=0 python synth_retrieval.py [--n 450] [--show 40]
Thủ tục chia 2 nửa theo băm tên (TRAIN / TEST rời nhau) + hạt giống biến thể khác nhau: chỉ tune trên TRAIN, báo TEST.
Đúng = thủ tục chọn ở đoạn đầu có thủ tục thuộc cùng family/cùng tên với thủ tục gốc.
"""
import argparse, hashlib, os, random, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from system3.data import api
from system3.data.textutil import fold
from system3.retrieval import Index, resolve

SEEDS = {"train": 1111, "test": 2222}
LEAD = ["dạ cho em hỏi vụ", "cho mình hỏi", "tui muốn làm", "em muốn hỏi về", "ad ơi cho hỏi", "bác ơi", "hổng biết", "cho hỏi xíu",
        "nhà em đang cần", "anh chị cho em hỏi", "mình mới chuyển tới, muốn hỏi", "dạ chào ad, cho em hỏi"]
TAIL = [" á", " nha", " z", " với", " ạ", " đó", " nhé", " dc ko", " hông ạ", " nè ad", " thế nào z"]
ASK = [("phí bao nhiêu", "{n} phí bao nhiêu"), ("nộp ở đâu", "{n} nộp ở đâu"), ("mất mấy bữa", "{n} mất mấy bữa"),
       ("văn bản nào quy định", "văn bản nào quy định {n}"), ("thu phí", "{n} có thu phí không"),
       ("cần giấy tờ gì", "làm {n} cần giấy tờ gì"), ("nộp online", "{n} nộp online được không"),
       ("các bước", "các bước {n}")]
ABBR = [("đăng ký", "đk"), ("giấy chứng nhận", "gcn"), ("không", "ko"), ("được", "dc"), ("thường trú", "tt"), ("tạm trú", "tt"),
        ("hộ khẩu", "hk"), ("giấy phép", "gp"), ("căn cước công dân", "cccd"), ("giấy khai sinh", "gks")]


def core(name):
    n = re.sub(r"\([^)]*\)", " ", name)
    n = re.sub(r"^\s*th[ủu] t[ụu]c\s+", "", n, flags=re.I)
    n = re.sub(r"\s+", " ", n).strip(" .,;")
    return n


def typo(w, r):
    if len(w) < 4:
        return w
    i = r.randrange(1, len(w) - 1)
    k = r.random()
    if k < 0.4:
        return w[:i] + w[i + 1] + w[i] + w[i + 2:] if i + 2 <= len(w) - 0 and i + 1 < len(w) else w
    if k < 0.7:
        return w[:i] + w[i + 1:]
    return w[:i] + w[i] + w[i:]


STORY = ["nhà em ở phường này, hôm qua có người chỉ là cần {x} mà em chưa rành lắm", "chồng em bảo phải đi làm {x}, không biết sao",
         "em ở quê mới lên, nghe nói phải {x}, giờ em không rành, mong được chỉ giúp", "tui nghe hàng xóm nói {x} mà hổng biết đi đâu"]


def shorten(n, r, prefixes):
    """Tên rất dài -> người dùng chỉ gõ phần đầu; chỉ cắt khi phần đầu không trùng thủ tục khác (tránh đề bài mơ hồ)."""
    ws = n.split()
    if len(ws) > 9:
        k = r.randint(6, 9)
        pre = fold(" ".join(ws[:k]))
        if prefixes.get(pre, 0) <= 1:
            return " ".join(ws[:k])
    return n


def variant(name, r, prefixes=None):
    n = shorten(core(name), r, prefixes or {})
    ws = n.split()
    kind = r.choice(["clean", "nodau", "drop", "casual", "casual_nodau", "ask", "ask_casual", "abbr", "typo", "swap", "long"])
    low = n[0].lower() + n[1:]
    if kind == "drop" and len(ws) > 4:
        i = r.randrange(1, len(ws) - 1)
        low = " ".join(ws[:i] + ws[i + 1:]).lower()
    if kind == "abbr":
        for a, b in ABBR:
            if a in low.lower():
                low = low.lower().replace(a, b)
                break
    if kind == "typo":
        j = r.randrange(len(ws))
        ws2 = list(ws)
        ws2[j] = typo(ws2[j].lower(), r)
        low = " ".join(ws2).lower()
    q = low
    if kind in ("casual", "casual_nodau", "ask_casual", "long"):
        q = f"{r.choice(LEAD)} {low}{r.choice(TAIL)}"
    if kind in ("ask", "ask_casual"):
        q = r.choice(ASK)[1].format(n=low)
        if kind == "ask_casual":
            q = f"{r.choice(LEAD)} {q}{r.choice(TAIL)}"
    if kind == "swap":
        a = r.choice(ASK)
        q = f"{a[0]} {low}"
    if kind == "long":
        q = r.choice(STORY).format(x=low) + ", " + r.choice(["cho em hỏi thủ tục thế nào", "chỉ giúp em với nhé", "thế nào ạ", "không biết có được hông"])
    if kind in ("nodau", "casual_nodau", "abbr"):
        q = fold(q)
    return kind, q


OOS = ["hỗ trợ chi phí hỏa táng", "xin giấy xác nhận đã nộp thuế", "làm hộ chiếu mới", "cách nấu phở bò", "giá vàng hôm nay",
       "tư vấn ly hôn ra tòa", "đăng ký nhãn hiệu sản phẩm", "đội tuyển Việt Nam đá mấy giờ", "viết giúp tôi bài thơ về mùa thu",
       "thi bằng lái xe ở đâu", "đăng ký visa đi Nhật", "tôi bị đau đầu uống thuốc gì", "giá xăng hôm nay bao nhiêu",
       "thủ tục xin cấp bằng sáng chế", "cho em hỏi thời tiết ngày mai", "mua bán chứng khoán thế nào", "đổi giấy phép lái xe quốc tế",
       "nộp đơn kiện ra tòa án nhân dân", "xin việc làm ở công ty nào tốt", "làm sao để giảm cân nhanh", "dịch giúp tôi câu tiếng Anh",
       "lịch thi đấu world cup", "đăng ký quyền tác giả cho cuốn sách", "mua vé máy bay đi Đà Nẵng", "cách sửa lỗi máy tính không bật được",
       "tra cứu điểm thi đại học", "thủ tục nhập quốc tịch Hàn Quốc", "ca sĩ nào hát bài này", "kê đơn thuốc huyết áp", "chuyển tiền ngân hàng qua app",
       "xin visa du học Mỹ", "hoàn thuế thu nhập cá nhân cuối năm", "thủ tục hải quan nhập khẩu ô tô", "so sánh iphone với samsung",
       "tư vấn đầu tư bitcoin", "viết code python đảo chuỗi", "bệnh tiểu đường ăn gì tốt", "đặt phòng khách sạn Đà Lạt",
       "kết quả bóng đá hôm qua", "bán nhà thì nộp thuế bao nhiêu phần trăm"]
CHAT = ["chào ad, mình mới biết trang này, ad khỏe hông", "hello bạn ơi", "xin chào, bạn là ai vậy", "alo alo ad ơi", "cảm ơn bạn nhiều nha",
        "dạ em cảm ơn ạ", "bạn tên gì thế", "hi ad, hôm nay khỏe không", "ok cảm ơn nha, tạm biệt", "chào buổi sáng ad", "ad ơi có đó không",
        "chào bạn, mình hỏi chút được hông", "tuyệt vời, cảm ơn ad", "bạn giúp được gì cho mình vậy", "hello ad, mới vô trang này lần đầu",
        "chào admin, bạn khỏe không nè", "thanks nha bot", "bye bye ad nhé", "ê bot, mày làm được gì z", "xin chào trợ lý"]


def build(split, n):
    conn = api.connect()
    rows = conn.execute("select p.proc_id, p.name, p.domain, coalesce(f.head,p.proc_id) head from procedures p left join families f on f.proc_id=p.proc_id "
                        "where p.status='active' and p.province is null and p.agency_levels like '%Xã/Phường%'").fetchall()
    rows = [x for x in rows if not set(x["domain"].split(";")) & {"Thuế", "Hải quan"} ]
    half = [x for x in rows if (hashlib.md5(x["name"].encode()).digest()[0] % 2 == 0) == (split == "train")]
    r = random.Random(SEEDS[split])
    by_dom = {}
    for x in half:
        by_dom.setdefault(x["domain"], []).append(x)
    pick = []
    doms = list(by_dom)
    r.shuffle(doms)
    while len(pick) < min(n, len(half)):      # phân tầng: lần lượt mỗi lĩnh vực lấy 1
        for d in doms:
            if by_dom[d]:
                pick.append(by_dom[d].pop(r.randrange(len(by_dom[d]))))
    prefixes = {}
    for x in rows:
        w = core(x["name"]).split()
        for k in range(6, 10):
            prefixes[fold(" ".join(w[:k]))] = prefixes.get(fold(" ".join(w[:k])), 0) + 1
    cases = []
    for x in pick[:n]:
        for _ in range(3):
            k, q = variant(x["name"], r, prefixes)
            cases.append((x, k, q))
    return cases


def run(split, n, show):
    conn = api.connect()
    idx = Index(conn)
    fam = {}
    for p in conn.execute("select p.proc_id, p.name, coalesce(f.head,p.proc_id) head from procedures p left join families f on f.proc_id=p.proc_id"):
        fam[p["proc_id"]] = (p["head"], fold(core(p["name"])))
    cases = build(split, n)
    ok = {}
    bad = []
    for x, k, q in cases:
        res = resolve(idx, [{"role": "user", "text": q}])
        top = next((s.proc_id for s in res.segments if s.proc_id), None)
        good = top is not None and (fam[top][0] == fam[x["proc_id"]][0] or fam[top][1] == fam[x["proc_id"]][1])
        a = ok.setdefault(k, [0, 0])
        a[0] += good
        a[1] += 1
        if not good:
            bad.append((k, q, x["name"][:70], top and fam[top][1][:50], res.segments[0].reason if res.segments else ""))
    tot = sum(v[0] for v in ok.values()), sum(v[1] for v in ok.values())
    print(f"[{split}] procs={len(cases)//3} cases={tot[1]} top1={100*tot[0]/tot[1]:.1f}%")
    print("   " + " | ".join(f"{k} {100*v[0]/v[1]:.0f}%({v[1]})" for k, v in sorted(ok.items())))
    for b in bad[:show]:
        print("   X", b)
    return 100 * tot[0] / tot[1]


def run_fixed():
    idx = Index(api.connect())
    o = [resolve(idx, [{"role": "user", "text": q}]) for q in OOS]
    leak = [(q, [s.proc_id for s in r.segments]) for q, r in zip(OOS, o) if any(s.proc_id for s in r.segments)]
    print(f"[oos] {len(OOS)-len(leak)}/{len(OOS)} chặn đúng")
    for l in leak:
        print("   LEAK", l, [(s.hits[0].name[:50], s.hits[0].score, s.hits[0].cov) for s in o[OOS.index(l[0])].segments if s.hits])
    c = [resolve(idx, [{"role": "user", "text": q}]) for q in CHAT]
    wrong = [q for q, r in zip(CHAT, c) if not r.chitchat]
    print(f"[chitchat] {len(CHAT)-len(wrong)}/{len(CHAT)} đúng")
    for w in wrong:
        print("   MISS", w)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=450)
    ap.add_argument("--show", type=int, default=0)
    ap.add_argument("--splits", default="train,test")
    a = ap.parse_args()
    for s in a.splits.split(","):
        run(s, a.n, a.show)
    run_fixed()
