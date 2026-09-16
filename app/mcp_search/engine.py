"""Máy tìm kiếm phía sau MCP server — dựng Evidence Pack.

    truy vấn (do LLM sinh) ─┬─> tra web song song (ddgs / searxng / brave / tavily)
                            ├─> gộp + xếp hạng nguồn: chính thống > pháp luật > báo chí
                            │                          + thứ hạng + độ mới
                            ├─> đọc toàn văn top trang (trafilatura), lỗi -> dùng snippet
                            ├─> chia đoạn, BM25 chung trên mọi đoạn, lấy cụm đoạn liền nhau tốt nhất
                            └─> Evidence Pack: top_k nguồn, có ngân sách ký tự

Không có LLM ở đây: mô hình chỉ nhận Evidence Pack đã gọn, có URL, ngày đăng,
ngày truy xuất — dễ trình diễn, dễ gỡ lỗi.
"""

from __future__ import annotations

import re
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

import httpx

from config import (BLOCKED_DOMAINS, EVIDENCE_MAX_CHARS, EVIDENCE_SOURCE_CHARS,
                    EVIDENCE_TOP_K, FETCH_DEADLINE, FETCH_TIMEOUT, FETCH_TOP_N,
                    LEGAL_DOMAINS, NEWS_DOMAINS, OFFICIAL_DOMAINS, SEARCH_API_KEY,
                    SEARCH_CACHE_SECONDS, SEARCH_DDGS_BACKEND, SEARCH_DEADLINE,
                    SEARCH_MAX_QUERIES, SEARCH_OFFICIAL_ONLY, SEARCH_PROVIDER,
                    SEARCH_REGION, SEARCH_RESULTS_PER_QUERY, SEARCH_TIMEOUT,
                    SEARCH_TOTAL_BUDGET, SEARXNG_URL)
from domain.text import BM25

_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"),
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.5",
}
TRUST_WEIGHT = {"official": 3.0, "legal": 2.0, "news": 1.5, "other": 1.0}
TRUST_LABEL = {"official": "nguồn chính thống", "legal": "cơ sở dữ liệu pháp luật",
               "news": "báo chí", "other": "nguồn khác", "attachment": "tệp đính kèm"}

# ---------------------------------------------------------------- cache ----
_cache: dict[str, tuple[float, object]] = {}
_cache_lock = threading.Lock()


def _cached(key: str, fn):
    now = time.time()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < SEARCH_CACHE_SECONDS:
            return hit[1]
    value = fn()
    if value:                                   # không cache kết quả rỗng
        with _cache_lock:
            if len(_cache) > 500:
                for old in sorted(_cache, key=lambda k: _cache[k][0])[:100]:
                    _cache.pop(old, None)
            _cache[key] = (now, value)
    return value


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _log(log: list | None, text: str) -> None:
    if log is not None:
        log.append(text)


# ------------------------------------------------------------- nguồn -------
def host_of(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower().removeprefix("www.")
    except Exception:
        return ""


def _matches(host: str, domains: list[str]) -> bool:
    return any(host == d or host.endswith("." + d) for d in domains)


def trust_of(url: str) -> str:
    host = host_of(url)
    if not host or _matches(host, BLOCKED_DOMAINS):
        return "blocked"
    if _matches(host, OFFICIAL_DOMAINS):
        return "official"
    if _matches(host, LEGAL_DOMAINS):
        return "legal"
    if _matches(host, NEWS_DOMAINS):
        return "news"
    return "other"


def _norm_url(url: str) -> str:
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc.lower().removeprefix("www."),
                       p.path.rstrip("/"), "", p.query, ""))


_YEAR_RE = re.compile(r"(?<!\d)(20[0-4]\d)(?!\d)")


def _recency(text: str) -> float:
    """Năm mới nhất nhắc tới trong tiêu đề/snippet/URL/ngày đăng -> điểm cộng/trừ."""
    this_year = datetime.now().year
    years = [int(y) for y in _YEAR_RE.findall(text or "") if int(y) <= this_year]
    if not years:
        return 0.0
    newest = max(years)
    if newest >= this_year - 1:
        return 0.6
    if newest <= this_year - 3:
        return -0.8
    return 0.0


# ------------------------------------------------------ khởi động ấm ------
def warm_up() -> int:
    """Import sẵn thư viện đọc trang. Lần import đầu (venv mới, chưa có bytecode)
    có thể mất vài giây — nếu để tới lúc đọc trang thì mọi trang đều "quá hạn"."""
    started = time.time()
    try:
        import trafilatura  # noqa: F401
        from trafilatura.metadata import extract_metadata  # noqa: F401
        trafilatura.extract("<html><body><p>khởi động</p></body></html>")
    except Exception:
        pass
    return int((time.time() - started) * 1000)


