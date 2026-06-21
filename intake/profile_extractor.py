from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse


EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
ORCID_RE = re.compile(r"(?:https?://orcid\.org/)?(\d{4}-\d{4}-\d{4}-[\dX]{4})", re.I)
SCHOLAR_URL_RE = re.compile(r"https?://scholar\.google\.[^\s)>\]]+", re.I)
SCHOLAR_USER_RE = re.compile(r"(?:user=|scholar[_\s-]*id[:：]?\s*)([A-Za-z0-9_-]{6,})", re.I)
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)
YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
WOS_RE = re.compile(r"\b(?:ResearcherID|Web of Science ID|WoS ID)[:：]?\s*([A-Z]{1,3}-?\d{4}-?\d{4}|\d{4}-\d{4}-\d{4}-[\dX]{4})", re.I)
SCOPUS_RE = re.compile(r"\b(?:Scopus Author ID|Scopus ID)[:：]?\s*(\d{6,})", re.I)

NAME_PATTERNS = [
    re.compile(r"^(?:Name|Full Name|Candidate|Applicant)[:：]\s*(.+)$", re.I),
    re.compile(r"^(?:姓名|申请人|候选人)[:：]\s*(.+)$"),
]
AFFILIATION_PATTERNS = [
    re.compile(r"^(?:Affiliation|Institution|Organization|Employer|Department)[:：]\s*(.+)$", re.I),
    re.compile(r"^(?:单位|工作单位|所在单位|机构|部门)[:：]\s*(.+)$"),
]
PUBLICATION_HEADINGS = {
    "publications",
    "selected publications",
    "representative publications",
    "research publications",
    "论文成果",
    "代表性论文",
    "发表论文",
    "出版物",
}


def extract_profile(text: str, source_label: str = "input") -> dict:
    lines = [normalize_space(line) for line in text.splitlines()]
    non_empty = [line for line in lines if line]

    emails = sorted(set(EMAIL_RE.findall(text)))
    orcid_match = ORCID_RE.search(text)
    scholar_url = _first(SCHOLAR_URL_RE.findall(text))
    scholar_user_id = extract_scholar_user_id(text)

    explicit_name = _match_first(lines, NAME_PATTERNS)
    explicit_affiliation = _match_first(lines, AFFILIATION_PATTERNS)

    name = explicit_name or infer_name(non_empty)
    affiliation = explicit_affiliation or infer_affiliation(non_empty, emails)
    publications = extract_publications(lines)
    dois = sorted({clean_doi(match) for match in DOI_RE.findall(text)})

    return {
        "source": source_label,
        "name": name,
        "name_variants": build_name_variants(name),
        "affiliation": affiliation,
        "emails": emails,
        "email_domains": sorted({email.split("@", 1)[1].lower() for email in emails}),
        "orcid": orcid_match.group(1) if orcid_match else "",
        "scholar_url": scholar_url,
        "scholar_user_id": scholar_user_id,
        "wos_researcher_id": _group_first(WOS_RE.search(text)),
        "scopus_author_id": _group_first(SCOPUS_RE.search(text)),
        "dois": dois,
        "publications": publications,
        "publication_titles": [item["title"] for item in publications if item.get("title")],
        "formatting_clues": empty_formatting_clues(),
        "document_warnings": [],
    }


def merge_profiles(*profiles: dict) -> dict:
    merged: dict = {
        "name": "",
        "name_variants": [],
        "affiliation": "",
        "emails": [],
        "email_domains": [],
        "orcid": "",
        "scholar_url": "",
        "scholar_user_id": "",
        "wos_researcher_id": "",
        "scopus_author_id": "",
        "dois": [],
        "publications": [],
        "publication_titles": [],
        "formatting_clues": empty_formatting_clues(),
        "document_warnings": [],
        "sources": [],
    }
    for profile in profiles:
        if not profile:
            continue
        merged["sources"].append(profile.get("source", "input"))
        for key in ("name", "affiliation", "orcid", "scholar_url", "scholar_user_id", "wos_researcher_id", "scopus_author_id"):
            if not merged[key] and profile.get(key):
                merged[key] = profile[key]
        for key in ("name_variants", "emails", "email_domains", "dois", "publication_titles"):
            merged[key] = sorted(set(merged[key]) | set(profile.get(key, [])))
        merged["document_warnings"] = sorted(set(merged["document_warnings"]) | set(profile.get("document_warnings", [])))
        merge_formatting_clues(merged["formatting_clues"], profile.get("formatting_clues", {}))
        existing_titles = {item.get("title", "").lower() for item in merged["publications"]}
        for item in profile.get("publications", []):
            title_key = item.get("title", "").lower()
            if title_key and title_key not in existing_titles:
                merged["publications"].append(item)
                existing_titles.add(title_key)
    if not merged["name_variants"]:
        merged["name_variants"] = build_name_variants(merged["name"])
    return merged


