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

ZH_STEEL = "钢材"
ZH_COLD_ROLLED = "冷轧"
ZH_PRODUCT = "品名"
ZH_SPEC = "规格"
ZH_MATERIAL = "材质"
ZH_MARKET = "市场"
ZH_MILL = "钢厂"
ZH_FREQUENCY = "价格频度"
ZH_BY_DATE = "按日期"
ZH_LATE_PRICE = "晚盘价格"
ZH_SEARCH = "搜索"
ZH_EXPORT_EXCEL = "导出Excel"
ZH_EXPORT = "导出"
ZH_CONFIRM = "确认"
ZH_OK = "确定"
ZH_TIME = "时间"
ZH_DATE = "日期"
ZH_COLD_COIL = "冷卷"
ZH_TAIAN = "泰安"
ZH_QRSTU = "QRSTU"
ZH_Q195 = "Q195"
ZH_TAISHAN_STEEL = "泰山钢铁"
ZH_EXPECTED_NAME = "Mysteel价格中心_冷卷-1_1250_C-Q195-泰安-泰山钢铁_2026-03-26.xlsx"

DEFAULT_URL = "https://price.mysteel.com/#/price-search?breedId=1-3"
EDGE_BINARY_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
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


def edge_binary() -> str | None:
    for candidate in EDGE_BINARY_CANDIDATES:
        if candidate.exists():
            return str(candidate)
    return None


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def default_target_date() -> str:
    return (date.today() - timedelta(days=1)).isoformat()


def create_page(user_data_dir: Path, download_dir: Path) -> ChromiumPage:
    user_data_dir.mkdir(parents=True, exist_ok=True)
    download_dir.mkdir(parents=True, exist_ok=True)

    co = ChromiumOptions()
    binary = edge_binary()
    if binary:
        co.set_browser_path(binary)
    co.set_user_data_path(str(user_data_dir))
    co.set_download_path(str(download_dir))
    co.auto_port()
    page = ChromiumPage(addr_or_opts=co)
    page.set.window.max()
    return page


def human_pause(low: float = 0.35, high: float = 0.9) -> None:
    time.sleep(random.uniform(low, high))


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


def page_has_login_entry(page: ChromiumPage) -> bool:
    try:
        return bool(page.ele('xpath://div[contains(@class,"login-bar")]//*[contains(normalize-space(.),"' + ZH_LOGIN + '")]', timeout=2))
    except Exception:
        return False


def wait_for_login_completion(page: ChromiumPage, timeout: float = 90) -> None:
    ok = wait_until(
        page,
        """
        const hasLogin = !!document.querySelector('.login-bar .topbar-nav-login');
        return !hasLogin;
        """,
        timeout=timeout,
        interval=0.5,
    )
    if not ok:
        raise RuntimeError('Login did not complete in time')
    page.wait.load_start()
    page.wait.doc_loaded()
    human_pause(1.5, 2.4)


def fill_login_form(page: ChromiumPage, username: str, password: str) -> bool:
    js = """
    const username = arguments[0];
    const password = arguments[1];
    const visible = el => !!el && el.offsetParent !== null;
    const inputs = Array.from(document.querySelectorAll('input')).filter(visible);
    const pwd = inputs.find(el => (el.type || '').toLowerCase() === 'password');
    const user = inputs.find(el => el !== pwd && ['text','tel','number','email'].includes((el.type || 'text').toLowerCase()))
      || inputs.find(el => el !== pwd);
    const setVal = (el, val) => {
      if (!el) return false;
      el.focus();
      el.value = val;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      el.dispatchEvent(new Event('blur', { bubbles: true }));
      return true;
    };
    return setVal(user, username) && setVal(pwd, password);
    """
    try:
        return bool(page.run_js(js, username, password))
    except Exception:
        return False


