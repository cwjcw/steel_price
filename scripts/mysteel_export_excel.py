from __future__ import annotations

import argparse
import json
import random
import re
import tomllib
import sys
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from DrissionPage import ChromiumOptions, ChromiumPage
from scripts.strategies.registry import STRATEGIES

ZH_PRODUCT = "\u54c1\u540d"
ZH_PRODUCT_KIND = "\u54c1\u79cd"
ZH_SPEC = "\u89c4\u683c"
ZH_MATERIAL = "\u6750\u8d28"
ZH_MARKET = "\u5e02\u573a"
ZH_MILL = "\u94a2\u5382"
ZH_ENTERPRISE = "\u4f01\u4e1a"
ZH_ORIGIN = "\u94a2\u5382/\u4ea7\u5730"
ZH_BRAND = "\u54c1\u724c"
ZH_DELIVERY_STATUS = "\u4ea4\u8d27\u72b6\u6001"
ZH_MESH_MODEL = "\u7f51\u7247\u578b\u53f7"
ZH_DIAMETER = "\u53e3\u5f84"
ZH_PRICE_TYPE = "\u4ef7\u683c\u7c7b\u578b"
ZH_CLASSIFICATION = "\u5206\u7c7b"
ZH_FREQUENCY = "\u4ef7\u683c\u9891\u5ea6"
ZH_BY_DATE = "\u6309\u65e5\u671f"
ZH_ALL_DAY_PRICE = "\u5168\u5929\u4ef7\u683c"
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
ZH_TAIAN = "\u6cf0\u5b89"
ZH_QRSTU = "QRSTU"
ZH_Q195 = "Q195"
ZH_TAISHAN_STEEL = "\u6cf0\u5c71\u94a2\u94c1"
ZH_COLD_COIL = "\u51b7\u5377"

PRODUCT_FIELD_PROFILES: dict[str, dict[str, Any]] = {
    "\u94a2\u7b4b\u710a\u63a5\u7f51": {
        "product_label": ZH_PRODUCT,
        "spec_label": ZH_SPEC,
        "material_label": ZH_MATERIAL,
        "market_label": ZH_MARKET,
        "mill_labels": [ZH_ORIGIN, ZH_ENTERPRISE, ZH_MILL],
        "price_type_label": ZH_PRICE_TYPE,
        "extra_groups": {
            "mesh_models": ZH_MESH_MODEL,
        },
        "expandable_groups": [],
    },
    "\u4e0d\u9508\u94a2\u5e73\u677f": {
        "product_label": ZH_PRODUCT_KIND,
        "spec_label": ZH_SPEC,
        "material_label": ZH_MATERIAL,
        "market_label": ZH_MARKET,
        "mill_labels": [ZH_ENTERPRISE],
        "price_type_label": ZH_CLASSIFICATION,
        "extra_groups": {
            "brands": ZH_BRAND,
            "delivery_states": ZH_DELIVERY_STATUS,
        },
        "expandable_groups": [ZH_MATERIAL, ZH_SPEC, ZH_ENTERPRISE],
    },
    "\u51b7\u8f67\u4e0d\u9508\u5e73\u677f": {
        "product_label": ZH_PRODUCT_KIND,
        "spec_label": ZH_SPEC,
        "material_label": ZH_MATERIAL,
        "market_label": ZH_MARKET,
        "mill_labels": [ZH_ENTERPRISE],
        "price_type_label": ZH_CLASSIFICATION,
        "extra_groups": {
            "brands": ZH_BRAND,
            "delivery_states": ZH_DELIVERY_STATUS,
        },
        "expandable_groups": [ZH_MATERIAL, ZH_SPEC, ZH_ENTERPRISE],
    },
    "\u70ed\u8f67\u4e0d\u9508\u5e73\u677f": {
        "product_label": ZH_PRODUCT_KIND,
        "spec_label": ZH_SPEC,
        "material_label": ZH_MATERIAL,
        "market_label": ZH_MARKET,
        "mill_labels": [ZH_ENTERPRISE],
        "price_type_label": ZH_CLASSIFICATION,
        "extra_groups": {
            "brands": ZH_BRAND,
            "delivery_states": ZH_DELIVERY_STATUS,
        },
        "expandable_groups": [ZH_MATERIAL, ZH_SPEC, ZH_ENTERPRISE],
    },
    "\u70ed\u8f67\u677f\u5377": {
        "product_label": ZH_PRODUCT_KIND,
        "spec_label": ZH_SPEC,
        "material_label": ZH_MATERIAL,
        "market_label": ZH_MARKET,
        "mill_labels": [ZH_ENTERPRISE, ZH_MILL, ZH_ORIGIN],
        "price_type_label": "",
        "extra_groups": {
            "diameters": ZH_DIAMETER,
        },
        "expandable_groups": [ZH_SPEC, ZH_MATERIAL, ZH_ENTERPRISE],
    },
    "\u70ed\u8f67\u9178\u6d17\u677f\u5377": {
        "product_label": ZH_PRODUCT_KIND,
        "spec_label": ZH_SPEC,
        "material_label": ZH_MATERIAL,
        "market_label": ZH_MARKET,
        "mill_labels": [ZH_ENTERPRISE, ZH_MILL, ZH_ORIGIN],
        "price_type_label": "",
        "extra_groups": {
            "diameters": ZH_DIAMETER,
        },
        "expandable_groups": [ZH_SPEC, ZH_MATERIAL, ZH_ENTERPRISE],
    },
    "\u70ed\u8f67": {
        "product_label": ZH_PRODUCT_KIND,
        "spec_label": ZH_SPEC,
        "material_label": ZH_MATERIAL,
        "market_label": ZH_MARKET,
        "mill_labels": [ZH_ENTERPRISE, ZH_MILL, ZH_ORIGIN],
        "price_type_label": "",
        "extra_groups": {
            "diameters": ZH_DIAMETER,
        },
        "expandable_groups": [ZH_SPEC, ZH_MATERIAL, ZH_ENTERPRISE],
    },
}