# --------------------------------------------------- làm sạch kết quả -----
_MONTHS = "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
_MONTH_NO = {m: i for i, m in enumerate(_MONTHS.split("|"), 1)}
# "Mar 4, 2025 · ", "March 20, 2025 - " — tem ngày công cụ tìm kiếm gắn đầu snippet
_STAMP_RE = re.compile(rf"(?:^|(?<=\s))({_MONTHS})[a-z]*\.?\s+(\d{{1,2}}),\s+(20\d\d)\s*[·\-–]\s*")


def _stamp_date(m: re.Match) -> str:
    return f"{m.group(3)}-{_MONTH_NO[m.group(1)]:02d}-{int(m.group(2)):02d}"


def clean_snippet(snippet: str) -> tuple[str, str]:
    """-> (snippet, ngày đăng theo tem).

    ddgs đôi khi GỘP đoạn trích của nhiều bài (mỗi bài một tem ngày) vào một kết
    quả: mô hình đọc thấy mức phí 2023 và 2026 cạnh nhau rồi trộn sai. Chỉ giữ
    đoạn có tem ngày mới nhất.
    """
    snippet = (snippet or "").strip()
    stamps = list(_STAMP_RE.finditer(snippet))
    if not stamps:
        return snippet, ""
    first = stamps[0]
    if first.start() > 0 and len(snippet[:first.start()].strip()) > 40:
        # có chữ trước tem đầu tiên: đó là đoạn không tem, giữ phần đó
        return snippet[:first.start()].strip(), ""
    # tách theo tem, giữ đoạn MỚI NHẤT (thông tin thủ tục cũ hay đã bị thay thế)
    segments = []
    for i, m in enumerate(stamps):
        end = stamps[i + 1].start() if i + 1 < len(stamps) else len(snippet)
        text = snippet[m.end():end].strip()
        if text:
            segments.append((_stamp_date(m), text))
    if not segments:
        return "", _stamp_date(first)
    date, text = max(segments, key=lambda x: x[0])
    return text, date


def _clean_title(title: str) -> str:
    """Tiêu đề bị gộp kiểu "Bài A ...Bài B ...Bài C" -> "Bài A ..."."""
    parts = re.split(r"(?<=\.\.\.)(?=\S)|(?<=…)(?=\S)", title or "")
    return parts[0].strip() if parts else (title or "")


