"""Domain (kế hoạch tuần tới 2c): chia hệ thống thành các lĩnh vực.

- Domain cứng (hard): không xoá được, luật riêng, chỉ dev thêm; có dataset dùng chung do dev tải lên, mọi người (được phép) cùng dùng.
- Domain mềm (soft): kiểu Friendly; user và dev thêm được. User tạo thì chỉ mình dùng. Dataset luôn là của riêng từng người
  và chỉ khi domain cho phép (user_upload; dev luôn được).
- Mỗi domain có thể thêm Guardrail: lời dặn gửi thẳng cho AI ngay trước khi soạn câu trả lời. Dataset của domain này không hiện ở domain khác.
- Dev chuyển mềm <-> cứng, khoá domain (chỉ dev và cán bộ dùng), khoá từng dataset. Domain 1 "Thủ tục" là System 3 (engine strict).
- Lĩnh vực cứng nào cũng tải thêm được dataset dùng chung (dev / cán bộ), bên cạnh dữ liệu cào / đồng bộ. Thủ tục có công tắc
  data_mode: "s3" = chỉ System 3 (DB thủ tục, mặc định) | "s4" = chỉ System 4 (pipeline Friendly trên dataset tải lên); không trộn.
"""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from . import datasets, db, profile

MAX_SOFT_PER_USER = 10


class DomainIn(BaseModel):
    name: str | None = None
    kind: str | None = None          # hard | soft (chỉ dev)
    guardrail: str | None = None
    locked: bool | None = None       # chỉ dev
    user_upload: bool | None = None  # chỉ dev
    profile: dict | None = None      # G4.3: hồ sơ lĩnh vực (người sửa được lĩnh vực); thay cả phần đã lưu
    data_mode: str | None = None     # chỉ lĩnh vực Thủ tục, chỉ dev/cán bộ: "s3" (System 3, DB thủ tục) | "s4" (System 4, dữ liệu tải lên)


class PinIn(BaseModel):
    pinned: bool


def staff(user: dict) -> bool:
    """Dev và cán bộ quản lý lĩnh vực + dữ liệu như nhau ở bảng điều khiển (⚙ Cài đặt và tài khoản vẫn chỉ dev)."""
    return user["role"] in db._ELEVATED


def can_edit(user: dict, d: dict) -> bool:
    return staff(user) or (d["kind"] == "soft" and d["owner_id"] == user["id"])


def can_upload(user: dict, d: dict) -> bool:
    """Lĩnh vực cứng (Thủ tục, ABI, …): dev / cán bộ tải THÊM bộ dữ liệu dùng chung, bên cạnh dữ liệu cào / đồng bộ (leader 19/10).
    ABI tìm chung dữ liệu đồng bộ + tệp tải thêm; Thủ tục chỉ dùng tệp tải lên khi ở chế độ System 4 (db.s4_mode)."""
    if staff(user):
        return True
    return d["kind"] == "soft" and bool(d["user_upload"])


def can_share(user: dict, d: dict) -> bool:
    """Đặt dataset "dùng chung" (mọi người dùng được lĩnh vực đều thấy, chỉ đọc): dev / cán bộ, ở lĩnh vực mềm không riêng ai.
    Lĩnh vực cứng vốn đã dùng chung mọi dataset; lĩnh vực mềm riêng của một người thì không chia sẻ."""
    return staff(user) and d["kind"] == "soft" and d["owner_id"] is None


