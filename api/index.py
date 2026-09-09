import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from webapp import app
    application = app
except Exception as e:
    import traceback
    from flask import Flask
    err_tb = traceback.format_exc()
    print(f"CRITICAL INIT ERROR:\n{err_tb}", flush=True)
    app = Flask(__name__)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def catch_all(path):
        return f"<pre style='color:#f43f5e;background:#181826;padding:20px;border-radius:8px;font-family:monospace;'>CRITICAL INIT ERROR:\n\n{err_tb}</pre>", 500
    application = app
