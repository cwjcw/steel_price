from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


DEFAULT_URL = "https://price.mysteel.com/#/price-search"
EDGE_BINARY_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]


@dataclass(frozen=True)
class Query:
    category: str = "钢材"
    subcategory: str = "冷轧"
    price_type: str = "市场价"
    product_name: str = "冷轧板"
    specification: str = "1*1250*C"
    material: str = "Q195"
    market: str = "泰安"
    price_scope: str = "按日期"
    publish_time: str = "晚盘价格"
    start_date: str = "2026-03-16"
    end_date: str = "2026-03-16"
    unit: str = "元/吨"


def now_tag() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def edge_binary() -> str | None:
    for candidate in EDGE_BINARY_CANDIDATES:
        if candidate.exists():
            return str(candidate)
    return None


def create_driver(user_data_dir: Path | None = None) -> webdriver.Edge:
    options = EdgeOptions()
    binary = edge_binary()
    if binary:
        options.binary_location = binary
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    if user_data_dir is not None:
        user_data_dir.mkdir(parents=True, exist_ok=True)
        options.add_argument(f"--user-data-dir={user_data_dir}")
    driver = webdriver.Edge(options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


def xpath_literal(value: str) -> str:
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    parts = value.split("'")
    return "concat(" + ", \"'\", ".join(f"'{part}'" for part in parts) + ")"


def wait_clickable(driver: webdriver.Edge, xpath: str, timeout: int = 20):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.XPATH, xpath))
    )


def click_js(driver: webdriver.Edge, element) -> None:
    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center', inline:'center'});", element
    )
    driver.execute_script("arguments[0].click();", element)


def click_by_text(driver: webdriver.Edge, text: str, timeout: int = 20) -> None:
    text_lit = xpath_literal(text)
    xpath = (
        f"//*[self::a or self::button or self::span or self::div or self::label]"
        f"[contains(normalize-space(.), {text_lit})]"
    )
    element = wait_clickable(driver, xpath, timeout=timeout)
    click_js(driver, element)


def find_group_container(driver: webdriver.Edge, group_label: str):
    label = xpath_literal(group_label)
    candidates = [
        f"//*[contains(normalize-space(.), {label})]/ancestor::*[self::li or self::div or self::td][1]",
        f"//*[contains(normalize-space(.), {label})]/ancestor::*[self::div or self::section or self::form][1]",
    ]
    last_error = None
    for xpath in candidates:
        try:
            return WebDriverWait(driver, 8).until(
                lambda d: d.find_element(By.XPATH, xpath)
            )
        except Exception as exc:
            last_error = exc
    raise last_error or RuntimeError(f"未找到筛选分组: {group_label}")


def option_is_selected(option_element) -> bool:
    attrs = " ".join(
        filter(
            None,
            [
                option_element.get_attribute("class"),
                option_element.get_attribute("aria-checked"),
                option_element.get_attribute("data-checked"),
            ],
        )
    ).lower()
    return any(token in attrs for token in ["active", "checked", "selected", "is-checked", "cur"])


def set_group_option(
    driver: webdriver.Edge, group_label: str, option_text: str, should_select: bool = True
) -> None:
    container = find_group_container(driver, group_label)
    option_lit = xpath_literal(option_text)
    option = container.find_element(
        By.XPATH,
        f".//*[self::label or self::span or self::a or self::div]"
        f"[contains(normalize-space(.), {option_lit})]",
    )
    selected = option_is_selected(option)
    if selected != should_select:
        click_js(driver, option)
        time.sleep(0.6)


def set_input_value(driver: webdriver.Edge, value: str, index: int) -> None:
    inputs = driver.find_elements(
        By.XPATH,
        "//input[contains(@placeholder, '时间') or contains(@placeholder, '日期') or @type='text']",
    )
    visible_inputs = [item for item in inputs if item.is_displayed() and item.is_enabled()]
    if index >= len(visible_inputs):
        raise RuntimeError(f"未找到第 {index + 1} 个日期输入框")
    input_box = visible_inputs[index]
    input_box.click()
    input_box.send_keys(Keys.CONTROL, "a")
    input_box.send_keys(value)
    input_box.send_keys(Keys.ENTER)
    time.sleep(0.5)


