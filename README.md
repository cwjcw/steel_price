# steel_price

用于自动登录 Mysteel 价格中心，按配置执行筛选、查询、勾选结果并导出 Excel。

## 项目概览

当前项目已经支持并验证通过以下 4 个执行策略：

- `cold_rolling`：冷轧
- `hot_rolling`：热轧
- `building_steel`：建筑钢材
- `stainless_flat`：不锈钢平板

默认输出位置：

- Excel 导出文件：`data/`
- 每次运行的结果摘要：`output/`

## Mysteel 数据更新时间

使用这套脚本时，最容易误判的不是“脚本出错”，而是“脚本跑通了，但 Mysteel 当次价格还没更新”。

经验上建议按下面的时间理解：

- 早盘数据一般在 `10:00` 之后更新
- 晚盘数据一般在 `16:30` 之后更新

建议定时任务的执行时间：

- 早盘任务尽量放在 `10:05` 之后
- 晚盘任务尽量放在 `16:35` 之后

如果脚本执行成功，但导出内容为空、条数明显不对，或者还是前一时段的数据，先优先确认是否还没到 Mysteel 的更新时间。

## 目录结构

```text
steel_price/
|- README.md
|- WINDOWS_SETUP.md
|- pyproject.toml
|- uv.lock
|- queries.toml
|- .env.example
|- .gitattributes
|- .gitignore
|- scripts/
|  |- mysteel_export_excel.py
|  `- strategies/
|     |- __init__.py
|     |- registry.py
|     |- cold_rolling.py
|     |- hot_rolling.py
|     |- building_steel.py
|     `- stainless_flat.py
|- data/
`- output/
```

说明：

- `data/`、`output/`、`.uv-cache/`、`Mysteel_Browser_Data/`、`.browser-profile/` 都属于本地运行产物，不建议纳入版本库同步。
- `.env` 是本地私有配置，不建议提交。

## 主脚本和策略脚本的区别

这是这个项目最重要的结构说明。

### 主脚本：`scripts/mysteel_export_excel.py`

主脚本负责通用流程，也就是不管哪个品类都大体一致的部分，例如：

- 读取 `.env`
- 读取 `queries.toml`
- 解析命令行参数
- 判断工作日
- 启动浏览器
- 自动登录 Mysteel
- 根据 `execution_strategy` 调用策略模块
- 设置日期、搜索、勾选结果、导出 Excel
- 生成 `output/*.json`

可以把主脚本理解成整个项目的“调度器 + 通用执行器”。

### 策略脚本：`scripts/strategies/*.py`

策略脚本负责页面差异适配。虽然几个页面整体流程相似，但字段名称、导航层级、是否需要展开、市场是否是 tab、是否存在额外字段，都可能不同。

每个策略脚本主要负责两件事：

- 定义当前页面的字段映射
- 定义当前页面的导航点击方式

可以把策略脚本理解成“页面适配器”。

### 两者关系

- 主脚本决定“怎么跑”
- 策略脚本决定“这个页面该点哪里、字段叫什么”

## 当前策略说明

### `cold_rolling`

适用于冷轧页面。

特征：

- 一级导航：`钢材`
- 二级导航：`冷轧`
- 产品字段使用 `品名`
- 市场通常需要先按字母分组切换 tab

### `hot_rolling`

适用于热轧页面。

特征：

- 一级导航：`钢材`
- 二级导航：`热轧`
- 产品字段使用 `品种`
- 支持可选扩展字段 `口径`
- `规格 / 材质 / 企业` 可能需要先展开

### `building_steel`

适用于建筑钢材页面。

当前已适配钢筋焊接网。

特征：

- 一级导航：`钢材`
- 二级导航：`建筑钢材`
- 产品字段使用 `品名`
- 支持扩展字段 `网片型号`
- 价格类型通常需要选择，例如 `市场价`

### `stainless_flat`

适用于不锈钢平板页面。

特征：

- 一级导航：`镍铬不锈钢`
- 二级导航：`不锈钢`
- 三级导航：`不锈钢平板`
- 产品字段使用 `品种`
- 分类字段使用 `分类`
- 市场是普通 checkbox 组，不走字母 tab
- `材质 / 规格 / 企业` 需要先展开
- `品牌` 保留，但不是必选
- `交货状态` 保留，但不是必选

## 配置说明

项目使用 `queries.toml` 维护所有查询配置。

当前结构是按策略分组：

- `strategies.<strategy_name>.defaults`：这个策略的默认值
- `strategies.<strategy_name>.queries`：这个策略下的具体查询项

常见字段包括：

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

说明：

- 不是每个策略都会用到所有字段
- 哪些字段真正生效，取决于对应策略脚本中的字段映射
- `brand`、`delivery_state`、`diameter`、`mesh_model` 这类字段通常是扩展项

## `.env` 变量说明

主脚本当前会读取以下环境变量：

- `MYSTEEL_USERNAME`
- `MYSTEEL_PASSWORD`
- `MYSTEEL_DOWNLOAD_DIR`
- `MYSTEEL_CHROME_PATH`
- `MYSTEEL_MANUAL_DATE`
- `MYSTEEL_FORCE_RUN_NON_WORKDAY`
- `MYSTEEL_RANDOM_START_ENABLED`
- `MYSTEEL_RANDOM_START_MAX_MINUTES`

其中：

- `MYSTEEL_USERNAME`、`MYSTEEL_PASSWORD` 必填
- `MYSTEEL_CHROME_PATH` 用于显式指定 Chrome 或 Chromium 可执行文件路径
- 如果 `MYSTEEL_CHROME_PATH` 为空，脚本会回退到内置的常见 Windows 路径自动探测

建议做法：

- 使用 `.env.example` 作为模板创建本地 `.env`
- 不要把真实账号密码提交进版本库

## 运行方式

### 安装依赖

```powershell
uv sync
```

如果你希望把 `uv` 缓存放在项目内，也可以先设置：

```powershell
$env:UV_CACHE_DIR='E:\code\steel_price\.uv-cache'
uv sync
```

### 单独运行某个策略

```powershell
$env:UV_CACHE_DIR='E:\code\steel_price\.uv-cache'
uv run python .\scripts\mysteel_export_excel.py --strategy cold_rolling
```

可用策略值：

- `cold_rolling`
- `hot_rolling`
- `building_steel`
- `stainless_flat`

### 全量运行

```powershell
$env:UV_CACHE_DIR='E:\code\steel_price\.uv-cache'
uv run python .\scripts\mysteel_export_excel.py
```

### 常用参数

```powershell
uv run python .\scripts\mysteel_export_excel.py --help
```

当前主脚本支持的主要参数：

- `--url`
- `--config`
- `--user-data-dir`
- `--download-dir`
- `--output-dir`
- `--target-date`
- `--strategy`
- `--manual-date`
- `--force-run-non-workday`

## 工作日逻辑说明

主脚本会先调用节假日 API 判断是否工作日。

逻辑如下：

- 如果节假日 API 可用，则优先使用 API 返回结果
- 如果 API 不可用，例如 SSL 异常，则自动回退到“按星期判断工作日”
- 周一到周五视为工作日，周六周日视为非工作日

如果你希望周末或节假日也强制运行，可以使用：

```powershell
uv run python .\scripts\mysteel_export_excel.py --force-run-non-workday
```

## 当前文档校对结果

这份 README 已按当前代码行为校对，重点确认过以下内容：

- 已支持的策略列表与 `scripts/strategies/registry.py` 一致
- `.env` 变量列表与主脚本读取逻辑一致
- `MYSTEEL_CHROME_PATH` 已在主脚本中生效
- `stainless_flat` 的导航层级和字段说明与当前实现一致
- 运行命令与当前 `uv + python` 执行方式一致

## 排错建议

### 1. Chrome 路径错误

如果看到：

```text
Configured Chrome binary does not exist
```

说明 `.env` 里的 `MYSTEEL_CHROME_PATH` 不存在或路径写错了。

先用 PowerShell 查实际 Chrome 路径，再更新 `.env`。

### 2. 节假日 API SSL 报错

如果看到类似：

```text
holiday API unavailable ... fallback weekday rule used
```

说明节假日接口调用失败，但脚本已经自动切换到“按星期判断工作日”逻辑。

这通常不会阻塞脚本继续运行。

### 3. 页面能打开，但找不到筛选项

优先检查：

- 当前 `execution_strategy` 是否正确
- Mysteel 页面标签是否变了
- 对应策略脚本字段映射是否还匹配当前页面

### 4. 脚本跑通，但没有数据

优先检查：

- 是否还没到 Mysteel 当次更新时间
- 日期范围是否正确
- 查询条件是否过窄

### 5. 新增品类怎么扩展

建议按这个顺序做：

1. 在 `queries.toml` 中新增一个策略分组
2. 在 `scripts/strategies/` 下新增一个策略脚本
3. 在 `registry.py` 中注册这个策略
4. 先用 `--strategy <新策略名>` 单独调通
5. 再做全量运行验证