def plausible_date(value: str, retrieved_today: bool = True) -> str:
    """Bỏ ngày đăng không tin được: ở tương lai, hoặc đúng HÔM NAY (thư viện đọc
    ngày hay lấy ngày hiện tại khi trang không ghi ngày)."""
    value = str(value or "")[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return ""
    today = datetime.now().strftime("%Y-%m-%d")
    if value > today or (retrieved_today and value == today):
        return ""
    return value


# ----------------------------------------------------------- nhà cung cấp --
def _search_ddgs(query: str, n: int) -> list[dict]:
    from ddgs import DDGS
    rows = DDGS(timeout=SEARCH_TIMEOUT).text(query, region=SEARCH_REGION, max_results=n,
                                             backend=SEARCH_DDGS_BACKEND) or []
    return [{"title": r.get("title", ""), "url": r.get("href") or r.get("url", ""),
             "snippet": r.get("body", "")} for r in rows]


def _search_searxng(query: str, n: int) -> list[dict]:
    r = httpx.get(SEARXNG_URL.rstrip("/") + "/search", timeout=SEARCH_TIMEOUT,
                  params={"q": query, "format": "json", "language": "vi-VN"})
    r.raise_for_status()
    return [{"title": x.get("title", ""), "url": x.get("url", ""),
             "snippet": x.get("content", ""), "published_at": x.get("publishedDate") or ""}
            for x in r.json().get("results", [])[:n]]


def _search_brave(query: str, n: int) -> list[dict]:
    r = httpx.get("https://api.search.brave.com/res/v1/web/search", timeout=SEARCH_TIMEOUT,
                  params={"q": query, "count": min(n, 20), "search_lang": "vi"},
                  headers={"X-Subscription-Token": SEARCH_API_KEY, "Accept": "application/json"})
    r.raise_for_status()
    return [{"title": x.get("title", ""), "url": x.get("url", ""),
             "snippet": re.sub(r"<[^>]+>", "", x.get("description", "")),
             "published_at": x.get("page_age", "")}
            for x in (r.json().get("web") or {}).get("results", [])]


def _search_tavily(query: str, n: int) -> list[dict]:
    r = httpx.post("https://api.tavily.com/search", timeout=SEARCH_TIMEOUT,
                   headers={"Authorization": f"Bearer {SEARCH_API_KEY}"},
                   json={"query": query, "max_results": min(n, 20), "search_depth": "basic"})
    r.raise_for_status()
    return [{"title": x.get("title", ""), "url": x.get("url", ""),
             "snippet": x.get("content", ""), "published_at": x.get("published_date", "")}
            for x in r.json().get("results", [])]


PROVIDERS = {"ddgs": _search_ddgs, "searxng": _search_searxng,
             "brave": _search_brave, "tavily": _search_tavily}


def web_search(query: str, max_results: int = SEARCH_RESULTS_PER_QUERY,
               log: list | None = None) -> list[dict]:
    """Một truy vấn -> kết quả đã gắn tên miền + độ tin cậy, đã bỏ nguồn bị chặn."""
    query = (query or "").strip()
    if not query:
        return []
    provider = SEARCH_PROVIDER if SEARCH_PROVIDER in PROVIDERS else "ddgs"
    started = time.time()
    try:
        rows = _cached(f"s:{provider}:{max_results}:{query}",
                       lambda: PROVIDERS[provider](query, max_results))
    except Exception as exc:
        _log(log, f"[{provider}] {query!r} -> LỖI {type(exc).__name__}: {exc}")
        return []

    out, seen, blocked = [], set(), 0
    for rank, row in enumerate(rows or []):
        url = (row.get("url") or "").strip()
        if not url.startswith("http"):
            continue
        key = _norm_url(url)
        if key in seen:
            continue
        seen.add(key)
        trust = trust_of(url)
        if trust == "blocked":
            blocked += 1
            continue
        snippet, stamped = clean_snippet(row.get("snippet") or "")
        out.append({"title": _clean_title((row.get("title") or "").strip()), "url": url,
                    "snippet": snippet,
                    "published_at": plausible_date(row.get("published_at")) or stamped,
                    "domain": host_of(url), "trust": trust, "rank": rank})
    _log(log, f"[{provider}] {query!r} -> {len(out)} kết quả"
              + (f", bỏ {blocked} nguồn bị chặn" if blocked else "")
              + f" ({int((time.time() - started) * 1000)} ms)")
    return out


# ----------------------------------------------------------------- đọc trang -
def fetch_page(url: str, log: list | None = None) -> dict:
    """Tải trang + trích nội dung chính. Không bao giờ ném lỗi ra ngoài."""
    def get(verify: bool) -> httpx.Response:
        with httpx.Client(timeout=FETCH_TIMEOUT, follow_redirects=True,
                          headers=_HEADERS, verify=verify) as client:
            return client.get(url)

    def run() -> dict:
        insecure = False
        try:
            r = get(verify=True)
        except httpx.ConnectError as exc:
            if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
                raise
            # Nhiều trang .gov.vn cấu hình thiếu chứng chỉ trung gian. Ở đây chỉ
            # ĐỌC nội dung công khai nên thử lại không xác thực, và ghi rõ vào nhật ký.
            r, insecure = get(verify=False), True
        ctype = r.headers.get("content-type", "").split(";")[0]
        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code}")
        if "html" not in ctype and "text" not in ctype:
            raise RuntimeError(f"bỏ qua nội dung {ctype or 'không rõ'}")
        html = r.text[:3_000_000]

        import trafilatura
        text = trafilatura.extract(html, include_tables=True, include_comments=False,
                                   favor_recall=True, deduplicate=True) or ""
        published = ""
        try:
            from trafilatura.metadata import extract_metadata
            meta = extract_metadata(html)
            published = (meta.date or "") if meta else ""
        except Exception:
            pass
        return {"url": str(r.url), "text": text.strip(), "published_at": plausible_date(published),
                "insecure": insecure}

    started = time.time()
    try:
        page = _cached(f"p:{url}", run)
        _log(log, f"đọc {host_of(url)} -> {len(page['text'])} ký tự "
                  f"({int((time.time() - started) * 1000)} ms)"
                  + (" [chứng chỉ SSL lỗi, đọc không xác thực]" if page.get("insecure") else ""))
        return page
    except Exception as exc:
        # tên miền không phân giải được -> trang đã ngừng (vd. cổng tỉnh cũ sau sáp nhập)
        dead = isinstance(exc, httpx.ConnectError) and any(
            k in str(exc) for k in ("getaddrinfo", "Name or service not known",
                                    "nodename nor servname", "No address associated"))
        _log(log, f"đọc {host_of(url)} -> LỖI {exc} "
                  + ("(trang không truy cập được, bỏ nguồn)" if dead else "(dùng snippet)"))
        return {"url": url, "text": "", "published_at": "", "error": str(exc), "dead": dead}


