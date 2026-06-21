#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from intake.author_resolver import resolve_author
from intake.deliverable_builder import build_final_summary, write_publication_clues_csv
from intake.document_reader import read_document
from intake.profile_extractor import extract_profile, merge_profiles
from intake.template_analyzer import analyze_template, default_requirements, merge_requirements


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Turn CVs, templates, or name+affiliation input into Scholar Impact Scraper plans and deliverables."
    )
    parser.add_argument("--input", help="CV/resume/profile file: docx, pdf, txt, or md.")
    parser.add_argument("--template", help="Optional application/job template file: docx, pdf, txt, or md.")
    parser.add_argument("--name", help="Target scholar name when no input file is provided.")
    parser.add_argument("--affiliation", help="Target scholar affiliation when no input file is provided.")
    parser.add_argument("--orcid", help="Known ORCID iD.")
    parser.add_argument("--scholar-id", help="Known Google Scholar user ID.")
    parser.add_argument("--scholar-url", help="Known Google Scholar profile URL.")
    parser.add_argument("--output-dir", default="intake_results", help="Output folder for local artifacts.")
    parser.add_argument("--max-clicks", type=int, default=5, help="Scholar show-more clicks when running the scraper.")
    parser.add_argument("--openalex-max-records", type=int, default=0, help="OpenAlex enrichment cap passed to scholar_playwright.py.")
    parser.add_argument("--no-run", action="store_true", help="Only generate intake artifacts and scrape_plan.json; do not run scrapers.")
    parser.add_argument("--yes", "--auto-confirm", dest="auto_confirm", action="store_true", help="Confirm the auto-detected scholar information and allow scraping when required fields are complete.")
    parser.add_argument("--all-years", action="store_true", help="Confirm that all available publication years should be collected.")
    parser.add_argument("--year", type=int, help="Collect one specific publication year.")
    parser.add_argument("--year-from", type=int, help="First publication year to collect.")
    parser.add_argument("--year-to", type=int, help="Last publication year to collect.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_profile = {}
    template_requirements = {}
    source_texts: list[str] = []
    if args.input:
        input_doc = read_document(args.input)
        source_texts.append(input_doc["text"])
        input_profile = extract_profile(input_doc["text"], source_label=args.input)
        attach_document_metadata(input_profile, input_doc)
    if args.template:
        template_doc = read_document(args.template)
        source_texts.append(template_doc["text"])
        template_profile = extract_profile(template_doc["text"], source_label=args.template)
        attach_document_metadata(template_profile, template_doc)
        input_profile = merge_profiles(input_profile, template_profile)
        template_requirements = analyze_template(template_doc["text"])

    cli_profile = extract_profile("", source_label="cli")
    cli_profile.update({
        "name": args.name or "",
        "affiliation": args.affiliation or "",
        "orcid": args.orcid or "",
        "scholar_user_id": args.scholar_id or "",
        "scholar_url": args.scholar_url or "",
    })
    if args.scholar_url and not args.scholar_id:
        from intake.profile_extractor import extract_scholar_user_id
        cli_profile["scholar_user_id"] = extract_scholar_user_id(args.scholar_url)

    profile = merge_profiles(input_profile, cli_profile)
    requirements = merge_requirements(analyze_template(" ".join(profile.get("publication_titles", []))), template_requirements)
    if not args.template and not template_requirements:
        requirements = default_requirements()

    resolution = resolve_author(profile)
    year_scope = build_year_scope("\n".join(source_texts), args)
    artifacts = {
        "intake_profile": output_dir / "intake_profile.json",
        "author_candidates": output_dir / "author_candidates.json",
        "scrape_plan": output_dir / "scrape_plan.json",
        "publication_clues": output_dir / "publication_clues.csv",
        "final_summary": output_dir / "final_summary.md",
    }
    confirmation = build_confirmation(profile, requirements, resolution, year_scope, args)
    scrape_plan = build_scrape_plan(profile, requirements, resolution, confirmation, year_scope, output_dir, args)
    scrape_plan["artifacts"].update({key: str(value) for key, value in artifacts.items()})
    if not args.no_run and scrape_plan.get("status") == "ready":
        run_scrape_plan(scrape_plan)

    write_json(artifacts["intake_profile"], profile)
    write_json(artifacts["author_candidates"], resolution)
    write_json(artifacts["scrape_plan"], scrape_plan)
    write_publication_clues_csv(profile, artifacts["publication_clues"])
    artifacts["final_summary"].write_text(
        build_final_summary(profile, requirements, resolution, scrape_plan, output_dir),
        encoding="utf-8",
    )

    print(f"Intake complete: {artifacts['final_summary']}")
    if scrape_plan.get("status") != "ready":
        print("Please review the generated summary before running a full scrape.")
    return 0


def build_confirmation(profile: dict, requirements: dict, resolution: dict, year_scope: dict, args) -> dict:
    blocking_reasons = []
    review_items = []

    if not profile.get("name"):
        blocking_reasons.append("No scholar name was detected.")
    if not profile.get("affiliation"):
        blocking_reasons.append("No affiliation or organization was detected.")
    if resolution.get("needs_confirmation"):
        blocking_reasons.append("Scholar identity needs user confirmation.")
    if requirements.get("is_default"):
        blocking_reasons.append("No explicit output format or template requirements were detected.")
    if not year_scope.get("confirmed"):
        blocking_reasons.append("No publication year range was specified. Confirm all years with --all-years, or pass --year / --year-from and --year-to.")
    if not profile.get("publications"):
        review_items.append("No publication list was detected in the provided material.")
    if profile.get("document_warnings"):
        review_items.extend(profile["document_warnings"])
    if has_formatting_clues(profile):
        review_items.append("Author formatting was detected in the source document; confirm bold, underlined, or starred author meanings before continuing.")
    if not (profile.get("scholar_user_id") or profile.get("orcid")):
        review_items.append("No directly runnable Google Scholar or ORCID identifier was detected.")
    if year_scope.get("description"):
        review_items.append(f"Publication year scope: {year_scope['description']}.")

    if not args.auto_confirm:
        review_items.append("Review the generated summary, then rerun with --yes to continue automatically.")

    return {
        "auto_confirmed": bool(args.auto_confirm),
        "can_run": bool(args.auto_confirm and not blocking_reasons),
        "blocking_reasons": blocking_reasons,
        "review_items": review_items,
    }


def build_year_scope(source_text: str, args) -> dict:
    if args.all_years:
        return {"mode": "all", "confirmed": True, "description": "all available years", "source": "cli"}
    if args.year:
        return {"mode": "single_year", "year": args.year, "confirmed": True, "description": str(args.year), "source": "cli"}
    if args.year_from or args.year_to:
        if args.year_from and args.year_to:
            return {
                "mode": "year_range",
                "year_from": args.year_from,
                "year_to": args.year_to,
                "confirmed": True,
                "description": f"{args.year_from}-{args.year_to}",
                "source": "cli",
            }
        return {
            "mode": "incomplete_range",
            "confirmed": False,
            "description": "incomplete year range",
            "source": "cli",
        }

    inferred = infer_year_scope(source_text)
    if inferred:
        return inferred
    return {"mode": "unspecified", "confirmed": False, "description": "", "source": "missing"}


def infer_year_scope(text: str) -> dict:
    normalized = text or ""
    range_match = re.search(r"\b((?:19|20)\d{2})\s*(?:-|–|—|to|至|到)\s*((?:19|20)\d{2})\b", normalized, re.I)
    if range_match:
        start, end = int(range_match.group(1)), int(range_match.group(2))
        if start <= end:
            return {"mode": "year_range", "year_from": start, "year_to": end, "confirmed": True, "description": f"{start}-{end}", "source": "document"}
    all_years_phrases = ("all years", "all publications", "complete publication list", "全部年份", "所有年份", "全部论文", "所有论文")
    if any(phrase in normalized.lower() for phrase in all_years_phrases):
        return {"mode": "all", "confirmed": True, "description": "all available years", "source": "document"}
    return {}


def build_scrape_plan(profile: dict, requirements: dict, resolution: dict, confirmation: dict, year_scope: dict, output_dir: Path, args) -> dict:
    commands: list[dict] = []
    scholar_id = profile.get("scholar_user_id", "")
    citation_format = requirements.get("citation_format", "gbt2025")
    if scholar_id and resolution.get("status") == "ready":
        output_csv = output_dir / "publications_enriched.csv"
        argv = [
            sys.executable,
            "scholar_playwright.py",
            "--user-id",
            scholar_id,
            "--output",
            str(output_csv),
            "--max-clicks",
            str(args.max_clicks),
            "--target-author",
            profile.get("name", ""),
            "--citation-format",
            citation_format,
            "--output-sort",
            "publication-date",
        ]
        if args.openalex_max_records:
            argv.extend(["--openalex-max-records", str(args.openalex_max_records)])
        commands.append({"kind": "scholar", "argv": argv, "status": "planned", "output": str(output_csv)})

    if profile.get("orcid"):
        output_csv = output_dir / "orcid_publications.csv"
        commands.append({
            "kind": "orcid",
            "argv": [sys.executable, "orcid_extractor.py", "--orcid", profile["orcid"], "--output", str(output_csv)],
            "status": "planned",
            "output": str(output_csv),
        })

    if requirements.get("requires_jcr") or requirements.get("requires_cas_partition"):
        jcr_input = output_dir / "jcr_input.json"
        jcr_items = [
            {"journal_name_or_issn": item.get("raw") or item.get("title"), "publication_year": item.get("year")}
            for item in profile.get("publications", [])
            if item.get("title")
        ]
        write_json(jcr_input, jcr_items)
        partition_source = "cas-local" if requirements.get("requires_cas_partition") else "jcr-live"
        commands.append({
            "kind": "partition",
            "argv": ["npm", "run", "fetch", "--", "--input", str(jcr_input), "--output", str(output_dir / "partition_results.md"), "--partition-source", partition_source],
            "status": "planned",
            "output": str(output_dir / "partition_results.md"),
        })

    return {
        "status": "ready" if commands and confirmation.get("can_run") else "needs_confirmation",
        "confirmation": confirmation,
        "year_scope": year_scope,
        "requirements": requirements,
        "commands": commands,
        "artifacts": {},
    }


def attach_document_metadata(profile: dict, document: dict) -> None:
    profile["formatting_clues"] = document.get("format_clues", {})
    profile["document_warnings"] = document.get("warnings", [])


def has_formatting_clues(profile: dict) -> bool:
    clues = profile.get("formatting_clues", {})
    return any(clues.get(key) for key in ("bold_segments", "underlined_segments", "starred_segments"))


def run_scrape_plan(scrape_plan: dict) -> None:
    if scrape_plan.get("status") != "ready":
        return
    for command in scrape_plan.get("commands", []):
        try:
            completed = subprocess.run(command["argv"], check=False)
            command["returncode"] = completed.returncode
            command["status"] = "completed" if completed.returncode == 0 else "failed"
        except OSError as exc:
            command["status"] = "failed"
            command["error"] = str(exc)


def write_json(path: str | Path, payload) -> None:
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
