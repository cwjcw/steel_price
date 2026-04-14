from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from pprint import pformat

from dotenv import load_dotenv

DEFAULT_TEXT_MESSAGE = "您好，请查收最新的钢铁价格追踪。"


def parse_recipients(raw: str) -> list[str]:
    normalized = raw.replace(";", ",").replace("|", ",").replace("\n", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def configure_wechat_import_path() -> str:
    configured = os.getenv("WECHAT_CODE_DIR", "").strip()
    if configured:
        target = str(Path(configured).expanduser().resolve())
        if target not in sys.path:
            sys.path.insert(0, target)
        return target

    pythonpath = os.getenv("PYTHONPATH", "").strip()
    if pythonpath:
        first = pythonpath.split(os.pathsep)[0].strip()
        if first:
            return first
    return ""


def env_presence(name: str) -> str:
    value = os.getenv(name)
    return "set" if value else "missing"


def format_wecom_result(result: object) -> str:
    if result is None:
        return "None"
    if isinstance(result, dict):
        errcode = result.get("errcode")
        errmsg = result.get("errmsg")
        if errcode is not None or errmsg is not None:
            return f"errcode={errcode}, errmsg={errmsg}"
    return pformat(result, compact=True)


def debug_context(path: Path, recipient: str, result: object | None = None) -> str:
    payload = {
        "file": str(path),
        "file_exists": path.exists(),
        "recipient": recipient,
        "cwd": str(Path.cwd()),
        "python_executable": sys.executable,
        "wechat_code_dir": os.getenv("WECHAT_CODE_DIR", ""),
        "pythonpath": os.getenv("PYTHONPATH", ""),
        "wx_corp_id": env_presence("WX_CORP_ID"),
        "wx_agent_id": env_presence("WX_AGENT_ID"),
        "wx_secret": env_presence("WX_SECRET"),
        "wechat_tousers": os.getenv("WECHAT_TOUSERS", ""),
        "result_type": type(result).__name__ if result is not None else "NoneType",
        "result": format_wecom_result(result),
    }
    return pformat(payload, compact=False, sort_dicts=False)


def ensure_wecom_success(result: object, recipient: str, path: Path) -> None:
    if result is None:
        raise RuntimeError(
            f"WeCom send returned None for recipient {recipient}.\nDebug context:\n{debug_context(path, recipient, result)}"
        )
    if isinstance(result, dict) and result.get("errcode") not in (None, 0):
        raise RuntimeError(
            f"WeCom send failed for recipient {recipient}: {format_wecom_result(result)}\nDebug context:\n{debug_context(path, recipient, result)}"
        )


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Send files to WeCom users through basic_code/wechat.py")
    parser.add_argument("--file", dest="files", action="append", default=[], help="File path to send, can be repeated")
    parser.add_argument("--touser", default=os.getenv("WECHAT_TOUSERS", ""), help="WeCom user ids, separated by comma/semicolon/|")
    parser.add_argument("--text", default=DEFAULT_TEXT_MESSAGE, help="Text message to send before files")
    args = parser.parse_args()

    default_file = os.getenv("WECHAT_DEFAULT_FILE", "").strip()
    file_args = [Path(item).expanduser() for item in args.files]
    if not file_args and default_file:
        file_args = [Path(default_file).expanduser()]
    if not file_args:
        raise RuntimeError("No file specified. Use --file or set WECHAT_DEFAULT_FILE in .env")

    recipients = parse_recipients(args.touser)
    if not recipients:
        raise RuntimeError("No recipients specified. Use --touser or set WECHAT_TOUSERS in .env")

    for path in file_args:
        if not path.exists():
            raise RuntimeError(f"File not found: {path}")

    import_root = configure_wechat_import_path()

    try:
        from wechat import WeChatPusher  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Unable to import wechat.py. Set WECHAT_CODE_DIR in .env or PYTHONPATH to the basic_code repository root before running this script."
        ) from exc

    print("WeCom debug summary:")
    print(pformat({
        "python_executable": sys.executable,
        "wechat_code_dir": os.getenv("WECHAT_CODE_DIR", ""),
        "pythonpath": os.getenv("PYTHONPATH", ""),
        "resolved_import_root": import_root,
        "wx_corp_id": env_presence("WX_CORP_ID"),
        "wx_agent_id": env_presence("WX_AGENT_ID"),
        "wx_secret": env_presence("WX_SECRET"),
        "recipients": recipients,
        "files": [str(path) for path in file_args],
    }, compact=False, sort_dicts=False))

    pusher = WeChatPusher()
    failures: list[str] = []
    for recipient in recipients:
        if args.text.strip():
            print(f"Sending text message to {recipient} ...")
            result = pusher.send_app_msg(args.text.strip(), msg_type="text", touser=recipient)
            error = ensure_wecom_success(result, recipient, Path(file_args[0]))
            if error:
                failures.append(error)
                print(error)
                continue
            print(f"Sent text message to {recipient}: {format_wecom_result(result)}")
    for path in file_args:
        for recipient in recipients:
            print(f"Sending {path.name} to {recipient} ...")
            result = pusher.send_app_msg(str(path), msg_type="file", touser=recipient)
            error = ensure_wecom_success(result, recipient, path)
            if error:
                failures.append(error)
                print(error)
                continue
            print(f"Sent {path.name} to {recipient}: {format_wecom_result(result)}")
    if failures:
        print(f"WeCom sending completed with {len(failures)} failure(s).")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
