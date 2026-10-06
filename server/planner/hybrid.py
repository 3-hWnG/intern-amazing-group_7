"""Phase 19 — Planner HYBRID: kế hoạch LUẬT luôn có; Qwen3-4B đề xuất kế hoạch JSON, `merge` chỉ nhận đề xuất khi
confidence >= ngưỡng VÀ qua kiểm (thủ tục có trong kho, field hợp lệ, không phá quyết định hỏi lại/xin lỗi của Policy).
Quá hạn / lỗi / JSON hỏng -> giữ kế hoạch luật. Mọi bước ghi vào `Plan.llm_trace` (-> trace["planner_llm"]).
LLM không tự đưa số, không tạo thủ tục ngoài danh sách ứng viên của retrieval (nó chọn chỉ số `cand`, mã thật lấy từ retrieval)."""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutTimeout

MODES = ("rules", "hybrid")
EDITABLE = ("ask_field", "find_procedure", "check_condition")
_cfg: dict | None = None
_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="planner-llm")
_lock = threading.Lock()
_cache: dict | None = None


def _load_cfg() -> dict:
    global _cfg
    if _cfg is None:
        import config
        _cfg = {"mode": config.PLANNER_MODE if config.PLANNER_MODE in MODES else "rules",
                "timeout": config.PLANNER_LLM_TIMEOUT, "confidence": config.PLANNER_LLM_CONFIDENCE, "draft": config.PLANNER_LLM_DRAFT}
    return _cfg


def get_config() -> dict:
    return dict(_load_cfg())


def set_config(mode=None, confidence=None, timeout=None) -> dict:
    """Đổi trong bộ nhớ (POST /config khi S3_DEV=1, test, eval). Giá trị sai -> ValueError."""
    c = _load_cfg()
    if mode is not None:
        if mode not in MODES:
            raise ValueError(f"mode phải thuộc {MODES}")
        c["mode"] = mode
    if confidence is not None:
        if not 0.0 <= float(confidence) <= 1.0:
            raise ValueError("confidence phải trong [0,1]")
        c["confidence"] = float(confidence)
    if timeout is not None:
        if not 0.5 <= float(timeout) <= 30.0:
            raise ValueError("timeout phải trong [0.5,30] giây")
        c["timeout"] = float(timeout)
    return dict(c)


# ---------------------------------------------------------------- gọi LLM ----
def _cache_get(key: str):
    global _cache
    path = os.environ.get("S3_PLANNER_LLM_CACHE")
    if not path:
        return None
    with _lock:
        if _cache is None:        # ponytail: cache jsonl chỉ để ĐO (quét ngưỡng không gọi lại LLM); không dùng ở production
            _cache = {}
            if os.path.isfile(path):
                for line in open(path, encoding="utf-8"):
                    try:
                        r = json.loads(line)
                        _cache[r["key"]] = r
                    except Exception:
                        pass
        return _cache.get(key)


def _cache_put(key: str, rec: dict) -> None:
    path = os.environ.get("S3_PLANNER_LLM_CACHE")
    if path:
        with _lock:
            _cache[key] = {"key": key, **rec}
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"key": key, **rec}, ensure_ascii=False) + "\n")


def ask(system: str, msg: str, chat_json, timeout: float, num_predict: int, schema: dict) -> tuple[dict | None, dict]:
    """-> (raw|None, info{ms, timeout, error, cached}). Hết hạn tính theo đồng hồ thật (future.result), không chỉ timeout của httpx."""
    import config
    key = hashlib.sha1(f"{config.LLM_MODEL}|{system}|{msg}|{num_predict}".encode("utf-8")).hexdigest()
    hit = _cache_get(key)
    if hit is not None:        # phát lại: ms đã ghi; quá hạn hiện tại -> coi như timeout (quét timeout không cần gọi lại)
        if hit.get("error") or hit["ms"] > timeout * 1000:
            return None, {"ms": hit["ms"], "timeout": bool(hit.get("timeout")) or hit["ms"] > timeout * 1000, "error": hit.get("error", ""), "cached": True}
        return hit["raw"], {"ms": hit["ms"], "timeout": False, "error": "", "cached": True}
    t0 = time.perf_counter()
    fut = _pool.submit(chat_json, system, msg, schema=schema, think=False, timeout=timeout, num_predict=num_predict)
    raw, err, to = None, "", False
    try:
        raw = fut.result(timeout=timeout + 0.5)
    except FutTimeout:
        err, to = "timeout", True
    except Exception as exc:        # Ollama sập / httpx timeout (LLMError) -> giữ luật
        to = "timed out" in str(exc).lower() or "timeout" in str(exc).lower()
        err = f"{type(exc).__name__}: {exc}"[:160]
    ms = round((time.perf_counter() - t0) * 1000)
    if raw is not None and not (isinstance(raw, dict) and isinstance(raw.get("tasks"), list) and raw["tasks"]):
        err = err or "json_empty"
        raw = None
    _cache_put(key, {"raw": raw, "ms": ms, "error": err, "timeout": to})
    return raw, {"ms": ms, "timeout": to, "error": err, "cached": False}


