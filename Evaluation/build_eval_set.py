#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_eval_set.py — Nhóm 7 / LLM Pháp lý
=========================================
Sinh bộ câu hỏi đánh giá (eval set) + dữ liệu fine-tune từ data_merged.xlsx.

Mỗi câu hỏi được gắn nhãn sẵn: nhãn = dòng thủ tục mà câu hỏi được sinh ra từ đó.
Không cần ai gán nhãn thủ công.

Dùng được cho 4 việc:
  1. Đo chất lượng truy hồi  (Recall@1 / Recall@5 / MRR)
  2. Hiệu chỉnh ngưỡng HIGH / LOW cho router
  3. Sinh dữ liệu fine-tune dạng in/out
  4. Làm index "câu hỏi <-> câu hỏi" nếu vẫn giữ RAG

Chạy:  python build_eval_set.py --xlsx data_merged.xlsx --out ./eval
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import unicodedata
from collections import Counter
from pathlib import Path

try:
    import openpyxl
except ImportError:  # pragma: no cover
    raise SystemExit("Cần cài openpyxl:  pip install openpyxl")

SEED = 7  # Nhóm 7 :)  — cố định để bộ dữ liệu tái lập được y hệt


# ---------------------------------------------------------------------------
# PHẦN 1 — TOPIC: đơn vị gán nhãn thật sự
# ---------------------------------------------------------------------------
# Một "topic" = một nhu cầu của người dân.
# Một topic có thể ứng với NHIỀU dòng trong xlsx (vd: "cấp lại thẻ căn cước"
# tồn tại cả ở cấp tỉnh và cấp trung ương). Khi đó nhãn đúng là CẢ NHÓM dòng,
# không phải một dòng duy nhất — nếu ép một nhãn thì hệ thống trả lời đúng
# vẫn bị chấm sai.
#
# rows = số thứ tự dòng trong data_merged.xlsx, đếm từ 1 (không tính dòng tiêu đề).
# seeds = câu hỏi tình huống, viết tay, mô phỏng cách người dân thật sự hỏi.
#         Đây là phần quan trọng nhất — nó kiểm tra hiểu ngữ nghĩa,
#         không chỉ khớp từ khoá.

