from __future__ import annotations

import argparse
import os
from pathlib import Path
from pprint import pformat

from dotenv import load_dotenv


def parse_recipients(raw: str) -> list[str]:
    normalized = raw.replace(";", ",").replace("|", ",").replace("\n", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def format_wecom_result(result: object) -> str:
    if result is None:
        return "None"
    if isinstance(result, dict):
        errcode = result.get("errcode")
        errmsg = result.get("errmsg")
        if errcode is not None or errmsg is not None:
            return f"errcode={errcode}, errmsg={errmsg}"
    return pformat(result, compact=True)


def ensure_wecom_success(result: object, recipient: str) -> None:
    if result is None:
        raise RuntimeError(
            f"WeCom send returned None for recipient {recipient}. Check PYTHONPATH, WX_* environment variables, and upstream API responses."
        )
    if isinstance(result, dict) and result.get("errcode") not in (None, 0):
        raise RuntimeError(
            f"WeCom send failed for recipient {recipient}: {format_wecom_result(result)}"
        )


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Send files to WeCom users through basic_code/wechat.py")
    parser.add_argument("--file", dest="files", action="append", default=[], help="File path to send, can be repeated")
    parser.add_argument("--touser", default=os.getenv("WECHAT_TOUSERS", ""), help="WeCom user ids, separated by comma/semicolon/|")
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

    try:
        from wechat import WeChatPusher  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Unable to import wechat.py. Set PYTHONPATH to the basic_code repository root before running this script."
        ) from exc

    pusher = WeChatPusher()
    for path in file_args:
        for recipient in recipients:
            result = pusher.send_app_msg(str(path), msg_type="file", touser=recipient)
            ensure_wecom_success(result, recipient)
            print(f"Sent {path.name} to {recipient}: {format_wecom_result(result)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
