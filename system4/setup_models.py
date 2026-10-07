"""Tải/kiểm model cho System 4 (Set up first time.bat gọi; cần internet chỉ ở bước tải).

    python system4/setup_models.py reranker    # tải BAAI/bge-reranker-v2-m3 vào system4/models/ (bỏ qua nếu đã có)
    python system4/setup_models.py check-gpu   # báo torch có dùng được GPU không (chỉ cảnh báo, không làm hỏng cài đặt)
"""
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):   # bat chạy trước khi đặt PYTHONIOENCODING: tránh lỗi in chữ có dấu
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

MODELS = Path(__file__).resolve().parent / "models"
RERANKER_REPO = "BAAI/bge-reranker-v2-m3"
RERANKER_DIR = MODELS / "bge-reranker-v2-m3"


def reranker() -> int:
    if (RERANKER_DIR / "model.safetensors").is_file():
        print(f"  Reranker already downloaded: {RERANKER_DIR}")
        return 0
    from huggingface_hub import snapshot_download
    snapshot_download(RERANKER_REPO, local_dir=str(RERANKER_DIR),
                      allow_patterns=["*.json", "*.safetensors", "*.model"])
    print(f"  Reranker downloaded to {RERANKER_DIR}")
    return 0


def check_gpu() -> int:
    try:
        import torch
    except ImportError:
        print("  WARNING: torch is not installed (see requirements.txt).")
        return 0
    if torch.cuda.is_available():
        p = torch.cuda.get_device_properties(0)
        print(f"  GPU OK: {p.name}, {p.total_memory / 2**30:.1f} GB, torch {torch.__version__}")
    else:
        print(f"  WARNING: torch {torch.__version__} cannot see a GPU. The reranker will run on CPU (slower). "
              "Check the NVIDIA driver (needs CUDA 12.6 support).")
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    sys.exit({"reranker": reranker, "check-gpu": check_gpu}.get(cmd, lambda: print(__doc__) or 2)())
