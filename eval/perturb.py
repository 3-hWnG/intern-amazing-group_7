"""Phase 23a: bộ BIẾN ĐỔI CÂU (metamorphic). Lấy các ca ĐÃ ĐÚNG ở DEV (cases.jsonl split=dev) và ctx (cases_ctx.jsonl), áp nhiễu KHÔNG đổi nghĩa
(nhãn lượt, đánh số/gạch đầu dòng, ngoặc kép, emoji, lời đệm ạ/nhé/giúp mình/cho hỏi/dạ, VIẾT HOA, khoảng trắng/dấu câu thừa, dính chữ, bỏ dấu, trộn nhiều loại)
và yêu cầu top-1 + hành vi GIỮ NGUYÊN so với đầu ra của câu gốc. In tỉ lệ bất biến theo từng loại nhiễu và liệt kê ca hỏng.
Chạy: python perturb.py [--name x] [--k 1] [-v]      (PYTHONPATH=.. S3_USE_LLM=0)  Gate: bất biến >= 98%. Ghi results/perturb_<name>.json.
Nhiễu sinh theo seed cố định từ (id, loại, lần) nên chạy lại ra đúng bộ cũ; không dùng bộ mù."""
import argparse, json, os, random, re, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import answer_adapter  # noqa: E402

LABELS = ["Turn {n}: ", "Turn {n} - ", "Lượt {n}: ", "Câu {n}: ", "Câu hỏi {n}: ", "Câu hỏi: ", "Q: ", "Q{n}: ", "Q{n}) ", "User: ", "Người dùng: ", "Bạn: ", "Hỏi: ",
          "Khách: ", "Human: ", "[User] ", "(Turn {n}) ", "**Q:** ", "Question {n}: ", "Customer: "]
BULLETS = ["{n}. ", "{n}) ", "({n}) ", "- ", "* ", "• ", "> ", "{n}: ", "– ", "{n} - "]
QUOTES = [("“", "”"), ('"', '"'), ("'", "'"), ("«", "»"), ("`", "`")]
EMOJI = ["🙏", "😊", "😅", "🤔", "❓", "👍", "😢", "🙂", "🥺", "✨"]
POL_PRE = ["Dạ ", "Dạ cho hỏi ", "Cho mình hỏi ", "Cho hỏi ", "Xin hỏi ", "Alo ad ơi ", "Chào bạn, ", "Dạ cho em hỏi ", "Mình muốn hỏi ", "Ad ơi "]
POL_SUF = [" ạ", " nhé", " nha", " giúp mình với", " giúp mình nhé", " với ạ", " nhé ạ", " dạ", " giúp em với ạ"]
PUNCT_END = ["???", "!!", "...", " ?", "?!", ". .", " ??", "!!!"]


def _words(t):
    return t.split(" ")


def p_label(t, r, n, role="user"):
    return r.choice(LABELS).format(n=n) + t


def p_bullet(t, r, n):
    return r.choice(BULLETS).format(n=n) + t


def p_quote(t, r, n):
    a, b = r.choice(QUOTES)
    return a + t + b


def p_emoji(t, r, n):
    e, k = r.choice(EMOJI), r.randint(0, 2)
    return e + " " + t if k == 0 else t + " " + e if k == 1 else t + " " + e + e


def p_polite(t, r, n):
    t = t.strip()
    k = r.randint(0, 2)
    tail = re.search(r"[?.!]+$", t)
    core, end = (t[:tail.start()], tail.group(0)) if tail else (t, "")
    pre = r.choice(POL_PRE) if k in (0, 2) else ""
    if pre:
        core = core[:1].lower() + core[1:]
    suf = r.choice(POL_SUF) if k in (1, 2) else ""
    return pre + core + suf + end


def p_upper(t, r, n):
    return t.upper() if r.random() < 0.7 else t.title()


def p_space(t, r, n):
    w = _words(t.strip())
    out = []
    for x in w:
        out.append(x)
        out.append(r.choice([" ", "  ", "   ", "\t", " \n "]) if r.random() < 0.35 else " ")
    return r.choice(["  ", " ", "\n", "\t"]) + "".join(out[:-1]) + r.choice(["  ", " ", "   \n", ""])


def p_punct(t, r, n):
    k = r.randint(0, 2)
    t = t.strip()
    base = re.sub(r"[?.!]+$", "", t)
    if k == 0:
        return base + r.choice(PUNCT_END)
    if k == 1:           # dấu phẩy/chấm thừa NGAY TRƯỚC từ nối mệnh đề (không chen vào giữa một từ ghép/tên thủ tục: đó là đổi nghĩa chứ không phải nhiễu)
        w = base.split(" ")
        i = next((j for j, x in enumerate(w) if j and x.lower() in ("và", "còn", "thì", "nếu", "cho", "mà", "nhưng", "vậy")), len(w))
        if i < len(w):
            w[i - 1] += r.choice([",", " ,", ";", ",,"])
        return " ".join(w) + r.choice(["?", ".", ""])
    return base                      # bỏ dấu kết câu


