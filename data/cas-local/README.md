# Local CAS Partition Data

中文说明在前，English version is provided in the second half of this file.

## 中文说明

这个目录用于放置用户自己下载或整理的中科院期刊分区数据。public release 不附带任何完整的中科院分区原始数据文件；用户需要自行确认数据来源、授权范围和本地使用权限。

推荐做法：

- 将本地中科院分区文件放在本目录，或通过 `--local-partition-file <path>` 指向其他本地路径。
- 建议按年份命名，例如 `cas_2024_partitions.csv`、`cas_2023_partitions.tsv` 或 `cas_2022_partitions.json`。
- 不要把受版权、数据库权利、平台条款、机构授权或再分发限制约束的数据文件提交到 GitHub。
- 不要发布包含账号、机构访问痕迹、下载链接 token、cookie、页面快照或个人信息的数据文件。

当前脚本支持 CSV、TSV 和 JSON。本地查询示例：

```bash
npm run fetch -- --input examples/jcr_input.example.json --output cas_results.md --partition-source cas-local
npm run fetch -- --journal "Advanced Functional Materials" --year 2024 --partition-source cas-local --local-partition-file data/cas-local/cas_2024_partitions.csv
```

常见字段名可以包括：

```text
journal_name
issn
year
cas_partition
cas_subject
cas_top
category
```

字段名可以是英文或常见中文表头，例如 `刊名`、`期刊名称`、`ISSN`、`年份`、`中科院分区`、`大类分区`、`大类学科`、`是否TOP`。脚本会尽量自动识别。

---

# Local CAS Partition Data

English version. The Chinese version is provided above.

This directory is for user-provided local CAS journal partition data. The public release does not bundle complete CAS partition raw-data files. Users must verify the data source, permission scope, and local-use rights themselves.

Recommended practice:

- Put local CAS partition files in this directory, or pass another local path through `--local-partition-file <path>`.
- Prefer year-specific filenames, such as `cas_2024_partitions.csv`, `cas_2023_partitions.tsv`, or `cas_2022_partitions.json`.
- Do not commit data files that are restricted by copyright, database rights, platform terms, institutional licenses, or redistribution limits.
- Do not publish files that contain account data, institutional access traces, tokenized download links, cookies, page snapshots, or personal information.

The current script supports CSV, TSV, and JSON. Example usage:

```bash
npm run fetch -- --input examples/jcr_input.example.json --output cas_results.md --partition-source cas-local
npm run fetch -- --journal "Advanced Functional Materials" --year 2024 --partition-source cas-local --local-partition-file data/cas-local/cas_2024_partitions.csv
```

Common field names may include:

```text
journal_name
issn
year
cas_partition
cas_subject
cas_top
category
```

The parser also recognizes common Chinese headers such as `刊名`, `期刊名称`, `ISSN`, `年份`, `中科院分区`, `大类分区`, `大类学科`, and `是否TOP`.
