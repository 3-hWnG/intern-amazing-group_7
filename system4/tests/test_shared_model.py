"""Strict và Friendly dùng chung một model: model chọn ở ⚙ Cài đặt (FRIENDLY_MODEL) cũng là model của bước LLM Strict.
Chạy: python run_server.py system4/tests/test_shared_model.py   (không cần Ollama; ô chọn model chỉ có options=[] khi Ollama tắt)"""
import os
import sys
import tempfile

SERVER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "server")
sys.path.insert(0, SERVER)
TMP = tempfile.mkdtemp()
os.environ.update(S3_DB_PATH=os.path.join(TMP, "s3.db"), S3_USE_LLM="0", S4_ENABLED="1", S4_WARMUP="0",
                  S4_RUNTIME_DIR=os.path.join(TMP, "s4"), OLLAMA_HOST="http://127.0.0.1:1")

from fastapi.testclient import TestClient
import main
from core import llm
from system3.system4.server import auth

with TestClient(main.app) as c:
    c.cookies.set(auth.COOKIE, c.post("/s4/auth/signup", json={"username": "boss", "password": "123456"}).cookies.get(auth.COOKIE))
    from system3.system4.server import settings
    assert llm.model_name() == settings.get("FRIENDLY_MODEL")
    settings.save({"FRIENDLY_MODEL": "model-gia:1b"})
    assert llm.model_name() == "model-gia:1b"                       # Strict đổi theo ngay, không cần khởi động lại
    assert c.get("/health").json()["model"] == "model-gia:1b"
    spec = next(s for s in settings.describe() if s["key"] == "FRIENDLY_MODEL")
    assert spec["options"] == [] and "Strict" in spec["label"]       # Ollama tắt -> danh sách rỗng, ô vẫn gõ tay được
    settings.reset(["FRIENDLY_MODEL"])
print("OK test_shared_model")