def p_glue(t, r, n):
    """Dính chữ: nối 1-2 cặp từ liền kề (người gõ nhanh quên dấu cách)."""
    w = t.strip().split(" ")
    for _ in range(min(2, max(1, len(w) // 4))):
        if len(w) < 2:
            break
        i = r.randrange(len(w) - 1)
        w[i:i + 2] = [w[i] + w[i + 1]]
    return " ".join(w)


def p_nodau(t, r, n):
    import unicodedata
    s = unicodedata.normalize("NFD", t.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


BASIC = {"label": p_label, "bullet": p_bullet, "quote": p_quote, "emoji": p_emoji, "polite": p_polite, "upper": p_upper, "space": p_space, "punct": p_punct,
         "glue": p_glue, "nodau": p_nodau}
SURFACE = ["quote", "emoji", "polite", "upper", "space", "punct"]       # thứ tự không quan trọng; 'mixed' chọn 2-3 loại + nhãn


def apply(kind, turns, r):
    """-> turns mới. label/bullet: đánh nhãn MỌI lượt user (nhãn đánh số theo thứ tự lượt) và nhãn chữ cho lượt trợ lý; còn lại chỉ đổi câu cuối."""
    out, n = [], 0
    last = max(i for i, t in enumerate(turns) if t["role"] == "user")
    for i, t in enumerate(turns):
        if t["role"] == "user":
            n += 1
        txt = t["text"]
        if kind in ("label", "bullet") and t["role"] == "user":
            txt = BASIC[kind](txt, r, n)
        elif kind == "label" and t["role"] != "user" and r.random() < 0.5:
            txt = r.choice(["Assistant: ", "Bot: ", "Trợ lý: "]) + txt
        elif kind == "mixed" and i == last:
            ks = r.sample(SURFACE, r.randint(1, 3))
            for k in ks:
                txt = BASIC[k](txt, r, n)
            txt = BASIC[r.choice(["label", "bullet"])](txt, r, n) if r.random() < 0.6 else txt
        elif kind not in ("label", "bullet", "mixed") and i == last:
            txt = BASIC[kind](txt, r, n)
        out.append({"role": t["role"], "text": txt})
    return out


KINDS = list(BASIC) + ["mixed"]


def sig(o):
    return ([t["proc_id"] for t in o["tasks"] if t.get("proc_id")][:3], o["behavior"])


def correct(c, o, ctx):
    ex = c["expected"]
    acc = set(ex["tasks"][0]["acceptable_proc_ids"]) if ex["tasks"] else set()
    tops = [t["proc_id"] for t in o["tasks"] if t.get("proc_id")]
    if ctx:
        bad = set(ex.get("forbid_proc_ids") or [])
        return (bool(tops) and tops[0] in acc and not (set(tops) & bad)) if acc else (not (set(tops) & bad) and o["behavior"] != "clarify")
    return o["behavior"] == ex["behavior"] and (not acc or (bool(tops) and tops[0] in acc))


def load():
    cs = [json.loads(l) for l in open(os.path.join(HERE, "cases.jsonl"), encoding="utf-8")]
    out = [(c, False) for c in cs if c["split"] == "dev"]
    cx = [json.loads(l) for l in open(os.path.join(HERE, "cases_ctx.jsonl"), encoding="utf-8")]
    return out + [(c, True) for c in cx]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="x")
    ap.add_argument("--k", type=int, default=1, help="số biến thể mỗi (ca, loại nhiễu)")
    ap.add_argument("-v", action="store_true")
    ap.add_argument("--kinds", default="")
    a = ap.parse_args()
    kinds = [k for k in KINDS if not a.kinds or k in a.kinds.split(",")]
    by, bad, base_n = defaultdict(lambda: [0, 0]), [], 0
    for c, ctx in load():
        turns = c["turns"]
        if not turns or turns[-1]["role"] != "user":
            continue
        o = answer_adapter.adapter(turns)
        if not correct(c, o, ctx):
            continue                               # chỉ lấy ca đã đúng: lỗi sẵn có không tính vào bất biến
        base_n += 1
        s0 = sig(o)
        for kind in kinds:
            if kind == "nodau" and o["behavior"] == "apologize":
                continue                           # từ chối nhờ lệch dấu ("sổ" vs "so"): bỏ dấu làm mất bằng chứng ấy, không đòi bất biến
            for j in range(a.k):
                r = random.Random(f"{c['id']}|{kind}|{j}")
                pt = apply(kind, turns, r)
                o2 = answer_adapter.adapter(pt)
                ok = sig(o2) == s0
                by[kind][0] += ok
                by[kind][1] += 1
                if not ok:
                    bad.append(dict(id=c["id"], kind=kind, orig=turns[-1]["text"], noisy=pt[-1]["text"], base=s0, got=sig(o2), ctx=ctx,
                                    why=(o2.get("extra") or {}).get("ctx", {}).get("why", "")[:120], routes=(o2.get("extra") or {}).get("routes")))
    print(f"ca gốc đã đúng: {base_n} | biến thể mỗi loại: {a.k}")
    for kind in kinds:
        ok, n = by[kind]
        print(f"  {kind:8s} {100 * ok / max(n, 1):5.1f}% ({ok}/{n})")
    tot, n = sum(v[0] for v in by.values()), sum(v[1] for v in by.values())
    rate = 100 * tot / max(n, 1)
    print(f"BẤT BIẾN {rate:.2f}% ({tot}/{n})  [gate >= 98%: {'ĐẠT' if rate >= 98 else 'CHƯA ĐẠT'}]")
    for b in bad[:60 if not a.v else 10 ** 6]:
        print("  FAIL", b["kind"], b["id"], "|", repr(b["orig"][:60]), "->", repr(b["noisy"][:70]), "| gốc", b["base"], "| được", b["got"], "|", b["why"], b["routes"])
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    json.dump(dict(base=base_n, by={k: v for k, v in by.items()}, rate=rate, bad=bad), open(os.path.join(HERE, "results", f"perturb_{a.name}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
