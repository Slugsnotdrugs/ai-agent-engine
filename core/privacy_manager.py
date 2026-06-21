"""
core/privacy_manager.py
─────────────────────────────────────────────────────────────────────────────
PrivacyManager: Masks PII in text before sending to cloud LLMs,
then restores original values in the response.

Design:
  - Zero external dependencies (stdlib regex only)
  - Deterministic: same value always gets the same token within a session
  - Safe: tokens are unique UUIDs so they cannot collide with real text
  - Ordered: patterns run most-specific first to avoid partial overlaps

Usage:
  pm = PrivacyManager()
  masked_text, entity_map = pm.mask(user_input)
  # ... send masked_text to LLM ...
  final_output = pm.unmask(llm_response, entity_map)
"""
import re
import uuid
from typing import Tuple


# ── PII patterns (order = most specific first) ────────────────────────────────
# Each tuple: (label, compiled_regex)
_PII_PATTERNS = [
    ("SSN",    re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("EMAIL",  re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")),
    ("PHONE",  re.compile(r"\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}")),
    ("URL",    re.compile(r"https?://[^\s]+")),
    ("ZIP",    re.compile(r"\b\d{5}(?:-\d{4})?\b")),
    ("DATE",   re.compile(r"\b(?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01])[/-](?:\d{2}|\d{4})\b")),
    ("NAME",   re.compile(r"\b[A-Z][a-z]{1,20}\s[A-Z][a-z]{1,20}\b")),
]


class PrivacyManager:
    """
    Stateless PII masker/unmasker.
    Each call to mask() produces a fresh entity_map scoped to that execution.
    """

    # ── Public API ────────────────────────────────────────────────────────────

    def mask(self, text: str) -> Tuple[str, dict]:
        """
        Scan `text` for PII and replace each match with a unique token.

        Returns:
            masked_text  : str  — text safe to send to an external LLM
            entity_map   : dict — {token: original_value} for unmasking
        """
        entity_map: dict[str, str] = {}
        value_to_token: dict[str, str] = {}  # deduplicate identical values
        masked = text

        for label, pattern in _PII_PATTERNS:
            def _replace(match, label=label):
                original = match.group()
                if original in value_to_token:
                    return value_to_token[original]
                token = f"[{label}_{uuid.uuid4().hex[:8].upper()}]"
                entity_map[token] = original
                value_to_token[original] = token
                return token

            masked = pattern.sub(_replace, masked)

        return masked, entity_map

    def unmask(self, text: str, entity_map: dict) -> str:
        """
        Replace all tokens in `text` with their original values from entity_map.

        Safe to call even if entity_map is empty (returns text unchanged).
        """
        if not entity_map:
            return text
        result = text
        for token, original in entity_map.items():
            result = result.replace(token, original)
        return result

    # ── Utility ───────────────────────────────────────────────────────────────

    def audit(self, text: str) -> list[dict]:
        """
        Non-destructive scan: returns a list of detected PII entities
        without modifying the text. Useful for logging and dashboards.

        Returns list of {label, value, start, end} dicts.
        """
        findings = []
        for label, pattern in _PII_PATTERNS:
            for match in pattern.finditer(text):
                findings.append({
                    "label": label,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                })
        # Sort by position in text
        findings.sort(key=lambda x: x["start"])
        return findings

    def entity_count(self, entity_map: dict) -> int:
        """Convenience: number of unique PII entities masked."""
        return len(entity_map)
