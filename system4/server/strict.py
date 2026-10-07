"""Tính năng kiểu ChatGPT cho Strict mode (NV4, 1A) — lớp thêm vào, KHÔNG đổi kiến trúc System 3.

System 3 nhớ ngữ cảnh trong từng hội thoại (thông tin đã kể, danh sách đánh số để "cái thứ hai" trỏ đúng). Vì vậy:
- Câu trả lời vẫn do System 3 tạo: System 4 gọi đúng API /chat của System 3 (gọi nội bộ, qua middleware như trình duyệt).
- Sửa tin / tạo lại = tạo một hội thoại System 3 mới (nhánh, ẩn khỏi danh sách), PHÁT LẠI các câu hỏi phía trước theo đúng
  thứ tự để System 3 dựng lại ngữ cảnh, rồi gửi câu đã sửa. Câu trả lời của các câu phát lại không hiện ra.
  Phát lại có thể mất vài giây mỗi câu khi bước AI của System 3 đang bật (đã chọn 1A).
- System 4 giữ cây tin nhắn (strict_nodes): mỗi nút trỏ tới một tin trong DB System 3; cùng cha = các phiên bản ‹ 1/2 ›.
- Hội thoại Strict có từ trước (chưa có cây) được dựng cây từ tin nhắn System 3 ở lần mở đầu tiên.
"""
from __future__ import annotations
import json

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel

from . import auth, db

RESET_TEXT = "Đã bắt đầu chủ đề mới"


class StrictChatIn(BaseModel):
    text: str
    root: str | None = None
    reply_to: int | None = None   # nút thẻ hỏi lại (tin trợ lý cuối) mà người dùng bấm lựa chọn


class NodeIn(BaseModel):
    node_id: int
    text: str | None = None
    value: int | None = None


def _node(nid: int) -> dict | None:
    return db.run("SELECT * FROM strict_nodes WHERE id=?", (nid,), one=True)


def _leaf(root: str) -> dict | None:
    r = db.run("SELECT leaf FROM strict_threads WHERE root=?", (root,), one=True)
    return _node(r["leaf"]) if r and r["leaf"] else None


def _set_leaf(root: str, nid: int) -> None:
    db.run("INSERT INTO strict_threads(root,leaf) VALUES (?,?) ON CONFLICT(root) DO UPDATE SET leaf=excluded.leaf", (root, nid))


def _add(root, parent, role, s3_cid, s3_mid, kind="", replied=False) -> int:
    return db.run("INSERT INTO strict_nodes(root,parent_id,role,kind,s3_cid,s3_mid,replied) VALUES (?,?,?,?,?,?,?)",
                  (root, parent, role, kind, s3_cid, s3_mid, 1 if replied else 0))


def _path(root: str, leaf: dict | None) -> list[dict]:
    nodes = {n["id"]: n for n in db.run("SELECT * FROM strict_nodes WHERE root=?", (root,), many=True)}
    out, cur = [], leaf["id"] if leaf else None
    while cur is not None and cur in nodes:
        out.append(nodes[cur]); cur = nodes[cur]["parent_id"]
    out.reverse()
    kids: dict = {}
    for n in nodes.values():
        kids.setdefault(n["parent_id"], []).append(n["id"])
    for n in out:
        n["versions"] = sorted(kids.get(n["parent_id"], [n["id"]]))
    return out