TOPICS: list[dict] = [
    # ---------------- HỘ TỊCH ----------------
    dict(key="xac_nhan_hon_nhan", topic="xác nhận tình trạng hôn nhân", rows=[1],
         seeds=["Tôi cần giấy chứng nhận độc thân để đăng ký kết hôn thì xin ở đâu",
                "Bên nhà trai yêu cầu giấy xác nhận chưa có vợ, tôi phải làm thủ tục gì"]),
    dict(key="khai_sinh", topic="đăng ký khai sinh", rows=[2],
         seeds=["Con tôi mới sinh được 3 ngày, giờ tôi phải làm gì để có giấy khai sinh",
                "Vợ tôi vừa sinh ở bệnh viện, cần mang theo gì ra phường làm khai sinh"]),
    dict(key="khai_tu", topic="đăng ký khai tử", rows=[3],
         seeds=["Bố tôi vừa mất ở nhà, tôi cần làm giấy tờ gì",
                "Người thân qua đời thì bao lâu phải đi khai tử"]),
    dict(key="ket_hon", topic="đăng ký kết hôn", rows=[4],
         seeds=["Hai đứa tôi muốn cưới, ra phường đăng ký cần mang gì",
                "Đăng ký kết hôn có phải về quê vợ làm không hay làm ở đây được"]),
    dict(key="cha_me_con", topic="nhận cha mẹ con", rows=[5],
         seeds=["Tôi muốn làm thủ tục nhận con ruột nhưng chưa đăng ký kết hôn với mẹ bé",
                "Làm sao để bổ sung tên cha vào giấy khai sinh của con"]),
    dict(key="ket_hon_nn", topic="đăng ký kết hôn có yếu tố nước ngoài", rows=[6],
         seeds=["Tôi lấy chồng người Hàn Quốc thì đăng ký kết hôn ở đâu",
                "Bạn gái tôi là người nước ngoài, thủ tục cưới có khác gì không"]),

    # ---------------- LAO ĐỘNG ----------------
    dict(key="noi_quy_lao_dong", topic="đăng ký nội quy lao động", rows=[7],
         seeds=["Công ty tôi mới mở, có phải nộp nội quy lao động không",
                "Doanh nghiệp bao nhiêu người thì phải đăng ký nội quy lao động"]),

    # ---------------- VĂN HOÁ – XÃ HỘI ----------------
    dict(key="khuyet_tat", topic="xác nhận mức độ khuyết tật", rows=[8, 21],
         seeds=["Con tôi bị khuyết tật bẩm sinh, làm sao để được cấp giấy xác nhận",
                "Tôi muốn giám định lại mức độ khuyết tật vì tình trạng nặng hơn"]),
    dict(key="hoa_tang", topic="hỗ trợ chi phí hoả táng", rows=[9, 14],
         seeds=["Gia đình tôi vừa hoả táng cho mẹ, nghe nói thành phố có hỗ trợ tiền",
                "Hộ khẩu TPHCM thì được hỗ trợ bao nhiêu khi hoả táng"]),
    dict(key="tho_cung_liet_si", topic="trợ cấp thờ cúng liệt sĩ", rows=[10, 13],
         seeds=["Nhà tôi đang thờ cúng liệt sĩ, muốn hưởng chế độ trợ cấp hàng năm",
                "Anh trai tôi là liệt sĩ, giờ tôi thờ cúng thì làm hồ sơ gì"]),
    dict(key="to_quoc_ghi_cong", topic="cấp đổi Bằng Tổ quốc ghi công", rows=[11],
         seeds=["Bằng Tổ quốc ghi công của gia đình tôi bị rách, xin đổi lại được không",
                "Làm sao cấp lại bằng Tổ quốc ghi công bị mất do lụt"]),
    dict(key="than_nhan_nguoi_co_cong", topic="cấp giấy xác nhận thân nhân người có công", rows=[12],
         seeds=["Tôi là con liệt sĩ, cần giấy xác nhận thân nhân để làm hồ sơ đi học",
                "Xin giấy chứng nhận thân nhân người có công ở đâu"]),
    dict(key="mai_tang", topic="hỗ trợ chi phí mai táng", rows=[15, 19],
         seeds=["Mẹ tôi đang hưởng trợ cấp bảo trợ xã hội vừa mất, có được hỗ trợ mai táng không",
                "Người hưởng trợ cấp hưu trí xã hội qua đời thì gia đình nhận hỗ trợ thế nào"]),
    dict(key="tro_cap_xa_hoi", topic="trợ cấp xã hội hàng tháng", rows=[16],
         seeds=["Bà tôi 82 tuổi, muốn làm hồ sơ hưởng trợ cấp xã hội hàng tháng",
                "Tôi muốn điều chỉnh mức trợ cấp bảo trợ xã hội đang nhận"]),
    dict(key="nguoi_co_cong_tu_tran", topic="trợ cấp khi người có công từ trần", rows=[17],
         seeds=["Ba tôi là thương binh vừa mất, gia đình được hưởng chế độ gì",
                "Người có công đang hưởng trợ cấp mà qua đời thì báo ở đâu"]),
    dict(key="huu_tri_xa_hoi", topic="trợ cấp hưu trí xã hội", rows=[18],
         seeds=["Tôi đủ tuổi nhưng không có lương hưu, nghe nói có trợ cấp hưu trí xã hội",
                "Thủ tục xin hưởng trợ cấp hưu trí xã hội gồm những gì"]),
    dict(key="ho_tro_hoc_dai_hoc", topic="hỗ trợ chi phí học đến đại học", rows=[20],
         seeds=["Con liệt sĩ đang học đại học có được hỗ trợ học phí không",
                "Xin chế độ hỗ trợ đi học cho con người có công làm ở đâu"]),
    dict(key="khang_chien", topic="chế độ người hoạt động kháng chiến", rows=[22],
         seeds=["Ông tôi tham gia kháng chiến chống Mỹ, giờ làm chế độ được không",
                "Hồ sơ hưởng chế độ người hoạt động kháng chiến gồm giấy tờ gì"]),
    dict(key="vay_von_viec_lam", topic="vay vốn hỗ trợ tạo việc làm", rows=[26, 30],
         seeds=["Tôi thất nghiệp muốn vay vốn quỹ quốc gia về việc làm để mở quán",
                "Cơ sở sản xuất nhỏ của tôi muốn vay vốn tạo việc làm thì làm sao"]),

    # ---------------- GIÁO DỤC ----------------
    dict(key="chuyen_truong_thcs", topic="chuyển trường cho học sinh THCS", rows=[27],
         seeds=["Gia đình tôi mới chuyển nhà, muốn chuyển trường cho con đang học lớp 7",
                "Thủ tục xin chuyển trường cấp 2 giữa năm học"]),
    dict(key="hoc_bong_chinh_sach", topic="xét cấp học bổng chính sách", rows=[39],
         seeds=["Con tôi thuộc diện chính sách, xin học bổng ở đâu",
                "Điều kiện và hồ sơ để được cấp học bổng chính sách"]),

    # ---------------- XÂY DỰNG – ĐẤT ĐAI ----------------
    dict(key="giay_phep_xay_dung", topic="cấp giấy phép xây dựng", rows=[23, 25],
         seeds=["Tôi muốn xây nhà 3 tầng trên đất của mình, cần xin phép gì",
                "Sửa nhà có phải xin giấy phép xây dựng không"]),
    dict(key="thong_tin_quy_hoach", topic="cung cấp thông tin quy hoạch", rows=[24],
         seeds=["Tôi định mua miếng đất, muốn biết có dính quy hoạch không",
                "Xin thông tin quy hoạch thửa đất thì hỏi cơ quan nào"]),
    dict(key="thong_bao_khoi_cong", topic="thông báo khởi công", rows=[28],
         seeds=["Có giấy phép xây dựng rồi thì trước khi làm móng phải báo ai",
                "Thông báo khởi công công trình nộp ở đâu"]),
    dict(key="dang_ky_dat_dai", topic="đăng ký đất đai tài sản gắn liền với đất lần đầu", rows=[29],
         seeds=["Đất ông bà để lại chưa có sổ, giờ tôi muốn làm sổ đỏ lần đầu",
                "Nhà xây xong muốn đăng ký tài sản gắn liền với đất"]),
    dict(key="cap_so_nha", topic="cấp số nhà", rows=[31],
         seeds=["Nhà tôi mới xây chưa có số nhà, xin cấp số ở đâu",
                "Thủ tục xin cấp số nhà mất bao lâu"]),
    dict(key="xac_nhan_vi_tri", topic="xác nhận vị trí nhà đất", rows=[32],
         seeds=["Ngân hàng yêu cầu giấy xác nhận vị trí nhà đất để vay",
                "Xin xác nhận vị trí thửa đất làm ở phường hay quận"]),
    dict(key="xac_nhan_tinh_trang_nha", topic="xác nhận tình trạng nhà ở", rows=[33],
         seeds=["Tôi cần giấy xác nhận chưa có nhà ở để mua nhà ở xã hội",
                "Xác nhận tình trạng nhà ở cần mang giấy tờ gì"]),

    # ---------------- HỘ KINH DOANH ----------------
    dict(key="lap_ho_kinh_doanh", topic="đăng ký thành lập hộ kinh doanh", rows=[34],
         seeds=["Tôi muốn mở quán cà phê nhỏ thì đăng ký kinh doanh thế nào",
                "Bán hàng tại nhà có cần đăng ký hộ kinh doanh không"]),
    dict(key="doi_ho_kinh_doanh", topic="thay đổi nội dung đăng ký hộ kinh doanh", rows=[35],
         seeds=["Quán tôi chuyển địa chỉ, giấy phép kinh doanh sửa thế nào",
                "Muốn thêm ngành nghề cho hộ kinh doanh đang hoạt động"]),
    dict(key="tam_ngung_kinh_doanh", topic="tạm ngừng kinh doanh của hộ kinh doanh", rows=[36],
         seeds=["Tôi muốn nghỉ bán vài tháng rồi mở lại, có phải báo không",
                "Thủ tục tạm ngừng kinh doanh hộ cá thể"]),
    dict(key="cham_dut_kinh_doanh", topic="chấm dứt hoạt động hộ kinh doanh", rows=[37],
         seeds=["Tôi đóng cửa tiệm luôn thì cần trả giấy phép không",
                "Giải thể hộ kinh doanh làm thủ tục ở đâu"]),
    dict(key="cap_lai_gcn_hkd", topic="cấp lại giấy chứng nhận đăng ký hộ kinh doanh", rows=[38],
         seeds=["Giấy phép kinh doanh của tôi bị mất, xin cấp lại được không",
                "Giấy chứng nhận hộ kinh doanh bị cháy thì làm sao"]),

    # ---------------- CHỨNG THỰC ----------------
    dict(key="chung_thuc", topic="chứng thực chữ ký và hợp đồng giao dịch", rows=[40],
         seeds=["Tôi cần công chứng giấy uỷ quyền cho em trai bán xe",
                "Muốn lập di chúc có người làm chứng thì ra đâu chứng thực"]),

    # ---------------- PHƯƠNG TIỆN GIAO THÔNG ----------------
    dict(key="thu_hoi_bien_so", topic="thu hồi giấy chứng nhận đăng ký và biển số xe", rows=[41],
         seeds=["Tôi bán xe rồi, giờ muốn thu hồi đăng ký và biển số",
                "Xe cũ hỏng nát muốn nộp lại biển số thì làm sao"]),
    dict(key="dang_ky_xe_lan_dau", topic="đăng ký xe lần đầu và cấp biển số", rows=[42, 43, 62],
         seeds=["Tôi vừa mua xe máy mới ở đại lý, đăng ký biển số thế nào",
                "Xe nhập khẩu về đăng ký lần đầu có làm online được không"]),

    # ---------------- XUẤT NHẬP CẢNH ----------------
    dict(key="ho_chieu", topic="cấp hộ chiếu phổ thông trong nước", rows=[44, 45],
         seeds=["Tôi muốn làm hộ chiếu đi du lịch, nộp hồ sơ ở đâu",
                "Làm passport lần đầu mất bao nhiêu tiền"]),
    dict(key="thi_thuc_dien_tu", topic="cấp thị thực điện tử", rows=[48, 49],
         seeds=["Bạn tôi người nước ngoài muốn xin visa điện tử vào Việt Nam",
                "Công ty bảo lãnh người nước ngoài xin thị thực điện tử thế nào"]),

    # ---------------- CĂN CƯỚC ----------------
    dict(key="cccd_cap_moi", topic="cấp thẻ căn cước cho người từ đủ 14 tuổi", rows=[67, 70],
         seeds=["Con tôi vừa tròn 14 tuổi, giờ đi làm căn cước ở đâu",
                "Lần đầu làm thẻ căn cước cần mang theo gì"]),
    dict(key="cccd_cap_lai", topic="cấp lại thẻ căn cước", rows=[54, 57],
         seeds=["Tôi làm mất thẻ căn cước công dân, xin cấp lại thế nào",
                "Căn cước bị mất khi đi du lịch, cấp lại mất bao lâu"]),
    dict(key="cccd_cap_doi", topic="cấp đổi thẻ căn cước", rows=[60, 63],
         seeds=["Thẻ căn cước của tôi bị mờ hết chữ, đổi lại được không",
                "Tôi mới đổi tên trong giấy tờ, cần cấp đổi căn cước"]),

    # ---------------- CƯ TRÚ ----------------
    dict(key="gia_han_tam_tru", topic="gia hạn tạm trú", rows=[59],
         seeds=["Tôi thuê trọ ở đây sắp hết hạn tạm trú, gia hạn thế nào",
                "Gia hạn tạm trú cho người nước ngoài mất bao lâu"]),
    dict(key="thong_bao_luu_tru", topic="thông báo lưu trú", rows=[61],
         seeds=["Nhà tôi có khách ở lại qua đêm, có phải báo công an không",
                "Khai báo lưu trú online được không"]),
    dict(key="xoa_thuong_tru", topic="xoá đăng ký thường trú", rows=[65],
         seeds=["Người thân tôi đã mất, giờ xoá tên khỏi hộ khẩu thế nào",
                "Tôi chuyển hẳn vào Nam, xoá thường trú ngoài quê ra sao"]),

    # ---------------- CON DẤU ----------------
    dict(key="con_dau_moi", topic="đăng ký mẫu con dấu mới", rows=[66],
         seeds=["Công ty mới thành lập muốn khắc con dấu thì đăng ký ở đâu",
                "Hồ sơ đăng ký mẫu con dấu lần đầu gồm những gì"]),
    dict(key="con_dau_lai", topic="đăng ký lại mẫu con dấu", rows=[50],
         seeds=["Con dấu công ty tôi bị mất, đăng ký lại thế nào",
                "Dấu cũ mòn không rõ nét, xin đăng ký lại được không"]),
    dict(key="con_dau_them", topic="đăng ký thêm con dấu", rows=[51],
         seeds=["Công ty tôi mở thêm chi nhánh, muốn khắc thêm một con dấu nữa",
                "Đăng ký thêm con dấu thứ hai có được không"]),
    dict(key="con_dau_dac_biet", topic="đăng ký dấu nổi dấu thu nhỏ dấu xi", rows=[53],
         seeds=["Đơn vị tôi cần làm dấu nổi để đóng lên phôi bằng",
                "Thủ tục đăng ký dấu xi và dấu thu nhỏ"]),
    dict(key="gcn_con_dau", topic="đổi cấp lại giấy chứng nhận đăng ký mẫu con dấu", rows=[56],
         seeds=["Giấy chứng nhận đăng ký mẫu dấu của công ty bị thất lạc",
                "Xin cấp lại giấy chứng nhận mẫu con dấu ở đâu"]),

    # ---------------- AN NINH TRẬT TỰ ----------------
    dict(key="antt_cap_moi", topic="cấp mới giấy chứng nhận đủ điều kiện về an ninh trật tự",
         rows=[46, 47],
         seeds=["Tôi mở tiệm cầm đồ, nghe nói phải xin giấy đủ điều kiện an ninh trật tự",
                "Kinh doanh karaoke cần giấy chứng nhận an ninh trật tự không"]),
    dict(key="antt_cap_doi", topic="cấp đổi giấy chứng nhận đủ điều kiện về an ninh trật tự",
         rows=[52, 55],
         seeds=["Giấy chứng nhận an ninh trật tự của quán tôi sắp hết hạn",
                "Đổi tên doanh nghiệp thì giấy an ninh trật tự có phải cấp đổi không"]),
    dict(key="antt_cap_lai", topic="cấp lại giấy chứng nhận đủ điều kiện về an ninh trật tự",
         rows=[58, 64],
         seeds=["Tôi làm mất giấy chứng nhận đủ điều kiện an ninh trật tự",
                "Giấy an ninh trật tự bị hư hỏng, xin cấp lại thế nào"]),

    # ---------------- VŨ KHÍ – VẬT LIỆU NỔ ----------------
    dict(key="vu_khi_trien_lam", topic="giấy phép trang bị sử dụng vũ khí công cụ hỗ trợ làm đạo cụ",
         rows=[68],
         seeds=["Đoàn phim của tôi cần dùng súng đạo cụ khi quay, xin phép thế nào",
                "Bảo tàng muốn trưng bày vũ khí thì xin giấy phép ở đâu"]),
    dict(key="tien_chat_thuoc_no", topic="giấy phép vận chuyển tiền chất thuốc nổ", rows=[69],
         seeds=["Công ty tôi cần vận chuyển tiền chất thuốc nổ giữa hai tỉnh",
                "Xin giấy phép vận chuyển tiền chất thuốc nổ mất bao lâu"]),
]


