import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "db" / "procedures.db"

def inspect():
    if not DB_PATH.exists():
        print(f"Chưa tìm thấy database tại: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("=" * 60)
    print("📊 THỐNG KÊ CƠ SỞ DỮ LIỆU PROCEDURES.DB")
    print("=" * 60)

    # Đếm số lượng
    cur.execute("SELECT COUNT(*) FROM procedures WHERE status = 'active'")
    total_active = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM procedures WHERE status = 'archived'")
    total_archived = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM procedure_checklists")
    total_checklists = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM procedure_fees")
    total_fees = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM procedure_files")
    total_files = cur.fetchone()[0]

    print(f"- Tổng số thủ tục đang áp dụng (active): {total_active}")
    print(f"- Tổng số thủ tục lưu trữ lịch sử (archived): {total_archived}")
    print(f"- Tổng số mục hồ sơ / checklist: {total_checklists}")
    print(f"- Tổng số mục lệ phí: {total_fees}")
    print(f"- Tổng số biểu mẫu đính kèm: {total_files}")
    print("=" * 60)

    # Hiển thị 10 thủ tục mẫu
    print("\n🔍 10 THỦ TỤC ĐẦU TIÊN TRONG DATABASE:")
    cur.execute("""
        SELECT p.id, p.proc_code, p.name, p.domain, p.duration_desc
        FROM procedures p
        WHERE p.status = 'active'
        LIMIT 10
    """)
    rows = cur.fetchall()
    for r in rows:
        print(f"[{r[0]}] {r[1]} | {r[2]} ({r[3]}) - Thời hạn: {r[4] or 'Chưa rõ'}")

    # Xem chi tiết 1 thủ tục mẫu (Thủ tục kết hôn - ID 4)
    print("\n" + "=" * 60)
    print("📋 XEM THỬ CHI TIẾT THỦ TỤC SỐ 4 (ĐĂNG KÝ KẾT HÔN):")
    print("=" * 60)
    cur.execute("SELECT name, authority, description FROM procedures WHERE id = 4")
    p = cur.fetchone()
    if p:
        print(f"Tên: {p[0]}")
        print(f"Cơ quan: {p[1]}")
        print(f"Mô tả: {p[2][:150]}...")

        print("\n💰 Lệ phí:")
        cur.execute("SELECT fee_type, amount_text, condition FROM procedure_fees WHERE procedure_id = 4")
        for f in cur.fetchall():
            print(f"  - {f[0]}: {f[1]} ({f[2] or 'Không điều kiện'})")

        print("\n📑 Hồ sơ checklist (5 mục đầu):")
        cur.execute("SELECT item_type, content FROM procedure_checklists WHERE procedure_id = 4 LIMIT 5")
        for c in cur.fetchall():
            print(f"  [ ] ({c[0]}) {c[1]}")

    conn.close()

if __name__ == "__main__":
    inspect()
