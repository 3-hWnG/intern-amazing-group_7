import sys, time
sys.path.insert(0, ".")
from planner_adapter import adapter
qs = ["Nếu thuộc hộ nghèo thì đăng ký tạm trú có được miễn phí không?",
      "Làm hộ chiếu mới ở đâu?",
      "Khai sinh cho con cần giấy tờ gì? Còn kết hôn có mất lệ phí không?",
      "Đăng ký khai sinh cần giấy tờ gì?"]
for q in qs:
    t = time.time()
    o = adapter([{"role": "user", "text": q}])
    print(round(time.time() - t, 1), "s |", q, "\n   ", o["behavior"], [(x["proc_id"], x["fields"], x["quantity"]) for x in o["tasks"]], o["extra"])
