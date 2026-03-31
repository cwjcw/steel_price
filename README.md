# steel_price

Automates Mysteel Price Center filtering, querying, result selection, and Excel export.

## Overview

Supported and verified strategies:

- `cold_rolling`
- `hot_rolling`
- `building_steel`
- `stainless_flat`

Default outputs:

- Excel files are saved to `data/`
- JSON run summaries are saved to `output/`

## Mysteel Update Timing

Please pay attention to Mysteel update timing, otherwise the script may run correctly while the latest prices are not published yet.

Recommended rule of thumb:

- Morning prices are usually updated after `10:00`
- Evening prices are usually updated after `16:30`

Recommended schedule:

- Morning jobs: after `10:05`
- Evening jobs: after `16:35`

## Repository Layout

```text
steel_price/
|- README.md
|- pyproject.toml
|- queries.toml
|- scripts/
|  |- mysteel_export_excel.py
|  |- strategies/
|  |  |- registry.py
|  |  |- cold_rolling.py
|  |  |- hot_rolling.py
|  |  |- building_steel.py
|  |  `- stainless_flat.py
|- data/
`- output/
```

## Main Script vs Strategy Scripts

### Main script: `scripts/mysteel_export_excel.py`

The main script handles the shared workflow:

- read `.env`
- read `queries.toml`
- parse CLI arguments
- check workday status
- open browser and log in
- call the selected strategy
- set date, search, select rows, export Excel
- write `output/*.json`

Think of it as the scheduler and the common executor.

### Strategy scripts: `scripts/strategies/*.py`

Each strategy script handles page-specific differences:

- how navigation should be clicked
- what each filter group is called on that page
- which groups must be expanded first
- whether extra fields exist, such as brand, delivery status, diameter, or mesh model

Think of each strategy as a page adapter.

### Relationship

- The main script decides how to run.
- The strategy script decides where to click on a specific page.

## Strategy Notes

### `cold_rolling`

- for cold rolling pages
- top navigation: steel category -> cold rolling
- product field uses product-name style grouping
- market usually uses alphabet-group tabs

### `hot_rolling`

- for hot rolling pages
- top navigation: steel category -> hot rolling
- product field uses product-kind style grouping
- supports optional `diameter`
- specification, material, and enterprise may need expansion first

### `building_steel`

- for building steel pages
- currently adapted for welded rebar mesh
- supports extra field `mesh_model`
- price type selection is commonly required

### `stainless_flat`

- for stainless flat plate pages
- navigation: nickel-chromium stainless steel -> stainless steel -> stainless flat plate
- product field uses product-kind style grouping
- classification field is required by page structure
- market is a normal checkbox group, not alphabet tabs
- material, specification, and enterprise are expandable groups
- brand is kept but optional
- delivery status is kept but optional

## Configuration

All queries are maintained in `queries.toml`.

Current structure:

- `strategies.<strategy_name>.defaults`
- `strategies.<strategy_name>.queries`

Common fields:

- `execution_strategy`
- `category`
- `subcategory`
- `second_nav`
- `third_nav`
- `price_type`
- `product_name`
- `specification`
- `material`
- `market_group`
- `market`
- `mill`
- `brand`
- `delivery_state`
- `mesh_model`
- `diameter`
- `price_scope`
- `publish_time`
- `unit`
- `start_date`
- `end_date`

## Environment Variables

The main script reads these values from `.env`:

- `MYSTEEL_USERNAME`
- `MYSTEEL_PASSWORD`
- `MYSTEEL_DOWNLOAD_DIR`
- `MYSTEEL_CHROME_PATH`
- `MYSTEEL_MANUAL_DATE`
- `MYSTEEL_FORCE_RUN_NON_WORKDAY`
- `MYSTEEL_RANDOM_START_ENABLED`
- `MYSTEEL_RANDOM_START_MAX_MINUTES`

Notes:

- `MYSTEEL_CHROME_PATH` lets you explicitly set the Chrome or Chromium executable path.
- If `MYSTEEL_CHROME_PATH` is empty, the script falls back to built-in common Windows install paths.

## Run Commands

Install dependencies:

```powershell
uv sync
```

Run a single strategy:

```powershell
$env:UV_CACHE_DIR='E:\code\steel_price\.uv-cache'; uv run python .\scripts\mysteel_export_excel.py --strategy cold_rolling
```

Available values:

- `cold_rolling`
- `hot_rolling`
- `building_steel`
- `stainless_flat`

Run all strategies:

```powershell
$env:UV_CACHE_DIR='E:\code\steel_price\.uv-cache'; uv run python .\scripts\mysteel_export_excel.py
```

## Migration Notes for Other PCs or Windows Server 2012 R2

### 1. Do not hard-code Chrome path in code

Use `.env` instead:

```env
MYSTEEL_CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
```

When moving to another machine, update `.env` first instead of editing Python code.

### 2. A real desktop browser session is required

This project uses DrissionPage with a real browser, not a pure HTTP API workflow.

On Windows Server 2012 R2, make sure:

- Chrome or compatible Chromium is installed
- the running account has desktop session permission
- browser can stay stable after remote desktop disconnect
- ideally, testing is done under the same logged-in account that will run scheduled jobs

### 3. Writable directories are required

Make sure these paths are writable:

- `data/`
- `output/`
- browser `user-data-dir`
- `.uv-cache`

### 4. Windows Server 2012 R2 is old

Check these items before deployment:

- whether a usable Chrome version can still be installed
- whether Python 3.12 runs reliably in that environment
- whether TLS and certificates are healthy
- whether required VC++ runtime libraries are installed

### 5. Use the same account for manual tests and scheduled tasks when possible

Otherwise you may hit issues such as:

- different browser profile directory
- lost login state
- different download permissions
- browser startup failure in a background session

### 6. Validate one strategy at a time before full runs

Recommended validation order after migration:

1. Confirm browser startup and Mysteel login
2. Run `cold_rolling`
3. Run `hot_rolling`
4. Run `building_steel`
5. Run `stainless_flat`
6. Run the full job

## Troubleshooting

- If the browser opens but filters cannot be found, first check whether the Mysteel page structure changed.
- If the script runs but returns no data, first check whether the latest prices have been published yet.
- When adding a new category, add a new strategy first, then validate it with `--strategy`, and only after that run the full job.
