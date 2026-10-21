"""Giới hạn số lượt hỏi theo vai trò (khách / người dân / cán bộ / dev), để một người không làm nghẽn cả máy chủ.

Đếm trong bộ nhớ tiến trình (không ghi DB; khởi động lại server thì đếm lại). Ba lớp:
  1. Lượt hỏi = một câu gửi cho AI / System 3 (tin mới, sửa tin, tạo lại): mỗi phút + mỗi ngày (theo lịch, làm mới lúc 0 giờ).
     Số lượt chỉnh ở ⚙ Cài đặt, nhóm "Giới hạn sử dụng" (LIMIT_*).
  2. Số câu đang trả lời cùng lúc (CONCURRENT): hàng chờ GPU có FRIENDLY_QUEUE_MAX chỗ cho CẢ máy; không chặn thì một người
     mở 20 tab gửi cùng lúc là chiếm hết hàng, người khác nhận "Hệ thống đang bận".
  3. Mọi yêu cầu API mỗi phút (API_PER_MIN): chống gọi dồn dập vào các API khác (danh sách, xuất tệp…).
Khách thêm hai lớp: theo IP (xoá cookie để lấy mã khách mới không được thêm lượt; GUEST_IP_FACTOR lần một khách vì cả nhà /
cả phòng có thể dùng chung một IP) và số phiên khách mới mỗi IP mỗi giờ (GUEST_NEW_PER_HOUR).
Test đặt S4_WARMUP=0 -> tắt (như đồng bộ ABI); bật riêng bằng S4_RATE_LIMIT=1, tắt riêng bằng S4_RATE_LIMIT=0.
"""
from __future__ import annotations
import os
import threading
import time
from collections import deque

from fastapi import HTTPException

from . import settings

CONCURRENT = {"guest": 1, "user": 1, "can_bo": 3, "dev": 5}
MAX_CHARS = {"guest": 1000, "user": 4000, "can_bo": 16000, "dev": 16000}
API_PER_MIN = {"guest": 60, "user": 300, "can_bo": 1200, "dev": 3000}
GUEST_IP_FACTOR = 5
GUEST_NEW_PER_HOUR = 20
_PREFIX = {"guest": "GUEST", "user": "USER", "can_bo": "CANBO", "dev": "DEV"}
_END = ('data: {"type": "done"', 'data: {"type": "error"')   # sự kiện SSE kết thúc câu trả lời (chat.py)


def on() -> bool:
    return os.environ.get("S4_RATE_LIMIT", os.environ.get("S4_WARMUP", "1")) == "1"


class Limited(HTTPException):
    def __init__(self, status: int, detail: str, wait: int = 0):
        super().__init__(status, detail, headers={"Retry-After": str(max(1, wait))} if wait else None)


class _Win:
    __slots__ = ("hits", "day", "n", "busy")

    def __init__(self):
        self.hits: deque[float] = deque()
        self.day, self.n, self.busy = "", 0, 0


_wins: dict[str, _Win] = {}
_lock = threading.Lock()


def _win(key: str, now: float) -> _Win:
    if len(_wins) > 50000:   # chặn phình bộ nhớ khi bị dò hàng loạt: bỏ các ô đã nguội
        for k in [k for k, w in _wins.items() if not w.busy and (not w.hits or now - w.hits[-1] > 3600) and w.day != _today(now)]:
            _wins.pop(k, None)
    return _wins.setdefault(key, _Win())


def _today(now: float) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(now))


def _to_midnight(now: float) -> int:
    t = time.localtime(now)
    return 86400 - (t.tm_hour * 3600 + t.tm_min * 60 + t.tm_sec)


def _wait(w: _Win, limit: int, now: float, span: int = 60) -> int:
    """Số giây phải chờ để còn chỗ trong cửa sổ `span` giây (0 = còn chỗ)."""
    while w.hits and now - w.hits[0] >= span:
        w.hits.popleft()
    return int(w.hits[0] + span - now) + 1 if len(w.hits) >= limit else 0


def _day(w: _Win, now: float) -> int:
    if w.day != _today(now):
        w.day, w.n = _today(now), 0
    return w.n


def limits(role: str) -> dict:
    p = _PREFIX.get(role, "USER")
    return {"per_min": settings.get(f"LIMIT_{p}_PER_MIN"), "per_day": settings.get(f"LIMIT_{p}_PER_DAY"),
            "concurrent": CONCURRENT.get(role, 1), "max_chars": MAX_CHARS.get(role, MAX_CHARS["user"])}


def _person(user: dict) -> str:
    return f"g:{user['guest']}" if user.get("role") == "guest" else f"u:{user['id']}"


class Ticket:
    """Một lượt hỏi đã được nhận. end(): câu trả lời xong (thả chỗ "đang trả lời"). refund(): lượt không chạy được (trả lại lượt)."""

    def __init__(self, keys: list[str], now: float):
        self.keys, self.now, self.busy = keys, now, True

    def end(self) -> None:
        with _lock:
            if self.busy:
                self.busy = False
                w = _wins.get(self.keys[0])
                if w and w.busy:
                    w.busy -= 1

    def refund(self) -> None:
        with _lock:
            for k in self.keys:
                w = _wins.get(k)
                if not w:
                    continue
                try:
                    w.hits.remove(self.now)
                except ValueError:
                    pass
                if w.day == _today(self.now) and w.n:
                    w.n -= 1
        self.end()