def make_router(app, s3_store) -> APIRouter:
    r = APIRouter(prefix="/s4/strict")

    def owner_check(request: Request, root: str) -> dict:
        u = getattr(request.state, "user", None)
        if not u:
            raise HTTPException(401, "Cần đăng nhập")
        if db.strict_owner(root) != u["id"] or not s3_store.conversation_exists(root):
            raise HTTPException(404, "conversation not found")
        return u

    def ensure_tree(root: str) -> None:
        """Hội thoại Strict cũ chưa có cây: dựng một nhánh thẳng từ tin nhắn System 3."""
        if db.run("SELECT 1 FROM strict_nodes WHERE root=? LIMIT 1", (root,), one=True):
            return
        parent = None
        for m in s3_store.get_messages(root):
            kind = "reset" if m["role"] == "assistant" and m["content"].startswith(RESET_TEXT) else ""
            parent = _add(root, parent, m["role"], root, m["id"], kind)
        if parent:
            _set_leaf(root, parent)

    def s3_message(cid: str, mid: int) -> dict | None:
        return next((m for m in s3_store.get_messages(cid) if m["id"] == mid), None)

    def view(root: str) -> list[dict]:
        path = _path(root, _leaf(root))
        cache: dict[str, dict] = {}
        out = []
        for n in path:
            if n["s3_cid"] not in cache:
                cache[n["s3_cid"]] = {m["id"]: m for m in s3_store.get_messages(n["s3_cid"])}
            m = cache[n["s3_cid"]].get(n["s3_mid"])
            if not m:
                continue
            out.append({**m, "id": n["id"], "node_id": n["id"], "versions": n["versions"], "feedback": n["feedback"],
                        "replied": bool(n["replied"])})
        return out

    async def s3(request: Request, method: str, url: str, body: dict | None = None) -> dict:
        """Gọi API System 3 trong cùng tiến trình, mang cookie của người dùng (qua middleware y như trình duyệt)."""
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://s3.internal", timeout=600,
                                     cookies={auth.COOKIE: request.cookies.get(auth.COOKIE, "")}) as c:
            resp = await c.request(method, url, json=body)
        if resp.status_code != 200:
            try:
                detail = resp.json().get("detail")
            except ValueError:
                detail = resp.text
            raise HTTPException(resp.status_code, detail or "System 3 lỗi")
        return resp.json()

    async def send(request: Request, cid: str | None, text: str, reply_mid: int | None) -> tuple[str, int, int]:
        """Gửi một câu cho System 3. Trả (hội thoại, id tin người dùng, id tin trợ lý)."""
        body = {"text": text, "conversation_id": cid}
        if reply_mid:
            body["reply_to"] = reply_mid
        res = await s3(request, "POST", "/chat", body)
        cid, amid = res["conversation_id"], res["message_id"]
        umid = max(m["id"] for m in s3_store.get_messages(cid) if m["role"] == "user" and m["id"] < amid)
        return cid, umid, amid

    async def replay(request: Request, root: str, path: list[dict]) -> str | None:
        """Phát lại các câu người dùng (và lệnh "chủ đề mới") của `path` vào một hội thoại System 3 mới. Trả id hội thoại đó."""
        cid, last_amid = None, None
        for n in path:
            if n["role"] == "user":
                m = s3_message(n["s3_cid"], n["s3_mid"])
                cid, _, last_amid = await send(request, cid, m["content"], last_amid if n["replied"] else None)
                db.run("INSERT OR IGNORE INTO strict_branch(cid,root) VALUES (?,?)", (cid, root))
            elif n["kind"] == "reset" and cid:
                await s3(request, "POST", f"/conversations/{cid}/reset_facts")
                last_amid = max(m["id"] for m in s3_store.get_messages(cid))
        return cid

    # ------------------------------------------------------------------ API
    @r.get("/{root}/messages")
    def messages(root: str, request: Request):
        owner_check(request, root)
        ensure_tree(root)
        return {"conversation_id": root, "messages": view(root)}

    @r.post("/chat")
    async def chat(body: StrictChatIn, request: Request):
        text = body.text.strip()
        if not text:
            raise HTTPException(422, "text rỗng")
        root, leaf = body.root, None
        if root:
            owner_check(request, root)
            ensure_tree(root)
            leaf = _leaf(root)
        reply_mid = None
        if body.reply_to and leaf and body.reply_to == leaf["id"] and leaf["role"] == "assistant":
            reply_mid = leaf["s3_mid"]   # chỉ thẻ hỏi lại cuối cùng bấm được (như System 3)
        cid, umid, amid = await send(request, leaf["s3_cid"] if leaf else None, text, reply_mid)
        root = root or cid
        un = _add(root, leaf["id"] if leaf else None, "user", cid, umid, replied=bool(reply_mid))
        an = _add(root, un, "assistant", cid, amid)
        _set_leaf(root, an)
        return {"conversation_id": root, "message_id": an}

    @r.post("/{root}/edit")
    async def edit(root: str, body: NodeIn, request: Request):
        """Sửa tin người dùng -> phiên bản mới: phát lại các câu trước nó vào nhánh mới rồi gửi câu đã sửa."""
        owner_check(request, root)
        n = _node(body.node_id)
        text = (body.text or "").strip()
        if not n or n["root"] != root or n["role"] != "user" or not text:
            raise HTTPException(422, "chỉ sửa được tin của người dùng, nội dung không được trống")
        parent = _node(n["parent_id"]) if n["parent_id"] else None
        before = _path(root, parent) if parent else []
        cid = await replay(request, root, before)
        cid, umid, amid = await send(request, cid, text, None)
        db.run("INSERT OR IGNORE INTO strict_branch(cid,root) VALUES (?,?)", (cid, root))
        db.set_strict_owner(cid, owner_check(request, root)["id"])
        un = _add(root, n["parent_id"], "user", cid, umid)
        an = _add(root, un, "assistant", cid, amid)
        _set_leaf(root, an)
        return {"conversation_id": root, "messages": view(root), "replayed": sum(1 for x in before if x["role"] == "user")}

    @r.post("/{root}/regenerate")
    async def regenerate(root: str, body: NodeIn, request: Request):
        """Tạo lại câu trả lời -> phiên bản mới (cùng câu hỏi)."""
        owner_check(request, root)
        a = _node(body.node_id)
        if not a or a["root"] != root or a["role"] != "assistant" or not a["parent_id"]:
            raise HTTPException(422, "chỉ tạo lại được câu trả lời của một câu hỏi")
        u = _node(a["parent_id"])
        if u["role"] != "user":
            raise HTTPException(422, "tin này không có câu hỏi đi kèm")
        parent = _node(u["parent_id"]) if u["parent_id"] else None
        before = _path(root, parent) if parent else []
        cid = await replay(request, root, before)
        last = max((m["id"] for m in s3_store.get_messages(cid) if m["role"] == "assistant"), default=None) if cid else None
        text = s3_message(u["s3_cid"], u["s3_mid"])["content"]
        cid, umid, amid = await send(request, cid, text, last if u["replied"] else None)
        db.run("INSERT OR IGNORE INTO strict_branch(cid,root) VALUES (?,?)", (cid, root))
        db.set_strict_owner(cid, owner_check(request, root)["id"])
        an = _add(root, u["id"], "assistant", cid, amid)
        _set_leaf(root, an)
        return {"conversation_id": root, "messages": view(root), "replayed": sum(1 for x in before if x["role"] == "user")}

    @r.post("/{root}/switch")
    def switch(root: str, body: NodeIn, request: Request):
        owner_check(request, root)
        n = _node(body.node_id)
        if not n or n["root"] != root:
            raise HTTPException(404, "message not found")
        best, todo = n["id"], [n["id"]]   # tới tin mới nhất trong nhánh của phiên bản được chọn
        while todo:
            cur = todo.pop()
            best = max(best, cur)
            todo += [x["id"] for x in db.run("SELECT id FROM strict_nodes WHERE parent_id=?", (cur,), many=True)]
        _set_leaf(root, best)
        return {"conversation_id": root, "messages": view(root)}

    @r.post("/{root}/reset")
    async def reset(root: str, request: Request):
        """"Bắt đầu chủ đề mới" trên nhánh đang xem."""
        owner_check(request, root)
        ensure_tree(root)
        leaf = _leaf(root)
        cid = leaf["s3_cid"] if leaf else root
        await s3(request, "POST", f"/conversations/{cid}/reset_facts")
        mid = max(m["id"] for m in s3_store.get_messages(cid))
        _set_leaf(root, _add(root, leaf["id"] if leaf else None, "assistant", cid, mid, "reset"))
        return {"conversation_id": root, "messages": view(root)}

    @r.post("/{root}/feedback")
    def feedback(root: str, body: NodeIn, request: Request):
        owner_check(request, root)
        n = _node(body.node_id)
        if not n or n["root"] != root or n["role"] != "assistant" or body.value not in (-1, 0, 1):
            raise HTTPException(422, "chỉ đánh giá câu trả lời, giá trị 1/-1/0")
        db.run("UPDATE strict_nodes SET feedback=? WHERE id=?", (body.value, n["id"]))
        return {"ok": True}

    @r.delete("/{root}")
    def delete(root: str, request: Request):
        owner_check(request, root)
        for b in db.strict_branches(root):
            s3_store.delete_conversation(b)
            db.forget_strict(b)
        s3_store.delete_conversation(root)
        db.forget_strict(root)
        return {"ok": True}

    @r.get("/{root}/export")
    def export(root: str, request: Request, format: str = "md"):
        """Xuất theo nhánh đang xem, dùng bộ xuất của System 3 (conv_export)."""
        owner_check(request, root)
        ensure_tree(root)
        import conv_export   # module của System 3 (server/), chỉ gọi hàm có sẵn
        conv = next((c for c in s3_store.list_conversations() if c["id"] == root), None)
        msgs = view(root)
        if format == "pdf":
            return Response(conv_export.to_print_html(conv, msgs), media_type="text/html; charset=utf-8")
        if format not in ("md", "json"):
            raise HTTPException(400, "format phải là md, json hoặc pdf")
        body = conv_export.to_markdown(conv, msgs) if format == "md" else conv_export.to_json(conv, msgs)
        mime = "text/markdown" if format == "md" else "application/json"
        return Response(body, media_type=f"{mime}; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{conv_export.filename(conv["title"], format)}"'})

    return r
