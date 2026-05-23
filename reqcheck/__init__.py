"""req-check — verify that your codebase implements your spec."""
from reqcheck.verifier import verify
from reqcheck.scanner import scan_codebase, format_codebase
from reqcheck.types import (
    Finding, Requirement, Status, VerificationReport,
)

__all__ = [
    "verify",
    "scan_codebase",
    "format_codebase",
    "Finding",
    "Requirement",
    "Status",
    "VerificationReport",
]
__version__ = "0.1.0"
