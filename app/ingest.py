import os
import sys
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
import torch
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

# Thiết lập đường dẫn tuyệt đối an toàn (chạy từ thư mục nào cũng chuẩn xác)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
ORIGINAL_PATH = os.path.join(DATA_DIR, "dataset.xlsx")
CRAWL_PATH = os.path.join(DATA_DIR, "data_crawl.xlsx")
MERGED_PATH = os.path.join(DATA_DIR, "data_merged.xlsx")
CHROMA_PATH = os.path.join(DATA_DIR, "chromadb")

CORE_COLUMNS = [
    'Tên thủ tục hành chính',
    'Lĩnh vực',
    'Hình thức nộp',
    'Thành phần hồ sơ',
    'Thời gian giải quyết',
    'Lệ phí',
    'Địa điểm tiếp nhận hồ sơ trực tiếp (nếu có)'
]

LOCATION_MAPPING = {
    'xác nhận tình trạng hôn nhân': 'Bộ phận Một cửa - UBND cấp xã/phường/thị trấn nơi thường trú',
    'nội quy lao động': 'Bộ phận Một cửa - Phòng Lao động - Thương binh và Xã hội (UBND cấp huyện) hoặc Sở LĐTBXH',
    'giấy phép xây dựng': 'Bộ phận Một cửa - UBND cấp huyện (Phòng Quản lý đô thị / Kinh tế - Hạ tầng)',
    'vay vốn hỗ trợ tạo việc làm': 'Phòng giao dịch Ngân hàng Chính sách xã hội (NHCSXH) cấp huyện hoặc Điểm giao dịch tại UBND xã',
    'thông báo khởi công': 'UBND cấp xã hoặc Đội Quản lý trật tự đô thị / Phòng Kinh tế - Hạ tầng cấp huyện',
    'đăng ký đất đai': 'Bộ phận Một cửa cấp huyện / Chi nhánh Văn phòng Đăng ký đất đai',
    'cấp số nhà': 'Bộ phận Một cửa - UBND cấp huyện (Phòng Quản lý đô thị / Kinh tế - Hạ tầng)',
    'vị trí nhà - đất': 'Bộ phận Một cửa - UBND cấp xã hoặc Chi nhánh Văn phòng Đăng ký đất đai',
    'tình trạng nhà ở': 'UBND cấp xã/phường/thị trấn nơi có nhà ở',
    'thông tin quy hoạch': 'Bộ phận Một cửa - UBND cấp huyện (Phòng Quản lý đô thị / Kinh tế - Hạ tầng)'
}

FEE_MAPPING = {
    'giấy phép xây dựng': 'Theo quy định của HĐND cấp tỉnh (khoảng 50.000 - 150.000 đồng/giấy phép)',
    'thành lập hộ kinh doanh': '100.000 đồng/lần (hoặc theo quy định của HĐND cấp tỉnh)',
    'thay đổi nội dung đăng ký hộ kinh doanh': '50.000 đồng/lần (hoặc theo quy định của HĐND cấp tỉnh)',
    'cấp lại giấy chứng nhận đăng ký hộ kinh doanh': '50.000 đồng/lần (hoặc theo quy định của HĐND cấp tỉnh)',
    'tạm ngừng kinh doanh': 'Miễn phí (Không thu lệ phí)',
    'chấm dứt hoạt động hộ kinh doanh': 'Miễn phí (Không thu lệ phí)',
    'thông báo khởi công': 'Miễn phí (Không thu lệ phí)',
    'thông tin quy hoạch': 'Miễn phí (cung cấp thông tin trực tiếp tại cơ quan có thẩm quyền)',
    'đăng ký đất đai': 'Theo quy định của HĐND cấp tỉnh (phí thẩm định hồ sơ và lệ phí cấp GCN quyền sử dụng đất)',
    'cấp số nhà': 'Theo quy định của HĐND cấp tỉnh',
    'vị trí nhà - đất': 'Miễn phí (hoặc phí đo đạc trích lục bản đồ theo quy định nếu có)',
    'tình trạng nhà ở': 'Miễn phí (Không thu lệ phí)',
    'chuyển trường': 'Miễn phí (Không thu lệ phí)',
    'học bổng chính sách': 'Miễn phí (Không thu lệ phí)',
    'khuyết tật': 'Miễn phí (Không thu lệ phí)',
    'nghĩa vụ quốc tế': 'Miễn phí (Không thu lệ phí)',
    'người có công': 'Miễn phí (Không thu lệ phí)',
    'liệt sĩ': 'Miễn phí (Không thu lệ phí)',
    'hỏa táng': 'Miễn phí (Không thu lệ phí)',
    'mai táng': 'Miễn phí (Không thu lệ phí)',
    'hưu trí xã hội': 'Miễn phí (Không thu lệ phí)'
}

