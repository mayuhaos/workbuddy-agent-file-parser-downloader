# WorkBuddy Agent File Parser Downloader

> Parse WorkBuddy expert marketplace metadata and download expert / expert-team `.tar.gz` agent bundles by category.

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Stars](https://img.shields.io/github/stars/mayuhaos/workbuddy-agent-file-parser-downloader?style=social)](https://github.com/mayuhaos/workbuddy-agent-file-parser-downloader/stargazers)

English | [简体中文](README.md)

## Overview

`workbuddy-agent-file-parser-downloader` is a small automation tool for archiving WorkBuddy expert and expert-team agent bundles. This avoids the need for manual "summoning" clicks and accounts for potential errors in machine vision recognition. The project supports both command-line workflows and a desktop GUI.

![WorkBuddy Agent File Parser Downloader](https://raw.githubusercontent.com/mayuhaos/blog-images/notepix/assets/20260612T050146773Z.png)

It reads the WorkBuddy expert marketplace manifest, parses each expert's category, Chinese / English names, and `plugin` identifier, downloads the corresponding `.tar.gz` bundle, and generates a structured Excel report with a summary dashboard.

Use it to:

- Archive WorkBuddy expert and expert-team agent files in bulk
- Replace repetitive manual click-to-download workflows
- Generate category-level statistics and download status reports

## Features

- Fetch the WorkBuddy expert marketplace manifest
- Split entries into `专家` and `专家团`
- Rename `.tar.gz` files with a consistent category-based format
- Write bundles into two flat output folders
- Use gentle defaults: single-threaded download and 1-2 seconds between remote bundle requests
- Skip existing files by default to reduce duplicate requests
- Continue on failures and write failed entries into a retry queue
- Generate an Excel report with dashboard and detail sheets
- Provide a desktop GUI for choosing an output folder, viewing live logs, and tracking download progress

## Output Structure

```text
agent-outputs-2026-04-04-131211/
├─ expert_center.json
├─ run.log
├─ 专家/
│  ├─ 专家-内容创作-content-creator.tar.gz
│  └─ 专家-项目质量-studio-operations-manager.tar.gz
├─ 专家团/
│  ├─ 专家团-行业顾问-fbs-iplib.tar.gz
│  └─ 专家团-技术工程-cloud-ops-team.tar.gz
└─ 专家专家团压缩包清单.xlsx
```

Filename format:

```text
专家-{Chinese category name}-{plugin}.tar.gz
专家团-{Chinese category name}-{plugin}.tar.gz
```

![xlsx导出](https://raw.githubusercontent.com/mayuhaos/blog-images/notepix/assets/20260612T061616783Z.png)

![文件汇总](https://raw.githubusercontent.com/mayuhaos/blog-images/notepix/assets/20260612T061752448Z.png)

## Repository Structure

```text
workbuddy-agent-file-parser-downloader/
├─ src/
│  ├─ README.md
│  └─ workbuddy_agent_file_parser_downloader/
│     ├─ cli.py              # CLI entrypoint and options
│     ├─ core.py             # Shared CLI/GUI workflow
│     ├─ gui.py              # Desktop GUI
│     ├─ gui_entry.py        # GUI application entrypoint
│     ├─ manifest.py         # Manifest fetching and parsing
│     ├─ downloader.py       # Bundle downloading and request throttling
│     ├─ excel_report.py     # Excel dashboard and report generation
│     └─ models.py           # Data models and filename rules
├─ scripts/                  # Helper scripts
├─ README.md                 # Chinese README
├─ README.en.md              # English README
├─ pyproject.toml            # Python project metadata
├─ LICENSE                   # MIT License
└─ .gitignore
```

## Quick Start

### Windows

```powershell
cd workbuddy-agent-file-parser-downloader
py -3 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .

# Test 3 bundles
python -m workbuddy_agent_file_parser_downloader run --out-dir outputs-test-3 --sample-agents 2 --sample-teams 1

# Full run
python -m workbuddy_agent_file_parser_downloader run
```

If the `python` command exits without output on Windows, use `py -3` to create the virtual environment. Windows may point `python` to the Microsoft Store app execution alias.

### macOS / Linux

```bash
cd workbuddy-agent-file-parser-downloader
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .

# Test 3 bundles
python -m workbuddy_agent_file_parser_downloader run --out-dir outputs-test-3 --sample-agents 2 --sample-teams 1

# Full run
python -m workbuddy_agent_file_parser_downloader run
```

## Common Options

Without `--out-dir`, the tool creates an `agent-outputs-YYYY-MM-DD-HHMMSS` directory automatically.

```powershell
python -m workbuddy_agent_file_parser_downloader run `
  --concurrency 1 `
  --delay-min 1 `
  --delay-max 2 `
  --retries 3
```

Small sample run:

```powershell
python -m workbuddy_agent_file_parser_downloader run --out-dir outputs-test-3 --sample-agents 2 --sample-teams 1
```

Reuse an existing Excel template for column widths:

```powershell
python -m workbuddy_agent_file_parser_downloader run `
  --xlsx-template "templates/expert_bundle_template.xlsx"
```

## Excel Report

The tool writes:

```text
agent-outputs-2026-04-04-131211/专家专家团压缩包清单.xlsx
```

Up to 4 sheets:

| Sheet | Description |
|---|---|
| `统计看板` | Total count, success count, failures, expert/team counts, category statistics |
| `专家` | Expert details, filename, category, Chinese name, plugin, file size; error message appears only when needed |
| `专家团` | Expert-team details, filename, category, Chinese name, plugin, file size; error message appears only when needed |
| `失败重跑队列` | Generated only when failures exist; includes failed entries, source URL, error message, and retry count |

## Logs

Each run writes a detailed log:

```text
agent-outputs-2026-04-04-131211/run.log
```

The log records timestamp, expert type, category, Chinese / English display names, Chinese / English profession names, `plugin`, output filename, local path, URL, and errors.

## Request Rate

The default strategy is intentionally gentle:

```text
--concurrency 1
--delay-min 1
--delay-max 2
```

Remote bundle requests are kept roughly one request every 1-2 seconds. Existing files are skipped without a remote request by default. To verify remote file size before skipping, use:

```powershell
python -m workbuddy_agent_file_parser_downloader run --verify-existing
```

## Default Endpoints

Manifest:

```text
https://acc-1258344699.cos.accelerate.myqcloud.com/workbuddy/expert-marketplace/expert_center.json
```

Bundle:

```text
https://acc-1258344699.cos.accelerate.myqcloud.com/workbuddy/expert-marketplace/bundles/{plugin}.tar.gz
```

## Recommended Repository Metadata

- Repository name: `workbuddy-agent-file-parser-downloader`
- Repository URL: `https://github.com/mayuhaos/workbuddy-agent-file-parser-downloader`
- Display name: `WorkBuddy Agent File Parser Downloader`
- Description: `解析 WorkBuddy 专家市场清单，并批量下载专家/专家团智能体压缩包。`
- Language: Python
- License: MIT License

## Disclaimer

This project is intended for learning, research, and personal archival automation. Please respect the target service's terms of use, access policies, and applicable laws. Keep the default low-frequency request strategy to avoid unnecessary load on remote services.

## License

[MIT](LICENSE)

## Star History

<a href="https://www.star-history.com/?repos=mayuhaos%2Fworkbuddy-agent-file-parser-downloader&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=mayuhaos/workbuddy-agent-file-parser-downloader&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=mayuhaos/workbuddy-agent-file-parser-downloader&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=mayuhaos/workbuddy-agent-file-parser-downloader&type=date&legend=top-left" />
 </picture>
</a>

<div align="center">

### Thanks for using WorkBuddy Agent File Parser Downloader

If this project helps you, ⭐️  a star would mean a lot. Thank you!

</div>
