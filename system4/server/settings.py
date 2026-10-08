"""Đọc/ghi cài đặt System 4: mặc định trong config.py + ghi đè trong runtime/settings.json.

- get(key)            : giá trị đang dùng (ghi đè nếu có, không thì mặc định)
- save(values)        : nút "Lưu" -> ghi vào settings.json
- set_default(values) : nút "Đặt làm mặc định" -> ghi vào khối MẶC ĐỊNH của config.py (+ config.py.bak),
                        rồi bỏ các khoá đó khỏi settings.json
- reset(keys)         : nút "Về mặc định" -> bỏ ghi đè
Mọi giá trị được kiểm kiểu/giới hạn theo config.SETTINGS trước khi ghi.
"""
from __future__ import annotations
import json
import re
import shutil
import threading
from pathlib import Path

from . import config

CONFIG_FILE = Path(config.__file__)
_BEGIN = "# ==== MẶC ĐỊNH"
_END = "# ==== HẾT MẶC ĐỊNH"
_LINE = re.compile(r"^([A-Z][A-Z0-9_]*) = (.+)$")

SPECS = {s["key"]: s for s in config.SETTINGS}
_lock = threading.Lock()
_defaults = {k: getattr(config, k) for k in SPECS}
_overrides: dict | None = None


def _load_overrides() -> dict:
    global _overrides
    if _overrides is None:
        try:
            raw = json.loads(config.SETTINGS_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raw = {}
        _overrides = {}
        for k, v in raw.items():   # bỏ khoá lạ/giá trị hỏng thay vì làm sập server
            try:
                _overrides[k] = validate(k, v)
            except ValueError:
                pass
    return _overrides


def get(key: str):
    o = _load_overrides()
    return o[key] if key in o else _defaults[key]


def validate(key: str, value):
    s = SPECS.get(key)
    if not s:
        raise ValueError(f"không có cài đặt {key}")
    t = s["type"]
    if t == "rules":
        return _validate_rules(s, value)
    try:
        if t == "bool":
            if not isinstance(value, bool):
                raise ValueError
        elif t == "int":
            if isinstance(value, bool) or float(value) != int(float(value)):
                raise ValueError
            value = int(float(value))
        elif t == "float":
            if isinstance(value, bool):
                raise ValueError
            value = float(value)
        else:
            if not isinstance(value, str):
                raise ValueError
            value = value.strip()
            if not value and not s.get("optional"):
                raise ValueError
    except (TypeError, ValueError):
        raise ValueError(f"{s['label']}: giá trị không hợp lệ") from None
    if t == "choice" and value not in s["choices"]:
        raise ValueError(f"{s['label']}: phải là một trong {', '.join(s['choices'])}")
    if t in ("int", "float") and not (s.get("min", value) <= value <= s.get("max", value)):
        raise ValueError(f"{s['label']}: phải từ {s['min']} đến {s['max']}")
    return value


RULE_KINDS = ("block", "instruct", "replace")


def _validate_rules(spec: dict, value) -> list[dict]:
    """Danh sách guardrail: mỗi luật {name, enabled, kind, match, message}."""
    if not isinstance(value, list):
        raise ValueError(f"{spec['label']}: phải là danh sách luật")
    out = []
    for i, r in enumerate(value, 1):
        if not isinstance(r, dict):
            raise ValueError(f"Luật {i}: không hợp lệ")
        name, kind = str(r.get("name", "")).strip(), r.get("kind")
        match, msg = str(r.get("match", "")).strip(), str(r.get("message", "")).strip()
        if not name:
            raise ValueError(f"Luật {i}: cần tên")
        if kind not in RULE_KINDS:
            raise ValueError(f"Luật \"{name}\": loại phải là {', '.join(RULE_KINDS)}")
        if not msg:
            raise ValueError(f"Luật \"{name}\": cần nội dung (câu trả lời / lời dặn)")
        if kind != "instruct" and not match:
            raise ValueError(f"Luật \"{name}\": loại {kind} cần cụm từ để khớp")
        out.append({"name": name, "enabled": bool(r.get("enabled", True)), "kind": kind, "match": match, "message": msg})
    return out


def _clean(values: dict) -> dict:
    return {k: validate(k, v) for k, v in values.items()}


def _write_overrides(o: dict) -> None:
    config.SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = config.SETTINGS_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(config.SETTINGS_PATH)


def save(values: dict) -> None:
    clean = _clean(values)   # kiểm hết trước, lỗi thì không ghi gì
    with _lock:
        o = dict(_load_overrides())
        for k, v in clean.items():
            if v == _defaults[k]:
                o.pop(k, None)   # bằng mặc định thì không cần ghi đè
            else:
                o[k] = v
        _write_overrides(o)
        _overrides.clear(); _overrides.update(o)


def reset(keys: list[str]) -> None:
    with _lock:
        o = {k: v for k, v in _load_overrides().items() if k not in keys}
        _write_overrides(o)
        _overrides.clear(); _overrides.update(o)


def set_default(values: dict) -> None:
    clean = _clean(values)
    with _lock:
        text = CONFIG_FILE.read_text(encoding="utf-8")
        lines = text.split("\n")
        try:
            b = next(i for i, l in enumerate(lines) if l.startswith(_BEGIN))
            e = next(i for i, l in enumerate(lines) if l.startswith(_END))
        except StopIteration:
            raise ValueError("config.py thiếu khối MẶC ĐỊNH") from None
        seen = set()
        for i in range(b + 1, e):
            m = _LINE.match(lines[i])
            if m and m.group(1) in clean:
                lines[i] = f"{m.group(1)} = {clean[m.group(1)]!r}"
                seen.add(m.group(1))
        for k in clean:   # khoá chưa có dòng trong khối -> thêm vào cuối khối
            if k not in seen:
                lines.insert(e, f"{k} = {clean[k]!r}"); e += 1
        shutil.copy2(CONFIG_FILE, CONFIG_FILE.with_name(CONFIG_FILE.name + ".bak"))
        tmp = CONFIG_FILE.with_suffix(".tmp")
        tmp.write_text("\n".join(lines), encoding="utf-8")
        tmp.replace(CONFIG_FILE)
        _defaults.update(clean)
        for k, v in clean.items():
            setattr(config, k, v)
        o = {k: v for k, v in _load_overrides().items() if k not in clean}
        _write_overrides(o)
        _overrides.clear(); _overrides.update(o)


def describe() -> list[dict]:
    """Cho panel: mỗi cài đặt kèm giá trị đang dùng, mặc định, có đang ghi đè không."""
    o = _load_overrides()
    return [{**s, "value": get(k), "default": _defaults[k], "overridden": k in o,
             **({"options": ollama_models()} if k in ("FRIENDLY_MODEL", "THINK_MODEL") else {})} for k, s in SPECS.items()]


def ollama_models() -> list[str]:
    """Tên model có trong Ollama (cho ô chọn model ở panel Cài đặt); Ollama tắt/lỗi -> []."""
    try:
        import ollama
        return sorted(m.model for m in ollama.Client(host=config.OLLAMA_HOST, timeout=3).list().models)
    except Exception:
        return []