DEFAULT_FIELD_PROFILE: dict[str, Any] = {
    "product_label": ZH_PRODUCT,
    "spec_label": ZH_SPEC,
    "material_label": ZH_MATERIAL,
    "market_label": ZH_MARKET,
    "mill_labels": [ZH_MILL, ZH_ENTERPRISE, ZH_ORIGIN],
    "price_type_label": ZH_PRICE_TYPE,
    "extra_groups": {},
    "expandable_groups": [],
}

DEFAULT_URL = "https://price.mysteel.com/#/price-search?breedId=1-3"
WORKDAY_API_TEMPLATE = "https://timor.tech/api/holiday/info/{date}"
ENV_PATH = Path(".env")
CONFIG_PATH = Path("queries.toml")
TOTAL_PRICE_FILENAME = "Total_Price.xlsx"

CHROME_BINARY_CANDIDATES = [
    Path(r"C:\Users\KN426\AppData\Local\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
]


@dataclass(frozen=True)
class Query:
    name: str
    execution_strategy: str
    category: str
    subcategory: str
    second_nav: str
    third_nav: str
    price_type: str
    product_names: list[str]
    specifications: list[str]
    materials: list[str]
    market_group: str
    markets: list[str]
    mills: list[str]
    brands: list[str]
    delivery_states: list[str]
    mesh_models: list[str]
    diameters: list[str]
    price_scope: str
    publish_time: str
    start_date: str
    end_date: str
    unit: str


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        raise RuntimeError(f"Missing env file: {path}")

    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def ensure_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def first_product_key(query: Query) -> str:
    return query.product_names[0] if query.product_names else ""


def strategy_module(query: Query):
    module = STRATEGIES.get(query.execution_strategy)
    if not module:
        raise RuntimeError(f"Unknown execution strategy: {query.execution_strategy}")
    return module


def profile_key_candidates(query: Query) -> list[str]:
    candidates = [first_product_key(query), query.third_nav, query.subcategory]
    return [item for item in candidates if item]


def product_profile(query: Query) -> dict[str, Any]:
    profile = dict(DEFAULT_FIELD_PROFILE)
    try:
        profile.update(strategy_module(query).field_profile(query))
    except Exception:
        pass
    for key in profile_key_candidates(query):
        specific = PRODUCT_FIELD_PROFILES.get(key, {})
        if specific:
            profile.update(specific)
            break
    return profile


def reorder_queries_by_strategy(queries: list[Query]) -> list[Query]:
    buckets: dict[str, deque[Query]] = defaultdict(deque)
    strategy_order: list[str] = []
    for query in queries:
        if query.execution_strategy not in buckets:
            strategy_order.append(query.execution_strategy)
        buckets[query.execution_strategy].append(query)

    ordered: list[Query] = []
    last_strategy = ""
    while buckets:
        candidates = [name for name in strategy_order if name in buckets and name != last_strategy]
        if not candidates:
            candidates = [name for name in strategy_order if name in buckets]
        chosen = max(candidates, key=lambda name: len(buckets[name]))
        ordered.append(buckets[chosen].popleft())
        last_strategy = chosen
        if not buckets[chosen]:
            del buckets[chosen]
    return ordered


def first_existing_form_item(page: ChromiumPage, label_texts: list[str], timeout: float = 4):
    for label_text in label_texts:
        item = form_item_by_label(page, label_text, timeout=timeout)
        if item:
            return item, label_text
    return None, None


def chrome_binary(configured_path: str = "") -> str | None:
    configured = str(configured_path or "").strip()
    if configured:
        configured_candidate = Path(configured).expanduser()
        if configured_candidate.exists():
            return str(configured_candidate)
        raise RuntimeError(f"Configured Chrome binary does not exist: {configured}")

    for candidate in CHROME_BINARY_CANDIDATES:
        if candidate.exists():
            return str(candidate)
    return None


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def default_target_date() -> str:
    return (date.today() - timedelta(days=1)).isoformat()


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_int(value: str | None, default: int) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def is_simple_workday(day_value: date) -> bool:
    return day_value.weekday() < 5


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


def maybe_wait_random_start(enabled: bool, max_minutes: int) -> None:
    if not enabled or max_minutes <= 0:
        log_stage("Random startup delay disabled")
        return
    delay_seconds = random.uniform(0, max_minutes * 60)
    log_stage(f"Random startup delay selected: {int(round(delay_seconds))} seconds")
    time.sleep(delay_seconds)


def prompt_manual_date_confirmation(start_date: str, end_date: str) -> None:
    print()
    print(f"Manual date input required: please set the page date range to {start_date} -> {end_date} in the browser.")
    input("Press Enter after you finish setting the dates manually...")
    print()


def human_pause(low: float = 0.8, high: float = 1.6) -> None:
    time.sleep(random.uniform(low, high))


def log_stage(stage: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {stage}")


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


def create_page(user_data_dir: Path, download_dir: Path, chrome_path: str = "") -> ChromiumPage:
    user_data_dir.mkdir(parents=True, exist_ok=True)
    download_dir.mkdir(parents=True, exist_ok=True)

    co = ChromiumOptions()
    binary = chrome_binary(chrome_path)
    if binary:
        co.set_browser_path(binary)
    co.set_user_data_path(str(user_data_dir))
    co.set_download_path(str(download_dir))
    co.auto_port()
    co.new_env(True)
    co.existing_only(False)
    co.headless(False)
    log_stage(f"Launching browser with user data dir: {user_data_dir}")
    log_stage(f"Using download dir: {download_dir}")
    if binary:
        log_stage(f"Using Chrome binary: {binary}")
    page = ChromiumPage(co)
    page.set.download_path(str(download_dir))
    page.set.window.max()
    return page


def latest_file(directory: Path, pattern: str) -> Path | None:
    files = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def safe_filename(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return "download"
    text = re.sub(r'[\/:*?"<>|]+', '_', text)
    text = re.sub(r'\s+', '_', text).strip(' ._')
    return text or "download"


def rename_downloaded_file(downloaded_file: Path, query: Query) -> Path:
    suffix = downloaded_file.suffix or '.xlsx'
    base_name = f"{safe_filename(query.name)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    target = downloaded_file.with_name(base_name + suffix)
    counter = 1
    while target.exists() and target != downloaded_file:
        target = downloaded_file.with_name(f"{base_name}_{counter}{suffix}")
        counter += 1
    if target == downloaded_file:
        return downloaded_file
    downloaded_file.replace(target)
    return target


def clear_download_dir(download_dir: Path) -> int:
    removed = 0
    patterns = ("*.xlsx", "*.xls", "~$*.xlsx", "~$*.xls")
    protected_names = {TOTAL_PRICE_FILENAME.lower(), f"~${TOTAL_PRICE_FILENAME}".lower()}
    seen: set[Path] = set()
    for pattern in patterns:
        for path in download_dir.glob(pattern):
            if path in seen or not path.is_file():
                continue
            if path.name.lower() in protected_names:
                continue
            seen.add(path)
            try:
                path.unlink()
                removed += 1
            except FileNotFoundError:
                pass
    return removed


def normalize_price_tabs(page: ChromiumPage, target_url: str) -> None:
    price_tab_id = None
    homepage_tab_ids: list[str] = []

    try:
        for tab in page.get_tabs():
            tab_id = getattr(tab, "tab_id", "") or ""
            tab_url = (getattr(tab, "url", "") or "").lower()
            if "price-search" in tab_url:
                price_tab_id = tab_id
            elif tab_url.rstrip("/") in {"https://www.mysteel.com", "https://www.mysteel.com/#", "https://www.mysteel.com/index.html"}:
                if tab_id:
                    homepage_tab_ids.append(tab_id)
    except Exception:
        return

    if price_tab_id:
        page.activate_tab(price_tab_id)
        human_pause(0.8, 1.4)
        for tab_id in homepage_tab_ids:
            if tab_id != price_tab_id:
                try:
                    page.close_tabs(tab_id)
                except Exception:
                    pass


def ensure_price_page(page: ChromiumPage, target_url: str) -> None:
    normalize_price_tabs(page, target_url)
    try:
        current_url = page.url or ""
    except Exception:
        current_url = ""
    if "price-search" in current_url:
        return

    try:
        for tab in page.get_tabs():
            tab_url = getattr(tab, "url", "") or ""
            if "price-search" in tab_url:
                page.activate_tab(getattr(tab, "tab_id", tab))
                human_pause(0.8, 1.4)
                normalize_price_tabs(page, target_url)
                return
    except Exception:
        pass

    page.get(target_url)
    page.wait.load_start()
    page.wait.doc_loaded()
    human_pause(1.0, 1.8)
    normalize_price_tabs(page, target_url)


def dismiss_intro_guide(page: ChromiumPage) -> None:
    for locator in (
        f"text={ZH_GUIDE_CLOSE}",
        f'xpath://button[contains(normalize-space(.),"{ZH_GUIDE_CLOSE}")]',
        f'xpath://div[contains(@class,"guide") or contains(@class,"driver")]//button[contains(normalize-space(.),"{ZH_GUIDE_CLOSE}")]',
    ):
        try:
            ele = page.ele(locator, timeout=2)
        except Exception:
            ele = None
        if not ele:
            continue
        log_stage("Intro guide detected; closing guide")
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
        log_stage("Already logged in; skipping login step")
        return

    log_stage("Login required; opening login modal")
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

    log_stage("Switching to account-login tab")
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
    log_stage("Entering username")
    if not input_value(username_input, username):
        raise RuntimeError("Could not fill username")
    log_stage("Entering password")
    if not input_value(password_input, password):
        raise RuntimeError("Could not fill password")
    human_pause(1.0, 1.8)

    log_stage("Submitting login")
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
    log_stage("Login completed; returning to price-search page")
    normalize_price_tabs(page, target_url)
    ensure_price_page(page, target_url)


def click_main_nav(page: ChromiumPage, label_text: str, timeout: float = 8) -> None:
    if not label_text:
        return
    locators = [
        f'xpath://div[contains(@class,"main-nav")]//div[contains(@class,"row") and normalize-space(.)="{label_text}"]',
        f'xpath://div[contains(@class,"main-nav")]//div[contains(@class,"row")][contains(normalize-space(.),"{label_text}")]',
        f'xpath://div[contains(@class,"menu-breed")]//*[self::div or self::span or self::a][contains(normalize-space(.),"{label_text}")]',
        f'text={label_text}',
    ]
    for locator in locators:
        try:
            ele = page.ele(locator, timeout=2)
        except Exception:
            ele = None
        if ele:
            ele.click(by_js=True)
            human_pause(1.2, 2.0)
            return
    raise RuntimeError(f"Main navigation item not found: {label_text}")


def visible_sub_navs(page: ChromiumPage):
    return page.eles(
        'xpath://div[contains(@class,"sub-nav__content") and not(ancestor::*[contains(@style,"display: none")])]',
        timeout=4,
    )


def click_sub_nav(page: ChromiumPage, label_text: str, nav_index: int = 0, timeout: float = 8) -> None:
    if not label_text:
        return
    target_locator = f'xpath:.//div[contains(@class,"row") and contains(normalize-space(.),"{label_text}")]'
    for _ in range(3):
        navs = visible_sub_navs(page)
        ordered_navs = []
        if len(navs) > nav_index:
            ordered_navs.append(navs[nav_index])
        ordered_navs.extend(nav for idx, nav in enumerate(navs) if idx != nav_index)

        for nav in ordered_navs:
            try:
                item = nav.ele(target_locator, timeout=2)
            except Exception:
                item = None
            if item:
                item.click(by_js=True)
                human_pause(1.0, 1.8)
                return

        try:
            fallback = page.ele(
                f'xpath://div[contains(@class,"sub-nav__content") and not(ancestor::*[contains(@style,"display: none")])]//div[contains(@class,"row") and contains(normalize-space(.),"{label_text}")]',
                timeout=2,
            )
        except Exception:
            fallback = None
        if fallback:
            fallback.click(by_js=True)
            human_pause(1.0, 1.8)
            return
        human_pause(0.8, 1.2)
    raise RuntimeError(f"Sub-navigation option not found: {label_text}")


def form_item_by_label(page: ChromiumPage, label_text: str, timeout: float = 8):
    return page.ele(
        f'xpath://div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"{label_text}")]]',
        timeout=timeout,
    )

def maybe_expand_group(page: ChromiumPage, group_label: str, timeout: float = 4) -> bool:
    group = form_item_by_label(page, group_label, timeout=timeout)
    if not group:
        return False
    try:
        button = group.ele('xpath:.//button[contains(@class,"el-button--text")][.//*[contains(normalize-space(.),"\u66f4\u591a")]]', timeout=2)
    except Exception:
        button = None
    if not button:
        return False
    button.click(by_js=True)
    human_pause(0.8, 1.4)
    return True


def click_checkbox_in_group(page: ChromiumPage, group_label: str, option_label: str, timeout: float = 8, raise_if_missing: bool = True) -> bool:
    group = form_item_by_label(page, group_label, timeout=timeout)
    if not group:
        if raise_if_missing:
            raise RuntimeError(f"Checkbox group not found: {group_label}")
        return False

    exact_locator = f'xpath:.//label[contains(@class,"el-checkbox")][.//span[contains(@class,"el-checkbox__label") and normalize-space(.)="{option_label}"]]'
    fuzzy_locator = f'xpath:.//label[contains(@class,"el-checkbox")][.//span[contains(@class,"el-checkbox__label") and contains(normalize-space(.),"{option_label}")]]'

    def find_option(current_group):
        if not current_group:
            return None
        for locator in (exact_locator, fuzzy_locator):
            try:
                option = current_group.ele(locator, timeout=2)
            except Exception:
                option = None
            if option:
                return option
        return None

    option = find_option(group)
    if not option:
        maybe_expand_group(page, group_label, timeout=2)
        group = form_item_by_label(page, group_label, timeout=timeout)
        option = find_option(group)
    if not option:
        if raise_if_missing:
            raise RuntimeError(f"Checkbox option not found: {group_label} -> {option_label}")
        return False
    option.click(by_js=True)
    human_pause(0.9, 1.6)
    return True


def click_checkbox_in_any_group(page: ChromiumPage, group_labels: list[str], option_label: str, timeout: float = 8) -> None:
    last_error = None
    for label in group_labels:
        if not label:
            continue
        try:
            click_checkbox_in_group(page, label, option_label, timeout=timeout)
            return
        except Exception as exc:
            last_error = exc
    raise RuntimeError(str(last_error) if last_error else f"Checkbox option not found: {option_label}")


def click_option_in_group(page: ChromiumPage, group_labels: list[str], option_label: str, timeout: float = 8) -> None:
    group, found_label = first_existing_form_item(page, group_labels, timeout=timeout)
    if not group:
        raise RuntimeError(f"Group not found: {'/'.join(group_labels)}")

    locators = [
        f'xpath:.//label[contains(@class,"el-radio-button")][.//span[contains(normalize-space(.),"{option_label}")]]',
        f'xpath:.//label[contains(@class,"el-radio")][.//span[contains(normalize-space(.),"{option_label}")]]',
        f'xpath:.//button[.//span[contains(normalize-space(.),"{option_label}")]]',
        f'xpath:.//*[contains(@class,"el-segmented") or contains(@class,"button") or contains(@class,"tab")][contains(normalize-space(.),"{option_label}")]',
    ]
    for locator in locators:
        try:
            option = group.ele(locator, timeout=2)
        except Exception:
            option = None
        if option:
            option.click(by_js=True)
            human_pause(0.9, 1.6)
            return
    raise RuntimeError(f"Group option not found: {found_label} -> {option_label}")


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

    exact_locator = f'xpath:.//label[contains(@class,"el-checkbox")][.//span[contains(@class,"el-checkbox__label") and normalize-space(.)="{option_label}"]]'
    fuzzy_locator = f'xpath:.//label[contains(@class,"el-checkbox")][.//span[contains(@class,"el-checkbox__label") and contains(normalize-space(.),"{option_label}")]]'

    option = None
    for locator in (exact_locator, fuzzy_locator):
        try:
            option = pane.ele(locator, timeout=2)
        except Exception:
            option = None
        if option:
            break
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


def _visible_date_picker_root(page: ChromiumPage, timeout: float = 4):
    return page.ele(
        'xpath://div[contains(@class,"el-picker-panel") and not(contains(@style,"display: none")) and .//div[contains(@class,"el-date-range-picker__header")]]',
        timeout=timeout,
    )


def _picker_visible_months(page: ChromiumPage) -> list[tuple[int, int]]:
    data = page.run_js(
        r"""
        const roots = [...document.querySelectorAll('.el-picker-panel')];
        const root = roots.find((item) => item.offsetParent !== null && item.querySelector('.el-date-range-picker__header'));
        if (!root) return [];
        const parseHeader = (text) => {
            const normalized = String(text || '').replace(/\s+/g, '');
            const match = normalized.match(/(\d{4})\D+(\d{1,2})\D*/);
            return match ? [Number(match[1]), Number(match[2])] : null;
        };
        return [...root.querySelectorAll('.el-date-range-picker__content')].map((content) => {
            const header = content.querySelector('.el-date-range-picker__header div');
            return parseHeader(header ? header.textContent : '');
        }).filter(Boolean);
        """
    )
    months: list[tuple[int, int]] = []
    for item in data or []:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            months.append((int(item[0]), int(item[1])))
    return months


def _picker_navigate_one_month(page: ChromiumPage, direction: str) -> bool:
    if direction not in {"prev", "next"}:
        raise ValueError(f"Unsupported picker navigation direction: {direction}")

    script = """
        const direction = "%s";
        const roots = [...document.querySelectorAll('.el-picker-panel')];
        const root = roots.find((item) => item.offsetParent !== null && item.querySelector('.el-date-range-picker__header'));
        if (!root) return false;
        const panels = [...root.querySelectorAll('.el-date-range-picker__content')];
        if (!panels.length) return false;
        const targetPanel = direction === 'prev' ? panels[0] : panels[panels.length - 1];
        const buttons = [...targetPanel.querySelectorAll('.el-date-range-picker__header button')];
        const wanted = direction === 'prev'
            ? buttons.find((btn) => btn.className.includes('arrow-left') && !btn.className.includes('d-arrow'))
            : buttons.find((btn) => btn.className.includes('arrow-right') && !btn.className.includes('d-arrow'));
        const fallback = direction === 'prev' ? buttons[0] : buttons[buttons.length - 1];
        const button = wanted || fallback;
        if (!button) return false;
        button.click();
        return true;
    """ % direction
    return bool(page.run_js(script))


def _move_picker_to_month(page: ChromiumPage, target_year: int, target_month: int, max_steps: int = 24) -> None:
    target_index = target_year * 12 + (target_month - 1)
    for _ in range(max_steps):
        months = _picker_visible_months(page)
        if len(months) < 2:
            break
        left_index = months[0][0] * 12 + (months[0][1] - 1)
        right_index = months[-1][0] * 12 + (months[-1][1] - 1)
        if left_index <= target_index <= right_index:
            return
        direction = "prev" if target_index < left_index else "next"
        if not _picker_navigate_one_month(page, direction):
            break
        human_pause(0.2, 0.5)
    raise RuntimeError(f"Could not navigate picker to target month {target_year:04d}-{target_month:02d}")


def _picker_select_day(page: ChromiumPage, target_year: int, target_month: int, target_day: int) -> None:
    result = page.run_js(
        r"""
        const year = %d;
        const month = %d;
        const day = %d;
        const roots = [...document.querySelectorAll('.el-picker-panel')];
        const root = roots.find((item) => item.offsetParent !== null && item.querySelector('.el-date-range-picker__header'));
        if (!root) return 'no-root';

        const parseHeader = (text) => {
            const normalized = String(text || '').replace(/\s+/g, '');
            const match = normalized.match(/(\d{4})\D+(\d{1,2})\D*/);
            return match ? [Number(match[1]), Number(match[2])] : null;
        };

        for (const content of root.querySelectorAll('.el-date-range-picker__content')) {
            const header = content.querySelector('.el-date-range-picker__header div');
            const headerValue = parseHeader(header ? header.textContent : '');
            if (!headerValue) continue;
            if (headerValue[0] !== year || headerValue[1] !== month) continue;

            const cells = [...content.querySelectorAll('td.available:not(.disabled):not(.prev-month):not(.next-month) span')];
            const matched = cells.find((cell) => Number(String(cell.textContent || '').trim()) === day);
            if (!matched) return 'no-day';
            matched.click();
            return 'selected';
        }
        return 'no-month';
        """
        % (target_year, target_month, target_day)
    )
    if result != "selected":
        raise RuntimeError(
            f"Could not select {target_year:04d}-{target_month:02d}-{target_day:02d} in picker (status: {result})"
        )


def set_date_via_picker(page: ChromiumPage, start_date: str, end_date: str, timeout: float = 10) -> None:
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    editor = page.ele(
        f'xpath://div[contains(@class,"el-form-item")][.//label[contains(normalize-space(.),"{ZH_PUBLISH_TIME}")]]//div[contains(@class,"el-date-editor--daterange") and .//input[@placeholder="{ZH_START_TIME}"] and .//input[@placeholder="{ZH_END_TIME}"]]',
        timeout=timeout,
    )
    if not editor:
        raise RuntimeError("Date-range editor not found")
    editor.click(by_js=True)
    human_pause(0.8, 1.4)
    if not _visible_date_picker_root(page, timeout=timeout):
        raise RuntimeError("Date-range picker panel did not open")

    _move_picker_to_month(page, start.year, start.month)
    _picker_select_day(page, start.year, start.month, start.day)
    human_pause(0.3, 0.7)

    _move_picker_to_month(page, end.year, end.month)
    _picker_select_day(page, end.year, end.month, end.day)
    human_pause(0.8, 1.4)


def set_date_range(page: ChromiumPage, start_date: str, end_date: str, manual_date: bool = False) -> None:
    if manual_date:
        log_stage("Manual date mode enabled; waiting for browser-side date input")
        prompt_manual_date_confirmation(start_date, end_date)
        return

    try:
        set_date_via_picker(page, start_date, end_date)
    except Exception as exc:
        log_stage(f"Automatic date selection failed ({exc}); switching to manual date input")
        prompt_manual_date_confirmation(start_date, end_date)


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
    conditions: list[str] = []

    def add_conditions(values: list[str]) -> None:
        if values:
            predicate = " or ".join([f'.//td[contains(normalize-space(.),"{item}")]' for item in values])
            conditions.append(f'( {predicate} )')

    add_conditions(query.product_names)
    add_conditions(query.specifications)
    add_conditions(query.materials)
    add_conditions(query.markets)
    add_conditions(query.mills)
    add_conditions(query.brands)
    add_conditions(query.delivery_states)
    add_conditions(query.mesh_models)
    add_conditions(query.diameters)

    where_clause = " and ".join(conditions) if conditions else 'true()'
    row_locator = (
        'xpath://table[contains(@class,"el-table__body")]//tr[contains(@class,"el-table__row")]'
        f'[{where_clause}]'
    )
    row = page.ele(row_locator, timeout=timeout)
    if not row:
        raise RuntimeError(f"Matching result row not found for query: {query.name}")
    return row


def selected_result_count(page: ChromiumPage) -> int:
    try:
        text = page.run_js(
            """
            const box = document.querySelector('.table-operate-buttons');
            return box ? (box.innerText || '') : '';
            """
        ) or ''
    except Exception:
        return 0

    import re

    pattern = re.escape(ZH_SELECTED) + r"\s*[?(]\s*(\d+)\s*?\s*[?)]"
    match = re.search(pattern, text)
    if match:
        return int(match.group(1))
    if ZH_SELECTED in text and ZH_ONE_ROW in text:
        return 1
    return 0


def wait_for_selected_state(page: ChromiumPage, expected_count: int = 1, timeout: float = 10) -> None:
    end = time.time() + timeout
    while time.time() < end:
        current_count = selected_result_count(page)
        if current_count >= expected_count:
            return
        if expected_count <= 1 and current_count == 1:
            return
        time.sleep(0.3)
    raise RuntimeError(f"Selected-state indicator did not reach expected count: {expected_count}")


def select_all_search_results(page: ChromiumPage, query: Query) -> None:
    rows = page.eles(
        'xpath://table[contains(@class,"el-table__body")]//tr[contains(@class,"el-table__row")]',
        timeout=10,
    )
    if not rows:
        raise RuntimeError(f"No result rows found for query: {query.name}")

    if selected_result_count(page) >= len(rows):
        log_stage(f"All result rows already selected ({len(rows)} row(s))")
        return

    header_checkbox = page.ele(
        'xpath://table[contains(@class,"el-table__header")]//th[contains(@class,"el-table-column--selection")]//label[contains(@class,"el-checkbox") and not(contains(@class,"is-disabled"))]',
        timeout=5,
    )
    if header_checkbox:
        log_stage(f"Selecting all result rows ({len(rows)} row(s))")
        header_checkbox.click(by_js=True)
        human_pause(1.0, 1.6)
        return

    log_stage("Header select-all checkbox not found; falling back to row-by-row selection")
    for row in rows:
        try:
            checkbox = row.ele(
                'xpath:.//td[contains(@class,"el-table-column--selection")]//label[contains(@class,"el-checkbox") and not(contains(@class,"is-checked"))]',
                timeout=1,
            )
        except Exception:
            checkbox = None
        if checkbox:
            checkbox.click(by_js=True)
            human_pause(0.2, 0.5)

    human_pause(0.8, 1.4)


def select_search_result(page: ChromiumPage, query: Query) -> None:
    select_all_search_results(page, query)


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


def wait_for_download(page: ChromiumPage, download_dir: Path, started_after: float, timeout: int = 60) -> Path:
    try:
        page.wait.downloads_done(timeout=timeout)
    except Exception:
        pass

    end = time.time() + timeout
    while time.time() < end:
        latest = latest_file(download_dir, "*.xlsx")
        partials = list(download_dir.glob("*.crdownload")) + list(download_dir.glob("*.tmp"))
        if latest and latest.stat().st_mtime >= started_after and not partials:
            return latest
        time.sleep(1)
    raise TimeoutError("Timed out waiting for Excel download")


def apply_filters(page: ChromiumPage, query: Query, manual_date: bool = False) -> None:
    log_stage(f"Applying filters for query: {query.name} (category: {query.category})")
    ensure_price_page(page, DEFAULT_URL)
    page.wait.ele_displayed(f"text={ZH_SEARCH}", timeout=20)
    human_pause(1.0, 1.8)
    dismiss_intro_guide(page)

    module = strategy_module(query)
    log_stage(f"Using execution strategy: {query.execution_strategy}")
    module.apply_navigation(
        page,
        query,
        {
            "click_main_nav": click_main_nav,
            "click_sub_nav": click_sub_nav,
        },
    )
    normalize_price_tabs(page, DEFAULT_URL)
    ensure_price_page(page, DEFAULT_URL)

    profile = product_profile(query)

    if query.price_type:
        log_stage(f"Selecting price type/classification: {query.price_type}")
        try:
            click_option_in_group(page, [profile.get("price_type_label", ZH_PRICE_TYPE), ZH_CLASSIFICATION, ZH_PRICE_TYPE], query.price_type)
        except RuntimeError as exc:
            if "Group not found" in str(exc):
                log_stage(f"Price type group not present; skipping: {query.price_type}")
            else:
                raise

    for item in query.product_names:
        log_stage(f"Selecting product: {item}")
        click_checkbox_in_group(page, profile.get("product_label", ZH_PRODUCT), item)
    for item in query.specifications:
        log_stage(f"Selecting specification: {item}")
        click_checkbox_in_group(page, profile.get("spec_label", ZH_SPEC), item)
    for item in query.materials:
        log_stage(f"Selecting material: {item}")
        click_checkbox_in_group(page, profile.get("material_label", ZH_MATERIAL), item)

    for item in query.mesh_models:
        log_stage(f"Selecting mesh model: {item}")
        click_checkbox_in_group(page, profile.get("extra_groups", {}).get("mesh_models", ZH_MESH_MODEL), item)
    for item in query.brands:
        log_stage(f"Selecting brand: {item}")
        click_checkbox_in_group(page, profile.get("extra_groups", {}).get("brands", ZH_BRAND), item, raise_if_missing=False)
    for item in query.delivery_states:
        log_stage(f"Selecting delivery status: {item}")
        click_checkbox_in_group(page, profile.get("extra_groups", {}).get("delivery_states", ZH_DELIVERY_STATUS), item, raise_if_missing=False)
    for item in query.diameters:
        log_stage(f"Selecting diameter: {item}")
        click_checkbox_in_group(page, profile.get("extra_groups", {}).get("diameters", ZH_DIAMETER), item, raise_if_missing=False)

    pane_id = ""
    if query.market_group and query.markets:
        log_stage(f"Selecting market group: {query.market_group}")
        pane_id = click_market_tab(page, query.market_group)
    for item in query.markets:
        log_stage(f"Selecting market: {item}")
        if pane_id:
            click_market_option(page, pane_id, item)
        else:
            click_checkbox_in_group(page, profile.get("market_label", ZH_MARKET), item)
    for item in query.mills:
        log_stage(f"Selecting mill/origin: {item}")
        click_checkbox_in_any_group(page, profile.get("mill_labels", [ZH_MILL]), item)
    if query.price_scope:
        log_stage(f"Selecting frequency: {query.price_scope}")
        click_radio_button_in_group(page, ZH_FREQUENCY, query.price_scope)
    log_stage(f"Selecting publish mode: {ZH_DATE_RANGE}")
    click_radio_in_group(page, ZH_PUBLISH_TIME, ZH_DATE_RANGE)
    if query.publish_time:
        log_stage(f"Selecting publish time: {query.publish_time}")
        click_publish_type(page, query.publish_time)
    log_stage(f"Selecting date range: {query.start_date} -> {query.end_date}")
    set_date_range(page, query.start_date, query.end_date, manual_date=manual_date)
    log_stage("Running search")
    click_search(page)
    log_stage("Filters submitted; waiting for results")


def export_excel(page: ChromiumPage, query: Query, download_dir: Path) -> Path:
    log_stage("Waiting for result row")
    wait_for_result_row(page, query, timeout=20)
    log_stage("Selecting result row")
    select_search_result(page, query)
    log_stage("Clicking Export Excel")
    click_export_excel_button(page)
    log_stage("Confirming export dialog")
    started_after = time.time()
    confirm_export_dialog(page)
    log_stage("Export confirmed; waiting for download completion")

    try:
        downloaded = wait_for_download(page, download_dir, started_after=started_after, timeout=60)
    except Exception as exc:
        log_stage(f"Download wait failed ({exc}); falling back to latest file detection")
        downloaded = latest_file(download_dir, "*.xlsx")
        if not downloaded:
            raise RuntimeError(f"No downloadable Excel file detected for query: {query.name}")

    renamed = rename_downloaded_file(downloaded, query)
    log_stage(f"Downloaded file captured: {renamed.name}")
    return renamed


def build_result(query: Query, page: ChromiumPage, downloaded_file: Path | None, output_dir: Path, elapsed_seconds: float) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "query": asdict(query),
        "current_url": page.url,
        "downloaded_file": str(downloaded_file) if downloaded_file else "",
        "downloaded_name": downloaded_file.name if downloaded_file else "",
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        "elapsed_seconds": round(elapsed_seconds, 2),
        "elapsed_readable": str(timedelta(seconds=round(elapsed_seconds))),
    }
    result_path = output_dir / f"mysteel_export_{query.name}_{timestamp()}.json"
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return result_path


def reset_filters(page: ChromiumPage) -> None:
    ensure_price_page(page, DEFAULT_URL)
    dismiss_intro_guide(page)


def load_queries(config_path: Path, fallback_date: str) -> list[Query]:
    if not config_path.exists():
        raise RuntimeError(f"Missing query config file: {config_path}")

    if config_path.suffix.lower() == ".toml":
        with config_path.open("rb") as fh:
            payload = tomllib.load(fh)
    else:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    shared = payload.get("shared", {})
    queries: list[Query] = []

    shared_start = str(shared.get("start_date") or fallback_date)
    shared_end = str(shared.get("end_date") or shared_start)

    def build_query(item: dict[str, Any], defaults: dict[str, Any], strategy_name: str, idx: int) -> Query:
        merged = dict(defaults)
        merged.update(item)
        name = str(merged.get("name") or f"{strategy_name}_{idx}")
        return Query(
            name=name,
            execution_strategy=str(merged.get("execution_strategy") or strategy_name),
            category=str(merged.get("category") or ""),
            subcategory=str(merged.get("subcategory") or ""),
            second_nav=str(merged.get("second_nav") or ""),
            third_nav=str(merged.get("third_nav") or ""),
            price_type=str(merged.get("price_type") or ""),
            product_names=ensure_list(merged.get("product_name") or merged.get("product_names")),
            specifications=ensure_list(merged.get("specification") or merged.get("specifications")),
            materials=ensure_list(merged.get("material") or merged.get("materials")),
            market_group=str(merged.get("market_group") or ""),
            markets=ensure_list(merged.get("market") or merged.get("markets")),
            mills=ensure_list(merged.get("mill") or merged.get("mills")),
            brands=ensure_list(merged.get("brand") or merged.get("brands")),
            delivery_states=ensure_list(merged.get("delivery_state") or merged.get("delivery_states")),
            mesh_models=ensure_list(merged.get("mesh_model") or merged.get("mesh_models")),
            diameters=ensure_list(merged.get("diameter") or merged.get("diameters")),
            price_scope=str(merged.get("price_scope") or ""),
            publish_time=str(merged.get("publish_time") or ""),
            start_date=str(merged.get("start_date") or shared_start),
            end_date=str(merged.get("end_date") or shared_end),
            unit=str(merged.get("unit") or ""),
        )

    strategy_groups = payload.get("strategies") or {}
    if strategy_groups:
        for strategy_name, strategy_payload in strategy_groups.items():
            if not isinstance(strategy_payload, dict):
                continue
            defaults = dict(strategy_payload.get("defaults") or {})
            defaults.setdefault("execution_strategy", strategy_name)
            items = strategy_payload.get("queries") or strategy_payload.get("items") or []
            for idx, item in enumerate(items, start=1):
                if not isinstance(item, dict):
                    continue
                queries.append(build_query(item, defaults, str(strategy_name), idx))
    else:
        category_groups = payload.get("categories") or {}
        for category_name, category_payload in category_groups.items():
            if not isinstance(category_payload, dict):
                continue
            defaults = dict(category_payload.get("defaults") or {})
            defaults.setdefault("category", category_name)
            defaults.setdefault("execution_strategy", defaults.get("execution_strategy") or "cold_rolling")
            items = category_payload.get("queries") or category_payload.get("items") or []
            for idx, item in enumerate(items, start=1):
                if not isinstance(item, dict):
                    continue
                queries.append(build_query(item, defaults, str(defaults["execution_strategy"]), idx))

    if not queries:
        raise RuntimeError("No queries found in config file")
    return reorder_queries_by_strategy(queries)


def main() -> int:
    parser = argparse.ArgumentParser(description="Mysteel Excel export automation")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--config", default=str(CONFIG_PATH))
    parser.add_argument("--user-data-dir", default="Mysteel_Browser_Data")
    parser.add_argument("--download-dir", default=None)
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--target-date", default=default_target_date())
    parser.add_argument("--strategy", default="", help="Run only one execution strategy, for example: cold_rolling")
    parser.add_argument("--manual-date", action="store_true")
    parser.add_argument("--force-run-non-workday", action="store_true")
    args = parser.parse_args()

    env = load_env_file(ENV_PATH)
    username = env.get("MYSTEEL_USERNAME", "")
    password = env.get("MYSTEEL_PASSWORD", "")
    download_dir_str = args.download_dir or env.get("MYSTEEL_DOWNLOAD_DIR", "data")
    clear_download_dir_enabled = parse_bool(env.get("MYSTEEL_CLEAR_DOWNLOAD_DIR"), default=True)
    chrome_path = env.get("MYSTEEL_CHROME_PATH", "")
    manual_date = args.manual_date or parse_bool(env.get("MYSTEEL_MANUAL_DATE"), default=False)
    force_run_non_workday = args.force_run_non_workday or parse_bool(env.get("MYSTEEL_FORCE_RUN_NON_WORKDAY"), default=False)
    random_start_enabled = parse_bool(env.get("MYSTEEL_RANDOM_START_ENABLED"), default=True)
    random_start_max_minutes = parse_int(env.get("MYSTEEL_RANDOM_START_MAX_MINUTES"), default=15)
    if not username or not password:
        raise RuntimeError("MYSTEEL_USERNAME or MYSTEEL_PASSWORD is missing in .env")

    try:
        target_day = date.fromisoformat(args.target_date)
    except ValueError as exc:
        raise RuntimeError(f"Invalid --target-date value: {args.target_date}") from exc

    is_workday, workday_reason = is_workday_via_api(target_day)
    log_stage(f"Workday check for target date {target_day.isoformat()}: {workday_reason}")
    if not force_run_non_workday and not is_workday:
        log_stage(f"Target date is not a workday ({target_day.isoformat()}); skipping run")
        return 0

    maybe_wait_random_start(random_start_enabled, random_start_max_minutes)

    queries = load_queries(Path(args.config), args.target_date)
    if args.strategy:
        queries = [query for query in queries if query.execution_strategy == args.strategy]
        if not queries:
            raise RuntimeError(f"No queries found for strategy: {args.strategy}")
        log_stage(f"Strategy filter applied: {args.strategy} ({len(queries)} query/queries)")
    download_dir = Path(download_dir_str)
    output_dir = Path(args.output_dir)
    if clear_download_dir_enabled:
        removed = clear_download_dir(download_dir)
        log_stage(f"Cleared download directory: removed {removed} old file(s)")
    page = create_page(Path(args.user_data_dir), download_dir, chrome_path=chrome_path)
    summaries: list[dict[str, Any]] = []

    try:
        log_stage("Opening price-search page")
        page.get(args.url)
        page.wait.load_start()
        page.wait.doc_loaded()
        human_pause(1.0, 1.8)
        auto_login_if_needed(page, username, password, args.url)
        dismiss_intro_guide(page)

        for query in queries:
            log_stage(f"Starting query: {query.name}")
            started_at = time.perf_counter()
            apply_filters(page, query, manual_date=manual_date)
            downloaded = export_excel(page, query, download_dir)
            elapsed_seconds = time.perf_counter() - started_at
            result_path = build_result(query, page, downloaded, output_dir, elapsed_seconds)
            summaries.append({
                "query": query.name,
                "downloaded_file": str(downloaded) if downloaded else "",
                "downloaded_name": downloaded.name if downloaded else "",
                "result_file": str(result_path),
                "elapsed_seconds": round(elapsed_seconds, 2),
                "elapsed_readable": str(timedelta(seconds=round(elapsed_seconds))),
            })
            log_stage(f"Completed query: {query.name}")
            if query != queries[-1]:
                reset_filters(page)
                page.get(args.url)
                page.wait.load_start()
                page.wait.doc_loaded()
                human_pause(1.0, 1.8)

        print(json.dumps(summaries, ensure_ascii=False, indent=2))
        return 0
    finally:
        print("Browser left open for inspection.")


if __name__ == "__main__":
    sys.exit(main())
