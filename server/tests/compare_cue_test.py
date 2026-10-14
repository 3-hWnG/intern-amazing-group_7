"""Tách câu so sánh: 'A khác gì so với B' (liên từ sau cụm so sánh) cùng các dạng cũ. Chạy: python run_server.py server/tests/compare_cue_test.py"""
import os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(HERE))
from retrieval.refs import split_compare
OK = {
    "Đăng ký khai sinh khác gì so với đăng ký khai tử?": ["Đăng ký khai sinh", "đăng ký khai tử"],
    "So sánh đăng ký khai sinh và đăng ký khai tử.": ["đăng ký khai sinh", "đăng ký khai tử"],
    "đăng ký khai sinh với đăng ký khai tử khác nhau thế nào": ["đăng ký khai sinh", "đăng ký khai tử"],
}
for q, want in OK.items():
    got = split_compare(q)
    assert got and [g.strip(" .?") for g in got] == want, (q, got)
for q in ("Đăng ký khai sinh cần giấy tờ gì?", "khai sinh khác gì?"):
    assert split_compare(q) is None, q
print("OK compare_cue_test")
