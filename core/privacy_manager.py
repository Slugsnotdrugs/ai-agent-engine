import re, uuid
from typing import Tuple
_PII_PATTERNS = [
    ("SSN",   re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("EMAIL", re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")),
    ("PHONE", re.compile(r"\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}")),
    ("URL",   re.compile(r"https?://[^\s]+")),
    ("ZIP",   re.compile(r"\b\d{5}(?:-\d{4})?\b")),
    ("NAME",  re.compile(r"\b[A-Z][a-z]{1,20}\s[A-Z][a-z]{1,20}\b")),
]
class PrivacyManager:
    def mask(self, text: str) -> Tuple[str, dict]:
        entity_map, v2t, masked = {}, {}, text
        for label, pattern in _PII_PATTERNS:
            def _replace(m, label=label):
                o = m.group()
                if o in v2t: return v2t[o]
                t = f"[{label}_{uuid.uuid4().hex[:8].upper()}]"
                entity_map[t] = o; v2t[o] = t; return t
            masked = pattern.sub(_replace, masked)
        return masked, entity_map
    def unmask(self, text: str, entity_map: dict) -> str:
        if not entity_map: return text
        for t, o in entity_map.items(): text = text.replace(t, o)
        return text
    def entity_count(self, entity_map: dict) -> int: return len(entity_map)
