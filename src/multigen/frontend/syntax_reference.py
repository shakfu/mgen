"""Render the supported-syntax contract from the feature registry.

Hand-written feature tables go stale silently. The checked-in reference claimed
exception handling was unsupported and context managers unimplemented long after
both worked, and cited line numbers that had moved. Generating the tables from
`feature_rules` and the profile definitions means the document cannot disagree
with the code that enforces it.

`docs/supported_syntax.md` carries the generated block between markers, so the
prose around it stays hand-written. A test regenerates and compares, which is
what makes staleness a build failure rather than a discovery.
"""

from .diagnostics import RuleId
from .static_profile import PROFILES, StaticProfile
from .subset_validator import FeatureRule, FeatureStatus, StaticPythonSubsetValidator

BEGIN_MARKER = "<!-- BEGIN GENERATED: feature-support -->"
END_MARKER = "<!-- END GENERATED: feature-support -->"

# How a profile treats each declared status.
ACCEPTED = "accepted"
WARNED = "warned"
REJECTED = "rejected"

_TIER_LABELS = {
    1: "1 - fundamental",
    2: "2 - structured",
    3: "3 - advanced",
    4: "4 - unsupported",
}


def profile_disposition(status: FeatureStatus, profile: StaticProfile) -> str:
    """How a profile treats a feature with the given declared status."""
    if status in (FeatureStatus.NOT_SUPPORTED, FeatureStatus.PLANNED):
        return REJECTED
    if status is FeatureStatus.EXPERIMENTAL:
        return REJECTED if profile.warnings_are_errors else WARNED
    return ACCEPTED


def _escape(text: str) -> str:
    """Make text safe inside a Markdown table cell."""
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _feature_table(rules: dict[str, FeatureRule], profiles: list[StaticProfile]) -> list[str]:
    """Render one row per feature, with a column per profile."""
    headers = ["Feature", "Tier", "Declared status"]
    headers.extend(profile.name for profile in profiles)
    headers.append("Notes")

    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]

    for _key, rule in sorted(rules.items(), key=lambda item: (item[1].tier.value, item[1].name)):
        cells = [
            _escape(rule.name),
            _TIER_LABELS.get(rule.tier.value, str(rule.tier.value)),
            rule.status.name,
        ]
        cells.extend(profile_disposition(rule.status, profile) for profile in profiles)
        notes = rule.description
        if rule.constraints:
            notes = f"{notes}. {'; '.join(rule.constraints)}"
        cells.append(_escape(notes))
        lines.append("| " + " | ".join(cells) + " |")

    return lines


def _diagnostic_table() -> list[str]:
    """Render the stable diagnostic identifiers."""
    lines = ["| Identifier | Meaning |", "|---|---|"]
    for attribute in sorted(vars(RuleId)):
        if attribute.startswith("_") or attribute == "CONSTRAINT_PREFIX":
            continue
        value = getattr(RuleId, attribute)
        meaning = attribute.replace("_", " ").capitalize()
        lines.append(f"| `{value}` | {meaning} |")
    lines.append("")
    lines.append(f"Universal constraint checks keep their own codes under the `{RuleId.CONSTRAINT_PREFIX}` prefix.")
    return lines


def render_feature_support() -> str:
    """Render the generated block, without the surrounding markers."""
    rules = StaticPythonSubsetValidator().feature_rules
    profiles = [PROFILES[name] for name in sorted(PROFILES)]

    lines = [
        "<!-- Generated from the feature registry. Do not edit by hand:",
        "     run `make docs-syntax` after changing a rule or a profile. -->",
        "",
        "### Profiles",
        "",
        "| Profile | Description |",
        "|---|---|",
    ]
    for profile in profiles:
        lines.append(f"| `{profile.name}` | {_escape(profile.description)} |")

    lines.extend(
        [
            "",
            "A feature is **accepted** when a profile allows it, **warned** when it is",
            "reported but not fatal, and **rejected** when it fails validation.",
            "",
            "### Feature support",
            "",
        ]
    )
    lines.extend(_feature_table(rules, profiles))
    lines.extend(
        [
            "",
            "### Diagnostic identifiers",
            "",
            "These are stable and append-only: they appear in `--format json` output",
            "and are safe to filter on.",
            "",
        ]
    )
    lines.extend(_diagnostic_table())

    return "\n".join(lines)


def render_document(existing: str) -> str:
    """Return `existing` with the generated block refreshed.

    Args:
        existing: Current document text, with or without the markers.

    Raises:
        ValueError: If only one of the two markers is present, which would mean
            silently appending a second copy of the block.
    """
    block = f"{BEGIN_MARKER}\n\n{render_feature_support()}\n\n{END_MARKER}"

    has_begin = BEGIN_MARKER in existing
    has_end = END_MARKER in existing
    if has_begin != has_end:
        raise ValueError("Document contains only one generation marker; refusing to guess where the block ends")

    if not has_begin:
        return existing.rstrip("\n") + "\n\n" + block + "\n"

    start = existing.index(BEGIN_MARKER)
    end = existing.index(END_MARKER) + len(END_MARKER)
    return existing[:start] + block + existing[end:]