# ---------------------------------------------------------------------------
# PHẦN 2 — câu hỏi NGOÀI PHẠM VI (nhãn = none)
# ---------------------------------------------------------------------------
# Dùng để đo: hệ thống có biết từ chối / chuyển sang web search không,
# hay vẫn cố nhét một thủ tục bất kỳ vào câu trả lời.

OUT_OF_SCOPE = [
    # luật / tư vấn pháp lý — KHÔNG phải thủ tục hành chính
    ("Tôi muốn ly hôn thì phải làm sao", "phap_ly"),
    ("Chồng tôi ngoại tình, tôi có được chia nhiều tài sản hơn không", "phap_ly"),
    ("Hàng xóm lấn đất nhà tôi, tôi kiện được không", "phap_ly"),
    ("Công ty nợ lương 3 tháng thì tôi làm gì", "phap_ly"),
    ("Bị lừa chuyển khoản 50 triệu có lấy lại được không", "phap_ly"),
    ("Tôi có được đơn phương chấm dứt hợp đồng lao động không", "phap_ly"),
    ("Vay nặng lãi bị đòi nợ kiểu khủng bố thì báo ai", "phap_ly"),
    ("Thừa kế không có di chúc thì chia thế nào", "phap_ly"),
    ("Tôi muốn kiện ra toà vì bị hàng xóm vu khống", "phap_ly"),
    ("Đánh nhau gây thương tích bao nhiêu phần trăm thì đi tù", "phap_ly"),
    # mức phạt — cần tra web, không có trong dataset
    ("Vượt đèn đỏ phạt bao nhiêu tiền", "muc_phat"),
    ("Không đội mũ bảo hiểm bị phạt bao nhiêu", "muc_phat"),
    ("Nồng độ cồn 0.3 thì phạt thế nào", "muc_phat"),
    ("Đi ngược chiều xe máy phạt bao nhiêu", "muc_phat"),
    ("Không mang giấy tờ xe bị phạt bao nhiêu", "muc_phat"),
    ("Xe máy không gương phạt bao nhiêu tiền", "muc_phat"),
    ("Ô tô đỗ sai quy định mức phạt mới nhất", "muc_phat"),
    ("Quá tốc độ 15km bị giữ bằng lái bao lâu", "muc_phat"),
    # thủ tục có thật nhưng KHÔNG có trong 70 dòng
    ("Tôi muốn làm giấy phép lái xe hạng B2", "ngoai_dataset"),
    ("Đổi bằng lái xe ô tô hết hạn ở đâu", "ngoai_dataset"),
    ("Thủ tục nhập khẩu cho con vào hộ khẩu ông bà", "ngoai_dataset"),
    ("Đăng ký kinh doanh công ty cổ phần cần gì", "ngoai_dataset"),
    ("Xin giấy phép phòng cháy chữa cháy cho nhà xưởng", "ngoai_dataset"),
    ("Làm thủ tục hưởng bảo hiểm thất nghiệp", "ngoai_dataset"),
    ("Đăng ký mã số thuế cá nhân", "ngoai_dataset"),
    ("Xin cấp lại sổ bảo hiểm xã hội bị mất", "ngoai_dataset"),
    ("Thủ tục đăng ký nghĩa vụ quân sự", "ngoai_dataset"),
    ("Cấp giấy chứng nhận vệ sinh an toàn thực phẩm", "ngoai_dataset"),
    ("Đăng ký kết hôn đồng giới ở Việt Nam được không", "ngoai_dataset"),
    ("Xin visa đi Nhật làm ở đâu", "ngoai_dataset"),
    # thời sự / ngoài lề — phải đi web search
    ("Giá vàng hôm nay bao nhiêu", "thoi_su"),
    ("Thời tiết mai có mưa không", "thoi_su"),
    ("Tỷ giá đô la hôm nay", "thoi_su"),
    ("Giá xăng mới nhất", "thoi_su"),
    ("Kết quả bóng đá tối qua", "thoi_su"),
    ("Lịch nghỉ lễ năm nay thế nào", "thoi_su"),
    ("Lương cơ sở năm nay là bao nhiêu", "thoi_su"),
    ("Chứng khoán hôm nay tăng hay giảm", "thoi_su"),
    # xã giao — phải vào nhánh chào hỏi, không tra DB
    ("Xin chào", "xa_giao"),
    ("Chào bạn nhé", "xa_giao"),
    ("Bạn là ai vậy", "xa_giao"),
    ("Bạn giúp được gì cho tôi", "xa_giao"),
    ("Cảm ơn bạn nhiều", "xa_giao"),
    ("Ok cảm ơn", "xa_giao"),
    ("Alo", "xa_giao"),
    ("Bạn có thông minh không", "xa_giao"),
    # mơ hồ — nên hỏi lại (Tier B), không nên đoán
    ("Tôi cần làm giấy tờ", "mo_ho"),
    ("Cho hỏi thủ tục", "mo_ho"),
    ("Giúp tôi với", "mo_ho"),
    ("Cần nộp hồ sơ", "mo_ho"),
    ("Bao lâu thì xong", "mo_ho"),
    ("Hết bao nhiêu tiền", "mo_ho"),
]