def click_login_submit(page: ChromiumPage) -> bool:
    candidates = [
        'xpath://button[.//span[contains(normalize-space(.),"' + ZH_LOGIN + '")]]',
        'xpath://button[contains(normalize-space(.),"' + ZH_LOGIN + '")]',
        'xpath://div[contains(@role,"button") and contains(normalize-space(.),"' + ZH_LOGIN + '")]',
        'xpath://span[contains(normalize-space(.),"' + ZH_LOGIN + '")]/ancestor::button[1]',
    ]
    for locator in candidates:
        ele = page.ele(locator, timeout=2)
        if ele:
            try:
                ele.scroll.to_see()
            except Exception:
                pass
            try:
                ele.click(by_js=True)
            except Exception:
                try:
                    ele.click()
                except Exception:
                    continue
            human_pause(1.0, 1.6)
            return True
    return False


def auto_login_if_needed(page: ChromiumPage, username: str, password: str) -> None:
    if not page_has_login_entry(page):
        return
    login_entry = page.ele('xpath://div[contains(@class,"login-bar")]//*[contains(normalize-space(.),"' + ZH_LOGIN + '")]', timeout=4)
    if not login_entry:
        return
    login_entry.click(by_js=True)
    human_pause(1.2, 2.0)
    page.wait.load_start()
    page.wait.doc_loaded()
    human_pause(1.2, 2.0)

    filled = fill_login_form(page, username, password)
    if not filled:
        raise RuntimeError('Could not find visible login form fields')
    human_pause(0.8, 1.4)
    if not click_login_submit(page):
        raise RuntimeError('Could not find login submit button')
    wait_for_login_completion(page, timeout=120)


def locator_candidates(text: str) -> tuple[str, ...]:
    safe = text.replace('"', "'")
    return (
        f'text={text}',
        f'xpath://label[contains(normalize-space(.),"{safe}")]',
        f'xpath://span[contains(normalize-space(.),"{safe}")]',
        f'xpath://div[contains(normalize-space(.),"{safe}")]',
        f'xpath://a[contains(normalize-space(.),"{safe}")]',
        f'xpath://button[contains(normalize-space(.),"{safe}")]',
    )


def click_first(page: ChromiumPage, label: str, timeout: float = 10, raise_if_missing: bool = True) -> bool:
    for locator in locator_candidates(label):
        ele = page.ele(locator, timeout=timeout)
        if not ele:
            continue
        try:
            ele.scroll.to_see()
        except Exception:
            pass
        try:
            ele.click(by_js=True)
        except Exception:
            try:
                ele.click()
            except Exception:
                continue
        human_pause()
        return True
    if raise_if_missing:
        raise RuntimeError(f"Clickable element not found: {label}")
    return False


def form_item_by_label(page: ChromiumPage, group_label: str, timeout: float = 10):
    return page.ele(
        f'xpath://div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"{group_label}")]]',
        timeout=timeout,
    )


def click_checkbox_in_group(page: ChromiumPage, group_label: str, option_label: str, timeout: float = 10) -> None:
    group = form_item_by_label(page, group_label, timeout=timeout)
    if not group:
        raise RuntimeError(f"Checkbox group not found: {group_label}")
    option = group.ele(
        f'xpath:.//label[contains(@class,"el-checkbox")][.//span[contains(@class,"el-checkbox__label") and contains(normalize-space(.),"{option_label}")]]',
        timeout=timeout,
    )
    if not option:
        raise RuntimeError(f"Checkbox option not found in group {group_label}: {option_label}")
    try:
        option.scroll.to_see()
    except Exception:
        pass
    option.click(by_js=True)
    human_pause()


def click_radio_button_in_group(page: ChromiumPage, group_label: str, option_label: str, timeout: float = 10) -> None:
    group = form_item_by_label(page, group_label, timeout=timeout)
    if not group:
        raise RuntimeError(f"Radio button group not found: {group_label}")
    option = group.ele(
        f'xpath:.//label[contains(@class,"el-radio-button")][.//span[contains(@class,"el-radio-button__inner") and contains(normalize-space(.),"{option_label}")]]',
        timeout=timeout,
    )
    if not option:
        raise RuntimeError(f"Radio button option not found in group {group_label}: {option_label}")
    try:
        option.scroll.to_see()
    except Exception:
        pass
    option.click(by_js=True)
    human_pause()


