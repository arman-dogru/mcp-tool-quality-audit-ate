# ATE — Data Dictionary

Column definitions for the public package. Methods details are in the accompanying technical report; this dictionary explains meaning, not pipeline history.

## `servers`

One row per MCP server listing. Primary key: `mcp_id`.

| Column | Type | Description | Source | Non-null % |
|--------|------|-------------|--------|------------|
| `mcp_id` | object | Stable 16-character hex identifier for the server listing. | this package | 100.0% |
| `name` | object | Server display name from the registry listing. | this package | 100.0% |
| `description` | object | Registry or repository description text for the server. | this package | 96.5% |
| `github_url` | object | Resolved GitHub repository URL when available. | this package | 96.5% |
| `source` | object | Registry or directory the listing was collected from. | this package | 100.0% |
| `scraped_at` | object | UTC timestamp when this listing was collected. | this package | 100.0% |
| `listing_created_at` | object | Creation timestamp supplied by the registry, if any. | this package | 79.5% |
| `listing_published_at` | object | Publication timestamp supplied by the registry, if any. | this package | 3.2% |
| `github_repo_created_at` | object | GitHub repository creation time when resolved. | this package | 90.2% |
| `created_at_best` | object | Best available creation timestamp across listing and repo sources. | this package | 97.2% |
| `created_at_best_source` | object | Which field supplied `created_at_best`. | this package | 97.2% |
| `n_tools` | int64 | Count of extracted tools attributed to this server. | this package | 100.0% |
| `has_tools` | bool | 1 if at least one tool was extracted for this server. | this package | 100.0% |
| `category` | object | High-level category for the server. | this package | 44.3% |
| `stars` | float64 | GitHub stargazer count when available. | this package | 75.9% |
| `categories_raw` | object | Raw category tags from the registry listing. | this package | 78.6% |
| `github_api_language` | object | Primary language reported by the GitHub API. | this package | 84.2% |
| `github_archived` | object | Whether the GitHub repository is archived. | this package | 90.1% |
| `github_forks_count` | float64 | GitHub fork count. | this package | 90.2% |
| `github_full_name` | object | GitHub owner/repo full name. | this package | 96.5% |
| `github_open_issues` | float64 | Open issues count on GitHub. | this package | 90.1% |
| `github_owner` | object | GitHub owner login. | this package | 96.5% |
| `github_pushed_at` | object | Last push timestamp on GitHub. | this package | 90.1% |
| `github_repo` | object | GitHub repository name. | this package | 96.5% |
| `github_stargazers_count` | float64 | GitHub stargazer count (API field). | this package | 90.2% |
| `github_watchers` | float64 | GitHub watchers count. | this package | 90.1% |
| `npm_downloads_month` | float64 | npm monthly downloads when a package is linked. | this package | 6.2% |
| `npm_package` | object | Linked npm package name, if any. | this package | 34.1% |
| `pypi_downloads_month` | float64 | PyPI monthly downloads when a package is linked. | this package | 3.9% |
| `pypi_package` | object | Linked PyPI package name, if any. | this package | 21.5% |
| `repo_missing` | object | 1 if a GitHub repository could not be resolved. | this package | 96.5% |
| `server_language` | object | Inferred human-readable implementation language. | this package | 100.0% |
| `server_language_code` | object | Normalized language code. | this package | 100.0% |
| `smithery_installs` | float64 | Smithery install count when available. | this package | 3.6% |
| `source_is_glama` | int64 | 1 if the listing was observed on Glama. | this package | 100.0% |
| `source_is_mcp_repository` | int64 | 1 if observed on mcp-repository. | this package | 100.0% |
| `source_is_mcp_so` | int64 | 1 if observed on mcp.so. | this package | 100.0% |
| `source_is_mcp_store` | int64 | 1 if observed on MCP Store. | this package | 100.0% |
| `source_is_mcp_world` | int64 | 1 if observed on MCP World. | this package | 100.0% |
| `source_is_official_registry` | int64 | 1 if observed on the official registry. | this package | 100.0% |
| `source_is_smithery` | int64 | 1 if observed on Smithery. | this package | 100.0% |
| `repo_resolved_at_enrichment` | int64 | 1 if a repo was resolved during enrichment. | this package | 100.0% |

## `tools`

One row per extracted tool. Primary key: `tool_row_id`.