def empty_formatting_clues() -> dict:
    return {
        "bold_segments": [],
        "underlined_segments": [],
        "starred_segments": [],
    }


def merge_formatting_clues(target: dict, source: dict) -> None:
    for key in ("bold_segments", "underlined_segments", "starred_segments"):
        target[key] = sorted(set(target.get(key, [])) | set(source.get(key, [])))


def extract_scholar_user_id(text: str) -> str:
    url = _first(SCHOLAR_URL_RE.findall(text))
    if url:
        parsed = urlparse(url)
        user = parse_qs(parsed.query).get("user", [""])[0]
        if user:
            return user
    match = SCHOLAR_USER_RE.search(text)
    return match.group(1) if match else ""


def extract_publications(lines: list[str]) -> list[dict]:
    publications: list[dict] = []
    in_section = False
    for line in lines:
        if not line:
            continue
        lowered = line.lower().strip(" :：")
        if lowered in PUBLICATION_HEADINGS or line.strip(" :：") in PUBLICATION_HEADINGS:
            in_section = True
            continue
        if in_section and looks_like_new_section(line):
            in_section = False
        if in_section or looks_like_publication(line):
            title = infer_publication_title(line)
            if title:
                publications.append({
                    "raw": line,
                    "title": title,
                    "year": _first(YEAR_RE.findall(line)) or "",
                    "doi": clean_doi(_first(DOI_RE.findall(line))),
                })
    return publications


def infer_name(lines: list[str]) -> str:
    skip_words = ("curriculum", "resume", "cv", "简历", "履历", "publications")
    for line in lines[:12]:
        if any(word in line.lower() for word in skip_words):
            continue
        if EMAIL_RE.search(line) or DOI_RE.search(line) or len(line) > 80:
            continue
        if re.search(r"\d", line):
            continue
        words = line.split()
        if 2 <= len(words) <= 5 or (2 <= len(line) <= 12 and re.search(r"[\u4e00-\u9fff]", line)):
            return line.strip(" -|")
    return ""


def infer_affiliation(lines: list[str], emails: list[str]) -> str:
    organization_words = (
        "university", "institute", "college", "school", "laboratory", "hospital",
        "academy", "department", "centre", "center", "公司", "大学", "学院", "研究所", "实验室", "医院",
    )
    for line in lines[:30]:
        lowered = line.lower()
        if any(word in lowered for word in organization_words):
            return line.strip(" -|")
    if emails:
        domain = emails[0].split("@", 1)[1]
        return domain
    return ""


def build_name_variants(name: str) -> list[str]:
    if not name:
        return []
    variants = {name.strip()}
    parts = name.split()
    if len(parts) >= 2:
        variants.add(f"{parts[-1]}, {' '.join(parts[:-1])}")
        variants.add(f"{parts[0][0]}. {' '.join(parts[1:])}")
    return sorted(variants)


def looks_like_publication(line: str) -> bool:
    if len(line) < 25:
        return False
    score = 0
    if YEAR_RE.search(line):
        score += 1
    if DOI_RE.search(line):
        score += 2
    if re.search(r"\b(journal|materials|science|nature|advanced|proceedings|transactions)\b", line, re.I):
        score += 1
    if any(token in line for token in (".", "，", ",", ";")):
        score += 1
    return score >= 2


def looks_like_new_section(line: str) -> bool:
    if len(line) > 50:
        return False
    return bool(re.match(r"^[A-Z][A-Za-z /&-]{2,}$", line) or re.match(r"^[\u4e00-\u9fff]{2,12}$", line))


def infer_publication_title(line: str) -> str:
    cleaned = re.sub(r"^\s*(?:\[\d+\]|\d+[\).、])\s*", "", line).strip()
    quoted = re.search(r"[\"“](.+?)[\"”]", cleaned)
    if quoted:
        return normalize_space(quoted.group(1))
    parts = re.split(r"\.\s+|;\s+|，|,\s+(?=(?:19|20)\d{2}\b)", cleaned)
    candidates = [part.strip() for part in parts if len(part.strip()) > 15 and not DOI_RE.search(part)]
    if len(candidates) >= 2 and re.search(r"\b[A-Z][a-z]+", candidates[0]):
        return normalize_space(candidates[1])
    return normalize_space(candidates[0]) if candidates else ""


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def clean_doi(value: str) -> str:
    return (value or "").rstrip(".,;)")


def _match_first(lines: list[str], patterns: list[re.Pattern]) -> str:
    for line in lines:
        for pattern in patterns:
            match = pattern.search(line)
            if match:
                return normalize_space(match.group(1))
    return ""


def _first(values) -> str:
    return values[0] if values else ""


def _group_first(match) -> str:
    return match.group(1) if match else ""
