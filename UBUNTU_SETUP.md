# Ubuntu 部署说明

这份文档用于指导你把 `steel_price` 部署到 Ubuntu 或其他常见 Linux 环境。

需要先说明一个重点：

- 这套脚本依赖真实浏览器自动化
- 在 Linux 上运行时，必须确保 Chrome 或 Chromium 可用
- 如果服务器没有桌面环境，还需要额外准备图形会话或虚拟显示环境

## 1. 需要带过去哪些文件

推荐做法：

- 在新机器上直接克隆 Git 仓库
- 或者只复制源码文件

建议保留的文件：

- `README.md`
- `WINDOWS_SETUP.md`
- `UBUNTU_SETUP.md`
- `pyproject.toml`
- `uv.lock`
- `queries.toml`
- `.env.example`
- `scripts/`

不建议复制的本地运行产物：

- `.env`
- `.uv-cache/`
- `data/`
- `output/`
- `Mysteel_Browser_Data/`
- `.browser-profile/`

## 2. 安装基础软件

建议先安装：

- Python 3.12
- `uv`
- Google Chrome 或 Chromium

检查 Python：

```bash
python3 --version
```

检查 `uv`：

```bash
uv --version
```

## 3. 查找 Chrome / Chromium 路径

在 Ubuntu 上，最方便的方式是直接查可执行文件路径：

```bash
which google-chrome
which chromium-browser
which chromium
```

也可以使用：

```bash
command -v google-chrome
command -v chromium-browser
command -v chromium
```

常见路径包括：

- `/usr/bin/google-chrome`
- `/usr/bin/chromium-browser`
- `/usr/bin/chromium`

找到后，把路径写进 `.env`：

```env
MYSTEEL_CHROME_PATH=/usr/bin/google-chrome
```

## 4. 创建 `.env`

建议从 `.env.example` 复制出 `.env`。

示例：

```env
MYSTEEL_USERNAME=your_mysteel_username
MYSTEEL_PASSWORD=your_mysteel_password
MYSTEEL_DOWNLOAD_DIR=/home/your_user/code/steel_price/data
MYSTEEL_CHROME_PATH=/usr/bin/google-chrome
MYSTEEL_MANUAL_DATE=false
MYSTEEL_FORCE_RUN_NON_WORKDAY=false
MYSTEEL_RANDOM_START_ENABLED=false
MYSTEEL_RANDOM_START_MAX_MINUTES=15
```

## 5. 安装依赖

在项目根目录执行：

```bash
export UV_CACHE_DIR="$PWD/.uv-cache"
uv sync
```

## 6. 第一次运行时的浏览器准备

建议在新机器上本地重新建立浏览器缓存和登录态，不要直接复制旧机器的浏览器 profile。

也就是说：

- 代码和配置可以迁移
- 浏览器缓存和登录态不要迁移

## 7. 先做单策略验证

建议顺序如下：

1. 先确认浏览器可以启动
2. 再确认 Mysteel 可以成功登录
3. 单独跑 `cold_rolling`
4. 单独跑 `hot_rolling`
5. 单独跑 `building_steel`
6. 单独跑 `stainless_flat`
7. 最后再跑全量

单策略示例：

```bash
export UV_CACHE_DIR="$PWD/.uv-cache"
uv run python ./scripts/mysteel_export_excel.py --strategy cold_rolling
```

## 8. 全量运行

```bash
export UV_CACHE_DIR="$PWD/.uv-cache"
uv run python ./scripts/mysteel_export_excel.py
```

## 9. Linux / Ubuntu 特别注意事项

### 真实浏览器环境

如果是在桌面版 Ubuntu 上运行，通常更容易成功。

如果是在服务器版 Ubuntu 上运行，需要重点注意：

- 是否有图形桌面环境
- 是否能启动真实浏览器
- 是否有可用的显示环境

如果没有桌面环境，常见做法是：

- 使用 `xvfb`
- 或准备其他虚拟显示方案

### 依赖兼容性

建议提前确认：

- Chrome 或 Chromium 能正常启动
- Python 3.12 可用
- 系统证书和 TLS 正常
- 当前账号对项目目录有读写权限

### 定时任务

如果用 `cron` 或 `systemd` 定时运行，需要确认：

- 环境变量已正确加载
- `MYSTEEL_CHROME_PATH` 正确
- 任务运行时浏览器有可用显示环境

## 10. 常见问题

### 1. 找不到 Chrome 路径

执行：

```bash
which google-chrome
which chromium-browser
which chromium
```

然后把结果写到 `.env` 的 `MYSTEEL_CHROME_PATH`。

### 2. 脚本能启动，但浏览器打不开

优先检查：

- Chrome / Chromium 是否安装
- 当前用户是否有图形会话
- 是否缺少显示环境

### 3. 脚本跑通但没有数据

优先检查：

- 是否还没到 Mysteel 当次更新时间
- 日期范围是否正确
- 查询条件是否过于严格