# ---------------------------------------------------------------------------
# PHẦN 3 — biến thể: làm câu hỏi "bẩn" giống người dùng thật
# ---------------------------------------------------------------------------

ABBREV = {
    "không": "ko", "được": "dc", "đăng ký": "đk", "giấy tờ": "gt",
    "hồ sơ": "hs", "bao nhiêu": "bn", "thủ tục": "tt", "tôi": "t",
    "bao lâu": "bl", "như thế nào": "ntn", "thế nào": "tn",
    "người": "ng", "với": "vs", "gì": "j", "biết": "bit",
}

OPENERS = ["cho hỏi ", "cho em hỏi ", "ad ơi ", "cho e hỏi với ", "a ơi ",
           "anh chị ơi ", "cho mình hỏi ", ""]
CLOSERS = [" ạ", " vs ạ", " với ạ", " nhỉ", " v", " ?", ""]

FACETS = [
    ("docs", "{t} cần giấy tờ gì"),
    ("docs", "hồ sơ {t} gồm những gì"),
    ("time", "{t} mất bao lâu"),
    ("time", "{t} bao nhiêu ngày thì xong"),
    ("fee", "{t} lệ phí bao nhiêu"),
    ("fee", "{t} có mất phí không"),
    ("place", "{t} nộp ở đâu"),
    ("online", "{t} làm online được không"),
]