# ------------------------------------------------------------- chọn đoạn ---
def _passages(text: str, size: int = 650) -> list[str]:
    """Gộp các dòng thành đoạn ~size ký tự, giữ nguyên thứ tự."""
    out, buf = [], ""
    for para in (p.strip() for p in re.split(r"\n+", text or "")):
        if not para:
            continue
        if buf and len(buf) + len(para) + 1 > size:
            out.append(buf)
            buf = para
        else:
            buf = f"{buf}\n{para}" if buf else para
        while len(buf) > size * 2:              # một dòng quá dài: cắt cứng
            out.append(buf[:size])
            buf = buf[size:]
    if buf:
        out.append(buf)
    return out


def _best_window(passages: list[str], scores: list[float], max_chars: int) -> tuple[str, float]:
    """Cụm đoạn LIỀN NHAU tốt nhất — danh sách hồ sơ / các bước hay trải qua nhiều đoạn."""
    if not passages:
        return "", 0.0
    best_i, best = 0, -1.0
    for i, s in enumerate(scores):
        window = s + 0.5 * (scores[i + 1] if i + 1 < len(scores) else 0.0)
        if window > best:
            best_i, best = i, window
    start = best_i - 1 if best_i > 0 and scores[best_i - 1] > 0.5 * scores[best_i] else best_i
    floor = 0.25 * scores[best_i]
    chosen, total = [], 0
    for j in range(start, len(passages)):
        if chosen and total + len(passages[j]) > max_chars:
            break
        # đoạn ngay sau đoạn tốt nhất luôn lấy (danh sách hồ sơ hay tràn sang);
        # xa hơn nữa thì dừng khi gặp đoạn không liên quan (tin khác trên trang)
        if j > best_i + 1 and scores[j] < floor:
            break
        chosen.append(passages[j])
        total += len(passages[j]) + 1
    return "\n".join(chosen)[:max_chars], max(best, 0.0)


# ---------------------------------------------------------- Evidence Pack --
def _parallel(fn, items: list, deadline: float, fallback, log: list, label: str,
              hard_limit: float | None = None) -> list:
    """Chạy song song với HẠN CHÓT chung: việc chậm nhất không được giữ cả lượt trả lời.

    Hết `deadline` mà CHƯA có kết quả dùng được nào thì chờ tiếp tới khi có một
    cái (tối đa `hard_limit`) — cắt hết thì người dùng chỉ nhận "không có nguồn".
    Việc quá hạn vẫn chạy nốt ở nền (kết quả vào cache cho lần sau) nhưng lượt
    này dùng `fallback` — ví dụ trang đọc chậm thì dùng snippet.
    """
    if not items:
        return []
    started = time.time()
    limit = max(deadline, hard_limit or deadline)
    pool = ThreadPoolExecutor(max_workers=len(items))
    futures = [pool.submit(fn, item) for item in items]
    done, pending = wait(futures, timeout=deadline)
    while pending and not any(f.result() for f in done) and time.time() - started < limit:
        more, pending = wait(pending, timeout=limit - (time.time() - started),
                             return_when=FIRST_COMPLETED)
        done |= more
    pool.shutdown(wait=False)
    out = []
    for fut, item in zip(futures, items):
        if fut in done:
            out.append(fut.result())
        else:
            name = item if isinstance(item, str) else host_of(item.get("url", ""))
            _log(log, f"{label} {name!r} -> quá hạn {deadline:g}s, bỏ qua")
            out.append(fallback(item))
    return out


