"""
STARTUP DIAGNOSTIC VERSION

This version is intentionally verbose. It:
1. Prints every startup step immediately.
2. Catches BaseException, including SystemExit (which `except Exception`
   does NOT catch).
3. Enables faulthandler.
4. Writes a permanent log to startup_debug.log.
5. Runs `api.routes` import in a CHILD Python process first, so if that
   import crashes/exits the interpreter, the parent process survives and
   reports the exact exit code and captured stderr/stdout.
"""

import sys
import os
import subprocess
import traceback
import faulthandler
from pathlib import Path
from contextlib import asynccontextmanager

faulthandler.enable()

APP_DIR = Path(__file__).resolve().parent
LOG_FILE = APP_DIR / "startup_debug.log"

# Make output both visible in terminal and permanently saved.
_log_handle = open(LOG_FILE, "a", encoding="utf-8", buffering=1)

def log(message: str) -> None:
    line = f"[STARTUP] {message}"
    print(line, flush=True)
    try:
        _log_handle.write(line + "\n")
        _log_handle.flush()
    except Exception:
        pass

def log_exception(prefix: str, exc: BaseException) -> None:
    log(f"{prefix}: {type(exc).__name__}: {exc!r}")
    traceback.print_exception(type(exc), exc, exc.__traceback__)
    try:
        traceback.print_exception(
            type(exc), exc, exc.__traceback__, file=_log_handle
        )
        _log_handle.flush()
    except Exception:
        pass


log("=" * 70)
log("01 - main.py STARTED")
log(f"02 - Python executable: {sys.executable}")
log(f"03 - Python version: {sys.version}")
log(f"04 - APP_DIR: {APP_DIR}")
log(f"05 - Log file: {LOG_FILE}")

try:
    sys.path.insert(0, str(APP_DIR))
    log("06 - sys.path configured")
except BaseException as e:
    log_exception("06 - FAILED configuring sys.path", e)
    raise


# ---------------------------------------------------------------------
# CRITICAL DIAGNOSTIC:
# Test api.routes in a separate Python process.
# This catches things such as SystemExit, os._exit(), native crashes,
# or interpreter-level failures that the normal try/except cannot catch.
# ---------------------------------------------------------------------
def preflight_import(module_name: str) -> None:
    log(f"07 - PRE-FLIGHT: testing import {module_name!r} in child process...")

    code = f"""
import sys
import faulthandler
faulthandler.enable()
sys.path.insert(0, {str(APP_DIR)!r})

print("CHILD: Python started", flush=True)
print("CHILD: importing {module_name}", flush=True)

try:
    __import__({module_name!r})
    print("CHILD: IMPORT SUCCESS", flush=True)
except BaseException as e:
    import traceback
    print(f"CHILD: CAUGHT {{type(e).__name__}}: {{e!r}}", flush=True)
    traceback.print_exc()
    raise
"""

    try:
        result = subprocess.run(
            [sys.executable, "-u", "-c", code],
            cwd=str(APP_DIR),
            capture_output=True,
            text=True,
            timeout=120,
            env=os.environ.copy(),
        )
    except subprocess.TimeoutExpired as e:
        log(f"07 - FAILED: import {module_name!r} timed out after 120 seconds")
        if e.stdout:
            log("07 - CHILD STDOUT:")
            for line in e.stdout.splitlines():
                log("    " + line)
        if e.stderr:
            log("07 - CHILD STDERR:")
            for line in e.stderr.splitlines():
                log("    " + line)
        raise RuntimeError(f"Pre-flight import timed out: {module_name}") from e
    except BaseException as e:
        log_exception("07 - FAILED launching child process", e)
        raise

    if result.stdout:
        log("07 - CHILD STDOUT:")
        for line in result.stdout.splitlines():
            log("    " + line)

    if result.stderr:
        log("07 - CHILD STDERR:")
        for line in result.stderr.splitlines():
            log("    " + line)

    log(f"07 - CHILD EXIT CODE: {result.returncode}")

    if result.returncode != 0:
        log(
            f"07 - !!! EXACT FAILURE: importing {module_name!r} "
            f"caused child Python to exit with code {result.returncode} !!!"
        )
        raise RuntimeError(
            f"Pre-flight import failed for {module_name!r}; "
            f"child exit code = {result.returncode}. "
            f"See startup_debug.log for full output."
        )

    log(f"07 - PRE-FLIGHT SUCCESS: {module_name!r}")


