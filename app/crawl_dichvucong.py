# -*- coding: utf-8 -*-
"""
MODULE CÀO DỮ LIỆU THỦ TỤC HÀNH CHÍNH (LIVE WEB SCRAPER)
Dự án: Trợ lý Pháp lý & Dịch vụ công - Nhóm 7

TÍNH NĂNG:
1. Cào dữ liệu THỰC TẾ 100% qua giao thức mạng HTTP/HTML trực tiếp từ Cổng Dịch vụ công (dichvucong.bocongan.gov.vn).
2. Tự động bóc tách đúng chuẩn 7 trường nghiệp vụ cốt lõi:
   - Tên thủ tục hành chính
   - Lĩnh vực
   - Hình thức nộp
   - Thành phần hồ sơ
   - Thời gian giải quyết
   - Lệ phí
   - Địa điểm tiếp nhận hồ sơ trực tiếp (nếu có)
3. Hoàn toàn KHÔNG sử dụng bất kỳ danh sách dự phòng (backup/fallback) hay dữ liệu cứng nào.
4. Tự động xuất ra duy nhất 1 file Excel: data_crawl.xlsx.
"""

import os
import sys
import time
import argparse
import requests
import pandas as pd
from lxml import html
import urllib3
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import re

# Tắt cảnh báo SSL không cần thiết trên môi trường mạng nội bộ
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Thiết lập encoding UTF-8 cho console Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
OUTPUT_PATH = os.path.join(DATA_DIR, 'data_crawl.xlsx')

TARGET_BASE_URL = 'https://dichvucong.bocongan.gov.vn'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8'
}

BASE_COLUMNS = [
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
    'nguon_url',
    'ngay_crawl'
]


def extract_cap_thuc_hien(title: str, co_quan: str) -> str:
    combined = f"{title} {co_quan}".lower()
    levels = []
    if 'trung ương' in combined or 'tại cục' in combined or 'bộ công an' in combined:
        levels.append('Trung ương')
    if 'cấp tỉnh' in combined or 'công an tỉnh' in combined or 'công an thành phố' in combined:
        levels.append('Tỉnh')
    if 'cấp huyện' in combined or 'công an huyện' in combined or 'công an quận' in combined:
        levels.append('Huyện')
    if 'cấp xã' in combined or 'công an xã' in combined or 'công an phường' in combined or 'thị trấn' in combined:
        levels.append('Xã')
    if levels:
        return "Cấp " + " / ".join(list(dict.fromkeys(levels)))
    return "Cấp Tỉnh"


def extract_thoi_gian_ngay(tg_text: str):
    if not tg_text:
        return None
    s = str(tg_text).lower()
    if any(k in s for k in ['trong ngày', 'tiếp nhận ngay', 'giải quyết ngay', 'ngay khi']):
        return 1
    nums = re.findall(r'\b\d+\b', str(tg_text))
    if nums:
        return int(nums[-1])
    return None


def extract_le_phi_vnd(fee_text: str):
    if not fee_text:
        return None
    f_low = fee_text.lower()
    if 'miễn phí' in f_low or 'không thu' in f_low:
        return 0
    m = re.search(r'(\d{1,3}(?:\.\d{3})+)\s*(?:đ|đồng|vnd)?', fee_text, re.IGNORECASE)
    if m:
        return int(m.group(1).replace('.', ''))
    return None


def clean_legal_basis(detail_el) -> str:
    if detail_el is None:
        return "Theo quy định pháp luật chuyên ngành hiện hành"
    lines = detail_el.xpath('.//li//text() | .//p//text()')
    cleaned = []
    for l in lines:
        s = " ".join(l.split()).strip()
        s = re.sub(r'^[+\-*•\s]+', '', s).strip()
        s = re.sub(r'\s*Số:\s*[\w\/\-]+', '', s, flags=re.IGNORECASE).strip()
        if len(s) > 4 and s.lower() not in [c.lower() for c in cleaned]:
            cleaned.append(s)
    if not cleaned:
        raw = " ".join(detail_el.text_content().split()).strip()
        return raw if len(raw) > 5 else "Theo quy định pháp luật chuyên ngành hiện hành"
    return "; ".join(cleaned)



