"""Chạy một script đo có sẵn của eval/ (run_golden.py, run_pseudo.py...) với canh nhiệt: chèn eval/thermal.py guard() + nghỉ theo nhịp
vào MỖI lần gọi answer_adapter.adapter, không sửa script gốc (máy không quá 70 °C, yêu cầu 24/10).

    python run_server.py eval/hard/paced.py eval/run_golden.py thu-tuc --by status
"""
import os
import runpy
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL = os.path.dirname(HERE)
sys.path[:0] = [EVAL]
import answer_adapter  # noqa: E402
from thermal import guard, low_priority  # noqa: E402

low_priority()
_orig = answer_adapter.adapter
DUTY = float(os.environ.get("THERMAL_DUTY", "1.0"))


def paced(turns, *a, **k):
    guard(every=3, label="paced")
    t0 = time.time()
    out = _orig(turns, *a, **k)
    time.sleep(min(2.0, (time.time() - t0) * DUTY))
    return out


answer_adapter.adapter = paced
script = sys.argv[1]
sys.argv = [script] + sys.argv[2:]
runpy.run_path(os.path.join(os.path.dirname(EVAL), script) if not os.path.isabs(script) else script, run_name="__main__")
