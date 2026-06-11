#!/usr/bin/env python3
"""
Run once in the background: python launcher.py
Then click 'Ready' in the web app — copilot.py starts automatically.
"""
import os
import sys
import platform
import subprocess
import threading
from pathlib import Path
from flask import Flask, jsonify, request

app = Flask(__name__)
BASE_DIR = Path(__file__).parent
_proc = None


def _read_dotenv(path: Path) -> dict:
    """Parse .env without requiring python-dotenv."""
    env = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            # Strip inline comments and surrounding quotes
            v = v.split("#")[0].strip().strip('"').strip("'")
            env[k.strip()] = v
    except FileNotFoundError:
        pass
    return env


# Merge .env into the environment passed to every copilot subprocess.
# os.environ takes lower priority so explicit shell exports still win.
_DOTENV = _read_dotenv(BASE_DIR / ".env")
_BASE_ENV = {**_DOTENV, **os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}

# On Windows prefer pythonw.exe (no-console GUI host) from the project venv.
# pythonw.exe is specifically designed for Tkinter/GUI apps — it launches the
# window without flashing a black console, and is truly independent from the
# terminal that spawned launcher.py.
def _find_python():
    if platform.system() == "Windows":
        for name in ("pythonw.exe", "python.exe"):
            p = BASE_DIR / "venv" / "Scripts" / name
            if p.exists():
                return str(p)
    else:
        p = BASE_DIR / "venv" / "bin" / "python"
        if p.exists():
            return str(p)
    return sys.executable

PYTHON = _find_python()

# Windows: CREATE_NEW_PROCESS_GROUP ensures copilot.py lives independently of
# the launcher and won't be killed when the parent console closes.
_POPEN_KWARGS = {"cwd": str(BASE_DIR), "env": _BASE_ENV}
if platform.system() == "Windows":
    _POPEN_KWARGS["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP


@app.after_request
def _cors(r):
    r.headers["Access-Control-Allow-Origin"] = "*"
    r.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return r


@app.route("/launch", methods=["POST", "OPTIONS"])
def launch():
    if request.method == "OPTIONS":
        return "", 204
    global _proc
    if _proc and _proc.poll() is None:
        _proc.terminate()
        _proc.wait()
    log = open(BASE_DIR / "copilot.log", "w", encoding="utf-8")
    _POPEN_KWARGS["stdout"] = log
    _POPEN_KWARGS["stderr"] = log
    _proc = subprocess.Popen([PYTHON, str(BASE_DIR / "copilot.py")], **_POPEN_KWARGS)
    print(f"  Launched copilot.py  (pid {_proc.pid})  using  {PYTHON}  — see copilot.log")
    return jsonify({"status": "launched", "pid": _proc.pid})


@app.route("/status", methods=["GET"])
def status():
    running = _proc is not None and _proc.poll() is None
    return jsonify({"running": running, "pid": _proc.pid if running else None})


@app.route("/shutdown", methods=["POST"])
def shutdown():
    def _exit():
        import time as _t
        _t.sleep(0.3)   # let response flush before killing
        os._exit(0)
    threading.Thread(target=_exit, daemon=True).start()
    return jsonify({"status": "shutting down"})


if __name__ == "__main__":
    port = int(os.getenv("LAUNCHER_PORT", "4004"))
    print("=" * 48)
    print("  Interview Copilot — Launcher")
    print("=" * 48)
    print(f"\n  Python : {PYTHON}")
    print(f"  Port   : http://localhost:{port}")
    print("  Click 'Ready' in the web app to launch copilot.py\n")
    app.run(port=port, debug=False, use_reloader=False)