def view(user: dict, d: dict) -> dict:
    ed = can_edit(user, d)
    return {"id": d["id"], "name": d["name"], "kind": d["kind"], "engine": d["engine"], "locked": bool(d["locked"]),
            "user_upload": bool(d["user_upload"]), "pinned": d.get("pinned", False), "mine": d["owner_id"] == user["id"],
            "builtin": d["id"] in db.BUILTIN_DOMAINS, "can_edit": ed, "can_delete": ed and d["kind"] == "soft" and d["id"] not in db.BUILTIN_DOMAINS,
            "can_upload": can_upload(user, d), "guardrail": d["guardrail"] if ed else "", "can_share": can_share(user, d),
            **({"data_mode": d.get("data_mode") or "s3"} if d["engine"] == "strict" else {}),
            **({"profile": profile.get(d), "profile_defaults": profile.defaults(d)} if ed and (d["engine"] != "strict" or db.s4_mode(d)) else {})}


def make_router() -> APIRouter:
    r = APIRouter(prefix="/s4/domains")

    def user_of(request: Request) -> dict:
        u = getattr(request.state, "user", None)
        if not u:
            raise HTTPException(401, "Cần đăng nhập")
        return u

    def get_usable(user: dict, did: int) -> dict:
        d = db.get_domain(did)
        if not d or not db.can_use_domain(user, d):
            raise HTTPException(404, "không có lĩnh vực này")
        return d

    def clean_name(user: dict, name: str, own_id: int | None = None) -> str:
        name = (name or "").strip()
        if not 1 <= len(name) <= 40:
            raise HTTPException(422, "Tên lĩnh vực 1–40 ký tự")
        if any(d["name"].casefold() == name.casefold() and d["id"] != own_id for d in db.visible_domains(user)):
            raise HTTPException(422, "Đã có lĩnh vực trùng tên")
        return name

    def clean_guardrail(g: str) -> str:
        g = (g or "").strip()
        if len(g) > 1000:
            raise HTTPException(422, "Guardrail tối đa 1000 ký tự")
        return g

    @r.get("")
    def list_domains(request: Request):
        u = user_of(request)
        return {"domains": [view(u, d) for d in db.visible_domains(u)]}

    @r.post("")
    def create(body: DomainIn, request: Request):
        u = user_of(request)
        dev = staff(u)
        kind = body.kind or "soft"
        if kind not in ("hard", "soft"):
            raise HTTPException(422, "kind phải là hard hoặc soft")
        if kind == "hard" and not dev:
            raise HTTPException(403, "Chỉ dev và cán bộ thêm được lĩnh vực cứng")
        if not dev:
            if db.run("SELECT COUNT(*) n FROM domains WHERE owner_id=?", (u["id"],), one=True)["n"] >= MAX_SOFT_PER_USER:
                raise HTTPException(422, f"Mỗi người tối đa {MAX_SOFT_PER_USER} lĩnh vực riêng")
            if body.locked or body.user_upload:
                raise HTTPException(403, "Chỉ dev và cán bộ đổi được khoá / quyền tải dữ liệu")
        name = clean_name(u, body.name or "")
        did = db.run("INSERT INTO domains(name,kind,engine,guardrail,locked,user_upload,owner_id) VALUES (?,?,?,?,?,?,?)",
                     (name, kind, "friendly", clean_guardrail(body.guardrail or ""), int(bool(body.locked)), int(bool(body.user_upload)),
                      None if dev else u["id"]))
        return {"domain": view(u, db.get_domain(did) | {"pinned": True}), "domains": [view(u, d) for d in db.visible_domains(u)]}

    @r.patch("/{did}")
    def patch(did: int, body: DomainIn, request: Request):
        u = user_of(request)
        d = get_usable(u, did)
        if not can_edit(u, d):
            raise HTTPException(403, "Bạn không sửa được lĩnh vực này")
        dev = staff(u)
        if (body.kind is not None or body.locked is not None or body.user_upload is not None or body.data_mode is not None) and not dev:
            raise HTTPException(403, "Chỉ dev và cán bộ đổi loại / khoá / quyền tải dữ liệu / nguồn dữ liệu")
        sets = {}
        if body.name is not None:
            if did == 1:
                raise HTTPException(422, "Lĩnh vực Thủ tục giữ nguyên tên")
            sets["name"] = clean_name(u, body.name, did)
        if body.guardrail is not None:
            sets["guardrail"] = clean_guardrail(body.guardrail)
        if body.data_mode is not None and body.data_mode != (d.get("data_mode") or "s3"):
            if d["engine"] != "strict":
                raise HTTPException(422, "Chỉ lĩnh vực Thủ tục có hai nguồn dữ liệu (System 3 / System 4)")
            if body.data_mode not in ("s3", "s4"):
                raise HTTPException(422, "data_mode phải là s3 hoặc s4")
            sets["data_mode"] = body.data_mode
        if body.profile is not None:
            if d["engine"] == "strict" and (sets.get("data_mode") or d.get("data_mode")) != "s4":
                raise HTTPException(422, "Lĩnh vực Thủ tục đang trả lời bằng luật System 3, không dùng hồ sơ này (chuyển sang System 4 trước)")
            try:
                sets["profile"] = json.dumps(profile.validate(body.profile, d), ensure_ascii=False)
            except ValueError as e:
                raise HTTPException(422, f"Hồ sơ lĩnh vực: {e}")
        if body.locked is not None:
            sets["locked"] = int(body.locked)
        if body.user_upload is not None:
            sets["user_upload"] = int(body.user_upload)
        if body.kind is not None and body.kind != d["kind"]:
            if body.kind not in ("hard", "soft"):
                raise HTTPException(422, "kind phải là hard hoặc soft")
            if did == 1 or d["engine"] in ("abi", "flm"):
                raise HTTPException(422, f"Lĩnh vực {d['name']} luôn là lĩnh vực cứng")
            if body.kind == "hard":   # dataset riêng của người dùng sẽ thành dùng chung: không cho (lộ dữ liệu cá nhân)
                n = db.run("SELECT COUNT(*) n FROM datasets x JOIN users y ON y.id=x.user_id WHERE x.domain_id=? AND y.role<>'dev'", (did,), one=True)["n"]
                if n:
                    raise HTTPException(422, f"Lĩnh vực có {n} bộ dữ liệu riêng của người dùng, xoá hoặc chuyển chúng trước khi đổi sang lĩnh vực cứng")
                sets["owner_id"] = None   # domain cứng dùng chung cho mọi người
            sets["kind"] = body.kind
        if sets:
            db.run(f"UPDATE domains SET {', '.join(k + '=?' for k in sets)} WHERE id=?", (*sets.values(), did))
        return {"domain": view(u, db.get_domain(did) | {"pinned": True}), "domains": [view(u, x) for x in db.visible_domains(u)]}

    @r.delete("/{did}")
    def delete(did: int, request: Request):
        u = user_of(request)
        d = get_usable(u, did)
        if d["kind"] == "hard" or did in db.BUILTIN_DOMAINS:
            raise HTTPException(403, "Lĩnh vực cứng / lĩnh vực có sẵn không xoá được")
        if not can_edit(u, d):
            raise HTTPException(403, "Bạn không xoá được lĩnh vực này")
        for ds in db.run("SELECT * FROM datasets WHERE domain_id=?", (did,), many=True):
            datasets.delete(ds)
        db.run("UPDATE conversations SET domain_id=2 WHERE domain_id=?", (did,))   # hội thoại cũ về Trò chuyện chung
        db.run("DELETE FROM domains WHERE id=?", (did,))
        return {"ok": True, "domains": [view(u, x) for x in db.visible_domains(u)]}

    @r.post("/{did}/pin")
    def pin(did: int, body: PinIn, request: Request):
        u = user_of(request)
        get_usable(u, did)
        db.run("INSERT INTO domain_pins(user_id,domain_id,pinned) VALUES (?,?,?) "
               "ON CONFLICT(user_id,domain_id) DO UPDATE SET pinned=excluded.pinned", (u["id"], did, int(body.pinned)))
        return {"domains": [view(u, x) for x in db.visible_domains(u)]}

    return r