def click_radio_in_group(page: ChromiumPage, group_label: str, option_label: str, timeout: float = 10) -> None:
    group = form_item_by_label(page, group_label, timeout=timeout)
    if not group:
        raise RuntimeError(f"Radio group not found: {group_label}")
    option = group.ele(
        f'xpath:.//label[contains(@class,"el-radio")][.//span[contains(@class,"el-radio__label") and contains(normalize-space(.),"{option_label}")]]',
        timeout=timeout,
    )
    if not option:
        raise RuntimeError(f"Radio option not found in group {group_label}: {option_label}")
    try:
        option.scroll.to_see()
    except Exception:
        pass
    option.click(by_js=True)
    human_pause()


def click_market_tab(page: ChromiumPage, tab_label: str, timeout: float = 10) -> str:
    tab = page.ele(
        f'xpath://div[contains(@class,"el-tabs__item") and @role="tab" and contains(normalize-space(.),"{tab_label}")]',
        timeout=timeout,
    )
    if not tab:
        raise RuntimeError(f"Market tab not found: {tab_label}")
    pane_id = tab.attr('aria-controls') or ''
    tab.click(by_js=True)
    human_pause()
    return pane_id


def click_market_option(page: ChromiumPage, pane_id: str, option_label: str, timeout: float = 10) -> None:
    pane = page.ele(
        f'xpath://div[@id="{pane_id}" and contains(@class,"el-tab-pane") and not(contains(@style,"display: none"))]',
        timeout=timeout,
    )
    if not pane:
        raise RuntimeError(f"Market pane not found or not visible: {pane_id}")
    option = pane.ele(
        f'xpath:.//label[contains(@class,"el-checkbox")][.//span[contains(@class,"el-checkbox__label") and contains(normalize-space(.),"{option_label}")]]',
        timeout=timeout,
    )
    if not option:
        raise RuntimeError(f"Market option not found: {option_label}")
    option.click(by_js=True)
    human_pause()


def set_date_via_picker(page: ChromiumPage, target_date: str) -> None:
    target = datetime.strptime(target_date, "%Y-%m-%d").date()
    day = str(target.day)

    range_editor = page.ele(
        'xpath://div[contains(@class,"el-date-editor--daterange") and .//input[@placeholder="' + ZH_START_TIME + '"] and .//input[@placeholder="' + ZH_END_TIME + '"]]',
        timeout=8,
    )
    if range_editor:
        try:
            range_editor.click(by_js=True)
            human_pause(0.6, 1.1)
        except Exception:
            pass

    start_input = page.ele(f'xpath://input[@placeholder="{ZH_START_TIME}"]', timeout=4)
    end_input = page.ele(f'xpath://input[@placeholder="{ZH_END_TIME}"]', timeout=4)

    try:
        page.run_js(
            """
            const startPlaceholder = arguments[1];
            const endPlaceholder = arguments[2];
            const targetValue = arguments[0];
            const editors = Array.from(document.querySelectorAll('.el-date-editor--daterange'))
              .filter(el => el.offsetParent !== null);
            const editor = editors.find(el => el.querySelector(`input[placeholder="${startPlaceholder}"]`) && el.querySelector(`input[placeholder="${endPlaceholder}"]`));
            const start = editor ? editor.querySelector(`input[placeholder="${startPlaceholder}"]`) : null;
            const end = editor ? editor.querySelector(`input[placeholder="${endPlaceholder}"]`) : null;
            if (start && end) {
              start.value = targetValue;
              end.value = targetValue;
              for (const el of [start, end]) {
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new Event('blur', { bubbles: true }));
              }
            }
            """,
            target_date,
            ZH_START_TIME,
            ZH_END_TIME,
        )
        human_pause(0.6, 1.1)
    except Exception:
        pass

    current_values = []
    for element in (start_input, end_input):
        if element:
            try:
                current_values.append((element.attr('value') or '').strip())
            except Exception:
                current_values.append('')
    if current_values == [target_date, target_date]:
        return

    day_locators = [
        f'xpath://div[contains(@class,"el-picker-panel") and not(contains(@style,"display: none"))]//td[not(contains(@class,"disabled")) and not(contains(@class,"prev")) and not(contains(@class,"next"))]//*[normalize-space(text())="{day}"]',
        f'xpath://div[contains(@class,"el-picker-panel") and not(contains(@style,"display: none"))]//div[contains(@class,"cell") and normalize-space(text())="{day}"]',
        f'xpath://td[not(contains(@class,"disabled")) and not(contains(@class,"prev")) and not(contains(@class,"next"))]//*[normalize-space(text())="{day}"]',
        f'xpath://div[contains(@class,"cell") and normalize-space(text())="{day}"]',
    ]
    clicked = 0
    for locator in day_locators:
        elements = page.eles(locator, timeout=2)
        for ele in elements:
            if not ele:
                continue
            try:
                ele.click(by_js=True)
                clicked += 1
                human_pause()
                if clicked >= 2:
                    return
            except Exception:
                continue
        if clicked >= 2:
            return


