# JCR 2024 Local Data

中文说明在前，English version is provided in the second half of this file.

## 中文说明

这个目录用于放置用户自己准备的 JCR 2024 分区原始文件。

默认情况下，public release 不附带完整的 JCR 2024 原始数据文件，原因是这类文件可能来自第三方分享，可能受到版权、数据库权利、平台条款或再分发限制约束。

推荐做法：

- 如果你只是自己本地使用，请把文件放在这个目录或其他本地路径中，但不要提交到 Git。
- 如果你确实要把数据文件一起发布，请先确认来源允许公开再分发，并在本目录添加清晰的来源、许可证、下载日期和校验信息。
- 不要发布包含账号、机构访问痕迹、下载链接 token、cookie、页面快照或个人信息的数据文件。

建议记录的信息：

```text
Source:
License or permission:
Downloaded or collected on:
Original filename:
SHA256:
Notes:
```

实时 JCR 查询仍然需要你自己的合法 Clarivate/JCR 访问权限，并通过 Playwright 浏览器登录网站获取当前账号可见的信息。

---

# JCR 2024 Local Data

English version. The Chinese version is provided above.

This directory is for a user-provided JCR 2024 quartile raw-data file.

By default, the public release does not bundle the full JCR 2024 raw-data file because third-party shared files may be subject to copyright, database rights, platform terms, or redistribution restrictions.

Recommended practice:

- For local-only use, place your file in this directory or another local path, but do not commit it to Git.
- If you want to publish a data file with the repository, first confirm that the source allows public redistribution, and document the source, license, collection date, and checksum.
- Do not publish files that contain account data, institutional access traces, tokenized download links, cookies, page snapshots, or personal information.

Suggested metadata:

```text
Source:
License or permission:
Downloaded or collected on:
Original filename:
SHA256:
Notes:
```

Live JCR lookup still requires your own legitimate Clarivate/JCR access and uses a Playwright browser session to query information visible to your account.