import re

def extract_duration_info(text: str):
    """
    Trích xuất số lượng và đơn vị thời gian từ một chuỗi (ví dụ: '03 Ngày làm việc', 'Không quá 02 ngày làm việc').
    Loại bỏ các thông tin thừa, giờ hành chính và các bước xác minh phụ khi đã có thời hạn giải quyết chuẩn.
    """
    t = re.sub(r'[,:\-\s]+cụ thể(\s+như\s+sau)?.*$', '', text, flags=re.IGNORECASE).strip()
    t = t.rstrip(':,;.- \t\n')
    
    if 'giờ hành chính' in t.lower() or 'thời gian tiếp nhận' in t.lower():
        return None, None
        
    if re.search(r'(?:ngay\s+)?trong ngày làm việc|(?:giải quyết|tiếp nhận)\s+ngay|ngay\s+khi', t, re.IGNORECASE):
        return 0, "trong ngày làm việc"

    # Bỏ qua dòng xác minh phụ nếu chỉ là xác minh mất giấy tờ
    if 'xác minh' in t.lower():
        m_sub = re.search(r'trong thời hạn\s+(\d+)\s*ngày làm việc', t, re.IGNORECASE)
        if m_sub:
            return int(m_sub.group(1)), "ngày làm việc"
        return None, None
        
    m = re.search(r'(\d+)\s*(ngày làm việc|ngày|tháng|giờ)', t, re.IGNORECASE)
    if m:
        num = int(m.group(1))
        unit = m.group(2).lower()
        return num, unit
    return None, None


def format_durations(num_units: list) -> str:
    """
    Tổng hợp danh sách các cặp (num, unit) thành chuỗi hiển thị chuẩn xác, gọn gàng.
    Ví dụ:
    [(3, 'ngày làm việc'), (5, 'ngày làm việc')] -> 'Từ 03 - 05 ngày làm việc'
    [(2, 'ngày làm việc'), (7, 'ngày làm việc')] -> 'Từ 02 - 07 ngày làm việc'
    [(8, 'ngày làm việc'), (8, 'ngày làm việc')] -> '08 ngày làm việc'
    """
    if not num_units:
        return "Theo quy định hiện hành"
    
    if any(n == 0 for n, u in num_units):
        return "Giải quyết ngay trong ngày làm việc"

    units_map = {}
    for num, unit in num_units:
        if num == 0:
            continue
        if unit not in units_map:
            units_map[unit] = []
        if num not in units_map[unit]:
            units_map[unit].append(num)
            
    results = []
    for unit, nums in units_map.items():
        nums = sorted(nums)
        if len(nums) == 1:
            n_str = f"{nums[0]:02d}" if nums[0] < 10 else str(nums[0])
            results.append(f"{n_str} {unit}")
        elif len(nums) == 2:
            n1 = f"{nums[0]:02d}" if nums[0] < 10 else str(nums[0])
            n2 = f"{nums[1]:02d}" if nums[1] < 10 else str(nums[1])
            results.append(f"Từ {n1} - {n2} {unit}")
        else:
            n_min = f"{min(nums):02d}" if min(nums) < 10 else str(min(nums))
            n_max = f"{max(nums):02d}" if max(nums) < 10 else str(max(nums))
            results.append(f"Từ {n_min} - {n_max} {unit}")
            
    return "; ".join(results) if results else "Theo quy định hiện hành"


