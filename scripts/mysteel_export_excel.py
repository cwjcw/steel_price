from __future__ import annotations

import argparse
import json
import random
import sys
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from DrissionPage import ChromiumOptions, ChromiumPage

ZH_PRODUCT = "\u54c1\u540d"
ZH_SPEC = "\u89c4\u683c"
ZH_MATERIAL = "\u6750\u8d28"
ZH_MARKET = "\u5e02\u573a"
ZH_MILL = "\u94a2\u5382"
ZH_FREQUENCY = "\u4ef7\u683c\u9891\u5ea6"
ZH_BY_DATE = "\u6309\u65e5\u671f"
ZH_LATE_PRICE = "\u665a\u76d8\u4ef7\u683c"
ZH_PUBLISH_TIME = "\u53d1\u5e03\u65f6\u95f4"
ZH_DATE_RANGE = "\u65e5\u671f\u6bb5"
ZH_START_TIME = "\u5f00\u59cb\u65f6\u95f4"
ZH_END_TIME = "\u7ed3\u675f\u65f6\u95f4"
ZH_SEARCH = "\u641c\u7d22"
ZH_EXPORT_EXCEL = "\u5bfc\u51faExcel"
ZH_EXPORT = "\u5bfc\u51fa"
ZH_EXPORT_DATA = "\u5bfc\u51fa\u6570\u636e"
ZH_LOGIN = "\u767b\u5f55"
ZH_ACCOUNT_LOGIN = "\u8d26\u53f7\u767b\u5f55"
ZH_GUIDE_CLOSE = "\u5173\u95ed\u5f15\u5bfc"
ZH_SELECTED = "\u5df2\u9009"
ZH_ONE_ROW = "1\u6761"
ZH_COLD_COIL = "\u51b7\u5377"
ZH_TAIAN = "\u6cf0\u5b89"
ZH_QRSTU = "QRSTU"
ZH_Q195 = "Q195"
ZH_TAISHAN_STEEL = "\u6cf0\u5c71\u94a2\u94c1"
ZH_EXPECTED_NAME = "Mysteel\u4ef7\u683c\u4e2d\u5fc3_\u51b7\u5377-1_1250_C-Q195-\u6cf0\u5b89-\u6cf0\u5c71\u94a2\u94c1_2026-03-26.xlsx"