def build_evidence_pack(question: str, queries: list[str] | None = None,
                        top_k: int = EVIDENCE_TOP_K) -> dict:
    started = time.time()
    log: list[str] = []
    question = (question or "").strip()
    queries = list(dict.fromkeys(q.strip() for q in (queries or []) if q and q.strip()))
    queries = queries[:SEARCH_MAX_QUERIES] or ([question] if question else [])
    pack = {"question": question, "queries": queries, "provider": SEARCH_PROVIDER,
            "retrieved_at": _now_iso(), "sources": [], "diagnostics": log, "error": ""}
    if not queries:
        pack["error"] = "không có truy vấn"
        return pack

    # 1. tra song song, gộp theo URL (truy vấn nào quá hạn thì bỏ, không chờ)
    merged: dict[str, dict] = {}
    def left() -> float:
        return SEARCH_TOTAL_BUDGET - (time.time() - started)

    batches = _parallel(lambda q: web_search(q, SEARCH_RESULTS_PER_QUERY, log), queries,
                        SEARCH_DEADLINE, lambda q: [], log, "tra",
                        hard_limit=max(SEARCH_DEADLINE, left()))
    if not any(batches) and left() > 5:
        # Nhà cung cấp miễn phí hay chặn khi dồn nhiều truy vấn song song -> thử lại
        # MỘT truy vấn đơn giản hơn (bỏ năm và toán tử site:, vốn làm hẹp kết quả).
        simple = re.sub(r"\s*\bsite:\S+", "", re.sub(r"\s*\b20\d\d\b", "", queries[0])).strip()
        _log(log, f"không có kết quả song song -> thử lại {simple!r}")
        rows = web_search(simple, SEARCH_RESULTS_PER_QUERY, log)
        if rows:
            batches = [rows]
    for rows in batches:
        for row in rows:
            base = (TRUST_WEIGHT[row["trust"]] + 1.0 / (1 + 0.35 * row["rank"])
                    + _recency(f"{row['title']} {row['snippet']} {row['url']}"))
            key = _norm_url(row["url"])
            if key in merged:                   # nhiều truy vấn cùng ra -> đáng tin hơn
                merged[key]["score"] = max(merged[key]["score"], base) + 0.3
            else:
                merged[key] = {**row, "score": base}
    ranked = sorted(merged.values(), key=lambda r: -r["score"])
    if SEARCH_OFFICIAL_ONLY:
        ranked = [r for r in ranked if r["trust"] == "official"]
    if not ranked:
        pack["error"] = "tra cứu không ra kết quả nào"
        pack["elapsed_ms"] = int((time.time() - started) * 1000)
        return pack

    # 2. đọc toàn văn các trang đứng đầu
    to_read = ranked[:max(1, FETCH_TOP_N)]
    pages = _parallel(lambda r: fetch_page(r["url"], log), to_read,
                      max(3.0, min(FETCH_DEADLINE, left())),
                      lambda r: {"url": r["url"], "text": "", "published_at": ""}, log, "đọc")

    # 3. chia đoạn + BM25 CHUNG để điểm liên quan so sánh được giữa các trang
    all_passages: list[str] = []
    spans = []
    alive = [(r, p) for r, p in zip(to_read, pages) if not p.get("dead")]
    if alive and len(alive) < len(to_read):
        to_read, pages = [r for r, _ in alive], [p for _, p in alive]
    for row, page in zip(to_read, pages):
        text = page.get("text") or ""
        fetched = len(text) >= 200
        passages = _passages(text if fetched else row["snippet"]) or [row["snippet"] or row["title"]]
        spans.append((row, page, fetched, len(all_passages), len(passages)))
        all_passages.extend(passages)
    scores = BM25(all_passages).scores(" ".join([question, *queries]))

    candidates = []
    for row, page, fetched, offset, count in spans:
        content, relevance = _best_window(all_passages[offset:offset + count],
                                          scores[offset:offset + count],
                                          EVIDENCE_SOURCE_CHARS)
        published = page.get("published_at") or row.get("published_at") or ""
        candidates.append({**row, "content": content, "relevance": relevance,
                           "fetched": fetched, "published_at": published,
                           "url": page.get("url") or row["url"]})
    top_rel = max(c["relevance"] for c in candidates) or 1.0
    for c in candidates:
        c["final"] = c["score"] + 2.0 * c["relevance"] / top_rel + 0.5 * _recency(c["published_at"])
    keep = [c for c in candidates if c["relevance"] >= 0.2 * top_rel] or candidates[:1]
    keep.sort(key=lambda c: -c["final"])

    # 4. đóng gói theo ngân sách ký tự
    used = 0
    for c in keep:
        room = EVIDENCE_MAX_CHARS - used
        if len(pack["sources"]) >= top_k or room < 300:
            break
        content = c["content"][:room]
        used += len(content)
        pack["sources"].append({
            "id": f"S{len(pack['sources']) + 1}",
            "title": c["title"] or c["domain"], "url": c["url"], "domain": c["domain"],
            "trust": c["trust"], "published_at": c["published_at"],
            "retrieved_at": pack["retrieved_at"], "snippet": c["snippet"][:300],
            "content": content, "fetched": c["fetched"], "score": round(c["final"], 2),
        })
    pack["elapsed_ms"] = int((time.time() - started) * 1000)
    log.append(f"=> {len(pack['sources'])} nguồn, {used} ký tự, {pack['elapsed_ms']} ms")
    return pack
