# WorkBuddy 智能体文件解析下载

> 从 WorkBuddy 专家市场接口解析专家/专家团清单，并按分类批量下载对应的 `.tar.gz` 智能体文件。

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Stars](https://img.shields.io/github/stars/mayuhaos/workbuddy-agent-file-parser-downloader?style=social)](https://github.com/mayuhaos/workbuddy-agent-file-parser-downloader/stargazers)

[English](README.en.md) | 简体中文

## 简介

`workbuddy-agent-file-parser-downloader` 是一个面向 WorkBuddy 专家/专家团资源归档的自动化工具。

![WorkBuddy 智能体文件解析下载](https://raw.githubusercontent.com/mayuhaos/blog-images/notepix/assets/20260612T050146773Z.png)

它会读取 WorkBuddy 专家市场清单，解析每个专家或专家团的分类、中文名、英文名、`plugin` 标识，并按照统一规则下载对应的 `.tar.gz` 包，最后生成一份带统计看板的 Excel 清单。

适合用于：

- 批量归档 WorkBuddy 专家/专家团智能体文件
- 替代手动点击下载流程
- 生成专家分类统计、下载结果和失败重跑清单
- 后续扩展为 GUI 桌面工具

## 功能特性

- 自动获取 WorkBuddy 专家市场 JSON 清单
- 自动区分 `专家` 和 `专家团`
- 按分类和 `plugin` 统一重命名 `.tar.gz`
- 输出两个平铺目录，无额外层级
- 默认单线程下载，每次远程请求间隔 1-2 秒
- 已存在文件默认跳过，减少重复请求
- 下载失败不中断，自动写入失败重跑队列
- 生成 Excel 清单，包含统计看板和明细表

## 输出结构

```text
outputs/
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

命名规则：

```text
专家-{分类中文名}-{plugin}.tar.gz
专家团-{分类中文名}-{plugin}.tar.gz
```

## 快速开始

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -e .
python -m workbuddy_agent_file_parser_downloader run
```

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m workbuddy_agent_file_parser_downloader run
```

## 常用参数

```powershell
python -m workbuddy_agent_file_parser_downloader run `
  --out-dir outputs `
  --concurrency 1 `
  --delay-min 1 `
  --delay-max 2 `
  --retries 3
```

测试少量数据：

```powershell
python -m workbuddy_agent_file_parser_downloader run --out-dir outputs-test-3 --sample-agents 2 --sample-teams 1
```

复用已有 Excel 模板的列宽：

```powershell
python -m workbuddy_agent_file_parser_downloader run `
  --xlsx-template "templates/expert_bundle_template.xlsx"
```

## Excel 清单

运行后会生成：

```text
outputs/专家专家团压缩包清单.xlsx
```

包含 4 个 sheet：

| Sheet | 说明 |
|---|---|
| `统计看板` | 总数、成功数、失败数、专家/专家团数量、分类统计 |
| `专家` | 专家明细、文件名、分类、中文名、plugin、下载状态、URL |
| `专家团` | 专家团明细、文件名、分类、中文名、plugin、下载状态、URL |
| `失败重跑队列` | 下载失败项、错误信息、重试次数 |

## 日志

每次运行都会生成详细日志：

```text
outputs/run.log
```

日志会记录：

- 下载时间
- 专家类型：专家 / 专家团
- 分类
- 中文展示名、英文展示名
- 中文职业名、英文职业名
- `plugin`
- 输出文件名和本地路径
- 下载 URL
- 错误信息

## 请求频率

默认下载策略偏保守：

```text
--concurrency 1
--delay-min 1
--delay-max 2
```

也就是说，远程 bundle 请求会尽量保持约 1-2 秒一次，避免高频请求。已存在文件默认直接跳过，不额外请求远端；如果需要校验远端大小，可以使用：

```powershell
python -m workbuddy_agent_file_parser_downloader run --verify-existing
```

## 默认接口

Manifest：

```text
https://acc-1258344699.cos.accelerate.myqcloud.com/workbuddy/expert-marketplace/expert_center.json
```

Bundle：

```text
https://acc-1258344699.cos.accelerate.myqcloud.com/workbuddy/expert-marketplace/bundles/{plugin}.tar.gz
```

## 推荐仓库信息

- 仓库名：`workbuddy-agent-file-parser-downloader`
- 仓库链接：`https://github.com/mayuhaos/workbuddy-agent-file-parser-downloader`
- 中文名：`WorkBuddy 智能体文件解析下载`
- 描述：`解析 WorkBuddy 专家市场清单，并批量下载专家/专家团智能体压缩包。`
- 语言：Python
- 开源协议：MIT License

## 免责声明

本项目仅用于学习、研究和个人数据归档自动化。请遵守目标服务的使用条款、robots/访问策略及适用法律法规。建议保持默认低频请求策略，避免对远程服务造成压力。

## License

[MIT](LICENSE)
