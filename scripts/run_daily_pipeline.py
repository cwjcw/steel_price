from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_step(args: list[str], title: str) -> None:
    print(f"[pipeline] {title}")
    completed = subprocess.run([sys.executable, *args], cwd=ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run export -> summary -> MariaDB upload -> optional WeCom send")
    parser.add_argument("--strategy", default="", help="Optional single strategy, for example: cold_rolling")
    parser.add_argument("--run-date", default="", help="Summary date in YYYY-MM-DD, default is today")
    parser.add_argument("--skip-db", action="store_true", help="Skip MariaDB upload")
    parser.add_argument("--skip-send", action="store_true", help="Skip WeCom sending")
    parser.add_argument("--send-file", action="append", default=[], help="Extra file path to send, can be repeated")
    parser.add_argument("--touser", default="", help="Override WECHAT_TOUSERS for this run")
    args = parser.parse_args()

    export_args = ["scripts/mysteel_export_excel.py"]
    if args.strategy:
        export_args.extend(["--strategy", args.strategy])
    run_step(export_args, "export Mysteel files")

    summary_args = ["scripts/build_total_price.py"]
    if args.run_date:
        summary_args.extend(["--run-date", args.run_date])
    run_step(summary_args, "build Total_Price.xlsx")

    if not args.skip_db:
        db_args = ["scripts/upload_total_price_to_mariadb.py"]
        run_step(db_args, "upload Total_Price.xlsx to MariaDB")

    if not args.skip_send:
        send_args = ["scripts/send_wechat_files.py"]
        for file_path in args.send_file:
            send_args.extend(["--file", file_path])
        if args.touser:
            send_args.extend(["--touser", args.touser])
        run_step(send_args, "send files to WeCom")

    print("[pipeline] done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
