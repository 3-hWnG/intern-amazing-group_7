"""ingest.py — Nạp dữ liệu đa view vào ChromaDB và dựng chỉ mục BM25."""

from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple
import json
import os
import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _APP_DIR.parent
for _p in [str(_APP_DIR), str(_ROOT_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import re
from typing import Any, Dict, List, Tuple
import pandas as pd

from config import (
    CHROMA_SPACE, DATA_MERGED_PATH, DATASET_PATH, EMBED_MODEL_NAME,
    INDEX_META_PATH, USE_LEXICAL, USE_MULTI_VIEW
)
from models import Procedure
from retrieval import bm25_manager, embeddings, vectorstore


def clean_local_references(text: Any) -> str:
    """Loại bỏ triệt để các tên riêng địa phương (phường Tăng Nhơn Phú, Lê Văn Việt...) để chuẩn hóa."""
    if not text or pd.isna(text):
        return ""
    s = str(text).strip()
    patterns = [
        (r"Trung tâm Phục vụ [Hh]ành chính công [Pp]hường Tăng Nhơn [Pp]hú,?\s*(Địa chỉ:?\s*)?(số\s*)?29\s*Lê Văn Việt.*?(TP\.?HCM|Thành phố Hồ Chí Minh)?", "Bộ phận Một cửa của UBND Xã/Phường nơi cư trú"),
        (r"Phòng Văn hóa - Xã hội thuộc Ủy ban nhân dân phường Tăng Nhơn Phú \(Địa chỉ: Số 29, đường Lê Văn Việt.*?\)\.?", "UBND Xã/Phường nơi cư trú"),
        (r"Trung tâm Phục vụ [Hh]ành chính công phường Tăng Nhơn [Pp]hú", "Bộ phận Một cửa của UBND Xã/Phường nơi cư trú"),
        (r"TTPVHCC phường Tăng Nhơn Phú", "Bộ phận Một cửa của UBND Xã/Phường nơi cư trú"),
        (r"Tổ [Nn]ội vụ - Phòng Văn hóa - [Xx]ã hội phường Tăng Nhơn Phú", "Bộ phận Một cửa của UBND Xã/Phường nơi cư trú"),
        (r"tại phường Tăng Nhơn Phú", "tại UBND Xã/Phường nơi cư trú"),
        (r"phường Tăng Nhơn Phú", "UBND Xã/Phường nơi cư trú"),
        (r"29 Lê Văn Việt", "trụ sở UBND Xã/Phường nơi cư trú"),
        (r"Khám ở Bệnh viện Tâm thần\. Địa chỉ: 766 Võ Văn Kiệt.*?TP\.HCM\)?", "Khám tại cơ sở y tế có thẩm quyền theo quy định"),
    ]
    for pattern, repl in patterns:
        s = re.sub(pattern, repl, s, flags=re.IGNORECASE)
    return s.strip()


def load_dataset() -> pd.DataFrame:
    """Tự động ưu tiên data_merged.xlsx, nếu không có thì đọc dataset.xlsx."""
    if DATA_MERGED_PATH.exists():
        print(f"[*] Đọc dataset chính: {DATA_MERGED_PATH.name}")
        return pd.read_excel(DATA_MERGED_PATH)
    if DATASET_PATH.exists():
        print(f"[*] Đọc dataset fallback: {DATASET_PATH.name}")
        return pd.read_excel(DATASET_PATH)
    raise FileNotFoundError("Không tìm thấy data_merged.xlsx hoặc dataset.xlsx trong thư mục data/")


@lru_cache(maxsize=1)
def load_procedures() -> List[Procedure]:
    """Chuyển đổi DataFrame thành danh sách đối tượng Procedure chuẩn hóa."""
    df = load_dataset()
    # Chuẩn hóa tên cột
    col_map = {
        "ten_thu_tuc": "ten",
        "Tên thủ tục hành chính": "ten",
        "thanh_phan_ho_so": "ho_so",
        "Thành phần hồ sơ": "ho_so",
        "thoi_gian_text": "thoi_gian",
        "Thời gian giải quyết": "thoi_gian",
        "le_phi_text": "le_phi",
        "Lệ phí": "le_phi",
        "dia_diem": "dia_diem",
        "Địa điểm tiếp nhận hồ sơ trực tiếp (nếu có)": "dia_diem",
        "can_cu_phap_ly": "can_cu_phap_ly",
        "nguon_url": "nguon_url",
        "ma_thu_tuc": "ma_thu_tuc",
        "linh_vuc": "linh_vuc",
        "cap_thuc_hien": "cap_thuc_hien",
        "co_quan": "co_quan",
        "gio_cat_off": "gio_cat_off"
    }

    procedures = []
    for idx, row in df.iterrows():
        d = {}
        for c in df.columns:
            target_key = col_map.get(c, c)
            val = row[c]
            clean_str = clean_local_references(val)
            d[target_key] = clean_str

        ten = d.get("ten", "")
        if not ten:
            continue

        dia_diem = d.get("dia_diem", "").strip()
        if not dia_diem:
            dia_diem = "Bộ phận Một cửa của UBND Xã/Phường nơi cư trú (hoặc cơ quan có thẩm quyền theo quy định)"

        co_quan = d.get("co_quan", "").strip()
        if not co_quan:
            co_quan = d.get("cap_thuc_hien", "Cơ quan có thẩm quyền theo quy định")

        p = Procedure(
            row_id=idx,
            ten=ten,
            linh_vuc=d.get("linh_vuc", "Hành chính công"),
            cap_thuc_hien=d.get("cap_thuc_hien", "Cơ quan có thẩm quyền"),
            co_quan=co_quan,
            ho_so=d.get("ho_so", ""),
            thoi_gian=d.get("thoi_gian", ""),
            le_phi=d.get("le_phi", ""),
            dia_diem=dia_diem,
            gio_cat_off=d.get("gio_cat_off", ""),
            ghi_chu=d.get("ghi_chu_dia_phuong", ""),
            can_cu_phap_ly=d.get("can_cu_phap_ly", ""),
            nguon_url=d.get("nguon_url", ""),
            ma_thu_tuc=d.get("ma_thu_tuc", f"TT-{idx+1:03d}")
        )
        procedures.append(p)
    return procedures


def get_procedures_map() -> Dict[int, Procedure]:
    return {p.row_id: p for p in load_procedures()}


def build_views(procedures: List[Procedure]) -> Tuple[List[str], List[str], List[dict]]:
    ids, docs, metas = [], [], []
    for p in procedures:
        views = p.views() if USE_MULTI_VIEW else [("title", p.view_title())]
        for v_name, text in views:
            if not text.strip():
                continue
            ids.append(f"{p.row_id}::{v_name}")
            docs.append(text)
            metas.append({
                "row_id": p.row_id,
                "title": p.ten,
                "view": v_name,
                "field": p.linh_vuc,
                "cap_thuc_hien": p.cap_thuc_hien,
                "ma_thu_tuc": p.ma_thu_tuc,
            })
    return ids, docs, metas


def run_ingest() -> None:
    print("=== BẮT ĐẦU NẠP DỮ LIỆU ===")
    procedures = load_procedures()
    print(f"[*] Đã nạp {len(procedures)} thủ tục hành chính.")

    ids, docs, metas = build_views(procedures)
    print(f"[*] Đã tạo {len(ids)} góc nhìn (views) đa chiều.")

    print(f"[*] Đang mã hóa vector embeddings ({EMBED_MODEL_NAME})...")
    vectors = embeddings.encode(docs, batch_size=32, show_progress_bar=True).tolist()

    print(f"[*] Ghi vào ChromaDB (metric = {CHROMA_SPACE})...")
    collection = vectorstore.reset_collection()
    batch_size = 256
    for i in range(0, len(ids), batch_size):
        collection.add(
            ids=ids[i:i+batch_size],
            documents=docs[i:i+batch_size],
            embeddings=vectors[i:i+batch_size],
            metadatas=metas[i:i+batch_size]
        )
    print(f"[*] Đã lưu thành công {collection.count()} view vào ChromaDB.")

    if USE_LEXICAL:
        print("[*] Đang xây dựng chỉ mục BM25 (bỏ dấu tiếng Việt)...")
        bm25_manager.build_index(procedures)
        print("[*] Chỉ mục BM25 sẵn sàng.")

    # Ghi nhận trạng thái Index Meta
    meta_info = {
        "embed_model": EMBED_MODEL_NAME,
        "dim": len(vectors[0]) if vectors else 0,
        "space": CHROMA_SPACE,
        "multi_view": USE_MULTI_VIEW,
        "n_views": len(ids),
        "n_procedures": len(procedures),
        "built_at": datetime.now().isoformat()
    }
    INDEX_META_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_META_PATH.write_text(json.dumps(meta_info, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[*] Đã ghi nhận vân tay chỉ mục vào {INDEX_META_PATH.name}.")
    print("=== HOÀN TẤT NẠP DỮ LIỆU! ===")


if __name__ == "__main__":
    run_ingest()
