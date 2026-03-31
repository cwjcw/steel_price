from __future__ import annotations

import os
import sys
from pathlib import Path


def _load_local_dotenv() -> None:
    root = Path(__file__).resolve().parent
    dotenv_path = root / ".env"
    if not dotenv_path.exists():
        return
    try:
        from dotenv import load_dotenv
    except Exception:
        return
    load_dotenv(dotenv_path, override=False)


def _add_basic_code_to_path() -> None:
    configured = os.getenv("BASIC_CODE_ROOT", "").strip()
    if not configured:
        return
    root = Path(configured).expanduser()
    if not root.exists():
        return
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


_load_local_dotenv()
_add_basic_code_to_path()