| Column | Type | Description | Source | Non-null % |
|--------|------|-------------|--------|------------|
| `tool_row_id` | int64 | Row primary key for an extracted tool record. | this package | 100.0% |
| `tool_id` | object | Logical tool key `{mcp_id}:{tool_name}`. | this package | 100.0% |
| `mcp_id` | object | Server identifier this tool belongs to. | this package | 100.0% |
| `server_name` | object | Server name at extraction time. | this package | 100.0% |
| `tool_name` | object | Tool name parsed from the server README or docs. | this package | 100.0% |
| `description` | object | Tool description text extracted from documentation. | this package | 92.9% |
| `in_analysis_set` | int64 | 1 if the tool entered embedding and matching after deduplication. | this package | 100.0% |
| `excluded_reason` | object | Why a row is outside the analysis set, if excluded. | this package | 0.3% |
| `cluster_id` | Int64 | Assigned cluster id (−1 for HDBSCAN noise / unassigned). | this package | 100.0% |
| `in_clustering` | int64 | 1 if the tool was included in the clustering input. | this package | 100.0% |
| `is_hdbscan_noise` | int64 | 1 if HDBSCAN labeled the tool as noise. | this package | 100.0% |

## `tasks`

Task statements, occupation codes, and titles come from the O*NET 29.2 Database (U.S. Department of Labor / National Center for O*NET Development).