def wait_for_selected_state(page: ChromiumPage, timeout: float = 10) -> None:
    ok = wait_until(
        page,
        """
        const box = document.querySelector('.table-operate-buttons');
        if (!box) return false;
        const text = box.innerText || '';
        return text.includes('\u5df2\u9009') && text.includes('1\u6761');
        """,
        timeout=timeout,
        interval=0.3,
    )
    if not ok:
        raise RuntimeError('Selected-state indicator did not appear after checking the row')


def select_search_result(page: ChromiumPage, query: Query) -> None:
    row = page.ele(
        f'xpath://table[contains(@class,"el-table__body")]//tr[contains(@class,"el-table__row")][.//td[contains(normalize-space(.),"{query.product_name}")] and .//td[contains(normalize-space(.),"{query.specification}")] and .//td[contains(normalize-space(.),"{query.material}")] and .//td[contains(normalize-space(.),"{query.market}")] and .//td[contains(normalize-space(.),"{query.mill}")]]',
        timeout=10,
    )
    if not row:
        raise RuntimeError("Matching result row not found")

    checkbox = row.ele(
        'xpath:.//td[contains(@class,"el-table-column--selection")]//label[contains(@class,"el-checkbox")]',
        timeout=4,
    )
    if not checkbox:
        raise RuntimeError("Result-row checkbox not found")
    try:
        checkbox.scroll.to_see()
    except Exception:
        pass
    checkbox.click(by_js=True)
    human_pause(0.7, 1.2)
    wait_for_selected_state(page, timeout=12)


def click_export_excel_button(page: ChromiumPage) -> None:
    button = page.ele(
        f'xpath://div[contains(@class,"table-operate-buttons")]//button[contains(@class,"el-button--primary")][.//span[contains(normalize-space(.),"{ZH_EXPORT_EXCEL}")]]',
        timeout=8,
    )
    if not button:
        raise RuntimeError("Bottom export Excel button not found")
    button.click(by_js=True)
    human_pause(0.6, 1.1)


def confirm_export_dialog(page: ChromiumPage) -> None:
    ok = wait_until(
        page,
        """
        const body = document.querySelector('.el-dialog__body');
        if (!body) return false;
        const title = body.querySelector('.dialog-title');
        return !!title && (title.innerText || '').includes('\u5bfc\u51fa\u6570\u636e');
        """,
        timeout=12,
        interval=0.3,
    )
    if not ok:
        raise RuntimeError('Export dialog did not appear')

    button = page.ele(
        'xpath://div[contains(@class,"el-dialog__body")]//div[contains(@class,"actions")]//button[contains(@class,"el-button--primary")][.//span[contains(normalize-space(.),"\u5bfc\u51fa")]]',
        timeout=8,
    )
    if not button:
        raise RuntimeError('Export dialog confirm button not found')
    try:
        button.scroll.to_see()
    except Exception:
        pass
    human_pause(0.8, 1.4)
    button.click(by_js=True)
    human_pause(0.8, 1.4)