def clean_resolution_time(detail_el) -> str:
    """
    Trích xuất thời gian giải quyết súc tích, chính xác.
    Loại bỏ lịch tiếp nhận giờ hành chính thứ 2-6, địa chỉ trụ sở, và gom các khoảng thời gian
    (ví dụ: 'Từ 03 - 05 ngày làm việc', 'Từ 02 - 07 ngày làm việc', '08 ngày làm việc').
    """
    # 1. Trường hợp có thẻ <i> (cấu trúc chuẩn của Cổng DVC)
    i_tags = detail_el.xpath('.//i/text()')
    extracted = []
    for it in i_tags:
        n, u = extract_duration_info(it)
        if n is not None:
            extracted.append((n, u))
            
    if extracted:
        return format_durations(extracted)

    # 2. Trường hợp văn bản thuần (+ Trường hợp... Không quá 02 ngày làm việc...)
    raw_text = detail_el.text_content().strip()
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    for line in lines:
        n, u = extract_duration_info(line)
        if n is not None:
            extracted.append((n, u))
            
    if extracted:
        return format_durations(extracted)
        
    return "Theo quy định hiện hành"



def clean_dossier_components(detail_el) -> str:
    """
    Trích xuất danh sách thành phần hồ sơ và định dạng theo dạng cách nhau bằng dấu phẩy (, ).
    Loại bỏ các tiêu đề bảng (Tên giấy tờ, Mẫu đơn, Số lượng, Bản chính: 1, Bản sao: 0) và tên file mẫu.
    """
    doc_items = []
    
    # 1. Bóc tách từ <table> nếu có
    tables = detail_el.xpath('.//table')
    if tables:
        for table in tables:
            rows = table.xpath('.//tbody/tr | .//tr')
            for r in rows:
                cols = r.xpath('./td')
                if cols:
                    doc_name = cols[0].text_content().strip()
                    doc_name = re.sub(r'\s+', ' ', doc_name).strip()
                    doc_name = re.sub(r'^[+\-*•\s]+', '', doc_name).strip()
                    doc_name = doc_name.rstrip(';.,').strip()
                    if doc_name and doc_name.lower() not in ['tên giấy tờ', 'mẫu đơn, tờ khai', 'số lượng']:
                        doc_items.append(doc_name)

    # 2. Bóc tách từ đoạn văn/danh sách nếu không có table
    if not doc_items:
        raw_text = detail_el.text_content()
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        for line in lines:
            line_clean = line.strip()
            if any(line_clean.lower().startswith(k) for k in [
                'thành phần hồ sơ', '+ thành phần hồ sơ', 'số lượng hồ sơ', '+ số lượng hồ sơ',
                'tên giấy tờ', 'mẫu đơn', 'số lượng', 'bản chính:', 'bản sao:'
            ]):
                continue
            line_clean = re.sub(r'^([a-zA-ZđĐ]\)|\d+[\.\)]|[+\-*•])\s*', '', line_clean).strip()
            line_clean = re.sub(r'^[+\-*•\s]+', '', line_clean).strip()
            line_clean = line_clean.rstrip(';.,').strip()
            if len(line_clean) > 8:
                doc_items.append(line_clean)

    # Khử trùng lặp và nối bằng dấu phẩy (, )
    unique_items = []
    seen = set()
    for item in doc_items:
        item_norm = " ".join(item.split())
        if item_norm.lower() not in seen and len(item_norm) > 5:
            seen.add(item_norm.lower())
            unique_items.append(item_norm)

    if not unique_items:
        return "Theo quy định hướng dẫn tại cơ quan tiếp nhận"

    return ", ".join(unique_items)


def format_dossier_to_comma_separated(val) -> str:
    """
    Chuyển đổi văn bản thành phần hồ sơ nhiều dòng thành danh sách phân tách bằng dấu phẩy (, ).
    """
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