| Column | Type | Description | Source | Non-null % |
|--------|------|-------------|--------|------------|
| `task_id` | object | From the O*NET 29.2 Database. | O*NET 29.2 | 100.0% |
| `task_text` | object | From the O*NET 29.2 Database. | O*NET 29.2 | 100.0% |
| `soc_code` | object | From the O*NET 29.2 Database. | O*NET 29.2 | 100.0% |
| `occupation_title` | object | From the O*NET 29.2 Database. | O*NET 29.2 | 100.0% |
| `software_performable` | bool | True if software could in principle perform the cognitive, digitizable core of the task. | this package | 100.0% |
| `sfi_score` | float64 | Specialization (SFI) score per Autor & Thompson (2025), 'Expertise'. | this package | 99.9% |
| `sfi_percentile_within_occupation` | float64 | Within-occupation percentile of `sfi_score` (0–100; higher = more specialized relative to the occupation's other tasks). | this package | 99.9% |

## `onet_matches`

One row per rank-1 tool–task match. Primary key: `tool_id`.

| Column | Type | Description | Source | Non-null % |
|--------|------|-------------|--------|------------|
| `mcp_id` | object | Server identifier for the matched tool. | this package | 100.0% |
| `tool_id` | object | Matched tool key `{mcp_id}:{tool_name}`. | this package | 100.0% |
| `server_name` | object | Server name of the matched tool. | this package | 100.0% |
| `tool_name` | object | Name of the matched tool. | this package | 100.0% |
| `tool_description` | object | Description text of the matched tool. | this package | 93.0% |
| `task_id` | object | From the O*NET 29.2 Database. | this package | 100.0% |
| `task_text` | object | From the O*NET 29.2 Database. | this package | 100.0% |
| `occupation_title` | object | From the O*NET 29.2 Database. | this package | 100.0% |
| `soc_code` | object | From the O*NET 29.2 Database. | this package | 100.0% |
| `rank` | int64 | Retrieval rank of the task for this tool (1 = nearest). | this package | 100.0% |
| `cosine_similarity` | float64 | Embedding cosine similarity between tool and task text. | this package | 100.0% |
| `match_quality` | object | Judge label for whether the tool genuinely performs the task (good/partial/bad). | this package | 100.0% |
| `match_notes` | object | Short free-text justification from the match judge. | this package | 100.0% |
| `sfi_score` | float64 | Specialization (SFI) score of the matched task (Autor & Thompson 2025). | this package | 99.6% |

## `clusters`

One row per tool cluster. Primary key: `cluster_id`.

| Column | Type | Description | Source | Non-null % |
|--------|------|-------------|--------|------------|
| `cluster_id` | int64 | Cluster identifier from the tool embedding clustering. | this package | 100.0% |
| `size` | int64 | Number of analysis-set tools assigned to the cluster. | this package | 100.0% |
| `top_keywords` | object | Top keywords characterizing the cluster. | this package | 100.0% |
| `gate_category` | object | Gate label (e.g. OCCUPATIONAL, PLUMBING, CONSUMER). | this package | 100.0% |
| `unlabelable` | bool | 1 if labeling was blocked as incoherent. | this package | 100.0% |
| `label` | object | Short human-readable cluster title. | this package | 66.5% |
| `onet_description` | object | Longer description of the work the cluster tools perform. | this package | 66.5% |
| `is_occupational` | int64 | 1 if the cluster is in the occupational (recognizable-work) set. | this package | 100.0% |

## `cluster_tools`

Tool-to-cluster assignment. Primary key: `tool_id`.

| Column | Type | Description | Source | Non-null % |
|--------|------|-------------|--------|------------|
| `tool_id` | object | Tool key `{mcp_id}:{tool_name}`. | this package | 100.0% |
| `mcp_id` | object | Server identifier. | this package | 100.0% |
| `cluster_id` | int64 | Assigned cluster id (−1 for noise). | this package | 100.0% |
| `is_hdbscan_noise` | int64 | 1 if HDBSCAN labeled the tool as noise. | this package | 100.0% |

## `cluster_taxonomy`

Occupational clusters with three-way work-type labels and themes. Primary key: `cluster_id`. EPOCH ratings use the Loaiza & Rigobon (2024) framework on a 0–4 scale.

| Column | Type | Description | Source | Non-null % |
|--------|------|-------------|--------|------------|
| `cluster_id` | int64 | Occupational cluster identifier. | this package | 100.0% |
| `label` | object | Short human-readable cluster title. | this package | 100.0% |
| `onet_description` | object | Longer description of the work the cluster tools perform. | this package | 100.0% |
| `size` | int64 | Number of analysis-set tools in the cluster. | this package | 100.0% |
| `work_type` | object | Three-way work-type classification: subatomic, composite, or new. | this package | 100.0% |
| `new_kind` | object | For `work_type=new`: working_with_agents, building_automation, or other; else null. | this package | 3.1% |
| `theme_name` | object | Theme label within the work-type; residuals use an explicit Other theme. | this package | 96.9% |
| `parent_task` | object | Nearest O*NET parent task text used in the occupation crosswalk. | this package | 100.0% |
| `parent_soc_code` | object | SOC of the parent task when available. | this package | 78.2% |
| `soc_code` | object | Assigned occupation SOC, or NEW_OCCUPATION. | this package | 100.0% |
| `occupation_title` | object | Assigned occupation title. | this package | 100.0% |
| `top1_cosine_similarity` | float64 | Cosine similarity to the top matching occupation task embedding. | this package | 100.0% |
| `is_new_occupation` | int64 | 1 if the cluster was labeled as a new occupation outside O*NET. | this package | 100.0% |
| `nearest_onet_similarity` | float64 | Maximum cosine similarity to any software-performable O*NET task. | this package | 100.0% |
| `mean_top5_similarity` | float64 | Mean cosine similarity to the five nearest software-performable tasks. | this package | 100.0% |
| `nearest_onet_task` | object | Text of the nearest software-performable O*NET task. | this package | 100.0% |
| `nearest_onet_task_id` | int64 | Task id of the nearest software-performable O*NET task. | this package | 100.0% |
| `nearest_onet_occupation` | object | Occupation title of the nearest software-performable task. | this package | 100.0% |
| `nearest_onet_soc` | object | SOC of the nearest software-performable task. | this package | 100.0% |
| `epoch_empathy` | float64 | Rating (0–4) of how much the work in this cluster draws on empathy and emotional intelligence, one of the five EPOCH human capabilities (Loaiza & Rigobon 2024). | this package | 100.0% |
| `epoch_presence` | float64 | Rating (0–4) of how much the work in this cluster draws on presence, networking, and connectedness, one of the five EPOCH human capabilities (Loaiza & Rigobon 2024). | this package | 100.0% |
| `epoch_opinion` | float64 | Rating (0–4) of how much the work in this cluster draws on opinion, judgment, and ethics, one of the five EPOCH human capabilities (Loaiza & Rigobon 2024). | this package | 100.0% |
| `epoch_creativity` | float64 | Rating (0–4) of how much the work in this cluster draws on creativity and imagination, one of the five EPOCH human capabilities (Loaiza & Rigobon 2024). | this package | 100.0% |
| `epoch_hope` | float64 | Rating (0–4) of how much the work in this cluster draws on hope, vision, and leadership, one of the five EPOCH human capabilities (Loaiza & Rigobon 2024). | this package | 100.0% |
| `epoch_composite` | float64 | Composite of the five EPOCH capability ratings for this cluster (each dimension rated 0–4). | this package | 100.0% |
| `epoch_within_sd` | float64 | Standard deviation of the EPOCH composite across repeated rating runs; a stability measure. | this package | 100.0% |
| `epoch_n_versions` | int64 | Number of rating runs behind `epoch_within_sd`. | this package | 100.0% |
| `agent_dependence_verdict` | object | Whether performing the work depends on an AI agent. | this package | 99.9% |

## `occupation_results`

One row per occupation in the software-performable task universe. Coverage figures typically keep occupations with at least 3 software-performable tasks. Sign of `delta_expertise`: positive means matched tools sit below the occupation's retained tasks (remaining work requires MORE expertise); prefer percentile columns for display. `share_tasks_matched` can hit 100% on thin denominators — interpret with the eligibility floor.

| Column | Type | Description | Source | Non-null % |
|--------|------|-------------|--------|------------|
| `onet_soc_code` | object | O*NET-SOC code. | this package | 100.0% |
| `occupation_title` | object | O*NET occupation title. | this package | 100.0% |
| `soc_major_group` | int64 | Two-digit SOC major group. | this package | 100.0% |
| `soc_major_group_label` | object | Readable SOC major-group label. | this package | 100.0% |
| `job_zone` | int64 | O*NET Job Zone 1–5 when available. | this package | 100.0% |
| `n_tasks_onet` | int64 | Count of all O*NET task statements for the occupation. | this package | 100.0% |
| `n_tasks_software_performable` | int64 | Count of software-performable tasks (coverage denominator). Occupations with fewer than 3 are typically excluded from coverage figures. | this package | 100.0% |
| `n_tasks_software_performable_with_sfi` | int64 | Software-performable tasks that also carry an SFI score. | this package | 100.0% |
| `n_matched_tasks` | int64 | Distinct software-performable tasks with ≥1 good rank-1 tool match. | this package | 100.0% |
| `n_matched_tasks_with_sfi` | int64 | Matched tasks that enter expertise calculations (SFI-bearing). | this package | 100.0% |
| `n_tools` | int64 | Distinct matched tools. | this package | 100.0% |
| `n_dedup_tools` | int64 | Matched tools after repository + tool-name deduplication. | this package | 100.0% |
| `share_tasks_matched` | float64 | `n_matched_tasks / n_tasks_software_performable`. Occupations with few eligible tasks can show 100% coverage on thin evidence — interpret with the ≥3 floor. | this package | 100.0% |
| `matched_percentile` | float64 | Mean within-occupation SFI percentile of unique matched tasks (blank if undefined). Primary display for expertise position of matched work. | this package | 54.9% |
| `expertise_percentile` | float64 | Mean within-occupation SFI percentile of retained (unmatched) tasks (blank if undefined). | this package | 54.9% |
| `delta_expertise` | float64 | Mean SFI of retained tasks minus mean SFI of all occupation tasks (blank if undefined). Sign convention: positive = matched tools sit below the occupation's retained tasks, i.e. remaining work requires MORE expertise. Prefer the percentile columns for display. | this package | 54.9% |

## `usage_stats`

Adoption signals per server. Primary key: `mcp_id`.

| Column | Type | Description | Source | Non-null % |
|--------|------|-------------|--------|------------|
| `mcp_id` | object | Server identifier. | this package | 100.0% |
| `name` | object | Server display name. | this package | 100.0% |
| `source` | object | Primary registry source for the listing. | this package | 100.0% |
| `github_url` | object | Resolved GitHub URL when available. | this package | 96.5% |
| `repo_full_name` | object | GitHub owner/repo full name. | this package | 96.5% |
| `github_stars` | float64 | GitHub stargazer count. | this package | 90.1% |
| `github_forks` | float64 | GitHub fork count. | this package | 90.1% |
| `github_watchers` | float64 | GitHub watchers count. | this package | 90.1% |
| `github_open_issues` | float64 | Open issues count. | this package | 90.1% |
| `github_created_at` | object | Repository creation timestamp. | this package | 90.1% |
| `github_pushed_at` | object | Last push timestamp. | this package | 90.1% |
| `github_archived` | object | Whether the repository is archived. | this package | 90.1% |
| `github_language` | object | Primary language reported by GitHub. | this package | 84.2% |
| `repo_missing` | object | 1 if no repository was resolved. | this package | 96.5% |
| `repo_shared_by_n_servers` | int64 | How many server listings share this repository. | this package | 100.0% |
| `smithery_installs` | float64 | Smithery install count when available. | this package | 3.6% |
| `npm_package` | object | Linked npm package name. | this package | 34.1% |
| `npm_downloads_month` | float64 | npm monthly downloads. | this package | 6.2% |
| `pypi_package` | object | Linked PyPI package name. | this package | 21.5% |
| `pypi_downloads_month` | float64 | PyPI monthly downloads. | this package | 3.9% |
| `usage_coverage` | object | Which adoption signals are present for this server. | this package | 92.8% |
| `signals_present` | object | Count of non-null adoption signals. | this package | 92.8% |
