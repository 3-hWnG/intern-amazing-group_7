"""Bản ghi thủ tục hành chính - NƠI DUY NHẤT biết về cấu trúc dataset.

Teammate thêm cột mới -> chỉ sửa file này và DATASET_COLUMNS trong config.py.
Phần còn lại của hệ thống chỉ làm việc với đối tượng `Procedure`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import pandas as pd

from config import DATASET_COLUMNS, DATASET_PATH
from domain.text import clean, truncate

# Mỗi thủ tục được đánh chỉ mục bằng NHIỀU "góc nhìn" (view).
# Lý do: baseline v0 cho thấy tên thủ tục bị phần "thành phần hồ sơ" nhấn chìm
# khi nhét tất cả vào MỘT vector - câu hỏi chứa sẵn tên thủ tục chỉ đạt R@1 0.57.
VIEW_TITLE = "title"        # chỉ tên + lĩnh vực -> khớp câu hỏi nêu tên
VIEW_SUMMARY = "summary"    # thời gian / lệ phí / nơi nộp -> khớp câu hỏi facet
VIEW_DOCS = "docs"          # thành phần hồ sơ -> khớp câu hỏi tình huống

VIEW_CHAR_LIMIT = 600       # ~200 token, an toàn với cả mô hình 256 token

_CAP_PATTERNS = [
    (re.compile(r"cấp trung ương|tại cục", re.IGNORECASE), "Trung ương"),
    (re.compile(r"cấp tỉnh", re.IGNORECASE), "Tỉnh"),
    (re.compile(r"cấp huyện", re.IGNORECASE), "Huyện"),
    (re.compile(r"cấp xã|phường|thị trấn", re.IGNORECASE), "Xã/Phường"),
]


def derive_cap(title: str, location: str = "") -> str:
    """Suy ra cấp thực hiện. Tạm thời moi từ tên thủ tục vì dataset chưa có cột."""
    blob = f"{title} {location}"
    for pattern, label in _CAP_PATTERNS:
        if pattern.search(blob):
            return label
    return ""


@dataclass
class Procedure:
    row_id: int                 # 0-based, khớp gold_chroma_id của bộ eval
    ten: str
    linh_vuc: str = ""
    hinh_thuc_nop: str = ""
    ho_so: str = ""
    thoi_gian: str = ""
    le_phi: str = ""
    dia_diem: str = ""
    cap_thuc_hien: str = ""
    ma_thu_tuc: str = ""
    can_cu_phap_ly: str = ""
    nguon_url: str = ""
    extra: dict = field(default_factory=dict)

    # ---- các "góc nhìn" để đánh chỉ mục -----------------------------------
    def view_title(self) -> str:
        parts = [f"Thủ tục: {self.ten}"]
        if self.linh_vuc:
            parts.append(f"Lĩnh vực: {self.linh_vuc}")
        if self.cap_thuc_hien:
            parts.append(f"Cấp: {self.cap_thuc_hien}")
        return ". ".join(parts)

    def view_summary(self) -> str:
        parts = [self.ten]
        if self.thoi_gian:
            parts.append(f"Thời gian giải quyết: {self.thoi_gian}")
        if self.le_phi:
            parts.append(f"Lệ phí: {self.le_phi}")
        if self.dia_diem:
            parts.append(f"Nộp tại: {self.dia_diem}")
        if self.hinh_thuc_nop:
            parts.append(f"Hình thức nộp: {self.hinh_thuc_nop}")
        return truncate(". ".join(parts), VIEW_CHAR_LIMIT)

    def view_docs(self) -> str:
        if not self.ho_so:
            return ""
        return truncate(f"{self.ten}. Thành phần hồ sơ: {self.ho_so}", VIEW_CHAR_LIMIT)

    def views(self) -> list[tuple[str, str]]:
        out = [(VIEW_TITLE, self.view_title()), (VIEW_SUMMARY, self.view_summary())]
        docs = self.view_docs()
        if docs:
            out.append((VIEW_DOCS, docs))
        return out

    def lexical_text(self) -> str:
        """Một chuỗi duy nhất cho BM25 - gồm mọi trường có ích."""
        return " ".join(filter(None, [
            self.ten, self.ten,            # lặp tên để tăng trọng số
            self.linh_vuc, self.cap_thuc_hien, self.hinh_thuc_nop,
            self.ho_so, self.thoi_gian, self.le_phi, self.dia_diem,
        ]))

    def to_metadata(self) -> dict:
        return {
            "row_id": self.row_id,
            "ten": self.ten,
            "linh_vuc": self.linh_vuc,
            "cap_thuc_hien": self.cap_thuc_hien,
            "ma_thu_tuc": self.ma_thu_tuc,
        }


def _col(row, key: str) -> str:
    name = DATASET_COLUMNS.get(key)
    if not name:
        return ""
    try:
        return clean(row.get(name, ""))
    except AttributeError:
        return ""


def load_procedures(path: Path | None = None) -> list[Procedure]:
    df = pd.read_excel(path or DATASET_PATH)
    title_col = DATASET_COLUMNS["title"]
    df = df.dropna(subset=[title_col]).reset_index(drop=True)

    out: list[Procedure] = []
    for idx, row in df.iterrows():
        ten = clean(row[title_col])
        if not ten:
            continue
        dia_diem = _col(row, "location")
        out.append(Procedure(
            row_id=int(idx),
            ten=ten,
            linh_vuc=_col(row, "linh_vuc"),
            hinh_thuc_nop=_col(row, "hinh_thuc_nop"),
            ho_so=_col(row, "requirements"),
            thoi_gian=_col(row, "duration"),
            le_phi=_col(row, "fee"),
            dia_diem=dia_diem,
            cap_thuc_hien=derive_cap(ten, dia_diem),
            ma_thu_tuc=_col(row, "ma_thu_tuc"),
            can_cu_phap_ly=_col(row, "can_cu_phap_ly"),
            nguon_url=_col(row, "nguon_url"),
        ))
    return out


@lru_cache(maxsize=1)
def get_procedures() -> list[Procedure]:
    return load_procedures()


@lru_cache(maxsize=1)
def by_row_id() -> dict[int, Procedure]:
    return {p.row_id: p for p in get_procedures()}
