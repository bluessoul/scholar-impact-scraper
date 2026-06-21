from __future__ import annotations

from intake.profile_extractor import normalize_space


FIELD_KEYWORDS = {
    "publication_list": ("publication", "论文", "成果", "articles", "papers"),
    "representative_works": ("representative", "selected", "代表作", "代表性"),
    "total_citations": ("total citations", "citation count", "总引用", "被引总数"),
    "h_index": ("h-index", "h index", "h指数", "h 因子"),
    "first_author": ("first author", "第一作者", "一作"),
    "corresponding_author": ("corresponding author", "通讯作者", "通信作者"),
    "doi": ("doi",),
    "jcr": ("jcr", "impact factor", "影响因子", "journal citation reports"),
    "cas_partition": ("中科院", "cas partition", "分区"),
}

CITATION_FORMATS = {
    "gbt2025": ("gb/t 7714-2025", "gb/t7714-2025", "gbt2025", "7714-2025"),
    "gbt": ("gb/t 7714", "gb/t7714", "gbt", "国标"),
    "apa": ("apa",),
    "ama": ("ama", "numeric", "vancouver"),
    "mla": ("mla",),
    "chicago": ("chicago",),
    "harvard": ("harvard",),
    "latex": ("bibtex", "latex"),
}


def analyze_template(text: str) -> dict:
    lowered = (text or "").lower()
    requested_fields = [
        field
        for field, keywords in FIELD_KEYWORDS.items()
        if any(keyword.lower() in lowered for keyword in keywords)
    ]
    detected_instructions = extract_instruction_lines(text)
    citation_format = infer_citation_format(lowered)
    output_style = infer_output_style(lowered, requested_fields)

    return {
        "requested_fields": requested_fields,
        "citation_format": citation_format,
        "output_style": output_style,
        "is_default": not bool(requested_fields or detected_instructions),
        "requires_jcr": "jcr" in requested_fields,
        "requires_cas_partition": "cas_partition" in requested_fields,
        "requires_author_roles": any(field in requested_fields for field in ("first_author", "corresponding_author")),
        "detected_instructions": detected_instructions,
    }


def default_requirements() -> dict:
    return {
        "requested_fields": ["publication_list", "total_citations", "h_index", "doi"],
        "citation_format": "gbt2025",
        "output_style": "CV-ready publication list + impact summary",
        "is_default": True,
        "requires_jcr": False,
        "requires_cas_partition": False,
        "requires_author_roles": True,
        "detected_instructions": [],
    }


def merge_requirements(*requirements: dict) -> dict:
    merged = default_requirements()
    explicit = False
    for item in requirements:
        if not item:
            continue
        fields = item.get("requested_fields", [])
        if fields:
            explicit = True
            merged["requested_fields"] = sorted(set(merged["requested_fields"]) | set(fields))
        if item.get("citation_format"):
            merged["citation_format"] = item["citation_format"]
        if item.get("output_style") and item["output_style"] != default_requirements()["output_style"]:
            merged["output_style"] = item["output_style"]
        merged["requires_jcr"] = merged["requires_jcr"] or item.get("requires_jcr", False)
        merged["requires_cas_partition"] = merged["requires_cas_partition"] or item.get("requires_cas_partition", False)
        merged["requires_author_roles"] = merged["requires_author_roles"] or item.get("requires_author_roles", False)
        merged["detected_instructions"].extend(item.get("detected_instructions", []))
    if not explicit:
        return default_requirements()
    merged["is_default"] = False
    return merged


def infer_citation_format(lowered_text: str) -> str:
    for name, keywords in CITATION_FORMATS.items():
        if any(keyword in lowered_text for keyword in keywords):
            return name
    return "gbt2025"


def infer_output_style(lowered_text: str, requested_fields: list[str]) -> str:
    if "table" in lowered_text or "表格" in lowered_text:
        return "template ordered table-ready summary"
    if "representative_works" in requested_fields:
        return "representative works + impact summary"
    if requested_fields:
        return "template ordered publication summary"
    return "CV-ready publication list + impact summary"


def extract_instruction_lines(text: str) -> list[str]:
    lines = []
    for raw in (text or "").splitlines():
        line = normalize_space(raw)
        lowered = line.lower()
        if not line or len(line) > 240:
            continue
        if any(keyword in lowered for keywords in FIELD_KEYWORDS.values() for keyword in keywords):
            lines.append(line)
    return lines[:20]
