"""Canonical rule-ID registry owned by the deterministic backend."""

RULE_IDS: dict[tuple[str, str], str] = {
    ("TURNOVER", "GREATER_THAN_OR_EQUAL"): "RULE-TURNOVER-GTE",
    ("GST", "STATUS_ACTIVE"): "RULE-GST-ACTIVE",
    ("PAN", "STATUS_ACTIVE"): "RULE-PAN-VALID",
    ("UDYAM", "STATUS_ACTIVE"): "RULE-UDYAM-ACTIVE",
    ("OEM_AUTHORIZATION", "STATUS_ACTIVE"): "RULE-OEM-AUTHORIZATION-ACTIVE",
}


def rule_id_for(requirement_type: str, operator: str) -> str:
    key = (str(requirement_type), str(operator))
    try:
        return RULE_IDS[key]
    except KeyError as exc:
        raise ValueError(
            f"No canonical rule is registered for type={requirement_type!r}, "
            f"operator={operator!r}. Do not invent a rule ID."
        ) from exc
