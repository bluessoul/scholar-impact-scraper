# Local JCR Data

中文说明在前，English version is provided in the second half of this file.

## 中文说明

这个目录用于放置用户自己准备的本地 JCR 数据文件。数据可以来自任意年份，例如 JCR 2024、JCR 2023、JCR 2022 或更早年份，只要用户确认自己拥有合法使用权限。

默认情况下，public release 不附带任何完整的 JCR 原始数据文件。原因是这类文件可能来自 Clarivate/JCR 或第三方分享，可能受到版权、数据库权利、平台条款、机构授权或再分发限制约束。

推荐做法：

- 如果只是本地使用，请把你自己下载或整理的 JCR 数据文件放在这个目录或其他本地路径中，但不要提交到 Git。
- 建议按年份组织文件名，例如 `jcr_2024_quartiles.csv`、`jcr_2023_quartiles.tsv` 或 `jcr_2022_quartiles.json`。
- 当前脚本支持 CSV、TSV 和 JSON，本地查询可通过 `--partition-source jcr-local` 启用。
- 如果确实要把数据文件一起发布，请先确认来源允许公开再分发，并记录来源、许可证或授权说明、下载日期和校验信息。
- 不要发布包含账号、机构访问痕迹、下载链接 token、cookie、页面快照或个人信息的数据文件。

常见字段名可以包括：

```text
journal_name
issn
year
category
rank
quartile
percentile
journal_impact_factor
five_year_jif
```

实时 JCR 查询仍然需要你自己的合法 Clarivate/JCR 访问权限，并通过 Playwright 浏览器登录网站获取当前账号可见的信息。

---

# Local JCR Data

English version. The Chinese version is provided above.

This directory is for user-provided local JCR data files. The files may cover any year, such as JCR 2024, JCR 2023, JCR 2022, or older years, as long as the user has legitimate permission to use them.

By default, the public release does not bundle complete JCR raw-data files. These files may come from Clarivate/JCR or third-party sources and may be subject to copyright, database rights, platform terms, institutional licenses, or redistribution restrictions.

Recommended practice:

- For local-only use, place your own JCR data files in this directory or another local path, but do not commit them to Git.
- Prefer year-specific filenames, such as `jcr_2024_quartiles.csv`, `jcr_2023_quartiles.tsv`, or `jcr_2022_quartiles.json`.
- The current script supports CSV, TSV, and JSON. Enable local lookup with `--partition-source jcr-local`.
- If you publish a data file with the repository, first confirm that the source allows public redistribution and document the source, license or permission, collection date, and checksum.
- Do not publish files that contain account data, institutional access traces, tokenized download links, cookies, page snapshots, or personal information.

Common field names may include:

```text
journal_name
issn
year
category
rank
quartile
percentile
journal_impact_factor
five_year_jif
```

Live JCR lookup still requires your own legitimate Clarivate/JCR access and uses a Playwright browser session to query information visible to your account.
