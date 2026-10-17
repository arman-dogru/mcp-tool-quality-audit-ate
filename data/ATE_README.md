---
pretty_name: ATE
language:
- multilingual
task_categories:
- other
tags:
- tabular
- mcp
- model-context-protocol
- onet
- occupational-tasks
- agents
- tools
size_categories:
- 100K<n<1M
configs:
- config_name: onet_matches
  default: true
  data_files:
  - split: train
    path: data/onet_matches/train-*.parquet
- config_name: servers
  data_files:
  - split: train
    path: data/servers/train-*.parquet
- config_name: tools
  data_files:
  - split: train
    path: data/tools/train-*.parquet
- config_name: tasks
  data_files:
  - split: train
    path: data/tasks/train-*.parquet
- config_name: clusters
  data_files:
  - split: train
    path: data/clusters/train-*.parquet
- config_name: cluster_tools
  data_files:
  - split: train
    path: data/cluster_tools/train-*.parquet
- config_name: cluster_taxonomy
  data_files:
  - split: train
    path: data/cluster_taxonomy/train-*.parquet
- config_name: occupation_results
  data_files:
  - split: train
    path: data/occupation_results/train-*.parquet
- config_name: usage_stats
  data_files:
  - split: train
    path: data/usage_stats/train-*.parquet
- config_name: coverage_by_column
  data_files:
  - split: train
    path: data/coverage_by_column/train-*.parquet
---

# Agentic Task Ecosystem (ATE)

**ATE** is a dataset of publicly listed Model Context Protocol (MCP) servers and their tools, linked to O*NET occupational tasks, with summaries of how those tools cluster into recognizable kinds of work.

See the accompanying blog post here: https://cohere.com/blog/automations-early-footprint

## Loading the data

Each original table is a Hugging Face **subset** (config). There is no train/validation/test split; the Hub `train` split is the full table.

```python
from datasets import load_dataset

servers = load_dataset("CohereLabs/ATE", "servers", split="train")
tools = load_dataset("CohereLabs/ATE", "tools", split="train")
tasks = load_dataset("CohereLabs/ATE", "tasks", split="train")
onet_matches = load_dataset("CohereLabs/ATE", "onet_matches", split="train")
```

Column definitions: [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md). Package integrity hashes: [`MANIFEST.json`](MANIFEST.json). Changelog: [`CHANGELOG.md`](CHANGELOG.md).

Parquet is the format published here. The original package also shipped CSV (for browsing) and JSONL copies of `servers` and `tools` with the same columns.

## What is an MCP server / tool?

An **MCP server** is a software package that exposes capabilities to AI agents through the Model Context Protocol. A **tool** is one named capability (for example, “list issues” or “run a query”) described in the server’s documentation. Listings in this package were collected from public registries: MCP World, MCP Store, Glama, Smithery, the official MCP registry, mcp.so, and mcp-repository.

## Snapshot dates

Listings and `usage_stats` are **point-in-time snapshots**, not live counts. Collection windows by registry (`scraped_at`):

| Registry | Snapshot window (UTC) |
|----------|------------------------|
| official_registry | 2026-05-07 |
| glama | 2026-05-07 |
| mcp_store | 2026-05-07 |
| mcp_world | 2026-05-07 |
| mcp_repository | 2026-05-07 |
| smithery | 2026-05-07 |
| mcp_so | 2026-05-08 |

## What is O*NET?

O*NET is the U.S. Department of Labor’s occupation and task database. Task statements, occupation codes, and titles in the `tasks` table come from the O*NET 29.2 Database. We mark which tasks are **software-performable** (software could in principle carry out the cognitive, digitizable core) and match tools to those tasks.

## What a match means

Each analysis-set tool is paired with its nearest software-performable O*NET task (by text embedding), then judged for whether the tool genuinely performs that task. About **2%** of tools receive a good match (18,058 of 694,411 rank-1 matches). Matching therefore covers a thin slice of the tool supply — absence of a match is common and expected.

## Specialization (SFI)

`sfi_score` is the Specialization (SFI) measure from Autor & Thompson (2025), “Expertise” — a word-frequency specialization formula, not a score we invented. We also ship `sfi_percentile_within_occupation` (0–100) so readers can see how specialized a task is **relative to other tasks in the same occupation**. Within-occupation percentiles are the preferred display when comparing matched vs remaining work.

## Three work types

Occupational tool clusters carry a three-way work-type classification:

| Work type | Meaning | Example |
|-----------|---------|---------|
| **subatomic** | A narrow slice of an existing O*NET task | Screen capture operations |
| **composite** | A bundle of several existing tasks into one workflow | Meeting transcript management |
| **new** | Work that does not sit inside existing O*NET tasks | Tools built primarily for coordinating AI agents |

New clusters also carry `new_kind` (`working_with_agents`, `building_automation`, or `other`). Themes within subatomic and composite work are named from member clusters; heterogeneous residuals are labeled explicitly as Other.

## EPOCH ratings

Cluster taxonomy includes EPOCH capability ratings (Loaiza & Rigobon 2024, “The EPOCH of AI: Human-Machine Complementarities at Work”): empathy, presence, opinion, creativity, and hope. Each dimension is rated **0–4** for how central that human capability is to the described work.

## Tables

| Subset | One row is | Rows |
|--------|------------|-----:|
| `servers` | One MCP server listing | 123,069 |
| `tools` | One extracted tool row | 696,291 |
| `tasks` | One O*NET task statement | 18,796 |
| `onet_matches` | One rank-1 tool→task match | 694,411 |
| `clusters` | One tool cluster | 1,712 |
| `cluster_tools` | One tool→cluster assignment | 694,411 |
| `cluster_taxonomy` | One occupational cluster with work type / theme / EPOCH | 1,139 |
| `occupation_results` | One occupation summary | 895 |
| `usage_stats` | One server’s adoption signals | 123,069 |
| `coverage_by_column` | One table/column non-null coverage statistic | 153 |

Primary keys: `mcp_id`, `tool_id` = `{mcp_id}:{tool_name}`, `cluster_id`, `task_id`.

## Known limitations

- Coverage is **publicly listed servers only**. That includes vendor-published enterprise servers that appear in public registries, but not bespoke internal deployments. This is a public-listing vs private-deployment distinction, not a three-way public/enterprise split.
- Tools are extracted by parsing server README / documentation text; incomplete docs yield missing tools.
- Occupation coverage shares can hit 100% when an occupation has very few software-performable tasks; published coverage figures typically keep occupations with at least three such tasks.

## Data sources and attribution

Listing text (names, descriptions, categories) is authored by the server developers and may include contact details they chose to publish. Reuse of verbatim description text is governed by the upstream repositories’ own licenses.

Task data comes from the O*NET 29.2 Database by the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA), used under the CC BY 4.0 license. O*NET® is a trademark of USDOL/ETA. Derived fields in this package (for example `software_performable` and SFI scores) are our own and are not endorsed by USDOL/ETA.

Methods provenance for matching, clustering, and expertise calculations is documented in the accompanying technical report.

The dataset license for this Hub repository has not been set yet. O*NET task text remains CC BY 4.0 regardless of the package license.

## Suggested citation


```bibtex
@online{agentictaskecosys2026,
  author = {Zanele Munyikwa, Campbell Lund, Thomas Euyang, Aidan Peppin, and Marzieh Fadaee},
  title = {Automation's Early Footprint: Where AI Agents Are (and Aren't) Being Built,
  year = 2026,
  url = {https://cohere.com/blog/automations-early-footprint}
}
```

Full paper coming soon...