def strip_diacritics(text: str) -> str:
    """bỏ dấu — cách gõ rất phổ biến trên điện thoại."""
    text = text.replace("đ", "d").replace("Đ", "D")
    nfd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def to_abbrev(text: str) -> str:
    out = text.lower()
    for full, short in ABBREV.items():
        out = out.replace(full, short)
    return out


def add_typo(text: str, rng: random.Random) -> str:
    """lỗi gõ thật: mất dấu cách, gõ đúp chữ, nuốt chữ.

    Bắt buộc phải khác chuỗi gốc — nếu không sẽ sinh ra câu trùng lặp
    và làm lệch điểm đánh giá.
    """
    words = text.split()
    if len(words) < 2:
        return text + text[-1] if text else text

    for _ in range(12):
        w = list(words)
        mode = rng.choice(["join", "double", "drop"])
        i = rng.randrange(len(w) - 1 if mode == "join" else len(w))
        if mode == "join":
            w[i : i + 2] = [w[i] + w[i + 1]]
        elif mode == "double":
            if len(w[i]) < 2:
                continue
            j = rng.randrange(1, len(w[i]))
            w[i] = w[i][:j] + w[i][j] + w[i][j:]
        else:  # drop
            if len(w[i]) < 4:
                continue
            j = rng.randrange(1, len(w[i]) - 1)
            w[i] = w[i][:j] + w[i][j + 1 :]
        out = " ".join(w)
        if out != text:
            return out

    # bảo hiểm: luôn trả về thứ gì đó khác gốc
    return words[0] + " " + " ".join(words)