# ----------------------------------------------------------------- hợp nhất --
def _summ(tasks) -> list:
    return [{"action": t.action, "proc": t.procedure_id, "fields": list(t.fields), "conditions": list(t.conditions)} for t in tasks]


def parse_tasks(raw: dict, cands: list[dict], last: str | None, conn, valid_fields) -> list[dict]:
    """Đề xuất của LLM -> [{action, pid, fields, bad}]. pid chỉ lấy từ danh sách ứng viên (cand) hoặc thủ tục đang nói (-2); ngoài ra pid=None."""
    out = []
    for r in (raw.get("tasks") or [])[:3]:
        if not isinstance(r, dict):
            continue
        c, pid = r.get("cand", -1), None
        if c == -2 and last:
            pid = last
        elif isinstance(c, int) and not isinstance(c, bool) and 0 <= c < len(cands):
            pid = cands[c]["proc_id"]
        if pid and not conn.execute("SELECT 1 FROM procedures WHERE proc_id=? AND status='active'", (pid,)).fetchone():
            pid = None                      # không có trong kho: bỏ
        fl = [f for f in (r.get("fields") or []) if isinstance(f, str)]
        out.append({"action": r.get("action"), "pid": pid, "fields": [f for f in dict.fromkeys(fl) if f in valid_fields],
                    "bad_fields": [f for f in fl if f not in valid_fields], "last": c == -2})
    return out


def _locked(t) -> str:
    """Task luật mà LLM không được đụng: quyết định hỏi lại/xin lỗi/ngữ cảnh/so sánh là của luật + Policy."""
    if t.action not in EDITABLE or not t.procedure_id:
        return "rule_" + (t.action if t.action not in EDITABLE else "no_procedure")
    if t.uncertain or t.ambiguous or t.near:
        return "rule_uncertain_or_near"
    if t.relation != "independent":
        return "rule_relation_" + t.relation
    return ""


def diff(rule_tasks: list, llm: list[dict]) -> list[dict]:
    """Các thay đổi LLM đề xuất so với luật (chưa quyết): edit_fields | edit_proc | add_task | delete_task. Mỗi loại tối đa 1 lần/kế hoạch cho add/delete."""
    ops, used_r, used_l = [], set(), set()
    for j, lt in enumerate(llm):                 # 1) cùng thủ tục -> so mục
        i = next((i for i, rt in enumerate(rule_tasks) if i not in used_r and lt["pid"] and rt.procedure_id == lt["pid"]), None)
        if i is None:
            continue
        used_r.add(i), used_l.add(j)
        if set(lt["fields"]) != set(rule_tasks[i].fields):
            ops.append({"op": "edit_fields", "task": i, "from": list(rule_tasks[i].fields), "to": lt["fields"], "bad_fields": lt["bad_fields"]})
    ur = [i for i in range(len(rule_tasks)) if i not in used_r]
    ul = [j for j in range(len(llm)) if j not in used_l]
    if not llm or all(l["pid"] is None for l in llm):
        return ops                               # LLM không chọn được thủ tục nào (ngoài phạm vi/-1): không có gì để sửa
    for i, j in zip(ur, ul):                     # 2) hai bên còn dư cùng số lượng -> LLM chọn thủ tục khác cho task i
        if llm[j]["pid"]:
            ops.append({"op": "edit_proc", "task": i, "from": rule_tasks[i].procedure_id, "to": llm[j]["pid"], "fields": llm[j]["fields"]})
    k = min(len(ur), len(ul))
    if len(ul) > k and llm[ul[k]]["pid"]:       # 3) LLM thêm ý
        ops.append({"op": "add_task", "task": len(rule_tasks), "to": llm[ul[k]]["pid"], "fields": llm[ul[k]]["fields"], "action": llm[ul[k]]["action"]})
    if len(ur) > k and all(llm[j]["pid"] for j in ul):    # 4) LLM bỏ ý (task thừa)
        ops.append({"op": "delete_task", "task": ur[k], "from": rule_tasks[ur[k]].procedure_id})
    return ops