def latest_file(directory: Path, pattern: str) -> Path | None:
    files = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def wait_for_download(download_dir: Path, started_after: float, timeout: int = 120) -> Path:
    end = time.time() + timeout
    while time.time() < end:
        partials = list(download_dir.glob("*.crdownload")) + list(download_dir.glob("*.tmp"))
        fresh = [p for p in download_dir.glob("*.xlsx") if p.stat().st_mtime >= started_after]
        if fresh and not partials:
            return sorted(fresh, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        time.sleep(1)
    latest = latest_file(download_dir, "*.xlsx")
    if latest and latest.stat().st_mtime >= started_after:
        return latest
    raise TimeoutError("Timed out waiting for Excel download")


def apply_filters(page: ChromiumPage, query: Query) -> None:
    page.wait.doc_loaded()
    human_pause(1.5, 2.4)
    click_first(page, ZH_STEEL, timeout=8, raise_if_missing=False)
    click_first(page, ZH_COLD_ROLLED, timeout=8, raise_if_missing=False)

    click_checkbox_in_group(page, ZH_PRODUCT, query.product_name)
    click_checkbox_in_group(page, ZH_SPEC, query.specification)
    click_checkbox_in_group(page, ZH_MATERIAL, query.material)

    pane_id = click_market_tab(page, query.market_group, timeout=8)
    click_market_option(page, pane_id, query.market)
    click_checkbox_in_group(page, ZH_MILL, query.mill)
    click_radio_button_in_group(page, ZH_FREQUENCY, query.price_scope)
    click_radio_in_group(page, ZH_PUBLISH_TIME, ZH_DATE_RANGE)
    click_first(page, query.publish_time, timeout=8, raise_if_missing=False)
    set_date_via_picker(page, query.target_date)
    click_first(page, ZH_SEARCH, timeout=8)
    human_pause(3.2, 4.6)


def export_excel(page: ChromiumPage, query: Query, download_dir: Path) -> Path:
    select_search_result(page, query)
    human_pause(0.9, 1.6)
    started_at = time.time()
    click_export_excel_button(page)
    confirm_export_dialog(page)
    return wait_for_download(download_dir, started_at, timeout=180)


def build_result(query: Query, page: ChromiumPage, downloaded_file: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "query": asdict(query),
        "current_url": page.url,
        "downloaded_file": str(downloaded_file),
        "downloaded_name": downloaded_file.name,
        "expected_filename": query.expected_filename,
        "filename_matches_expected": downloaded_file.name == query.expected_filename,
        "captured_at": datetime.now().isoformat(timespec="seconds"),
    }
    result_path = output_dir / f"mysteel_export_{timestamp()}.json"
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return result_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Mysteel Excel export automation")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--user-data-dir", default=".browser-profile/mysteel-drission")
    parser.add_argument("--download-dir", default="downloads")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--target-date", default=default_target_date())
    args = parser.parse_args()

    query = Query(target_date=args.target_date)
    page = create_page(Path(args.user_data_dir), Path(args.download_dir))

    try:
        page.get(args.url)
        auto_login_if_needed(page, TEST_USERNAME, TEST_PASSWORD)
        apply_filters(page, query)
        downloaded = export_excel(page, query, Path(args.download_dir))
        result_path = build_result(query, page, downloaded, Path(args.output_dir))
        print(json.dumps({
            "downloaded_file": str(downloaded),
            "downloaded_name": downloaded.name,
            "result_file": str(result_path),
        }, ensure_ascii=False, indent=2))
        return 0
    finally:
        print("Browser left open for inspection.")


if __name__ == "__main__":
    sys.exit(main())
