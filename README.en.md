# WorkBuddy Agent File Parser Downloader

> Parse WorkBuddy expert marketplace metadata and download expert / expert-team `.tar.gz` agent bundles by category.

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Stars](https://img.shields.io/github/stars/mayuhaos/workbuddy-agent-file-parser-downloader?style=social)](https://github.com/mayuhaos/workbuddy-agent-file-parser-downloader/stargazers)

English | [简体中文](README.md)

## Overview

`workbuddy-agent-file-parser-downloader` is a small automation tool for archiving WorkBuddy expert and expert-team agent bundles.

It fetches the public `expert_center.json` manifest, parses each expert's category, Chinese / English names, and `plugin` identifier, downloads the corresponding `.tar.gz` bundle, and generates a structured Excel report with a summary dashboard.

Use it to:

- Archive WorkBuddy expert and expert-team agent files in bulk
- Replace repetitive manual click-to-download workflows
- Generate category-level statistics and download status reports
- Prepare a reusable core for a future GUI desktop app

## Features

- Fetch the WorkBuddy expert marketplace manifest
- Split entries into `专家` and `专家团`
- Rename `.tar.gz` files with a consistent category-based format
- Write bundles into two flat output folders
- Use gentle defaults: single-threaded download and 1-2 seconds between remote bundle requests
- Skip existing files by default to reduce duplicate requests
- Continue on failures and write failed entries into a retry queue
- Generate an Excel report with dashboard and detail sheets
- Include Windows one-click scripts

## Output Structure

```text
outputs/
├─ expert_center.json
├─ sync.log
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

## Quick Start

### Windows One-Click Scripts

Full sync:

```text
run-full.bat
```

Test only 3 bundles:

```text
run-test-3.bat
```

Notes:

- `run-full.bat` downloads all experts and expert teams to `outputs/`
- `run-test-3.bat` downloads `2 experts + 1 expert team` to `outputs-test-3/`
- Both scripts create `.venv` and install dependencies automatically

### Command Line

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -e .
python -m workbuddy_agent_file_parser_downloader sync
```

macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m workbuddy_agent_file_parser_downloader sync
```

## Common Options

```powershell
python -m workbuddy_agent_file_parser_downloader sync `
  --out-dir outputs `
  --concurrency 1 `
  --delay-min 1 `
  --delay-max 2 `
  --retries 3
```

Small sample run:

```powershell
python -m workbuddy_agent_file_parser_downloader sync --out-dir outputs-test-3 --sample-agents 2 --sample-teams 1
```

Reuse an existing Excel template for column widths:

```powershell
python -m workbuddy_agent_file_parser_downloader sync `
  --xlsx-template "C:\Users\EDY\Documents\workbuddy智能体获取\专家专家团压缩包清单.xlsx"
```

## Excel Report

The tool writes:

```text
outputs/专家专家团压缩包清单.xlsx
```

Sheets:

| Sheet | Description |
|---|---|
| `统计看板` | Total count, success count, failures, expert/team counts, category statistics |
| `专家` | Expert details, filename, category, Chinese name, plugin, status, URL |
| `专家团` | Expert-team details, filename, category, Chinese name, plugin, status, URL |
| `失败重跑队列` | Failed entries, error messages, retry count |

## Logs

Each run writes a detailed log:

```text
outputs/sync.log
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
python -m workbuddy_agent_file_parser_downloader sync --verify-existing
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
- Display name: `WorkBuddy Agent File Parser Downloader`
- Description: `解析 WorkBuddy 专家市场清单，并批量下载专家/专家团智能体压缩包。`
- Language: Python
- License: MIT License

## Disclaimer

This project is intended for learning, research, and personal archival automation. Please respect the target service's terms of use, access policies, and applicable laws. Keep the default low-frequency request strategy to avoid unnecessary load on remote services.

## License

[MIT](LICENSE)