TEST_USERNAME = "18559698081"
TEST_PASSWORD = "123456cc"
DEFAULT_URL = "https://price.mysteel.com/#/price-search?breedId=1-3"
CHROME_BINARY_CANDIDATES = [
    Path(r"C:\Users\KN426\AppData\Local\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
]


@dataclass(frozen=True)
class Query:
    product_name: str = ZH_COLD_COIL
    specification: str = "1*1250*C"
    material: str = ZH_Q195
    market_group: str = ZH_QRSTU
    market: str = ZH_TAIAN
    mill: str = ZH_TAISHAN_STEEL
    price_scope: str = ZH_BY_DATE
    publish_time: str = ZH_LATE_PRICE
    target_date: str = "2026-03-25"
    expected_filename: str = ZH_EXPECTED_NAME


def chrome_binary() -> str | None:
    for candidate in CHROME_BINARY_CANDIDATES:
        if candidate.exists():
            return str(candidate)
    return None


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def default_target_date() -> str:
    return (date.today() - timedelta(days=1)).isoformat()


def human_pause(low: float = 0.8, high: float = 1.6) -> None:
    time.sleep(random.uniform(low, high))


def log_stage(stage: str) -> None:
    print(f"[{datetime.now().strftime("%H:%M:%S")}] {stage}")


def wait_until(page: ChromiumPage, condition_js: str, timeout: float = 10, interval: float = 0.25) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        try:
            if page.run_js(condition_js):
                return True
        except Exception:
            pass
        time.sleep(interval)
    return False


def create_page(user_data_dir: Path, download_dir: Path) -> ChromiumPage:
    user_data_dir.mkdir(parents=True, exist_ok=True)
    download_dir.mkdir(parents=True, exist_ok=True)

    co = ChromiumOptions()
    binary = chrome_binary()
    if binary:
        co.set_browser_path(binary)
    co.set_user_data_path(str(user_data_dir))
    page = ChromiumPage(co)
    page.set.download_path(str(download_dir))
    page.set.window.max()
    return page


def latest_file(directory: Path, pattern: str) -> Path | None:
    files = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def ensure_price_page(page: ChromiumPage, target_url: str) -> None:
    try:
        current_url = page.url or ""
    except Exception:
        current_url = ""
    if "price-search" in current_url:
        return
    page.get(target_url)
    page.wait.load_start()
    page.wait.doc_loaded()
    human_pause(1.0, 1.8)


def dismiss_intro_guide(page: ChromiumPage) -> None:
    for locator in (
        f'text={ZH_GUIDE_CLOSE}',
        f'xpath://button[contains(normalize-space(.),"{ZH_GUIDE_CLOSE}")]',
        f'xpath://div[contains(@class,"guide") or contains(@class,"driver")]//button[contains(normalize-space(.),"{ZH_GUIDE_CLOSE}")]',
    ):
        try:
            ele = page.ele(locator, timeout=2)
        except Exception:
            ele = None
        if not ele:
            continue
        try:
            ele.click(by_js=True)
        except Exception:
            try:
                ele.click()
            except Exception:
                continue
        human_pause(0.9, 1.6)
        return


def page_has_login_entry(page: ChromiumPage) -> bool:
    try:
        return bool(page.ele('xpath://div[contains(@class,"login-bar")]//*[contains(normalize-space(.),"' + ZH_LOGIN + '")]', timeout=2))
    except Exception:
        return False


def input_value(ele, value: str) -> bool:
    if not ele:
        return False
    try:
        ele.clear(by_js=True)
    except Exception:
        pass
    try:
        ele.input(value, clear=True)
        human_pause(0.9, 1.5)
        return True
    except Exception:
        pass
    try:
        ele.click(by_js=True)
        ele.input(value)
        human_pause(0.9, 1.5)
        return True
    except Exception:
        return False


def auto_login_if_needed(page: ChromiumPage, username: str, password: str, target_url: str) -> None:
    if not page_has_login_entry(page):
        return

    login_entry = page.ele('xpath://div[contains(@class,"login-bar")]//*[contains(normalize-space(.),"' + ZH_LOGIN + '")]', timeout=4)
    if not login_entry:
        return
    login_entry.click(by_js=True)
    human_pause(1.0, 1.6)

    modal_ok = wait_until(
        page,
        """
        const modal = document.querySelector('.login-common');
        return !!modal && modal.offsetParent !== null;
        """,
        timeout=15,
        interval=0.3,
    )
    if not modal_ok:
        raise RuntimeError("Login modal did not appear")

    log_stage("?????????")
    account_tab = page.ele(
        'xpath://div[contains(@class,"login-common")]//*[contains(@class,"form-tab-account") and contains(normalize-space(.),"' + ZH_ACCOUNT_LOGIN + '")]',
        timeout=6,
    )
    if not account_tab:
        raise RuntimeError("Account-login tab not found")
    account_tab.click(by_js=True)
    human_pause(1.2, 2.0)

    username_input = page.ele(
        'xpath://div[contains(@class,"login-common")]//div[contains(@class,"form-content") and not(contains(@style,"display: none"))]//div[contains(@class,"form-content-username")]//input',
        timeout=6,
    )
    password_input = page.ele(
        'xpath://div[contains(@class,"login-common")]//div[contains(@class,"form-content") and not(contains(@style,"display: none"))]//div[contains(@class,"form-content-password")]//input[@type="password"]',
        timeout=6,
    )
    log_stage("???????")
    if not input_value(username_input, username):
        raise RuntimeError("Could not fill username")
    log_stage("??????")
    if not input_value(password_input, password):
        raise RuntimeError("Could not fill password")
    human_pause(1.0, 1.8)

    log_stage("??????")
    login_button = page.ele(
        'xpath://div[contains(@class,"login-common")]//div[contains(@class,"form-button-login") and contains(normalize-space(.),"' + ZH_LOGIN + '")]',
        timeout=6,
    )
    if not login_button:
        raise RuntimeError("Login submit button not found")
    login_button.click(by_js=True)

    logged_in = wait_until(
        page,
        """
        const entry = document.querySelector('.login-bar .topbar-nav-login');
        return !entry;
        """,
        timeout=30,
        interval=0.5,
    )
    if not logged_in:
        raise RuntimeError("Login did not complete in time")

    human_pause(2.0, 3.0)
    log_stage("??????????????")
    ensure_price_page(page, target_url)


def form_item_by_label(page: ChromiumPage, label_text: str, timeout: float = 8):
    return page.ele(
        f'xpath://div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"{label_text}")]]',
        timeout=timeout,
    )


def click_checkbox_in_group(page: ChromiumPage, group_label: str, option_label: str, timeout: float = 8) -> None:
    group = form_item_by_label(page, group_label, timeout=timeout)
    if not group:
        raise RuntimeError(f"Checkbox group not found: {group_label}")
    option = group.ele(
        f'xpath:.//label[contains(@class,"el-checkbox")][.//span[contains(@class,"el-checkbox__label") and contains(normalize-space(.),"{option_label}")]]',
        timeout=timeout,
    )
    if not option:
        raise RuntimeError(f"Checkbox option not found: {group_label} -> {option_label}")
    option.click(by_js=True)
    human_pause(0.9, 1.6)


def click_radio_button_in_group(page: ChromiumPage, group_label: str, option_label: str, timeout: float = 8) -> None:
    group = form_item_by_label(page, group_label, timeout=timeout)
    if not group:
        raise RuntimeError(f"Radio-button group not found: {group_label}")
    option = group.ele(
        f'xpath:.//label[contains(@class,"el-radio-button")][.//span[contains(@class,"el-radio-button__inner") and contains(normalize-space(.),"{option_label}")]]',
        timeout=timeout,
    )
    if not option:
        raise RuntimeError(f"Radio-button option not found: {group_label} -> {option_label}")
    option.click(by_js=True)
    human_pause(0.9, 1.6)


def click_radio_in_group(page: ChromiumPage, group_label: str, option_label: str, timeout: float = 8) -> None:
    group = form_item_by_label(page, group_label, timeout=timeout)
    if not group:
        raise RuntimeError(f"Radio group not found: {group_label}")
    option = group.ele(
        f'xpath:.//label[contains(@class,"el-radio")][.//span[contains(@class,"el-radio__label") and contains(normalize-space(.),"{option_label}")]]',
        timeout=timeout,
    )
    if not option:
        raise RuntimeError(f"Radio option not found: {group_label} -> {option_label}")
    option.click(by_js=True)
    human_pause(0.9, 1.6)


def click_market_tab(page: ChromiumPage, tab_label: str, timeout: float = 8) -> str:
    tab = page.ele(
        f'xpath://div[contains(@class,"el-tabs__item") and @role="tab" and contains(normalize-space(.),"{tab_label}")]',
        timeout=timeout,
    )
    if not tab:
        raise RuntimeError(f"Market tab not found: {tab_label}")
    pane_id = tab.attr("aria-controls") or ""
    tab.click(by_js=True)
    human_pause(0.9, 1.6)
    return pane_id


def click_market_option(page: ChromiumPage, pane_id: str, option_label: str, timeout: float = 8) -> None:
    pane = page.ele(
        f'xpath://div[@id="{pane_id}" and contains(@class,"el-tab-pane") and not(contains(@style,"display: none"))]',
        timeout=timeout,
    )
    if not pane:
        raise RuntimeError(f"Visible market pane not found: {pane_id}")
    option = pane.ele(
        f'xpath:.//label[contains(@class,"el-checkbox")][.//span[contains(@class,"el-checkbox__label") and contains(normalize-space(.),"{option_label}")]]',
        timeout=timeout,
    )
    if not option:
        raise RuntimeError(f"Market option not found: {option_label}")
    option.click(by_js=True)
    human_pause(0.9, 1.6)


def click_publish_type(page: ChromiumPage, label_text: str, timeout: float = 8) -> None:
    group = form_item_by_label(page, ZH_PUBLISH_TIME, timeout=timeout)
    if not group:
        raise RuntimeError(f"Publish-time group not found: {ZH_PUBLISH_TIME}")

    trigger = group.ele(
        'xpath:.//div[contains(@class,"el-select")]//input[contains(@class,"el-input__inner")]',
        timeout=timeout,
    )
    if not trigger:
        raise RuntimeError("Publish-type dropdown trigger not found")

    trigger.click(by_js=True)
    human_pause(0.9, 1.6)

    option = page.ele(
        f'xpath://div[contains(@class,"el-select-dropdown") and not(contains(@style,"display: none"))]//*[contains(@class,"el-select-dropdown__item")][contains(normalize-space(.),"{label_text}")]',
        timeout=4,
    )
    if not option:
        option = page.ele(
            f'xpath://div[contains(@class,"el-popper") and not(contains(@style,"display: none"))]//*[contains(@class,"el-select-dropdown__item")][contains(normalize-space(.),"{label_text}")]',
            timeout=4,
        )
    if not option:
        raise RuntimeError(f"Publish-type option not found: {label_text}")
    option.click(by_js=True)
    human_pause(0.9, 1.6)


def set_date_via_picker(page: ChromiumPage, target_date: str, timeout: float = 10) -> None:
    target = datetime.strptime(target_date, "%Y-%m-%d").date()
    day = str(target.day)

    editor = page.ele(
        f'xpath://div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"{ZH_PUBLISH_TIME}")]]//div[contains(@class,"el-date-editor--daterange") and .//input[@placeholder="{ZH_START_TIME}"] and .//input[@placeholder="{ZH_END_TIME}"]]',
        timeout=timeout,
    )
    if not editor:
        raise RuntimeError("Date-range editor not found")
    editor.click(by_js=True)
    human_pause(0.6, 1.0)

    day_locator = (
        'xpath://div[contains(@class,"el-picker-panel") and not(contains(@style,"display: none"))]'
        f'//td[contains(@class,"available") and not(contains(@class,"disabled"))]//span[normalize-space(text())="{day}"]'
    )
    day_eles = page.eles(day_locator, timeout=4)
    if not day_eles:
        raise RuntimeError(f"Could not find selectable date cell for day {day}")

    day_eles[0].click(by_js=True)
    human_pause(0.2, 0.4)
    day_eles[0].click(by_js=True)
    human_pause(0.6, 1.0)


def click_search(page: ChromiumPage) -> None:
    button = page.ele(
        f'xpath://div[contains(@class,"operate-buttons")]//button[contains(@class,"el-button--primary")][.//span[contains(normalize-space(.),"{ZH_SEARCH}")]]',
        timeout=8,
    )
    if not button:
        raise RuntimeError("Search button not found")
    button.click(by_js=True)
    human_pause(2.5, 4.0)


def wait_for_result_row(page: ChromiumPage, query: Query, timeout: float = 15):
    row_locator = (
        'xpath://table[contains(@class,"el-table__body")]//tr[contains(@class,"el-table__row")]'
        f'[.//td[contains(normalize-space(.),"{query.product_name}")]'
        f' and .//td[contains(normalize-space(.),"{query.specification}")]'
        f' and .//td[contains(normalize-space(.),"{query.material}")]'
        f' and .//td[contains(normalize-space(.),"{query.market}")]'
        f' and .//td[contains(normalize-space(.),"{query.mill}")]]'
    )
    row = page.ele(row_locator, timeout=timeout)
    if not row:
        raise RuntimeError("Matching result row not found")
    return row


def wait_for_selected_state(page: ChromiumPage, timeout: float = 10) -> None:
    ok = wait_until(
        page,
        f"""
        const box = document.querySelector('.table-operate-buttons');
        if (!box) return false;
        const text = box.innerText || '';
        return text.includes('{ZH_SELECTED}') && text.includes('{ZH_ONE_ROW}');
        """,
        timeout=timeout,
        interval=0.3,
    )
    if not ok:
        raise RuntimeError("Selected-state indicator did not appear")


def select_search_result(page: ChromiumPage, query: Query) -> None:
    row = wait_for_result_row(page, query)
    checkbox = row.ele(
        'xpath:.//td[contains(@class,"el-table-column--selection")]//label[contains(@class,"el-checkbox")]',
        timeout=5,
    )
    if not checkbox:
        raise RuntimeError("Result-row checkbox not found")
    checkbox.click(by_js=True)
    human_pause(0.6, 1.0)
    wait_for_selected_state(page, timeout=10)


def click_export_excel_button(page: ChromiumPage) -> None:
    button = page.ele(
        f'xpath://div[contains(@class,"table-operate-buttons")]//button[contains(@class,"el-button--primary")][.//span[contains(normalize-space(.),"{ZH_EXPORT_EXCEL}")]]',
        timeout=8,
    )
    if not button:
        raise RuntimeError("Bottom export Excel button not found")
    button.click(by_js=True)
    human_pause(0.8, 1.2)


def confirm_export_dialog(page: ChromiumPage) -> None:
    ok = wait_until(
        page,
        f"""
        const body = document.querySelector('.el-dialog__body');
        if (!body) return false;
        const title = body.querySelector('.dialog-title');
        return !!title && (title.innerText || '').includes('{ZH_EXPORT_DATA}');
        """,
        timeout=10,
        interval=0.3,
    )
    if not ok:
        raise RuntimeError("Export dialog did not appear")

    button = page.ele(
        f'xpath://div[contains(@class,"el-dialog__body")]//div[contains(@class,"actions")]//button[contains(@class,"el-button--primary")][.//span[contains(normalize-space(.),"{ZH_EXPORT}")]]',
        timeout=6,
    )
    if not button:
        raise RuntimeError("Export confirm button not found")
    button.click(by_js=True)
    human_pause(0.8, 1.2)


def wait_for_download(page: ChromiumPage, download_dir: Path, timeout: int = 60) -> Path:
    try:
        page.wait.downloads_done(timeout=timeout)
    except Exception:
        pass

    end = time.time() + timeout
    while time.time() < end:
        latest = latest_file(download_dir, "*.xlsx")
        partials = list(download_dir.glob("*.crdownload")) + list(download_dir.glob("*.tmp"))
        if latest and not partials:
            return latest
        time.sleep(1)
    raise TimeoutError("Timed out waiting for Excel download")


def apply_filters(page: ChromiumPage, query: Query) -> None:
    log_stage("????????")
    ensure_price_page(page, DEFAULT_URL)
    page.wait.ele_displayed(f'text={ZH_SPEC}', timeout=20)
    human_pause(1.0, 1.8)
    dismiss_intro_guide(page)

    log_stage(f"??????: {query.product_name}")
    click_checkbox_in_group(page, ZH_PRODUCT, query.product_name)
    log_stage(f"??????: {query.specification}")
    click_checkbox_in_group(page, ZH_SPEC, query.specification)
    log_stage(f"??????: {query.material}")
    click_checkbox_in_group(page, ZH_MATERIAL, query.material)

    log_stage(f"????????: {query.market_group}")
    pane_id = click_market_tab(page, query.market_group)
    log_stage(f"??????: {query.market}")
    click_market_option(page, pane_id, query.market)
    log_stage(f"??????: {query.mill}")
    click_checkbox_in_group(page, ZH_MILL, query.mill)
    log_stage(f"????????: {query.price_scope}")
    click_radio_button_in_group(page, ZH_FREQUENCY, query.price_scope)
    log_stage(f"??????????: {ZH_DATE_RANGE}")
    click_radio_in_group(page, ZH_PUBLISH_TIME, ZH_DATE_RANGE)
    log_stage(f"????????: {query.publish_time}")
    click_publish_type(page, query.publish_time)
    log_stage(f"??????: {query.target_date}")
    set_date_via_picker(page, query.target_date)
    log_stage("??????")
    click_search(page)


def export_excel(page: ChromiumPage, query: Query, download_dir: Path) -> Path:
    log_stage("??????????")
    wait_for_result_row(page, query, timeout=20)
    log_stage("????????")
    select_search_result(page, query)
    log_stage("??????Excel")
    click_export_excel_button(page)
    log_stage("????????")
    confirm_export_dialog(page)
    return wait_for_download(page, download_dir, timeout=90)


def build_result(query: Query, page: ChromiumPage, downloaded_file: Path, output_dir: Path, elapsed_seconds: float) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "query": asdict(query),
        "current_url": page.url,
        "downloaded_file": str(downloaded_file),
        "downloaded_name": downloaded_file.name,
        "expected_filename": query.expected_filename,
        "filename_matches_expected": downloaded_file.name == query.expected_filename,
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        "elapsed_seconds": round(elapsed_seconds, 2),
        "elapsed_readable": str(timedelta(seconds=round(elapsed_seconds))),
    }
    result_path = output_dir / f"mysteel_export_{timestamp()}.json"
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return result_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Mysteel Excel export automation")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--user-data-dir", default="Mysteel_Browser_Data")
    parser.add_argument("--download-dir", default="data")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--target-date", default=default_target_date())
    args = parser.parse_args()

    query = Query(target_date=args.target_date)
    download_dir = Path(args.download_dir)
    output_dir = Path(args.output_dir)
    page = create_page(Path(args.user_data_dir), download_dir)

    try:
        log_stage("??????????")
        page.get(args.url)
        page.wait.load_start()
        page.wait.doc_loaded()
        human_pause(1.0, 1.8)
        auto_login_if_needed(page, TEST_USERNAME, TEST_PASSWORD, args.url)
        dismiss_intro_guide(page)
        log_stage("???????")
        started_at = time.perf_counter()
        apply_filters(page, query)
        downloaded = export_excel(page, query, download_dir)
        elapsed_seconds = time.perf_counter() - started_at
        result_path = build_result(query, page, downloaded, output_dir, elapsed_seconds)
        print(json.dumps({
            "downloaded_file": str(downloaded),
            "downloaded_name": downloaded.name,
            "result_file": str(result_path),
            "elapsed_seconds": round(elapsed_seconds, 2),
            "elapsed_readable": str(timedelta(seconds=round(elapsed_seconds))),
        }, ensure_ascii=False, indent=2))
        return 0
    finally:
        print("Browser left open for inspection.")


if __name__ == "__main__":
    sys.exit(main())
