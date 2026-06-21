from __future__ import annotations

import csv
from pathlib import Path


def build_final_summary(profile: dict, requirements: dict, resolution: dict, scrape_plan: dict, output_dir: str | Path) -> str:
    output = Path(output_dir)
    confirmation = scrape_plan.get("confirmation", {})
    lines: list[str] = []
    lines.append("# Scholar Auto-Import Summary")
    lines.append("")
    lines.append("## Review Before Continuing")
    if scrape_plan.get("status") == "ready":
        lines.append("- Status: confirmed and ready to continue.")
    else:
        lines.append("- Status: please review before running a full scrape.")
    if confirmation.get("blocking_reasons"):
        lines.append("- Must confirm or fix:")
        for reason in confirmation["blocking_reasons"]:
            lines.append(f"  - {reason}")
    if confirmation.get("review_items"):
        lines.append("- Please also review:")
        for item in confirmation["review_items"]:
            lines.append(f"  - {item}")
    if not confirmation.get("auto_confirmed"):
        lines.append("- To continue after review, rerun the command with `--yes`.")
    lines.append("")
    lines.append("## Detected Scholar Information")
    lines.append(f"- Name: {profile.get('name') or 'Needs confirmation'}")
    lines.append(f"- Affiliation: {profile.get('affiliation') or 'Not detected'}")
    lines.append(f"- Email(s): {', '.join(profile.get('emails', [])) or 'Not detected'}")
    lines.append(f"- ORCID: {profile.get('orcid') or 'Not detected'}")
    lines.append(f"- Google Scholar ID: {profile.get('scholar_user_id') or 'Not detected'}")
    lines.append("")

    lines.append("## Detected Output Requirements")
    lines.append(f"- Style: {requirements.get('output_style')}")
    lines.append(f"- Citation format: {requirements.get('citation_format')}")
    lines.append(f"- Requested fields: {', '.join(requirements.get('requested_fields', []))}")
    year_scope = scrape_plan.get("year_scope", {})
    lines.append(f"- Publication years: {year_scope.get('description') or 'Needs confirmation'}")
    if not year_scope.get("confirmed"):
        lines.append("- Note: confirm all years with `--all-years`, or specify `--year 2024` / `--year-from 2020 --year-to 2024`.")
    if requirements.get("is_default"):
        lines.append("- Note: no explicit template requirement was detected, so default output settings were used.")
    if requirements.get("detected_instructions"):
        lines.append("- Template instructions:")
        for instruction in requirements["detected_instructions"][:8]:
            lines.append(f"  - {instruction}")
    lines.append("")

    lines.append("## Detected Author Formatting")
    formatting = profile.get("formatting_clues", {})
    bold = formatting.get("bold_segments", [])
    underlined = formatting.get("underlined_segments", [])
    starred = formatting.get("starred_segments", [])
    if bold or underlined or starred:
        lines.append(f"- Bold text segments: {', '.join(bold) or 'None'}")
        lines.append(f"- Underlined text segments: {', '.join(underlined) or 'None'}")
        lines.append(f"- Starred author-like segments: {', '.join(starred) or 'None'}")
        lines.append("- Please confirm whether these marks indicate the target author, first author, or corresponding author.")
    else:
        lines.append("- No bold, underlined, or starred author-like formatting was detected.")
    if profile.get("document_warnings"):
        lines.append("- Document warnings:")
        for warning in profile["document_warnings"]:
            lines.append(f"  - {warning}")
    lines.append("")

    lines.append("## Scholar Match")
    lines.append(f"- Status: {resolution.get('status')}")
    accepted = resolution.get("accepted_candidate")
    if accepted:
        lines.append(f"- Accepted: {accepted.get('source')} {accepted.get('id')} ({accepted.get('confidence')})")
        lines.append(f"- Evidence: {'; '.join(accepted.get('evidence', []))}")
    else:
        lines.append("- Accepted: none; user confirmation is required before running source scraping.")
    lines.append("")

    lines.append("## Planned Or Completed Actions")
    commands = scrape_plan.get("commands", [])
    if commands:
        for command in commands:
            status = command.get("status", "planned")
            lines.append(f"- [{status}] {' '.join(command.get('argv', []))}")
    else:
        lines.append("- No runnable command was generated.")
    lines.append("")

    lines.append("## Extracted Publication Clues")
    publications = profile.get("publications", [])
    if publications:
        for item in publications[:20]:
            suffix = f" ({item.get('year')})" if item.get("year") else ""
            doi = f" DOI: {item.get('doi')}" if item.get("doi") else ""
            lines.append(f"- {item.get('title') or item.get('raw')}{suffix}{doi}")
    else:
        lines.append("- No publication list was detected in the intake material.")
    lines.append("")

    lines.append("## Local Result Files")
    for key, value in scrape_plan.get("artifacts", {}).items():
        lines.append(f"- {key}: {value}")
    lines.append(f"- result folder: {output}")
    lines.append("")

    lines.append("## Quality Control")
    if scrape_plan.get("status") != "ready":
        lines.append("- Full scraping was not run because review is required first.")
    if not profile.get("scholar_user_id") and not profile.get("orcid"):
        lines.append("- No runnable Scholar or ORCID identifier was detected.")
    if not publications:
        lines.append("- No publication clues were available for cross-checking.")
    if not any(line.startswith("-") for line in lines[-4:]):
        lines.append("- No blocking issue detected in the intake step.")
    return "\n".join(lines) + "\n"


def write_publication_clues_csv(profile: dict, path: str | Path) -> None:
    publications = profile.get("publications", [])
    with Path(path).open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["title", "year", "doi", "raw"])
        writer.writeheader()
        for item in publications:
            writer.writerow({
                "title": item.get("title", ""),
                "year": item.get("year", ""),
                "doi": item.get("doi", ""),
                "raw": item.get("raw", ""),
            })
