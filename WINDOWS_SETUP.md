# Windows Setup Guide

This guide is for setting up `steel_price` on a new Windows machine.

It is also suitable for Windows Server 2012 R2, but older systems need extra compatibility checks.

## 1. What to copy to the new machine

Recommended:

- clone the Git repository on the new machine
- or copy the project source files only

Keep these files:

- `README.md`
- `WINDOWS_SETUP.md`
- `pyproject.toml`
- `uv.lock`
- `queries.toml`
- `.env.example`
- `scripts/`

Do not copy these runtime files or local caches:

- `.env`
- `.uv-cache/`
- `data/`
- `output/`
- `Mysteel_Browser_Data/`
- `.browser-profile/`

Reason:

- browser cache and login state are machine-dependent
- local output files do not belong to deployment assets
- cache directories can be rebuilt automatically

## 2. Install required software

Install these first:

- Python 3.12
- `uv`
- Google Chrome

Check Python:

```powershell
python --version
```

Check `uv`:

```powershell
uv --version
```

Check Chrome path:

```powershell
Get-ChildItem 'C:\Program Files\Google\Chrome\Application\chrome.exe',
'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
"$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe" -ErrorAction SilentlyContinue
```

## 3. Create the local environment file

Create `.env` from `.env.example`.

Minimum required values:

```env
MYSTEEL_USERNAME=your_mysteel_username
MYSTEEL_PASSWORD=your_mysteel_password
MYSTEEL_DOWNLOAD_DIR=E:\code\steel_price\data
MYSTEEL_CHROME_PATH=C:\Users\YourUser\AppData\Local\Google\Chrome\Application\chrome.exe
MYSTEEL_MANUAL_DATE=false
MYSTEEL_FORCE_RUN_NON_WORKDAY=false
MYSTEEL_RANDOM_START_ENABLED=false
MYSTEEL_RANDOM_START_MAX_MINUTES=15
```

Notes:

- `MYSTEEL_USERNAME` and `MYSTEEL_PASSWORD` are required
- `MYSTEEL_CHROME_PATH` should match the actual Chrome path on the new machine
- `MYSTEEL_DOWNLOAD_DIR` can be changed if needed

## 4. Install project dependencies

From the project root:

```powershell
uv sync
```

If you want to keep local cache inside the repository:

```powershell
$env:UV_CACHE_DIR='E:\code\steel_price\.uv-cache'
uv sync
```

## 5. First-time browser preparation

This project uses a real browser session through DrissionPage.

On the new machine:

- do not copy old browser cache from another PC
- let the browser profile be created locally
- allow the script to log in and build a fresh local session

The first run may take a little longer because browser data is being created.

## 6. Run a single strategy first

Before running everything, test one strategy at a time.

Example:

```powershell
$env:UV_CACHE_DIR='E:\code\steel_price\.uv-cache'
uv run python .\scripts\mysteel_export_excel.py --strategy cold_rolling
```

Then test:

- `hot_rolling`
- `building_steel`
- `stainless_flat`

## 7. Run the full job

After single-strategy checks pass:

```powershell
$env:UV_CACHE_DIR='E:\code\steel_price\.uv-cache'
uv run python .\scripts\mysteel_export_excel.py
```

## 8. Recommended run time

Mysteel prices are usually not updated immediately at the start of the day.

Recommended time windows:

- morning run: after `10:05`
- evening run: after `16:35`

If the script runs successfully but data looks old or empty, first check whether Mysteel has published the latest update.

## 9. Windows Server 2012 R2 notes

If the target machine is Windows Server 2012 R2, pay extra attention to these items.

### Browser and desktop session

The script needs a real browser and a usable desktop session.

Make sure:

- Chrome can launch normally
- the running account has desktop access
- browser can remain stable after remote login

If browser automation fails only on scheduled runs, the common reason is that the task is running without a proper interactive desktop session.

### Compatibility

Check these before long-term deployment:

- Python 3.12 compatibility
- Chrome version availability
- TLS / certificate support
- required VC++ runtime libraries

### Scheduled tasks

If you use Windows Task Scheduler:

- prefer the same Windows account used for manual testing
- verify browser startup under that account
- verify file write permissions for:
  - project directory
  - `data/`
  - `output/`
  - `.uv-cache/`

## 10. Troubleshooting

### Chrome path error

If you see:

```text
Configured Chrome binary does not exist
```

Then fix `MYSTEEL_CHROME_PATH` in `.env`.

### Holiday API SSL error

If you see a holiday API SSL warning, the script can still fall back to weekday-based workday logic.

This usually does not block execution unless your environment has wider TLS problems.

### Filter not found

If the browser opens but a filter group cannot be found:

- verify the selected strategy is correct
- verify Mysteel page labels have not changed
- verify the query configuration matches the target page

### No rows found

If the script runs but returns no rows:

- check whether Mysteel has updated the latest prices
- check date range
- check whether the query is too restrictive