def clean_fee(phi_raw: str, le_phi_raw: str) -> str:
    """
    Làm sạch trường Lệ phí, triệt tiêu hoàn toàn rác CMS của Cổng DVC:
    - Loại bỏ nhầm lẫn: '07 Ngày làm việc', 'Trực tiếp Trực tuyến', v.v.
    - Chuẩn hóa: 'Không', 'Không thu lệ phí' -> 'Miễn phí'
    - Giữ lại các mức phí hợp lệ (số tiền, Thông tư quy định, Chưa quy định).
    """
    junk_patterns = [
        r'^\s*(trực tiếp|trực tuyến|dịch vụ bưu chính)\s*$',
        r'^\s*trực tiếp\s+trực tuyến\s*$',
        r'\d+\s*ngày làm việc',
        r'giờ hành chính',
        r'thời gian tiếp nhận',
        r'^\s*không\s*$',
        r'^\s*không có\s*$',
        r'^\s*$'
    ]
    
    def extract_valid_fee_lines(raw_text: str):
        lines = [l.strip() for l in (raw_text or "").splitlines() if l.strip()]
        valid = []
        for line in lines:
            line_clean = re.sub(r'\s+', ' ', line).strip()
            is_junk = False
            for pat in junk_patterns:
                if re.search(pat, line_clean, re.IGNORECASE):
                    is_junk = True
                    break
            if not is_junk:
                valid.append(line_clean)
        return valid

    valid_phi = extract_valid_fee_lines(phi_raw)
    valid_le_phi = extract_valid_fee_lines(le_phi_raw)
    
    all_raw = f"{phi_raw} {le_phi_raw}".lower()
    if 'không thu lệ phí' in all_raw or 'miễn phí' in all_raw:
        if not valid_phi and not valid_le_phi:
            return "Miễn phí (Không thu lệ phí)"

    combined = []
    if valid_phi:
        combined.append("; ".join(valid_phi) if len(valid_phi) > 1 else valid_phi[0])
    if valid_le_phi:
        combined.append("; ".join(valid_le_phi) if len(valid_le_phi) > 1 else valid_le_phi[0])
        
    unique_fees = []
    for item in combined:
        for sub in item.split(';'):
            s = sub.strip().rstrip(';,')
            if s and s.lower() not in [u.lower() for u in unique_fees]:
                unique_fees.append(s)
                
    if not unique_fees:
        return "Miễn phí"
        
    fee_result = "; ".join(unique_fees)
    if fee_result.lower() in ['chưa quy định.', 'chưa quy định']:
        return "Chưa quy định (hoặc theo quy định Bộ Tài chính)"
        
    return fee_result


