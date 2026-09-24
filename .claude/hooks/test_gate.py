"""Hook nhắc chạy bộ kiểm tra hồi quy của V10.5.

- `mark` (PostToolUse Edit|Write): vừa sửa file .py trong Backend/ hoặc
  Database/pipeline/ -> đặt cờ.
- `stop` (Stop): có cờ -> xoá cờ, chặn kết thúc lượt, bắt Claude HỎI user có
  chạy Evaluation/check_natural_questions.py không (chỉ chạy khi user đồng ý).
  Mỗi lượt hỏi tối đa 1 lần.
"""
import json
import sys
import tempfile
from pathlib import Path

FLAG = Path(tempfile.gettempdir()) / "reimagine_v105_dirty"
WATCHED = ("/Backend/", "/Database/pipeline/")

REASON = ("Lượt này đã sửa file Python trong Backend/ hoặc Database/pipeline/. Dùng "
          "AskUserQuestion hỏi user có muốn chạy bộ kiểm tra không: "
          ".venv\\Scripts\\python.exe Evaluation\\check_natural_questions.py "
          "(không cần Ollama, ~10 giây). Chỉ chạy nếu user đồng ý, rồi báo số [OK]/FAIL "
          "và dòng '100 câu: chip …, đúng top-3 …' thật.")


def main(mode: str) -> None:
    data = json.load(sys.stdin)
    if mode == "mark":
        path = ((data.get("tool_input") or {}).get("file_path") or "").replace("\\", "/")
        if path.endswith(".py") and any(w in path for w in WATCHED):
            FLAG.touch()
    elif mode == "stop" and not data.get("stop_hook_active") and FLAG.exists():
        FLAG.unlink()
        print(json.dumps({"decision": "block", "reason": REASON}))


if __name__ == "__main__":
    main(sys.argv[1])
