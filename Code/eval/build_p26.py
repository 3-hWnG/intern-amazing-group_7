"""Phase 26: ca test cho bộ nhớ người dùng. Câu TỰ NGHĨ (không lấy từ bộ mù h2/h3/h4/pseudo_real/team). Ghi eval/cases_p26.jsonl (file riêng,
KHÔNG vào cases.jsonl nên gate DEV cũ 209 ca không lẫn). Chạy: python build_p26.py   rồi   python run_p26.py
Nhóm:
  a  câu mơ hồ theo đối tượng + hồ sơ khớp: pick (đúng 1 ứng viên hợp -> không hỏi lại) hoặc shrink (thẻ chỉ còn ứng viên hợp)
  b  cùng câu của nhóm a, KHÔNG hồ sơ -> hỏi lại như cũ
  c  hồ sơ sai/lạc, hoặc câu nêu rõ thủ tục -> vẫn đúng thủ tục theo câu (hồ sơ không can thiệp)
  d  hồ sơ rỗng ({} hoặc loại 'other') -> y hệt cũ (so cả Routed)
Đáp án nhóm a lấy theo QUY TẮC ĐỐI TƯỢNG của dữ liệu (procedure_subjects), không theo ý định thật của người hỏi: xem P26_REPORT.md (ca tự soạn dễ hơn thật).
Build chỉ assert SỰ THẬT DỮ LIỆU (thủ tục có thật, đối tượng của đáp án khớp hồ sơ), không dựa vào đầu ra của hệ thống."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [ROOT]
from system3.data import api  # noqa: E402

conn = api.connect()
BIZ, CIT = {"user_type": "business"}, {"user_type": "citizen"}
HTX, TC = {"mcq_subject": "Hợp tác xã"}, {"mcq_subject": "Tổ chức (không bao gồm doanh nghiệp, HTX)"}
SUBJ = {"business": {"Doanh nghiệp", "Doanh nghiệp Việt Nam"}, "citizen": {"Công dân Việt Nam"}}

# (câu hỏi, hồ sơ, [proc_id đáp án theo quy tắc đối tượng])
PICK = [
    ("Cho hỏi thủ tục đăng ký đóng bảo hiểm", BIZ, ["1.002051"]),
    ("Cho hỏi thủ tục đăng ký đóng bảo hiểm", HTX, ["1.002051"]),
    ("thủ tục khám chữa bệnh bảo hiểm y tế", CIT, ["1.014193"]),
    ("Khám bệnh chữa bệnh bằng thẻ bảo hiểm y tế làm sao", CIT, ["1.014193"]),
    ("Cấp giấy chứng nhận quyền sử dụng đất", BIZ, ["1.012753"]),
    ("cấp giấy chứng nhận quyền sử dụng đất cần giấy tờ gì", BIZ, ["1.012753"]),
    ("phê duyệt dự án", BIZ, ["1.014736"]),
    ("phê duyệt dự án", HTX, ["1.014736"]),
    ("Cấp gia hạn giấy phép", HTX, ["1.014198"]),
    ("gia hạn giấy phép", CIT, ["1.013227"]),
]
SHRINK = [
    ("Thủ tục đăng ký đất đai tài sản gắn liền với đất lần đầu", CIT, ["1.115373", "1.013978"]),
    ("Thủ tục đăng ký đất đai tài sản gắn liền với đất lần đầu", BIZ, ["1.115375", "1.012753"]),
    ("Thủ tục đăng ký đất đai tài sản gắn liền với đất lần đầu", TC, ["1.115375", "1.012753", "1.115894"]),
    ("thủ tục nhập cảnh xuất cảnh", HTX, ["1.013586", "1.013585"]),
    ("thủ tục nhập cảnh xuất cảnh", BIZ, ["1.013569", "1.013586", "1.013585"]),
    ("Giải quyết hưởng chế độ tai nạn lao động", CIT, ["1.001521", "1.001632", "1.001643"]),
    ("Giải quyết hưởng chế độ tai nạn lao động", BIZ, ["1.001632", "1.001643", "1.001667"]),
    ("gia hạn sử dụng đất khi hết thời hạn", BIZ, ["1.115379", "1.116109"]),
    ("gia hạn sử dụng đất khi hết thời hạn", HTX, ["1.115379", "1.116109"]),
    ("Đăng ký, cấp Giấy chứng nhận đối với trường hợp hộ gia đình đã được cấp giấy chứng nhận một phần diện tích", CIT, ["1.115210", "1.115514"]),
    ("gia hạn giấy phép", HTX, ["1.014201", "1.014198"]),
    ("phê duyệt dự án", CIT, ["1.012536", "1.014737", "1.014594", "1.014592"]),
    ("phê duyệt dự án", TC, ["1.012536", "1.014474", "1.014737"]),
    ("thủ tục khám chữa bệnh bảo hiểm y tế", BIZ, ["1.001798", "1.116466"]),
    ("thủ tục khám chữa bệnh bảo hiểm y tế", TC, ["1.001798", "1.116466"]),
    ("Cấp giấy chứng nhận quyền sử dụng đất", CIT, ["1.115750", "1.013979"]),
    ("Cấp giấy chứng nhận quyền sử dụng đất", TC, ["1.012753", "1.013979"]),
    ("Cấp gia hạn giấy phép", CIT, ["1.013227", "1.013225"]),
]
# c: (câu, hồ sơ, hành vi mong đợi, [proc_id chấp nhận | các nút phải có])
CASES_C = [
    ("Đăng ký khai sinh cần giấy tờ gì?", BIZ, "answer", ["1.001193"]),
    ("Làm thủ tục đăng ký kết hôn cần gì", HTX, "answer", ["1.000894"]),
    ("đăng ký khai tử mất bao lâu", TC, "answer", ["1.000656"]),
    ("khai báo tạm vắng nộp ở đâu", BIZ, "answer", ["1.003677"]),
    ("tách hộ lệ phí bao nhiêu", HTX, "answer", ["1.010038"]),
    ("đăng ký thường trú cho con cần giấy tờ gì", BIZ, "answer", ["1.004222"]),
    ("chứng thực chữ ký ở đâu", TC, "answer", ["2.000884"]),
    ("đăng ký giám hộ cần giấy tờ gì", HTX, "answer", ["1.004837"]),
    ("xóa đăng ký thường trú", BIZ, "answer", ["1.003197"]),
    ("đăng ký tạm trú mất bao lâu", CIT, "answer", ["1.004194"]),
    ("gia hạn tạm trú", TC, "answer", ["1.002755"]),
    ("đăng ký nhận cha mẹ con", BIZ, "answer", ["1.001022"]),
    ("Đăng ký thành lập hợp tác xã", CIT, "answer", ["1.005280"]),
    ("ký hợp đồng khám bệnh chữa bệnh bảo hiểm y tế", CIT, "answer", ["1.001798"]),                    # câu nêu rõ thủ tục dành cho tổ chức, hồ sơ người dân
    ("hỗ trợ chuyển đổi nghề giải bản tàu cá", CIT, "answer", ["1.014604"]),
    ("đăng ký đất đai tài sản gắn liền với đất lần đầu đối với tổ chức đang sử dụng đất", HTX, "answer", ["1.115373"]),   # đáp án chỉ khai 'Công dân', hồ sơ HTX: không được đổi
    ("Đăng ký thành lập tổ hợp tác", HTX, "clarify", ["2.002637"]),                                    # câu chỉ nằm trong tên MỘT ứng viên: hồ sơ HTX không được kéo sang 'hợp tác xã'
    ("thủ tục thu hồi giấy chứng nhận lần đầu đã cấp không đúng quy định", BIZ, "clarify", ["1.115941"]),   # không ứng viên nào hợp hồ sơ: giữ thẻ nguyên
    ("xin trợ cấp hàng tháng", BIZ, "clarify", ["1.001776"]),
    ("làm hộ chiếu ở đâu", BIZ, "apologize", []),
    # câu có cụm chữ nằm trong tên đúng MỘT ứng viên = đã nêu rõ: hồ sơ chỉ hợp ứng viên khác cũng KHÔNG được kéo sang (lúc đầu tôi xếp các ca này vào nhóm a,
    # chạy thử thấy hồ sơ đổi đáp án, nên thêm luật 'nêu rõ' ở policy._names_candidate rồi chuyển chúng sang nhóm c)
    ("thủ tục hỗ trợ giải bản tàu cá", BIZ, "clarify", ["1.014599"]),
    ("thủ tục hỗ trợ giải bản tàu cá", TC, "clarify", ["1.014599"]),
    ("Thu hồi giấy chứng nhận đã cấp không đúng quy định", BIZ, "clarify", ["1.115898"]),
    ("Thu hồi giấy chứng nhận đã cấp không đúng quy định", HTX, "clarify", ["1.115898"]),
]
# d: hồ sơ rỗng; trộn câu mơ hồ, rõ, ngoài phạm vi
EMPTY = [{}, {"user_type": "other"}]
CASES_D = ["Cho hỏi thủ tục đăng ký đóng bảo hiểm", "thủ tục khám chữa bệnh bảo hiểm y tế", "phê duyệt dự án", "Cấp giấy chứng nhận quyền sử dụng đất",
           "thủ tục nhập cảnh xuất cảnh", "gia hạn sử dụng đất khi hết thời hạn", "Đăng ký khai sinh cần giấy tờ gì?", "đăng ký tạm trú mất bao lâu",
           "Điều chỉnh quyết định giao đất cho thuê đất", "xin trợ cấp hàng tháng", "hôm nay trời đẹp quá", "Đăng ký thành lập tổ hợp tác"]


def subj(pid):
    return {r[0] for r in conn.execute("SELECT TRIM(s.subject_name) FROM procedures p JOIN procedure_subjects s ON s.row_id=p.row_id WHERE p.proc_id=? AND p.status='active'", (pid,))}


def want(profile):
    return SUBJ[profile["user_type"]] if "user_type" in profile else {profile["mcq_subject"]}


def main():
    cases, n = [], {"a": 0, "b": 0, "c": 0, "d": 0}

    def add(g, q, profile, exp):
        n[g] += 1
        cases.append({"id": f"p26-{g}-{n[g]:02d}", "group": g, "question": q, "profile": profile, "expected": exp})

    for kind, rows in (("pick", PICK), ("shrink", SHRINK)):
        for q, prof, acc in rows:
            for pid in acc:                                   # sự thật dữ liệu: thủ tục có thật và có đối tượng khớp hồ sơ
                assert conn.execute("SELECT 1 FROM procedures WHERE proc_id=? AND status='active'", (pid,)).fetchone(), pid
                assert subj(pid) & want(prof), (q, pid, subj(pid))
            add("a", q, prof, {"note": kind, "acceptable": acc})
    for c in [c for c in cases if c["group"] == "a"]:
        add("b", c["question"], {}, {"behavior": "clarify"})
    for q, prof, beh, acc in CASES_C:
        for pid in acc:
            assert conn.execute("SELECT 1 FROM procedures WHERE proc_id=? AND status='active'", (pid,)).fetchone(), pid
        add("c", q, prof, {"behavior": beh, "acceptable": acc})
    for i, q in enumerate(CASES_D):
        add("d", q, EMPTY[i % 2], {})
    with open(os.path.join(HERE, "cases_p26.jsonl"), "w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    qs = {c["question"] for c in cases}
    print(f"cases_p26.jsonl: {len(cases)} ca ({n}), {len(qs)} câu khác nhau; a-pick {len(PICK)}, a-shrink {len(SHRINK)}")


if __name__ == "__main__":
    main()
