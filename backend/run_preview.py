from __future__ import annotations

import sys
import traceback
from pathlib import Path


ROOT = Path(__file__).resolve().parent

path_str = str(ROOT)
if path_str not in sys.path:
    sys.path.insert(0, path_str)

import uvicorn


if __name__ == "__main__":
    try:
        (ROOT / "preview_start.log").write_text("starting\n", encoding="utf-8")
        uvicorn.run("main:app", host="127.0.0.1", port=8000)
        (ROOT / "preview_start.log").write_text("stopped\n", encoding="utf-8")
    except Exception:
        (ROOT / "preview_error.log").write_text(traceback.format_exc(), encoding="utf-8")
        raise
