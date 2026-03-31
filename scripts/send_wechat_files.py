from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv


def parse_recipients(raw: str) -> list[str]:
    normalized = raw.replace(";", ",").replace("|", ",").replace("\n", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


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
            "Unable to import wechat.py. Set BASIC_CODE_ROOT in .env or environment variables so Python can import the basic_code repository."
        ) from exc

    pusher = WeChatPusher()
    for path in file_args:
        for recipient in recipients:
            result = pusher.send_app_msg(str(path), msg_type="file", touser=recipient)
            print(f"Sent {path.name} to {recipient}: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