def merge(rule_plan, ops: list[dict], conf: float, thr: float, conn, valid_fields, vet, label, mk_task) -> list[dict]:
    """Áp dụng TỪNG đề xuất lên rule_plan (sửa tại chỗ) nếu qua kiểm; trả danh sách quyết định [{..., accepted, reason}].
    vet(plan) -> (behavior, routes[]) chạy Policy trên kế hoạch; hành vi phải GIỮ NGUYÊN so với kế hoạch luật và task bị sửa phải route direct."""
    base_beh, _ = vet(rule_plan)
    for op in ops:
        op["accepted"], op["reason"] = False, ""
        if conf < thr:
            op["reason"] = f"confidence {conf:.2f} < ngưỡng {thr:.2f}"
        elif base_beh != "answer":
            op["reason"] = f"luật/Policy quyết '{base_beh}': không sửa"
        else:
            op["reason"] = _check(rule_plan, op, valid_fields)
        if op["reason"]:
            continue
        before = _snap(rule_plan)
        _apply(rule_plan, op, conn, label, mk_task)
        beh, routes = vet(rule_plan)
        if beh != base_beh or any(r != "direct" for r in routes):
            _restore(rule_plan, before)
            op["reason"] = f"Policy từ chối ({beh}: {','.join(routes)})"
            continue
        op["accepted"], op["reason"] = True, "ok"
    return ops


def _check(plan, op: dict, valid_fields) -> str:
    """Lý do TỪ CHỐI ('' = hợp lệ) theo luật + dữ liệu."""
    t = plan.tasks[op["task"]] if op["task"] < len(plan.tasks) else None
    if op["op"] == "add_task":
        if len(plan.tasks) >= 3:
            return "đã đủ 3 task"
        bad = [x for x in plan.tasks if _locked(x)]
        return f"kế hoạch luật có task khoá ({_locked(bad[0])})" if bad else ""
    lk = _locked(t)
    if lk:
        return f"task luật bị khoá ({lk})"
    if op["op"] == "edit_fields":
        if op["bad_fields"]:
            return f"field không hợp lệ {op['bad_fields']}"
        if not op["to"] and op["from"]:
            return "LLM bỏ hết mục luật đã bắt"
        if len(op["to"]) > 4:
            return "LLM liệt kê > 4 mục"
        if any(f not in valid_fields for f in op["to"]):
            return "field không hợp lệ"
    if op["op"] == "edit_proc" and t.refers_to == "last":
        return "thủ tục do ngữ cảnh (kế thừa) quyết"
    if op["op"] == "delete_task" and len(plan.tasks) < 2:
        return "không xoá task duy nhất"
    return ""


def _snap(plan):
    import copy
    return copy.deepcopy(plan.tasks)


def _restore(plan, snap):
    plan.tasks[:] = snap


def _apply(plan, op: dict, conn, label, mk_task) -> None:
    if op["op"] == "edit_fields":
        t = plan.tasks[op["task"]]
        t.fields = list(op["to"])
        t.action = "ask_field" if t.fields else "find_procedure"
        t.quantity = "amount" if "fees" in t.fields else ("duration" if "processing_time" in t.fields else "none")
    elif op["op"] == "edit_proc":
        t = plan.tasks[op["task"]]
        t.candidates = [op["to"]] + [c for c in t.candidates if c != op["to"]]
        t.procedure_id, t.procedure_label = op["to"], label(conn, op["to"])
    elif op["op"] == "add_task":
        plan.tasks.append(mk_task(op["to"], op["fields"], label(conn, op["to"])))
    elif op["op"] == "delete_task":
        del plan.tasks[op["task"]]
