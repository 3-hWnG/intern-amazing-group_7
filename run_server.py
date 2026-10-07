"""Launcher: chạy server dù thư mục gốc đặt tên gì (clone về `abc/`, `intern-amazing-group_7/`...).
Mã import theo dạng `system3.*`; file này đăng ký thư mục chứa nó làm package `system3`, không cần PYTHONPATH.
    python run_server.py                          # server, http://127.0.0.1:8300 (APP_HOST/APP_PORT đổi được)
    python run_server.py -m system3.data.build    # chạy module bất kỳ của package (build DB, test_data, eval...)
    python run_server.py server/tests/memory_test.py   # hoặc một script, với `system3` đã đăng ký
"""
import importlib.machinery
import importlib.util
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def register_package(root: Path = ROOT, name: str = "system3"):
    """sys.modules[name] = package trỏ vào `root` (thay cho việc đặt tên thư mục = system3 + PYTHONPATH)."""
    spec = importlib.machinery.ModuleSpec(name, None, is_package=True)
    spec.submodule_search_locations = [str(root)]
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    return mod


if __name__ == "__main__":
    register_package()
    args = sys.argv[1:]
    if args[:1] == ["-m"] and len(args) >= 2:
        sys.argv = args[1:]
        runpy.run_module(args[1], run_name="__main__", alter_sys=True)
    elif args and args[0].endswith(".py"):
        sys.argv = args
        sys.path.insert(0, str(Path(args[0]).resolve().parent))
        runpy.run_path(args[0], run_name="__main__")
    else:
        runpy.run_path(str(ROOT / "server" / "main.py"), run_name="__main__")