DURATION_MAPPING = {
    'đăng ký đất đai': ('Không quá 30 ngày làm việc (Nghị định 101/2024/NĐ-CP)', 30),
    'cấp số nhà': ('Không quá 15 ngày làm việc (Thông tư 08/2024/TT-BXD)', 15),
    'học bổng chính sách': ('15 ngày làm việc xét duyệt (chi trả định kỳ theo học kỳ)', 15),
    'lưu trú': ('Giải quyết ngay trong ngày làm việc', 1),
}

import re

def clean_text(val):
    if pd.isna(val):
        return ""
    s = str(val).strip()
    s = re.sub(r'[\r\n\t]+', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def format_dossier_to_comma_separated(val) -> str:
    if not isinstance(val, str) or not val.strip():
        return str(val) if pd.notna(val) else ""
    lines = [l.strip() for l in val.splitlines() if l.strip()]
    cleaned_items = []
    for line in lines:
        c = re.sub(r'^([a-zA-ZđĐ]\)|\d+[\.\)]|[+\-*•])\s*', '', line).strip()
        c = re.sub(r'^[+\-*•\s]+', '', c).strip()
        c = c.rstrip(';.,').strip()
        if c and not any(c.lower().startswith(k) for k in ['thành phần hồ sơ', '+ thành phần hồ sơ', 'số lượng hồ sơ']):
            cleaned_items.append(c)
    if cleaned_items:
        return ", ".join(cleaned_items)
    return val.strip()

def enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for idx, row in df.iterrows():
        r = row.to_dict()
        # 1. Làm sạch Tên thủ tục (xóa \n thừa)
        orig_title = str(r.get('Tên thủ tục hành chính', ''))
        cleaned_title = clean_text(orig_title)
        r['Tên thủ tục hành chính'] = cleaned_title
        title_lower = cleaned_title.lower()

        # 2. Bổ sung Địa điểm tiếp nhận hồ sơ trực tiếp nếu bị trống
        orig_loc = r.get('Địa điểm tiếp nhận hồ sơ trực tiếp (nếu có)', '')
        if pd.isna(orig_loc) or str(orig_loc).strip() in ['', 'nan', 'None']:
            new_loc = None
            for kw, mapped_loc in LOCATION_MAPPING.items():
                if kw in title_lower:
                    new_loc = mapped_loc
                    break
            r['Địa điểm tiếp nhận hồ sơ trực tiếp (nếu có)'] = new_loc or "Bộ phận Một cửa - Cơ quan có thẩm quyền theo quy định"

        # 3. Chuẩn hóa Lệ phí
        orig_fee = r.get('Lệ phí', '')
        fee_str = clean_text(orig_fee)
        fee_lower = fee_str.lower()
        needs_fee_enrich = (
            fee_lower in ['0', 'không', 'không có', 'không đồng', 'theo quy định', 'nan', 'none', '']
            or fee_lower.startswith('không thu')
        )
        if needs_fee_enrich:
            new_fee = None
            for kw, mapped_fee in FEE_MAPPING.items():
                if kw in title_lower:
                    new_fee = mapped_fee
                    break
            if not new_fee:
                if fee_lower in ['0', 'không', 'không có', 'không đồng'] or fee_lower.startswith('không thu'):
                    new_fee = "Miễn phí (Không thu lệ phí)"
                elif 'theo quy định' in fee_lower:
                    new_fee = "Theo quy định của HĐND cấp tỉnh/thành phố hoặc Bộ Tài chính"
                else:
                    new_fee = "Miễn phí"
            r['Lệ phí'] = new_fee

        records.append(r)
    return pd.DataFrame(records)

NATIONAL_WARD_CODES = {
    'khai sinh': ('1.002824', 'Luật Hộ tịch 2014; Nghị định 123/2015/NĐ-CP; Thông tư 04/2020/TT-BTP'),
    'khai tử': ('1.002823', 'Luật Hộ tịch 2014; Nghị định 123/2015/NĐ-CP; Thông tư 04/2020/TT-BTP'),
    'kết hôn': ('1.002822', 'Luật Hộ tịch 2014; Luật Hôn nhân và gia đình 2014; Nghị định 123/2015/NĐ-CP'),
    'tình trạng hôn nhân': ('1.002821', 'Luật Hộ tịch 2014; Nghị định 123/2015/NĐ-CP; Thông tư 04/2020/TT-BTP'),
    'nhận cha mẹ con': ('1.002820', 'Luật Hộ tịch 2014; Nghị định 123/2015/NĐ-CP'),
    'nuôi con nuôi': ('1.002819', 'Luật Nuôi con nuôi 2010; Nghị định 19/2011/NĐ-CP'),
    'hộ kinh doanh': ('1.001205', 'Nghị định 01/2021/NĐ-CP về đăng ký doanh nghiệp; Thông tư 02/2023/TT-BKHĐT'),
    'giấy phép xây dựng': ('1.003412', 'Luật Xây dựng 2014 (sửa đổi 2020); Nghị định 15/2021/NĐ-CP'),
    'đăng ký đất đai': ('1.003450', 'Luật Đất đai 2024; Nghị định 101/2024/NĐ-CP; Nghị định 102/2024/NĐ-CP'),
    'chứng thực': ('1.002855', 'Nghị định 23/2015/NĐ-CP về cấp bản sao, chứng thực chữ ký, chứng thực hợp đồng'),
}

UNIFIED_COLUMNS = [
    'ma_thu_tuc',
    'ten_thu_tuc',
    'linh_vuc',
    'cap_thuc_hien',
    'co_quan',
    'thanh_phan_ho_so',
    'thoi_gian_text',
    'thoi_gian_ngay',
    'le_phi_text',
    'le_phi_vnd',
    'can_cu_phap_ly',
    'dia_diem',
    'gio_cat_off',
    'ghi_chu_dia_phuong',
    'nguon_url',
    'ngay_crawl'
]


def extract_thoi_gian_ngay(tg_text: str):
    if not tg_text or pd.isna(tg_text):
        return None
    s = str(tg_text).strip().lower()
    if any(k in s for k in ['trong ngày', 'tiếp nhận ngay', 'giải quyết ngay', 'ngay khi']):
        return 1
    nums = re.findall(r'\b\d+\b', s)
    if nums:
        return int(nums[-1])
    return None


def extract_le_phi_vnd(fee_text: str):
    if not fee_text:
        return None
    f_low = str(fee_text).lower()
    if 'miễn phí' in f_low or 'không thu' in f_low or 'không' in f_low:
        return 0
    m = re.search(r'(\d{1,3}(?:\.\d{3})+)\s*(?:đ|đồng|vnd)?', str(fee_text), re.IGNORECASE)
    if m:
        return int(m.group(1).replace('.', ''))
    return None


def load_and_prepare_dataset() -> pd.DataFrame:
    """
    Tự động chuẩn hóa Base Layer (crawled) và Local Overlay (ward form),
    hợp nhất thành bảng thống nhất và lưu vào data_merged.xlsx.
    """
    processed_records = []

    # 1. Đọc và chuẩn hóa dữ liệu cào (Base Layer) nếu có
    if os.path.exists(CRAWL_PATH):
        print(f"[*] Đang nạp dữ liệu cào Base Layer từ: {CRAWL_PATH}")
        df_crawl = pd.read_excel(CRAWL_PATH)
        for _, row in df_crawl.iterrows():
            r = row.to_dict()
            title_clean = clean_text(r.get('ten_thu_tuc', ''))
            title_lower = title_clean.lower()
            co_quan = str(r.get('co_quan', '')).strip()

            tg_text = clean_text(r.get('thoi_gian_text', ''))
            tg_ngay = r.get('thoi_gian_ngay')
            if pd.isna(tg_ngay) or tg_ngay is None:
                for kw, (d_txt, d_days) in DURATION_MAPPING.items():
                    if kw in title_lower:
                        if not tg_text or 'theo quy định' in tg_text.lower() or tg_text in ['nan', 'none']:
                            tg_text = d_txt
                        tg_ngay = d_days
                        break
            if pd.isna(tg_ngay) or tg_ngay is None:
                tg_ngay = extract_thoi_gian_ngay(tg_text)

            processed_records.append({
                'ma_thu_tuc': str(r.get('ma_thu_tuc', '')).strip(),
                'ten_thu_tuc': title_clean,
                'linh_vuc': clean_text(r.get('linh_vuc', 'Hành chính công')),
                'cap_thuc_hien': clean_text(r.get('cap_thuc_hien', 'Cấp Tỉnh')),
                'co_quan': co_quan,
                'thanh_phan_ho_so': format_dossier_to_comma_separated(r.get('thanh_phan_ho_so', '')),
                'thoi_gian_text': tg_text,
                'thoi_gian_ngay': tg_ngay,
                'le_phi_text': clean_text(r.get('le_phi_text', 'Miễn phí')),
                'le_phi_vnd': r.get('le_phi_vnd'),
                'can_cu_phap_ly': clean_text(r.get('can_cu_phap_ly', '')),
                'dia_diem': co_quan or 'Bộ phận Một cửa theo quy định',
                'gio_cat_off': 'Giờ hành chính (Thứ 2 - Thứ 6)',
                'ghi_chu_dia_phuong': '',
                'nguon_url': str(r.get('nguon_url', 'https://dichvucong.bocongan.gov.vn')).strip(),
                'ngay_crawl': str(r.get('ngay_crawl', datetime.now().strftime('%Y-%m-%d'))).strip()
            })

    # 2. Đọc và chuẩn hóa dữ liệu cấp phường (Local Overlay) nếu có
    if os.path.exists(ORIGINAL_PATH):
        print(f"[*] Đang nạp và ghép dữ liệu Local Overlay từ: {ORIGINAL_PATH}")
        df_orig = pd.read_excel(ORIGINAL_PATH)
        for idx, row in df_orig.iterrows():
            orig_title = clean_text(row.get('Tên thủ tục hành chính', ''))
            if not orig_title:
                continue
            title_lower = orig_title.lower()

            # Tìm mã thủ tục quốc gia và căn cứ pháp lý
            ma_tt = f"TP-{idx+1:03d}"
            can_cu = "Theo quy định pháp luật chuyên ngành hiện hành"
            for kw, (cd, leg) in NATIONAL_WARD_CODES.items():
                if kw in title_lower:
                    ma_tt = cd
                    can_cu = leg
                    break

            # Lệ phí
            raw_fee = clean_text(row.get('Lệ phí', ''))
            fee_lower = raw_fee.lower()
            new_fee = None
            for kw, mapped_fee in FEE_MAPPING.items():
                if kw in title_lower:
                    new_fee = mapped_fee
                    break
            if not new_fee:
                if fee_lower in ['0', 'không', 'không có', 'không đồng'] or fee_lower.startswith('không thu'):
                    new_fee = "Miễn phí (Không thu lệ phí)"
                elif 'theo quy định' in fee_lower:
                    new_fee = "Theo quy định của HĐND cấp tỉnh/thành phố hoặc Bộ Tài chính"
                else:
                    new_fee = raw_fee or "Miễn phí"

            fee_vnd = extract_le_phi_vnd(new_fee)

            # Địa điểm
            raw_loc = clean_text(row.get('Địa điểm tiếp nhận hồ sơ trực tiếp (nếu có)', ''))
            if not raw_loc or raw_loc.lower() in ['nan', 'none']:
                for kw, mapped_loc in LOCATION_MAPPING.items():
                    if kw in title_lower:
                        raw_loc = mapped_loc
                        break
                if not raw_loc:
                    raw_loc = "Bộ phận Một cửa - Cơ quan có thẩm quyền theo quy định"

            # Thời gian và giờ cắt hồ sơ
            raw_tg = clean_text(row.get('Thời gian giải quyết', ''))
            gio_cat = "Giờ hành chính (Thứ 2 - Thứ 6)"
            if re.search(r'sau 15 (?:giờ|h)', raw_tg, re.IGNORECASE):
                gio_cat = "Sau 15:00 tính sang ngày làm việc tiếp theo"

            tg_ngay = extract_thoi_gian_ngay(raw_tg)
            if tg_ngay is None:
                for kw, (d_txt, d_days) in DURATION_MAPPING.items():
                    if kw in title_lower:
                        raw_tg = d_txt
                        tg_ngay = d_days
                        break
            if not raw_tg:
                raw_tg = 'Trong ngày làm việc'
                if tg_ngay is None:
                    tg_ngay = 1

            ghi_chu = clean_text(row.get('Ghi chú', ''))

            processed_records.append({
                'ma_thu_tuc': ma_tt,
                'ten_thu_tuc': orig_title,
                'linh_vuc': clean_text(row.get('Lĩnh vực', 'Hộ tịch - Tư pháp')),
                'cap_thuc_hien': 'Cấp Xã',
                'co_quan': raw_loc,
                'thanh_phan_ho_so': format_dossier_to_comma_separated(row.get('Thành phần hồ sơ', '')),
                'thoi_gian_text': raw_tg or 'Trong ngày làm việc',
                'thoi_gian_ngay': tg_ngay,
                'le_phi_text': new_fee,
                'le_phi_vnd': fee_vnd,
                'can_cu_phap_ly': can_cu,
                'dia_diem': raw_loc,
                'gio_cat_off': gio_cat,
                'ghi_chu_dia_phuong': ghi_chu,
                'nguon_url': 'https://dichvucong.gov.vn',
                'ngay_crawl': datetime.now().strftime('%Y-%m-%d')
            })

    if not processed_records:
        raise FileNotFoundError(f"Không tìm thấy file dữ liệu nào tại {DATA_DIR}")

    df_unified = pd.DataFrame(processed_records)[UNIFIED_COLUMNS]
    # Khử trùng lặp theo tên thủ tục hoặc mã thủ tục (ưu tiên bản ghi sau)
    df_unified = df_unified.drop_duplicates(subset=['ten_thu_tuc'], keep='last')

    try:
        df_unified.to_excel(MERGED_PATH, index=False)
        print(f"[OK] Đã hợp nhất dữ liệu chuẩn hóa vào: {MERGED_PATH} ({len(df_unified)} thủ tục)")
    except PermissionError:
        print(f"[!] File {MERGED_PATH} đang mở trong Excel, sử dụng dữ liệu trong bộ nhớ để nạp ChromaDB.")

    return df_unified

def run_ingest():
    df = load_and_prepare_dataset()

    # Làm sạch dữ liệu
    df = df.dropna(subset=["ten_thu_tuc"])

    documents = []
    metadatas = []
    ids = []

    for idx, row in df.iterrows():
        ma_tt = str(row.get("ma_thu_tuc", "")).strip()
        title = str(row.get("ten_thu_tuc", "")).strip()
        field = str(row.get("linh_vuc", "Hành chính công")).strip()
        cap_th = str(row.get("cap_thuc_hien", "Cấp Tỉnh")).strip()
        co_quan = str(row.get("co_quan", "")).strip()
        reqs = str(row.get("thanh_phan_ho_so", "")).strip()
        time_text = str(row.get("thoi_gian_text", "")).strip()
        fee_text = str(row.get("le_phi_text", "")).strip()
        can_cu = str(row.get("can_cu_phap_ly", "")).strip()
        dia_diem = str(row.get("dia_diem", "")).strip()
        gio_cat = str(row.get("gio_cat_off", "")).strip()
        ghi_chu = str(row.get("ghi_chu_dia_phuong", "")).strip()
        nguon_url = str(row.get("nguon_url", "")).strip()
        
        update_timestamp = datetime.now().strftime("%Y-%m-%d")
        
        # Chunk 1: Chuyên về Thành phần hồ sơ & Căn cứ pháp lý
        doc_hoso = (
            f"Thủ tục: {title} (Mã TTHC: {ma_tt})\n"
            f"Lĩnh vực: {field} | Cấp thực hiện: {cap_th}\n"
            f"Căn cứ pháp lý: {can_cu}\n"
            f"Thành phần hồ sơ cần chuẩn bị:\n{reqs}\n"
            f"Nguồn tra cứu: {nguon_url}"
        )
        documents.append(doc_hoso)
        metadatas.append({
            "ma_thu_tuc": ma_tt,
            "title": title,
            "field": field,
            "cap_thuc_hien": cap_th,
            "can_cu_phap_ly": can_cu,
            "nguon_url": nguon_url,
            "chunk_type": "ho_so",
            "updated_at": update_timestamp
        })
        ids.append(f"{ma_tt}_{idx}_hoso")
        
        # Chunk 2: Chuyên về Lệ phí, Thời gian giải quyết & Địa điểm nộp địa phương
        doc_lephi = (
            f"Thủ tục: {title} (Mã TTHC: {ma_tt})\n"
            f"Lĩnh vực: {field} | Cấp thực hiện: {cap_th} | Cơ quan: {co_quan}\n"
            f"Thời gian giải quyết: {time_text}\n"
            f"Lệ phí: {fee_text}\n"
            f"Địa điểm tiếp nhận hồ sơ trực tiếp: {dia_diem}\n"
            f"Quy định tiếp nhận / Giờ cắt hồ sơ: {gio_cat}\n"
            f"Ghi chú địa phương: {ghi_chu}\n"
            f"Nguồn tra cứu: {nguon_url}"
        )
        documents.append(doc_lephi)
        metadatas.append({
            "ma_thu_tuc": ma_tt,
            "title": title,
            "field": field,
            "cap_thuc_hien": cap_th,
            "dia_diem": dia_diem,
            "gio_cat_off": gio_cat,
            "nguon_url": nguon_url,
            "chunk_type": "le_phi_thoi_gian",
            "updated_at": update_timestamp
        })
        ids.append(f"{ma_tt}_{idx}_lephi")

    print(f"Đã tạo {len(documents)} chunks từ {len(df)} thủ tục hành chính.")

    # Khởi tạo ChromaDB và làm mới collection
    print(f"Khởi tạo ChromaDB tại: {CHROMA_PATH}")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        client.delete_collection(name="legal_docs")
        print("Đã làm mới collection 'legal_docs' cũ.")
    except Exception:
        pass

    collection = client.get_or_create_collection(name="legal_docs")

    # Nạp mô hình embedding với GPU acceleration (nếu có)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading embedding model (device={device})...")
    model = SentenceTransformer("keepitreal/vietnamese-sbert", device=device)

    print("Đang tạo embeddings và lưu vào Vector Database...")
    embeddings = model.encode(documents, device=device).tolist()

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print(f"Hoàn thành! Đã nạp thành công {len(documents)} chunks vào ChromaDB với đầy đủ mã TTHC, căn cứ pháp lý và địa phương.")


if __name__ == '__main__':
    run_ingest()