# This is the import that the previous diagnostic proved to be the
# stopping point.
preflight_import("api.routes")


# Now perform the real imports, with BaseException handling.
try:
    log("08 - REAL IMPORT: api.routes ...")
    from api.routes import router
    log("08 - SUCCESS: api.routes imported")
except BaseException as e:
    log_exception("08 - FAILED importing api.routes", e)
    raise

try:
    log("09 - REAL IMPORT: config ...")
    from config import HOST, PORT, STATIC_DIR
    log(
        f"09 - SUCCESS: config imported "
        f"(HOST={HOST!r}, PORT={PORT!r}, STATIC_DIR={STATIC_DIR!r})"
    )
except BaseException as e:
    log_exception("09 - FAILED importing config", e)
    raise

try:
    log("10 - IMPORT: uvicorn ...")
    import uvicorn
    log(f"10 - SUCCESS: uvicorn {getattr(uvicorn, '__version__', 'unknown')}")
except BaseException as e:
    log_exception("10 - FAILED importing uvicorn", e)
    raise

try:
    log("11 - IMPORT: FastAPI ...")
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    log("11 - SUCCESS: FastAPI imported")
except BaseException as e:
    log_exception("11 - FAILED importing FastAPI", e)
    raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    log("12 - FASTAPI LIFESPAN STARTED")

    try:
        log("13 - importing core.router ...")
        from core import router as semantic_router
        log("13 - SUCCESS: core.router")
    except BaseException as e:
        log_exception("13 - FAILED importing core.router", e)
        raise

    try:
        log("14 - importing core.vectorstore ...")
        from core import vectorstore
        log("14 - SUCCESS: core.vectorstore")
    except BaseException as e:
        log_exception("14 - FAILED importing core.vectorstore", e)
        raise

    try:
        log("15 - calling semantic_router.get_centroids() ...")
        semantic_router.get_centroids()
        log("15 - SUCCESS: get_centroids()")
    except BaseException as e:
        log_exception("15 - FAILED: get_centroids()", e)
        raise

    try:
        log("16 - calling vectorstore.get_collection() ...")
        vectorstore.get_collection()
        log("16 - SUCCESS: get_collection()")
    except BaseException as e:
        log_exception("16 - FAILED: get_collection()", e)
        raise

    log("17 - DATABASE + SEMANTIC ROUTER READY")
    yield
    log("18 - FASTAPI LIFESPAN ENDED")


try:
    log("19 - creating FastAPI app ...")
    app = FastAPI(
        title="Trợ Lý Pháp Lý - Nhóm 7",
        lifespan=lifespan,
    )
    log("19 - SUCCESS: FastAPI app created")
except BaseException as e:
    log_exception("19 - FAILED creating FastAPI app", e)
    raise


try:
    log(f"20 - mounting static directory: {STATIC_DIR!r}")
    app.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="static",
    )
    log("20 - SUCCESS: static directory mounted")
except BaseException as e:
    log_exception("20 - FAILED mounting static directory", e)
    raise


try:
    log("21 - registering API router ...")
    app.include_router(router)
    log("21 - SUCCESS: API router registered")
except BaseException as e:
    log_exception("21 - FAILED registering API router", e)
    raise


if __name__ == "__main__":
    log("22 - __main__ == True")
    log(f"23 - starting Uvicorn on {HOST}:{PORT}")
    try:
        uvicorn.run(
            app,
            host=HOST,
            port=PORT,
            log_level="debug",
        )
        log("24 - uvicorn.run() returned normally")
    except BaseException as e:
        log_exception("23 - FAILED inside uvicorn.run()", e)
        raise
else:
    log("22 - __main__ == False (main.py was imported)")
