"""
core/custom_recognizers.py
────────────────────────────────────────────────────────────────────────────
Ready-to-use custom Presidio recognizers for common domain-specific
entity types not covered by Presidio's built-in set.

Usage
─────
from core.privacy_manager import PrivacyManager
from core.custom_recognizers import MedicalRecordNumberRecognizer, NHSNumberRecognizer

pm = PrivacyManager()
pm.add_recognizer(MedicalRecordNumberRecognizer())
pm.add_recognizer(NHSNumberRecognizer())

Add your own by subclassing PatternRecognizer or SpacyRecognizer.
"""

from __future__ import annotations

from presidio_analyzer import PatternRecognizer, Pattern


class MedicalRecordNumberRecognizer(PatternRecognizer):
    """
    Detects Medical Record Numbers (MRN) in common formats:
        MRN-123456  |  MRN: 123456  |  MR123456
    """
    PATTERNS = [
        Pattern("MRN_DASHED",  r"\bMRN[-:\s]?\d{5,8}\b",  score=0.90),
        Pattern("MRN_PREFIX",  r"\bMR\d{5,8}\b",           score=0.80),
    ]
    CONTEXT = ["mrn", "medical record", "patient id", "record number"]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="MEDICAL_RECORD_NUMBER",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
        )


class NHSNumberRecognizer(PatternRecognizer):
    """
    Detects UK NHS numbers (10-digit, optionally space-separated in groups).
        Example: 943 476 5919
    """
    PATTERNS = [
        Pattern("NHS_SPACED",  r"\b\d{3}\s\d{3}\s\d{4}\b", score=0.85),
        Pattern("NHS_PLAIN",   r"\b\d{10}\b",               score=0.50),
    ]
    CONTEXT = ["nhs", "nhs number", "national health"]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="NHS_NUMBER",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
        )


class CaseNumberRecognizer(PatternRecognizer):
    """
    Detects legal case / docket numbers.
        Examples: CASE-2024-00123  |  Docket 23-cv-04512
    """
    PATTERNS = [
        Pattern("CASE_PREFIXED", r"\bCASE[-:\s]?\d{4}[-\s]\d{3,6}\b",     score=0.88),
        Pattern("DOCKET",        r"\b\d{2}-[a-z]{2}-\d{4,6}\b",            score=0.82),
    ]
    CONTEXT = ["case", "docket", "matter", "file number", "claim"]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="CASE_NUMBER",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
        )


class AccountNumberRecognizer(PatternRecognizer):
    """
    Detects internal account / portfolio numbers.
        Examples: ACC-00412  |  ACCT#998712
    """
    PATTERNS = [
        Pattern("ACC_DASHED",  r"\bACC[-:\s]?\d{4,8}\b",   score=0.88),
        Pattern("ACCT_HASH",   r"\bACCT#\d{4,8}\b",         score=0.88),
    ]
    CONTEXT = ["account", "portfolio", "client id", "acct"]

    def __init__(self) -> None:
        super().__init__(
            supported_entity="ACCOUNT_NUMBER",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
        )
