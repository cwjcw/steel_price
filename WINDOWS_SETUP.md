# Windows 部署说明

这份文档用于指导你把 `steel_price` 部署到一台新的 Windows 机器上。

同样适用于 Windows Server 2012 R2，但老系统需要额外关注兼容性。

## 1. 新机器需要带过去哪些文件

推荐做法：

- 在新机器上直接克隆 Git 仓库
- 或者只复制项目源码文件

建议保留的文件：

- `README.md`
- `WINDOWS_SETUP.md`
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

原因：

- 浏览器缓存和登录态强依赖本机环境
- 本地导出文件不是部署资源
- 缓存目录可以在新机器上自动重建

## 2. 新机器需要安装的软件

建议先安装：

- Python 3.12
- `uv`
- Google Chrome

检查 Python：

```powershell
python --version
```

检查 `uv`：

```powershell
uv --version
```

检查 Chrome 实际路径：

```powershell
Get-ChildItem 'C:\Program Files\Google\Chrome\Application\chrome.exe',
'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
"$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe" -ErrorAction SilentlyContinue
```

## 3. 在新机器创建 `.env`

建议从 `.env.example` 复制出 `.env`。

最少需要配置这些值：

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

说明：

- `MYSTEEL_USERNAME` 和 `MYSTEEL_PASSWORD` 必填
- `MYSTEEL_CHROME_PATH` 必须和新机器上的实际 Chrome 路径一致
- `MYSTEEL_DOWNLOAD_DIR` 可以按你的部署路径调整

## 4. 安装项目依赖

在项目根目录执行：

```powershell
uv sync
```

如果你希望本地缓存也放在仓库目录里：

```powershell
$env:UV_CACHE_DIR='E:\code\steel_price\.uv-cache'
uv sync
```

## 5. 第一次运行时的浏览器准备

这个项目使用 DrissionPage 驱动真实浏览器，不是纯 HTTP 抓取。

在新机器上，建议这样做：

- 不要复制旧机器的浏览器缓存
- 不要复制旧机器的登录态目录
- 让新机器第一次运行时本地生成浏览器 profile
- 第一次登录 Mysteel 时重新建立本地会话

也就是说：

- 代码和配置可以迁移
- 浏览器缓存和登录态不要迁移

## 6. 先按单策略验证

不要一上来就直接跑全量。

建议顺序如下：

1. 先确认浏览器能正常启动
2. 再确认 Mysteel 能成功登录
3. 单独跑 `cold_rolling`
4. 单独跑 `hot_rolling`
5. 单独跑 `building_steel`
6. 单独跑 `stainless_flat`
7. 最后再跑全量

单策略示例：

```powershell
$env:UV_CACHE_DIR='E:\code\steel_price\.uv-cache'
uv run python .\scripts\mysteel_export_excel.py --strategy cold_rolling
```

## 7. 全量运行

当单策略都通过后，再执行全量：

```powershell
$env:UV_CACHE_DIR='E:\code\steel_price\.uv-cache'
uv run python .\scripts\mysteel_export_excel.py
```

## 8. 建议执行时间

Mysteel 当天价格通常不是一开盘就全部更新。

建议按下面时间跑：

- 早盘：`10:05` 之后
- 晚盘：`16:35` 之后

如果脚本运行成功，但结果偏旧、为空、或条数不对，先检查 Mysteel 是否完成了当次更新。

## 9. Windows Server 2012 R2 注意事项

如果目标环境是 Windows Server 2012 R2，请重点注意下面几项。

### 浏览器和桌面会话

脚本依赖真实浏览器和可用的桌面会话。

请确认：

- Chrome 能正常安装并启动
- 运行账号有桌面会话权限
- 远程桌面断开后浏览器仍然稳定

如果定时任务能启动 Python，但浏览器自动化失败，常见原因就是任务运行时没有真正的交互式桌面环境。

### 兼容性

老系统建议提前确认：

- Python 3.12 是否稳定
- Chrome 是否还有可用版本
- TLS / 证书环境是否正常
- VC++ 运行库是否齐全

### 定时任务

如果后面要用 Windows 任务计划程序：

- 尽量使用和手工测试相同的 Windows 账号
- 先验证这个账号下 Chrome 能正常启动
- 再确认这些目录有写权限：
  - 项目根目录
  - `data/`
  - `output/`
  - `.uv-cache/`

## 10. 常见问题

### 1. Chrome 路径错误

如果看到：

```text
Configured Chrome binary does not exist
```

说明 `.env` 里的 `MYSTEEL_CHROME_PATH` 写错了。

先查新机器上 Chrome 的真实路径，再更新 `.env`。

### 2. 节假日 API SSL 报错

如果看到节假日 API 的 SSL 警告，主脚本会自动回退到“按星期判断工作日”的逻辑。

一般不会因此阻塞主流程。

### 3. 页面打开了，但筛选项找不到

优先检查：

- 当前策略是否选对了
- Mysteel 页面结构是否变化
- 查询条件是否和页面字段匹配

### 4. 脚本跑完但没有结果

优先检查：

- Mysteel 是否已更新最新价格
- 日期范围是否正确
- 查询条件是否过于严格

## 11. 当前部署文档校对结果

这份文档已按当前项目状态核对，确认过以下内容：

- 新机器推荐迁移方式正确
- `MYSTEEL_CHROME_PATH` 已是当前主脚本支持的正式配置项
- 单策略和全量运行命令与当前代码一致
- Windows Server 2012 R2 的主要风险点已覆盖
