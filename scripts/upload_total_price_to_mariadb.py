from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pymysql
from dotenv import load_dotenv

from scripts.build_total_price import load_existing_rows, normalize_excel_date, normalize_text


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    return int(raw)


def db_text(value: Any) -> str:
    return normalize_text(value)


def load_rows_from_total_price(output_path: Path) -> list[list[Any]]:
    rows = load_existing_rows(output_path)
    if not rows:
        raise RuntimeError(f"No rows found in summary workbook: {output_path}")
    print(f"Loaded {len(rows)} rows from summary workbook: {output_path}")
    return rows


def create_database_if_missing(host: str, port: int, user: str, password: str, database: str) -> None:
    conn = pymysql.connect(host=host, port=port, user=user, password=password, charset="utf8mb4", autocommit=True)
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    finally:
        conn.close()


def ensure_table(connection, table_name: str) -> None:
    ddl = f"""
    CREATE TABLE IF NOT EXISTS `{table_name}` (
        `record_id` VARCHAR(32) NOT NULL,
        `biz_type` VARCHAR(64) NOT NULL,
        `category` VARCHAR(64) NOT NULL,
        `subcategory` VARCHAR(64) NOT NULL,
        `product_name` VARCHAR(128) NOT NULL,
        `specification` VARCHAR(128) NOT NULL,
        `material` VARCHAR(128) NOT NULL,
        `market` VARCHAR(128) NOT NULL,
        `brand` VARCHAR(128) NOT NULL,
        `mill` VARCHAR(128) NOT NULL,
        `price` DECIMAL(18, 2) NULL,
        `publish_time` VARCHAR(64) NOT NULL,
        `price_date` DATE NOT NULL,
        `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (`record_id`),
        KEY `idx_price_date` (`price_date`),
        KEY `idx_product_date` (`product_name`, `price_date`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    with connection.cursor() as cursor:
        cursor.execute(ddl)


def upload_rows_to_mariadb(rows: list[list[Any]]) -> int:
    host = os.getenv("MARIADB_HOST", "127.0.0.1").strip() or "127.0.0.1"
    port = env_int("MARIADB_PORT", 3307)
    user = os.getenv("MARIADB_USER", "root").strip() or "root"
    password = os.getenv("MARIADB_PASSWORD", "").strip()
    database = os.getenv("MARIADB_DATABASE", "steel_price").strip() or "steel_price"
    table_name = os.getenv("MARIADB_TABLE", "total_price_history").strip() or "total_price_history"

    if not password:
        raise RuntimeError("Missing MARIADB_PASSWORD in environment variables or .env")

    create_database_if_missing(host, port, user, password, database)
    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
        autocommit=False,
    )
    try:
        ensure_table(connection, table_name)
        sql = f"""
        INSERT INTO `{table_name}` (
            `record_id`, `biz_type`, `category`, `subcategory`, `product_name`, `specification`,
            `material`, `market`, `brand`, `mill`, `price`, `publish_time`, `price_date`
        ) VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE
            `biz_type` = VALUES(`biz_type`),
            `category` = VALUES(`category`),
            `subcategory` = VALUES(`subcategory`),
            `product_name` = VALUES(`product_name`),
            `specification` = VALUES(`specification`),
            `material` = VALUES(`material`),
            `market` = VALUES(`market`),
            `brand` = VALUES(`brand`),
            `mill` = VALUES(`mill`),
            `price` = VALUES(`price`),
            `publish_time` = VALUES(`publish_time`),
            `price_date` = VALUES(`price_date`)
        """
        payload = [
            (
                db_text(row[0]), db_text(row[1]), db_text(row[2]), db_text(row[3]), db_text(row[4]), db_text(row[5]),
                db_text(row[6]), db_text(row[7]), db_text(row[8]), db_text(row[9]), row[10], db_text(row[11]), normalize_excel_date(row[12]),
            )
            for row in rows
        ]
        with connection.cursor() as cursor:
            cursor.executemany(sql, payload)
        connection.commit()
        return len(payload)
    finally:
        connection.close()


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Upload Total_Price.xlsx to MariaDB")
    parser.add_argument("--input-file", default=str(Path("data") / "Total_Price.xlsx"), help="Summary workbook path")
    args = parser.parse_args()

    input_path = Path(args.input_file).expanduser().resolve()
    rows = load_rows_from_total_price(input_path)
    affected = upload_rows_to_mariadb(rows)
    print(f"MariaDB upsert completed: {affected} rows prepared")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