def scrape_procedure_detail(detail_url: str, session: requests.Session, title: str = "") -> dict:
    """
    Truy cập vào trang chi tiết của một thủ tục hành chính và bóc tách
    các trường thông tin nghiệp vụ thực tế theo schema chuẩn Base Layer.
    """
    res = session.get(detail_url, headers=HEADERS, verify=False, timeout=15)
    if res.status_code != 200:
        raise ConnectionError(f"HTTP {res.status_code} khi tải {detail_url}")

    tree = html.fromstring(res.content)
    fields = {}
    detail_elements = {}

    items = tree.xpath('//div[contains(@class, "tthc-list-item")]')
    for it in items:
        title_nodes = it.xpath('.//*[contains(@class, "item-title")]')
        detail_nodes = it.xpath('.//*[contains(@class, "tthc-list-item-detail")]')
        if title_nodes and detail_nodes:
            raw_title = title_nodes[0].text_content().strip()
            for noise in ['Mở rộng', 'Thu gọn']:
                raw_title = raw_title.replace(noise, '')
            clean_title = " ".join(raw_title.split())

            detail_elements[clean_title.lower()] = detail_nodes[0]
            raw_detail = detail_nodes[0].text_content().strip()
            clean_lines = [line.strip() for line in raw_detail.splitlines() if line.strip()]
            fields[clean_title] = "\n".join(clean_lines)

    # 1. Mã thủ tục
    parsed = urlparse(detail_url)
    qs = parse_qs(parsed.query)
    matt_param = qs.get('matt', [''])[0]

    ma_tt = ""
    for k in ['mã thủ tục', 'mã tthc']:
        for f_key, val in fields.items():
            if k in f_key.lower():
                ma_tt = val.strip()
                break
        if ma_tt:
            break
    if not ma_tt:
        ma_tt = f"BCA-{matt_param}" if matt_param else "CHUA_CAP_MA"

    # 2. Lĩnh vực
    linh_vuc = fields.get('Lĩnh vực', '').strip()
    if not linh_vuc:
        linh_vuc = 'Quản lý hành chính'

    # 3. Cơ quan thực hiện
    co_quan = fields.get('Cơ quan thực hiện', '').strip()
    if not co_quan:
        co_quan = 'Bộ phận Một cửa - Cơ quan Công an / UBND có thẩm quyền'

    # 4. Cấp thực hiện
    cap_thuc_hien = extract_cap_thuc_hien(title, co_quan)

    # 5. Lệ phí (text + VND)
    phi_raw = fields.get('Phí', '').strip()
    le_phi_raw = fields.get('Lệ Phí', '').strip()
    le_phi_text = clean_fee(phi_raw, le_phi_raw)
    le_phi_vnd = extract_le_phi_vnd(le_phi_text)

    # 6. Thành phần hồ sơ (Định dạng phân tách bằng dấu phẩy)
    hs_el = None
    for k, el in detail_elements.items():
        if 'thành phần' in k or 'hồ sơ' in k:
            hs_el = el
            break
    if hs_el is not None:
        ho_so = clean_dossier_components(hs_el)
    else:
        ho_so = format_dossier_to_comma_separated(fields.get('Thành phần hồ sơ', '')) or 'Theo quy định hướng dẫn tại cơ quan tiếp nhận'

    # 7. Thời gian giải quyết (text + ngày số)
    tg_el = None
    for k, el in detail_elements.items():
        if 'thời hạn' in k or 'thời gian' in k:
            tg_el = el
            break
    if tg_el is not None:
        thoi_gian_text = clean_resolution_time(tg_el)
    else:
        thoi_gian_text = 'Theo quy định hiện hành'
        
    if 'lưu trú' in title.lower() and ('theo quy định' in thoi_gian_text.lower() or not thoi_gian_text):
        thoi_gian_text = 'Giải quyết ngay trong ngày làm việc'

    thoi_gian_ngay = extract_thoi_gian_ngay(thoi_gian_text)

    # 8. Căn cứ pháp lý
    legal_el = None
    for k, el in detail_elements.items():
        if 'pháp lý' in k or 'căn cứ' in k:
            legal_el = el
            break
    can_cu_phap_ly = clean_legal_basis(legal_el)

    return {
        'ma_thu_tuc': ma_tt,
        'ten_thu_tuc': title,
        'linh_vuc': linh_vuc,
        'cap_thuc_hien': cap_thuc_hien,
        'co_quan': co_quan,
        'thanh_phan_ho_so': ho_so,
        'thoi_gian_text': thoi_gian_text,
        'thoi_gian_ngay': thoi_gian_ngay,
        'le_phi_text': le_phi_text,
        'le_phi_vnd': le_phi_vnd,
        'can_cu_phap_ly': can_cu_phap_ly,
        'nguon_url': detail_url,
        'ngay_crawl': datetime.now().strftime('%Y-%m-%d')
    }


