from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
WORKDAY_API_TEMPLATE = "https://timor.tech/api/holiday/info/{date}"


def is_simple_workday(day_value: date) -> bool:
    return day_value.weekday() < 5


def default_target_date() -> str:
    return (date.today() - timedelta(days=1)).isoformat()


def is_workday_via_api(day_value: date) -> tuple[bool, str]:
    url = WORKDAY_API_TEMPLATE.format(date=day_value.isoformat())
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        fallback = is_simple_workday(day_value)
        return fallback, f"holiday API unavailable ({exc}); fallback weekday rule used"

    if payload.get("code") != 0:
        fallback = is_simple_workday(day_value)
        return fallback, f"holiday API returned code={payload.get('code')}; fallback weekday rule used"

    day_type = ((payload.get("type") or {}).get("type"))
    day_name = ((payload.get("type") or {}).get("name")) or "unknown"
    is_workday = day_type in (0, 3)
    return is_workday, f"holiday API type={day_type} ({day_name})"

def run_step(args: list[str], title: str) -> None:
    print(f"[pipeline] {title}")
    completed = subprocess.run([sys.executable, *args], cwd=ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run export -> summary -> MariaDB upload -> optional WeCom send")
    parser.add_argument("--strategy", default="", help="Optional single strategy, for example: cold_rolling")
    parser.add_argument("--run-date", default="", help="Summary date in YYYY-MM-DD, default is today")
    parser.add_argument("--target-date", default=default_target_date(), help="Export target date in YYYY-MM-DD, default is yesterday")
    parser.add_argument("--force-run-non-workday", action="store_true", help="Run even when target date is a non-workday")
    parser.add_argument("--skip-db", action="store_true", help="Skip MariaDB upload")
    parser.add_argument("--skip-send", action="store_true", help="Skip WeCom sending")
    parser.add_argument("--send-file", action="append", default=[], help="Extra file path to send, can be repeated")
    parser.add_argument("--touser", default="", help="Override WECHAT_TOUSERS for this run")
    args = parser.parse_args()

    target_day = date.fromisoformat(args.target_date)
    is_workday, workday_reason = is_workday_via_api(target_day)
    print(f"[pipeline] Workday check for target date {target_day.isoformat()}: {workday_reason}")
    if not args.force_run_non_workday and not is_workday:
        print(f"[pipeline] Target date is not a workday ({target_day.isoformat()}); exiting pipeline")
        return 0

    export_args = ["scripts/mysteel_export_excel.py", "--target-date", args.target_date]
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