def wait_for_manual_login(driver: webdriver.Edge) -> None:
    print("浏览器已打开，请在页面中完成 Mysteel 登录。")
    print("登录完成并回到价格查询页后，在这里按回车继续...")
    input()
    driver.switch_to.window(driver.window_handles[-1])


def dump_debug(driver: webdriver.Edge, output_dir: Path, prefix: str) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / f"{prefix}.html"
    png_path = output_dir / f"{prefix}.png"
    html_path.write_text(driver.page_source, encoding="utf-8")
    driver.save_screenshot(str(png_path))
    return {"html": str(html_path), "screenshot": str(png_path)}


def extract_visible_tables(driver: webdriver.Edge) -> list[pd.DataFrame]:
    tables = []
    for css in ["table", ".el-table__body-wrapper table", ".ant-table table"]:
        for element in driver.find_elements(By.CSS_SELECTOR, css):
            try:
                if not element.is_displayed():
                    continue
                html = element.get_attribute("outerHTML")
                parsed = pd.read_html(html)
                tables.extend(parsed)
            except Exception:
                continue
    return tables


def save_tables(tables: list[pd.DataFrame], output_dir: Path, stem: str) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for idx, table in enumerate(tables, start=1):
        csv_path = output_dir / f"{stem}_table_{idx}.csv"
        table.to_csv(csv_path, index=False, encoding="utf-8-sig")
        saved.append(str(csv_path))
    return saved


def apply_filters(driver: webdriver.Edge, query: Query) -> None:
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(2)

    click_by_text(driver, query.category)
    time.sleep(1)
    click_by_text(driver, query.subcategory)
    time.sleep(1)

    for group_label, option_text in [
        ("价格类型", query.price_type),
        ("品名", query.product_name),
        ("规格", query.specification),
        ("材质", query.material),
    ]:
        set_group_option(driver, group_label, option_text, should_select=True)

    try:
        click_by_text(driver, "QRSTU", timeout=6)
        time.sleep(0.5)
    except TimeoutException:
        pass
    set_group_option(driver, "市场", query.market, should_select=True)

    try:
        set_group_option(driver, "价格频度", query.price_scope, should_select=True)
    except Exception:
        pass

    try:
        click_by_text(driver, query.publish_time, timeout=8)
    except Exception:
        pass

    set_input_value(driver, query.start_date, 0)
    set_input_value(driver, query.end_date, 1)

    click_by_text(driver, "搜索")
    time.sleep(5)


def main() -> int:
    parser = argparse.ArgumentParser(description="Mysteel 价格查询自动化抓取")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--user-data-dir", default=".browser-profile/mysteel-edge")
    args = parser.parse_args()

    query = Query()
    output_dir = Path(args.output_dir)
    user_data_dir = Path(args.user_data_dir)
    debug_tag = f"mysteel_{now_tag()}"

    driver = create_driver(user_data_dir=user_data_dir)
    try:
        driver.get(args.url)
        wait_for_manual_login(driver)
        apply_filters(driver, query)

        debug_files = dump_debug(driver, output_dir, debug_tag)
        tables = extract_visible_tables(driver)
        table_files = save_tables(tables, output_dir, debug_tag)

        result = {
            "query": asdict(query),
            "url": driver.current_url,
            "tables_found": len(tables),
            "table_files": table_files,
            "debug_files": debug_files,
        }
        result_path = output_dir / f"{debug_tag}_result.json"
        result_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        print("按回车关闭浏览器...")
        try:
            input()
        except EOFError:
            pass
        driver.quit()


if __name__ == "__main__":
    sys.exit(main())