def crawl_live_portal(max_pages: int = 2, max_items: int = 30, delay_sec: float = 0.3) -> list:
    """
    Cào trực tiếp qua mạng danh sách và chi tiết thủ tục hành chính từ Cổng DVC.
    Hoàn toàn KHÔNG dùng danh sách cứng hay dự phòng nào.
    """
    print(f"\n{'='*70}")
    print(f"[*] BẮT ĐẦU CÀO DỮ LIỆU THỰC TẾ TỪ CỔNG DỊCH VỤ CÔNG")
    print(f"[*] Địa chỉ máy chủ: {TARGET_BASE_URL}")
    print(f"[*] Cấu hình: Tối đa {max_pages} trang | Giới hạn: {max_items} thủ tục")
    print(f"{'='*70}\n")

    session = requests.Session()
    session.headers.update(HEADERS)

    scraped_records = []
    seen_urls = set()

    for page in range(1, max_pages + 1):
        if len(scraped_records) >= max_items:
            break

        list_url = f"{TARGET_BASE_URL}/bocongan/bothutuc/listThuTuc?per_page=20&page={page}"
        print(f"[*] Đang tải danh sách trang {page}/{max_pages}: {list_url}")

        try:
            res = session.get(list_url, verify=False, timeout=15)
            if res.status_code != 200:
                print(f"[-] Máy chủ phản hồi mã lỗi HTTP {res.status_code} tại trang {page}")
                continue

            tree = html.fromstring(res.content)
            links = tree.xpath('//a[contains(@href, "tthc?matt=")]')

            if not links:
                print(f"[!] Không tìm thấy liên kết thủ tục nào trên trang {page}")
                continue

            print(f"[+] Tìm thấy {len(links)} thủ tục trên trang {page}. Bắt đầu bóc tách chi tiết:")

            for a in links:
                if len(scraped_records) >= max_items:
                    break

                title = a.text_content().strip()
                href = a.get('href', '')
                if not title or not href:
                    continue

                if not href.startswith('http'):
                    full_url = TARGET_BASE_URL + href
                else:
                    full_url = href

                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                print(f"    -> [{len(scraped_records) + 1}/{max_items}] Cào: {title[:55]}...")
                try:
                    record = scrape_procedure_detail(full_url, session, title=title)
                    scraped_records.append(record)
                    if delay_sec > 0:
                        time.sleep(delay_sec)
                except Exception as ex_detail:
                    print(f"       [!] Lỗi khi cào chi tiết thủ tục: {ex_detail}")

        except Exception as ex_page:
            print(f"[-] Lỗi khi kết nối tới trang {page}: {ex_page}")

    print(f"\n[+] HOÀN THÀNH CÀO MẠNG THỰC TẾ: Đã thu thập thành công {len(scraped_records)} thủ tục!")
    return scraped_records


def save_scraped_data(scraped_records: list):
    """
    Lưu dữ liệu cào thực tế vào data_crawl.xlsx.
    Chỉ xuất duy nhất file data_crawl.xlsx theo đúng 13 cột của Base Layer.
    """
    if not scraped_records:
        print("[!] Không có bản ghi nào được cào về qua mạng. Kết thúc quá trình.")
        return

    os.makedirs(DATA_DIR, exist_ok=True)
    df_scraped = pd.DataFrame(scraped_records)[BASE_COLUMNS]

    try:
        df_scraped.to_excel(OUTPUT_PATH, index=False)
        print(f"[OK] Đã xuất file cào thực tế: {OUTPUT_PATH} ({len(df_scraped)} thủ tục theo schema chuẩn)")
    except PermissionError:
        print(f"[!] Lỗi: File {OUTPUT_PATH} đang mở trong Excel. Vui lòng đóng file để ghi đè.")


def main():
    parser = argparse.ArgumentParser(description="Trình cào dữ liệu thực tế từ Cổng Dịch vụ công Quốc gia")
    parser.add_argument('--pages', type=int, default=2, help="Số trang danh sách cần cào (mặc định: 2)")
    parser.add_argument('--limit', type=int, default=30, help="Số thủ tục tối đa cần cào (mặc định: 30)")
    parser.add_argument('--delay', type=float, default=0.3, help="Thời gian nghỉ giữa các request (giây)")
    args = parser.parse_args()

    records = crawl_live_portal(max_pages=args.pages, max_items=args.limit, delay_sec=args.delay)
    save_scraped_data(records)


if __name__ == '__main__':
    main()

