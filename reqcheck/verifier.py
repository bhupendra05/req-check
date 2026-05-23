"""Core verifier — uses Opus 4.7 extended thinking to verify spec against code."""
from __future__ import annotations

import json
from typing import Optional

import anthropic

from reqcheck.types import (
    Finding, Requirement, Status, VerificationReport,
)

_MODEL = "claude-opus-4-7"

_SYSTEM = """\
You are a rigorous software auditor. Your job is to verify whether a codebase actually implements
the requirements stated in a specification document.

You will receive:
1. A SPECIFICATION — natural language requirements, PRD, RFC, or contract
2. A CODEBASE — the actual implementation

Your task has two phases:

PHASE 1 — EXTRACT REQUIREMENTS
Read the spec carefully. Extract every testable requirement as a list. Give each one a stable
ID (REQ-001, REQ-002, ...). Distinguish:
  - functional: "the system shall do X"
  - non-functional: "response time < 100ms"
  - constraint: "must use Postgres"

PHASE 2 — VERIFY EACH REQUIREMENT
For each requirement, examine the code carefully and decide:
  - satisfied:        code clearly implements this
  - partial:          partially implemented or only for some cases
  - not_satisfied:    no implementation found
  - contradicted:     code does something opposite/incompatible
  - untestable:       cannot determine from code alone (e.g. UX requirement)

For each verdict, cite SPECIFIC evidence from the code (file:line ranges, function names).
Reason carefully. Don't assume implementation exists just because a function is named after it —
look at what the code actually does.

Think deeply. A requirement like "users must be able to reset their password via email" requires
checking that (a) reset endpoint exists, (b) it sends email, (c) it validates the token, (d) it
actually updates the password. Missing ANY step means partial or not_satisfied.

Return ONLY valid JSON matching this schema:
{
  "spec_summary": "string — 2-3 sentence summary of what spec describes",
  "findings": [
    {
      "requirement": {
        "id": "REQ-001",
        "text": "string",
        "source": "section / filename",
        "type": "functional | non-functional | constraint"
      },
      "status": "satisfied | partial | not_satisfied | contradicted | untestable",
      "confidence": 0.0,
      "reasoning": "string — why this verdict",
      "evidence": ["file.py:42-50 — function name does X"],
      "gaps": ["specific missing piece"],
      "suggestions": ["how to close the gap"]
    }
  ],
  "critical_gaps": ["the 2-3 most important missing things"]
}
"""


def _build_prompt(spec_text: str, codebase: str) -> str:
    return f"""\
## SPECIFICATION

{spec_text}

---

## CODEBASE

{codebase}

---

Extract every testable requirement from the spec. Then verify each one against the code.
For each finding, cite specific code evidence. Use extended thinking to reason carefully —
don't assume a function does what its name suggests, read the actual implementation.
"""


def verify(
    spec_text: str,
    codebase: str,
    client: anthropic.Anthropic,
    thinking_budget: int = 12000,
    model: str = _MODEL,
) -> VerificationReport:
    """Verify a codebase against a spec. Returns structured findings."""
    prompt = _build_prompt(spec_text, codebase)

    response = client.messages.create(
        model=model,
        max_tokens=thinking_budget + 6000,
        thinking={"type": "enabled", "budget_tokens": thinking_budget},
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    thinking_text: Optional[str] = None
    result_text = ""
    for block in response.content:
        if block.type == "thinking":
            full = block.thinking
            thinking_text = full[:600] + "..." if len(full) > 600 else full
        elif block.type == "text":
            result_text = block.text

    raw = result_text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    data = json.loads(raw)

    findings: list[Finding] = []
    for f in data.get("findings", []):
        req = Requirement(**f["requirement"])
        findings.append(Finding(
            requirement=req,
            status=Status(f["status"]),
            confidence=float(f.get("confidence", 0.5)),
            reasoning=f.get("reasoning", ""),
            evidence=f.get("evidence", []),
            gaps=f.get("gaps", []),
            suggestions=f.get("suggestions", []),
        ))

    counts = {s: 0 for s in Status}
    for f in findings:
        counts[f.status] += 1

    total = len(findings)
    coverage = counts[Status.satisfied] / total if total > 0 else 0.0

    return VerificationReport(
        spec_summary=data.get("spec_summary", ""),
        total_requirements=total,
        satisfied=counts[Status.satisfied],
        partial=counts[Status.partial],
        not_satisfied=counts[Status.not_satisfied],
        contradicted=counts[Status.contradicted],
        untestable=counts[Status.untestable],
        overall_coverage=coverage,
        findings=findings,
        critical_gaps=data.get("critical_gaps", []),
        thinking_excerpt=thinking_text,
    )