def keyword_only(topic: str, rng: random.Random) -> str:
    """kiểu gõ cụt lủn — rất hay gặp ở ô chat."""
    tail = rng.choice(["", " cần gì", " ở đâu", " bao lâu", " phí", " hồ sơ"])
    return topic + tail


def colloquial(text: str, rng: random.Random) -> str:
    return (rng.choice(OPENERS) + text.lower() + rng.choice(CLOSERS)).strip()


# ---------------------------------------------------------------------------
# PHẦN 4 — sinh dữ liệu
# ---------------------------------------------------------------------------

def load_rows(xlsx_path: Path) -> dict[int, dict]:
    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    header = [str(h).strip() if h else "" for h in rows[0]]
    out: dict[int, dict] = {}
    n = 0
    for raw in rows[1:]:
        if not raw or not raw[0]:
            continue
        n += 1
        rec = {header[i]: raw[i] for i in range(len(header))}
        rec["_row_no"] = n            # 1-based, khớp với TOPICS["rows"]
        rec["_chroma_id"] = str(n - 1)  # 0-based, khớp id do ingest.py sinh ra
        out[n] = rec
    return out


def build(xlsx_path: Path, out_dir: Path, per_topic: int) -> None:
    rng = random.Random(SEED)
    rows = load_rows(xlsx_path)
    records: list[dict] = []
    qid = 0

    covered: set[int] = set()

    for spec in TOPICS:
        topic = spec["topic"]
        gold_rows = spec["rows"]
        covered.update(gold_rows)
        missing = [r for r in gold_rows if r not in rows]
        if missing:
            print(f"  ! CẢNH BÁO: topic '{spec['key']}' trỏ tới dòng không tồn tại {missing}")
        titles = [str(rows[r]["Tên thủ tục hành chính"]).strip() for r in gold_rows if r in rows]
        linh_vuc = str(rows[gold_rows[0]].get("Lĩnh vực", "")).strip() if gold_rows[0] in rows else ""
        gold_chroma = [rows[r]["_chroma_id"] for r in gold_rows if r in rows]

        variants: list[tuple[str, str, str]] = []  # (question, variant, difficulty)

        # 1. câu tình huống viết tay — khó nhất, kiểm tra hiểu ngữ nghĩa thật
        for s in spec["seeds"]:
            variants.append((s, "situational", "hard"))

        # 2. câu hỏi theo từng khía cạnh (giấy tờ / thời gian / phí / nơi nộp)
        facets = rng.sample(FACETS, k=len(FACETS))
        for name, tmpl in facets:
            variants.append((tmpl.format(t=topic), f"facet_{name}", "easy"))

        # 3. biến thể "bẩn"
        base_for_noise = spec["seeds"] + [f"{topic} cần giấy tờ gì"]
        variants.append((strip_diacritics(rng.choice(base_for_noise)), "no_diacritics", "hard"))
        variants.append((to_abbrev(rng.choice(base_for_noise)), "abbrev", "hard"))
        variants.append((add_typo(rng.choice(base_for_noise), rng), "typo", "hard"))
        variants.append((keyword_only(topic, rng), "keyword", "medium"))
        variants.append((colloquial(rng.choice(base_for_noise), rng), "colloquial", "medium"))

        # cắt / bù cho đủ per_topic
        variants = variants[:per_topic]

        for q, variant, diff in variants:
            qid += 1
            records.append({
                "qid": f"Q{qid:04d}",
                "question": q.strip(),
                "topic_key": spec["key"],
                "topic": topic,
                "gold_row_no": ";".join(str(r) for r in gold_rows),
                "gold_chroma_id": ";".join(gold_chroma),
                "gold_title": " | ".join(titles),
                "linh_vuc": linh_vuc,
                "variant": variant,
                "difficulty": diff,
                "in_scope": 1,
                "oos_kind": "",
            })

    # ---- ngoài phạm vi ----
    for q, kind in OUT_OF_SCOPE:
        qid += 1
        records.append({
            "qid": f"Q{qid:04d}",
            "question": q,
            "topic_key": "none",
            "topic": "",
            "gold_row_no": "",
            "gold_chroma_id": "",
            "gold_title": "",
            "linh_vuc": "",
            "variant": "out_of_scope",
            "difficulty": "hard",
            "in_scope": 0,
            "oos_kind": kind,
        })

    out_dir.mkdir(parents=True, exist_ok=True)
    fields = list(records[0].keys())

    with (out_dir / "eval_questions.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(records)

    with (out_dir / "eval_questions.jsonl").open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ---- báo cáo ----
    uncovered = sorted(set(rows) - covered)
    in_scope = [r for r in records if r["in_scope"] == 1]
    report = {
        "tong_so_cau_hoi": len(records),
        "trong_pham_vi": len(in_scope),
        "ngoai_pham_vi": len(records) - len(in_scope),
        "so_topic": len(TOPICS),
        "so_dong_xlsx": len(rows),
        "so_dong_duoc_phu": len(covered),
        "dong_chua_phu": uncovered,
        "topic_nhieu_hon_1_dong": {
            s["key"]: s["rows"] for s in TOPICS if len(s["rows"]) > 1
        },
        "phan_bo_variant": dict(Counter(r["variant"] for r in records)),
        "phan_bo_do_kho": dict(Counter(r["difficulty"] for r in records)),
        "phan_bo_ngoai_pham_vi": dict(
            Counter(r["oos_kind"] for r in records if r["in_scope"] == 0)
        ),
    }
    with (out_dir / "report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Đã ghi {len(records)} câu hỏi vào {out_dir}")
    print(f"  - trong phạm vi : {report['trong_pham_vi']}")
    print(f"  - ngoài phạm vi : {report['ngoai_pham_vi']}")
    print(f"  - phủ {len(covered)}/{len(rows)} dòng")
    if uncovered:
        print(f"  ! chưa phủ dòng: {uncovered}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", default="data_merged.xlsx")
    ap.add_argument("--out", default="./eval")
    ap.add_argument("--per-topic", type=int, default=15,
                    help="số câu hỏi mỗi topic (mặc định 15)")
    args = ap.parse_args()
    build(Path(args.xlsx), Path(args.out), args.per_topic)


if __name__ == "__main__":
    main()