_NOOP = Ticket([""], 0.0)
_NOOP.busy = False


def begin_turn(user: dict, ip: str, n_chars: int = 0, now: float | None = None) -> Ticket:
    """Nhận một lượt hỏi hoặc ném Limited (429 / 413) kèm câu báo tiếng Việt và Retry-After."""
    if not on():
        return _NOOP
    now = time.time() if now is None else now
    role = user.get("role", "user")
    lim = limits(role)
    guest = role == "guest"
    if n_chars > lim["max_chars"]:
        raise Limited(413, f"Câu hỏi dài quá: tối đa {lim['max_chars']} ký tự mỗi câu"
                           + (" với khách. Đăng nhập để gửi câu dài hơn." if guest else ". Hãy tách thành vài câu ngắn hơn."))
    me = _person(user)
    keys = [me] + ([f"ip:{ip}"] if guest else [])
    with _lock:
        w = _win("chat:" + me, now)
        if w.busy >= lim["concurrent"]:
            raise Limited(429, "Câu trước của bạn vẫn đang được trả lời. Chờ trả lời xong (hoặc bấm Dừng) rồi gửi tiếp."
                          if lim["concurrent"] == 1 else f"Bạn đang có {w.busy} câu đang trả lời cùng lúc (tối đa {lim['concurrent']}). "
                          "Chờ một câu xong rồi gửi tiếp.", 5)
        wait = _wait(w, lim["per_min"], now)
        if wait:
            raise Limited(429, f"Bạn gửi hơi nhanh: tối đa {lim['per_min']} câu mỗi phút. Thử lại sau {wait} giây.", wait)
        if _day(w, now) >= lim["per_day"]:
            if guest:
                raise Limited(429, f"Bạn đã dùng hết {lim['per_day']} câu hỏi dành cho khách hôm nay. Đăng nhập hoặc đăng ký (miễn phí) "
                                   f"để hỏi tiếp: tài khoản được {limits('user')['per_day']} câu mỗi ngày.", _to_midnight(now))
            raise Limited(429, f"Bạn đã dùng hết {lim['per_day']} câu hỏi hôm nay. Lượt hỏi được làm mới lúc 0 giờ.", _to_midnight(now))
        wip = None
        if guest:
            wip = _win("chat:ip:" + ip, now)
            wait = _wait(wip, lim["per_min"] * GUEST_IP_FACTOR, now)
            if wait:
                raise Limited(429, f"Mạng của bạn đang có nhiều khách hỏi cùng lúc. Thử lại sau {wait} giây, hoặc đăng nhập để không bị giới hạn chung.",
                              wait)
            if _day(wip, now) >= lim["per_day"] * GUEST_IP_FACTOR:
                raise Limited(429, "Mạng của bạn đã dùng hết lượt hỏi dành cho khách hôm nay. Đăng nhập hoặc đăng ký (miễn phí) để hỏi tiếp.",
                              _to_midnight(now))
        for x in (w, wip):
            if x:
                x.hits.append(now)
                x.n += 1
        w.busy += 1
    return Ticket(["chat:" + k for k in keys], now)


async def guarded(ticket: Ticket, gen):
    """Bọc luồng SSE của chat.run: thả chỗ "đang trả lời" ngay khi có sự kiện done / error (luồng còn mở thêm tới 90 giây để báo
    bộ nhớ cập nhật) hoặc khi luồng đóng (bấm Dừng, mất mạng)."""
    try:
        async for ev in gen:
            yield ev
            if ev.startswith(_END):
                ticket.end()
    finally:
        ticket.end()
        await gen.aclose()


def api_hit(user: dict, ip: str, now: float | None = None) -> None:
    """Mọi yêu cầu API (đã đăng nhập hoặc khách). Quá API_PER_MIN trong một phút -> Limited 429."""
    if not on():
        return
    now = time.time() if now is None else now
    limit = API_PER_MIN.get(user.get("role"), API_PER_MIN["user"])
    with _lock:
        w = _win("api:" + _person(user), now)
        wait = _wait(w, limit, now)
        if wait:
            raise Limited(429, f"Quá nhiều yêu cầu trong một phút. Thử lại sau {wait} giây.", wait)
        w.hits.append(now)


def guest_new(ip: str, now: float | None = None) -> None:
    """Tạo phiên khách mới: tối đa GUEST_NEW_PER_HOUR lần mỗi IP mỗi giờ."""
    if not on():
        return
    now = time.time() if now is None else now
    with _lock:
        w = _win("new:" + ip, now)
        wait = _wait(w, GUEST_NEW_PER_HOUR, now, 3600)
        if wait:
            raise Limited(429, f"Tạo phiên khách quá nhiều lần. Thử lại sau {(wait + 59) // 60} phút hoặc đăng nhập.", wait)
        w.hits.append(now)


def usage(user: dict, now: float | None = None) -> dict:
    """Hạn mức của người này + số lượt đã dùng hôm nay (giao diện hiện "còn N câu hôm nay")."""
    now = time.time() if now is None else now
    lim = limits(user.get("role", "user"))
    with _lock:
        w = _wins.get("chat:" + _person(user))
        used = _day(w, now) if w else 0
    return {**lim, "used_today": used, "left_today": max(0, lim["per_day"] - used), "enforced": on()}


def reset() -> None:
    with _lock:
        _wins.clear()
