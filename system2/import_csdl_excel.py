# -*- coding: utf-8 -*-
"""import_csdl_excel.py — Nạp dữ liệu từ CSDL_THU_TUC_HANH_CHINH.xlsx vào procedures.db
Lọc các thủ tục thuộc 38 lĩnh vực tương đương 14 nhóm lĩnh vực của dataset cũ
theo đúng chỉ đạo của Leader.
"""
import sys
import sqlite3
from pathlib import Path
import openpyxl
from collections import defaultdict

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
ROOT_DIR = HERE.parent
DATA_EXCEL = ROOT_DIR / "data" / "CSDL_THU_TUC_HANH_CHINH.xlsx"
DB_PATH = HERE / "db" / "procedures.db"

# Thêm đường dẫn để dùng các helper của importer
sys.path.insert(0, str(HERE))
import importer

# 38 Lĩnh vực chuẩn quốc gia tương ứng 14 nhóm nghiệp vụ cũ
CANDIDATE_DOMAINS = {
    # 1. Giao thông / Đường bộ
    "Đường bộ",
    "Đăng ký, quản lý phương tiện giao thông cơ giới, xe máy chuyên dùng",
    "Sát hạch, cấp giấy phép lái xe",

    # 2. Đất đai & Đô thị & Xây dựng
    "Đất đai",
    "Nhà ở và công sở",
    "Hoạt động xây dựng",
    "Hạ tầng kỹ thuật",
    "Quy hoạch đô thị và nông thôn",
    "Phát triển đô thị",
    "Quản lý chất lượng công trình xây dựng",

    # 3. Hộ tịch & Tư pháp cơ sở
    "Hộ tịch",
    "Nuôi con nuôi",
    "Quốc tịch",
    "Chứng thực",
    "Công chứng, chứng thực",

    # 4. Chính sách & Bảo trợ xã hội
    "Người có công",
    "Bảo trợ xã hội",
    "Bảo hiểm xã hội",
    "Thực hiện chính sách BHXH",
    "Thực hiện chính sách BHYT",
    "Trẻ em",
    "Gia đình",
    "Dân số, Bà mẹ - Trẻ em",

    # 5. Lao động & Việc làm
    "Việc làm",
    "Lao động, tiền lương",
    "Lao động",
    "Lao động, tiền lương và bảo hiểm xã hội",
    "Việc làm (G07-LĐ11)",

    # 6. Giáo dục & Đào tạo
    "Giáo dục và Đào tạo thuộc hệ thống giáo dục quốc dân",
    "Giáo dục nghề nghiệp",
    "Giáo dục mầm non",
    "Giáo dục trung học",
    "Giáo dục tiểu học",

    # 7. Quản lý hành chính & ANTT & Kinh doanh
    "Cấp, quản lý căn cước",
    "Quản lý ngành nghề đầu tư, kinh doanh có điều kiện về an ninh, trật tự",
    "Thành lập và hoạt động doanh nghiệp (hộ kinh doanh)",
    "Quản lý xuất nhập cảnh",
    "Đăng ký, quản lý cư trú",
    "Đăng ký, quản lý con dấu",
    "thủ tục hành chính liên thông",
}


