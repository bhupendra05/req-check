"""Pydantic models for req-check — spec vs implementation verification."""
from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Status(str, Enum):
    satisfied = "satisfied"
    partial = "partial"
    not_satisfied = "not_satisfied"
    contradicted = "contradicted"
    untestable = "untestable"


class Requirement(BaseModel):
    """A single extracted requirement from the spec."""
    id: str                           # e.g. "REQ-001"
    text: str                         # the requirement statement
    source: str                       # which file/section it came from
    type: str = "functional"          # functional / non-functional / constraint


class Finding(BaseModel):
    """Verification result for a single requirement."""
    requirement: Requirement
    status: Status
    confidence: float                 # 0.0 – 1.0
    reasoning: str                    # why this status
    evidence: list[str] = Field(default_factory=list)   # code refs supporting verdict
    gaps: list[str] = Field(default_factory=list)       # what's missing
    suggestions: list[str] = Field(default_factory=list)  # how to close gaps


class VerificationReport(BaseModel):
    """Full report of spec-to-code verification."""
    spec_summary: str
    total_requirements: int
    satisfied: int
    partial: int
    not_satisfied: int
    contradicted: int
    untestable: int
    overall_coverage: float           # 0.0 – 1.0
    findings: list[Finding]
    critical_gaps: list[str]          # the most important things missing
    thinking_excerpt: Optional[str] = None
