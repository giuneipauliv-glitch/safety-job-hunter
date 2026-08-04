# ⛑️ 安全工程岗位雷达

面向安全工程行业的每日招聘信息聚合工具。每天自动抓取**智联招聘**（社招主力）与**国聘·国资央企招聘平台**（国企/央企，校招+社招）的「安全工程师 / 注册安全工程师 / EHS / HSE / 安全评价师 / 消防 / 危化品」等 22 个关键词、全国范围岗位，解析学历、地点、经验、待遇、要求与投递链接，区分**校招/社招/实习**，生成可筛选的美观网页，并附带注安等证书的报考指南。

## 功能特性

- 📡 每日自动更新（GitHub Actions 定时任务，免费、无人值守）
- 🏛️ 多数据源：智联主站（社招）+ 国聘（国企央企校招/社招），后续可扩展企业官网、高校就业网等
- 🎓 校招/社招/实习区分：一键筛选校招岗位，校招优先展示
- 🔍 多维度筛选：搜索、城市、学历、经验、薪资、排序
- 🏷️ 智能标签：今日新增 / 需证书 / 外派岗 / 国企 一键过滤
- 🎓 内置报考指南：中级/初级注安、消防设施操作员等证书信息
- 📱 响应式设计，手机浏览器直接可用
- 💾 数据全量沉淀 `data/jobs.json`，可随时导出分析

## 目录结构

```
safety-job-hunter/
├── config.py                  # 关键词、页数、证书词表等配置
├── run.py                     # 主流程：抓取→去重→生成网页
├── run_local.ps1 / .bat       # 本地手动/计划任务脚本
├── build_site.py              # 网页生成器
├── guide.py                   # 报考指南内容（可自行维护）
├── src/
│   ├── fetch.py               # 抓取层（智联主站：Playwright / Chrome 双后端）
│   ├── fetch_iguopin.py       # 国聘 API 抓取器（API直连 + 浏览器兑底）
│   ├── parse.py               # HTML 解析（纯标准库，零依赖）
│   └── store.py               # 去重与增量合并
├── site/template.html         # 网页模板（深色主题）
├── data/jobs.json             # 岗位数据（自动生成）
├── docs/index.html            # GitHub Pages 站点（自动生成）
├── tests/                     # 解析器单元测试
└── .github/workflows/update.yml  # 每日定时工作流
```

## 快速开始（本地）

要求：Python 3.10+（或使用项目旁便携版），Windows 需有 Chrome/Edge。

```powershell
# 方式一：Chrome 兜底后端（推荐本地，无需装任何包）
powershell -ExecutionPolicy Bypass -File run_local.ps1

# 方式二：Playwright 后端（更稳，需先装）
pip install playwright
python -m playwright install chromium
python run.py --backend playwright
```

运行后：
- `data/jobs.json` 更新
- `docs/index.html` 重新生成，双击即可本地预览

## 部署到 GitHub（每日自动更新 + 免费托管）

1. 在 GitHub 新建仓库（Public 即可，Actions 免费额度足够），例如 `safety-job-hunter`
2. 把本项目文件推上去：
   ```bash
   git init
   git add .
   git commit -m "init"
   git branch -M main
   git remote add origin https://github.com/<你的用户名>/safety-job-hunter.git
   git push -u origin main
   ```
3. 仓库 Settings → **Pages** → Source 选 `Deploy from a branch` → 分支 `main` → 目录 `/docs` → Save
4. 等 1-2 分钟，你的站点地址：`https://<用户名>.github.io/safety-job-hunter/`
5. Actions 每天北京时间 11:00 自动抓取更新。可在 **Actions** 页面手动 `Run workflow` 立即测试一次

> ⚠️ 云端（GitHub 数据中心 IP）抓取智联可能被反爬拦截。工作流已内置失败自动开 Issue 通知，届时在本地电脑跑一次 `run_local.ps1` 补上即可（家庭宽带 IP 成功率远高于云端）。

## Windows 计划任务（本地兜底自动更新）

想完全不受云端反爬影响，可配置电脑定时运行本地脚本：

1. 打开「任务计划程序」→「创建任务」
2. 触发器：每天 12:00（选电脑通常开着的时段）
3. 操作：启动程序 → 程序 `powershell.exe`，参数：
   ```
   -ExecutionPolicy Bypass -File "E:\work space\safety-job-hunter\run_local.ps1"
   ```
4. 条件：取消勾选「只有在计算机使用交流电源时才启动」（笔记本用户）

运行成功后数据会推到 GitHub（需先在仓库配置好凭据），网页自动更新。

## 自定义

- **关键词**：编辑 `config.py` 的 `KEYWORDS`
- **抓取页数**：`PAGES_PER_KEYWORD`（1 页约 60 条）
- **数据源开关**：`config.py` 的 `SOURCES`（zhaopin / iguopin / zhaopin_xy）
- **校招识别词**：`CAMPUS_KEYWORDS`（标题含这些词标记为校招）
- **证书高亮词**：`CERT_KEYWORDS`
- **报考指南**：编辑 `guide.py`，重新运行 `python build_site.py`
- **抓取时刻**：改 `.github/workflows/update.yml` 的 `cron`（当前北京时间 11:00 = UTC 03:00）

## 扩展新数据源

在 `src/` 下新建抓取器（如企业官网、高校就业网），返回统一 schema（`job_id` 带源前缀避免冲突，字段见 `src/fetch_iguopin.py` 的 `make_job`），然后在 `run.py` 中追加调度即可。`job_id` 前缀示例：`zhaopin_` / `gp_` / `xy_`。

## 常见问题

| 问题 | 处理 |
|---|---|
| 抓取全部被拦（exit 2 / 开 Issue） | 本地跑 `run_local.ps1`；或稍等重试 |
| 云端偶尔成功但数据少 | 数据中心 IP 限流，属正常，本地兜底即可 |
| 网页空白 | 确认 `docs/index.html` 非空、`data/jobs.json` 存在 |
| 想改界面 | 编辑 `site/template.html` 后重跑 `build_site.py` |

## 免责声明

数据来自智联招聘公开搜索页面，仅供个人求职筛选参考。投递前请至招聘方官方页面核实最新状态。请合理控制抓取频率，尊重目标网站服务条款。