def run_etl(excel_file: Path, db_file: Path) -> None:
    if not excel_file.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {excel_file}")
    if not db_file.exists():
        raise FileNotFoundError(f"Không tìm thấy CSDL: {db_file}")

    print(f"Đang tải workbook '{excel_file.name}'...")
    wb = openpyxl.load_workbook(str(excel_file), data_only=True)

    # 1. Sheet Căn cứ pháp lý
    print("Đang đọc sheet 'Căn cứ pháp lý'...")
    sh_legal = wb["Căn cứ pháp lý"]
    legal_by_proc = defaultdict(list)
    for r in range(3, sh_legal.max_row + 1):
        pid = str(sh_legal.cell(r, 1).value or "").strip()
        so_hieu = str(sh_legal.cell(r, 3).value or "").strip()
        ten_vb = str(sh_legal.cell(r, 4).value or "").strip()
        if pid and (so_hieu or ten_vb):
            entry = f"{so_hieu} ({ten_vb})" if so_hieu and ten_vb else (so_hieu or ten_vb)
            legal_by_proc[pid].append(entry)

    # 2. Sheet Phí
    print("Đang đọc sheet 'Phí'...")
    sh_fee = wb["Phí"]
    fees_by_proc = defaultdict(list)
    for r in range(3, sh_fee.max_row + 1):
        pid = str(sh_fee.cell(r, 1).value or "").strip()
        loai = str(sh_fee.cell(r, 3).value or "Lệ phí").strip()
        so_tien = sh_fee.cell(r, 4).value
        mo_ta = str(sh_fee.cell(r, 5).value or "").strip()
        cach_nop = str(sh_fee.cell(r, 6).value or "").strip()
        if pid:
            amount_text = f"{so_tien:,} VNĐ" if isinstance(so_tien, (int, float)) else (str(so_tien or "") or mo_ta or "Theo quy định")
            condition = f"{mo_ta} ({cach_nop})" if mo_ta and cach_nop else (mo_ta or cach_nop or None)
            fees_by_proc[pid].append({
                "fee_type": loai,
                "amount_text": amount_text,
                "condition": condition,
            })

    # 3. Sheet Checklist
    print("Đang đọc sheet 'Checklist'...")
    sh_check = wb["Checklist"]
    checklists_by_proc = defaultdict(list)
    for r in range(3, sh_check.max_row + 1):
        pid = str(sh_check.cell(r, 1).value or "").strip()
        step_num = sh_check.cell(r, 3).value or 1
        giay_to = str(sh_check.cell(r, 5).value or "").strip()
        ban_chinh = sh_check.cell(r, 8).value
        ban_sao = sh_check.cell(r, 9).value
        if pid and giay_to:
            notes = []
            if ban_chinh:
                notes.append(f"Bản chính: {ban_chinh}")
            if ban_sao:
                notes.append(f"Bản sao: {ban_sao}")
            checklists_by_proc[pid].append({
                "step_order": step_num if isinstance(step_num, int) else 1,
                "item_type": "giay_to_phai_nop",
                "content": giay_to,
                "note": "; ".join(notes) if notes else None,
            })

    # 4. Sheet Tệp đính kèm
    print("Đang đọc sheet 'Tệp đính kèm'...")
    sh_files = wb["Tệp đính kèm"]
    files_by_proc = defaultdict(list)
    for r in range(3, sh_files.max_row + 1):
        pid = str(sh_files.cell(r, 1).value or "").strip()
        ten_tep = str(sh_files.cell(r, 3).value or "").strip()
        duong_dan = str(sh_files.cell(r, 5).value or "").strip()
        if pid and ten_tep:
            files_by_proc[pid].append({
                "file_name": ten_tep,
                "download_url": duong_dan or "",
                "file_size": None,
            })

    # 5. Sheet Thủ tục & Lọc theo domain
    print("Đang đọc và lọc sheet 'Thủ tục'...")
    sh_proc = wb["Thủ tục"]
    valid_records = []
    
    for r in range(2, sh_proc.max_row + 1):
        pid = str(sh_proc.cell(r, 1).value or "").strip()
        province_raw = str(sh_proc.cell(r, 2).value or "").strip()
        name = str(sh_proc.cell(r, 3).value or "").strip()
        domain = str(sh_proc.cell(r, 4).value or "").strip()
        
        if not pid or not name or domain not in CANDIDATE_DOMAINS:
            continue
            
        agency_levels = str(sh_proc.cell(r, 6).value or "").strip()
        executing_agency = str(sh_proc.cell(r, 8).value or "").strip()
        receiving_address = str(sh_proc.cell(r, 9).value or "").strip()
        processing_time_text = str(sh_proc.cell(r, 10).value or "").strip()
        online_url = str(sh_proc.cell(r, 13).value or "").strip()
        has_online = str(sh_proc.cell(r, 14).value or "").strip()
        decision_date = sh_proc.cell(r, 23).value
        description = str(sh_proc.cell(r, 29).value or "").strip()

        province = None if (not province_raw or province_raw == "(toàn quốc)") else province_raw
        app_method = "Cả hai" if has_online == "CÓ" else "Trực tiếp"
        legal_text = "; ".join(legal_by_proc.get(pid, [])) or None

        rec = {
            "proc_code": pid,
            "name": name,
            "domain": domain,
            "level": agency_levels or None,
            "province": province,
            "description": description or None,
            "duration_desc": processing_time_text or None,
            "authority": executing_agency or None,
            "application_method": app_method,
            "receiving_location": receiving_address or None,
            "online_url": online_url or None,
            "meta_source": legal_text,
            "effective_date": str(decision_date) if decision_date else None,
            "expiration_date": None,
            "checklists": checklists_by_proc.get(pid, []),
            "fees": fees_by_proc.get(pid, []),
            "files": files_by_proc.get(pid, []),
        }
        valid_records.append(rec)

    print(f"\n=> Đã lọc được {len(valid_records)} thủ tục hợp lệ thuộc các lĩnh vực được chọn.")

    # 6. Ghi vào SQLite DB
    print(f"\nĐang nạp vào CSDL '{db_file}'...")
    conn = sqlite3.connect(str(db_file))
    try:
        # Xóa dữ liệu cũ (triggers tự động xóa FTS5 và các bảng phụ)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DELETE FROM procedures")
        conn.commit()

        # Nạp dữ liệu mới
        importer.import_batch(conn, valid_records)

        # Kiểm tra FTS5
        fts_count = conn.execute("SELECT COUNT(*) FROM procedures_fts").fetchone()[0]
        proc_count = conn.execute("SELECT COUNT(*) FROM procedures WHERE status='active'").fetchone()[0]
        chk_count = conn.execute("SELECT COUNT(*) FROM procedure_checklists").fetchone()[0]
        fee_count = conn.execute("SELECT COUNT(*) FROM procedure_fees").fetchone()[0]
        legal_count = conn.execute("SELECT COUNT(*) FROM procedures WHERE meta_source IS NOT NULL").fetchone()[0]

        print("\n" + "="*60)
        print("KẾT QUẢ NẠP CSDL THỦ TỤC HÀNH CHÍNH MỚI:")
        print(f"- Số thủ tục active: {proc_count}")
        print(f"- Số bản ghi FTS5:    {fts_count}")
        print(f"- Số checklist hồ sơ: {chk_count}")
        print(f"- Số biểu phí/lệ phí: {fee_count}")
        print(f"- Số thủ tục có luật: {legal_count}")
        print("="*60)
    finally:
        conn.close()


if __name__ == "__main__":
    run_etl(DATA_EXCEL, DB_PATH)
