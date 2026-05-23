# req-check 📋

> **Does your code actually do what the spec says?** Feed `req-check` a specification + your codebase — Claude Opus 4.7's extended thinking extracts every requirement, verifies each one against the actual implementation, and tells you exactly what's missing.

[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org)
[![Built on Claude Opus 4.7](https://img.shields.io/badge/built_on-Claude_Opus_4.7-9F5EFA)](https://www.anthropic.com)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## The problem

Specs drift. You write a PRD in January. Six engineers ship code through June. By July, no one knows what the spec actually said — let alone whether the code matches it.

The usual results:
- **Silent gaps:** "Wait, we never built the email notification?"
- **Silent contradictions:** Code does the opposite of what the spec said
- **Audit hell:** Compliance asks "where do you satisfy requirement 4.2?" and nobody can answer
- **Wasted refactors:** Engineers rewrite features that were already in the spec, just not where they looked

Traditional tools can't help. A linter checks syntax. A test suite checks the behaviors *you remembered to test*. Neither verifies whether your code matches your written requirements.

**That's what `req-check` is for.**

## What it does

```bash
req-check verify --spec spec.md --code ./src
```

In one Opus 4.7 extended-thinking pass, `req-check`:

1. **Extracts** every testable requirement from your spec (REQ-001, REQ-002, …)
2. **Scans** your codebase (skips node_modules, .git, etc.)
3. **Verifies** each requirement against the actual code with one of 5 verdicts
4. **Reports** evidence (file:line), gaps, and suggestions to close them

| Verdict | Meaning |
|---------|---------|
| ✅ **satisfied** | Code clearly implements this |
| 🟡 **partial** | Some cases handled, not all |
| ❌ **not_satisfied** | No implementation found |
| ⛔ **contradicted** | Code does the opposite |
| ❓ **untestable** | Can't tell from code alone (e.g. UX requirements) |

## Demo

Given `spec.md` describing a URL shortener and `./sample_impl/main.py` (which intentionally misses several features), `req-check` outputs:

```
╔══════════════════════════════════════════════════════════════╗
║  📋 REQ-CHECK REPORT                                         ║
║                                                              ║
║  URL shortener service that turns long URLs into shareable   ║
║  short codes with optional analytics and expiration.         ║
║                                                              ║
║  Coverage: 33% (3/9 requirements satisfied)                  ║
║    ✅ Satisfied:     3                                       ║
║    🟡 Partial:       0                                       ║
║    ❌ Missing:       5                                       ║
║    ⛔ Contradicted:  1                                       ║
║    ❓ Untestable:    0                                       ║
╚══════════════════════════════════════════════════════════════╝

ID       Status        Conf.  Requirement                  Why
─────────────────────────────────────────────────────────────────────────────
REQ-1    ✅ satisfied  95%    POST /shorten returns code   main.py:24-30 shortens
REQ-2    ✅ satisfied  95%    GET /<code> redirects 302    main.py:33-38 uses 302
REQ-3    ❌ not_sat    98%    Dedup same URL → same code   Every call generates new code
REQ-4    ❌ not_sat    99%    Custom alias support         No alias param in request
REQ-5    ❌ not_sat    99%    GET /<code>/stats analytics  No stats endpoint
REQ-6    ❌ not_sat    99%    Optional expiration / 410    No TTL logic
REQ-9    ⛔ contradict 99%    Must use Postgres            Uses in-memory dict
...

🚨 Critical Gaps
  • REQ-9 contradicted: in-memory storage will lose all data on restart
  • REQ-7 (rate limiting) missing — service is vulnerable to abuse
  • REQ-5 (analytics) missing — core feature for the product
```

## Why extended thinking matters

Surface-level matching fails. A function named `verify_password` might not actually verify the password. Extended thinking lets Opus 4.7:

- **Read what the code DOES**, not what it's named
- **Trace control flow** to confirm the requirement is actually exercised
- **Find partial implementations** ("password reset endpoint exists, but never sends the email")
- **Detect contradictions** ("spec says must use Postgres, code uses in-memory dict")

A smaller model approves features that *look* implemented. Opus 4.7 actually reads the code.

## Install

```bash
pip install req-check
export ANTHROPIC_API_KEY=sk-ant-...
```

## Usage

### CLI

```bash
# Basic
req-check verify --spec spec.md --code ./src

# Markdown output → drop into PR description
req-check verify -s PRD.md -c . --output markdown > coverage.md

# JSON output → integrate with dashboards
req-check verify -s spec.md -c ./src --output json | jq '.findings[] | select(.status != "satisfied")'

# CI mode — exit non-zero if anything is missing or contradicted
req-check verify --spec spec.md --code ./src --strict

# Larger codebases — bump the char limit
req-check verify -s spec.md -c ./src --max-code-chars 100000

# Deeper analysis (more thinking tokens)
req-check verify -s spec.md -c ./src --thinking-budget 20000
```

### Python

```python
from anthropic import Anthropic
from reqcheck import verify, scan_codebase, format_codebase
from reqcheck.report import print_terminal

spec = open("spec.md").read()
files = scan_codebase("./src")
codebase = format_codebase(files)

report = verify(spec, codebase, Anthropic(), thinking_budget=12000)

print_terminal(report)

# Or access structured data
for f in report.findings:
    if f.status.value in ("not_satisfied", "contradicted"):
        print(f"❌ {f.requirement.id}: {f.requirement.text}")
        for gap in f.gaps:
            print(f"   gap: {gap}")
```

### GitHub Action

```yaml
# .github/workflows/spec-check.yml
- name: Verify code matches spec
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: |
    pip install req-check
    req-check verify --spec docs/spec.md --code ./src --strict
```

The `--strict` flag exits non-zero when any requirement is missing or contradicted, failing the PR.

## Use cases

| Scenario | What req-check catches |
|----------|------------------------|
| **PRD → MVP** | Features the spec required but no one built |
| **Compliance audit** | Map every SOC 2/HIPAA requirement to actual code |
| **Acceptance review** | Catch silent gaps before client demo |
| **Refactor safety** | Verify the rewrite still satisfies the original spec |
| **Vendor delivery** | Audit contractor code against the statement of work |
| **API contract verification** | OpenAPI spec → actual handler behavior |

## Architecture

```
req-check/
├── cli.py          # Click CLI — req-check verify
├── verifier.py     # Opus 4.7 extended thinking orchestrator
├── scanner.py      # Codebase walker (skips node_modules, etc.)
├── types.py        # Pydantic models (Requirement, Finding, Report)
└── report.py       # Rich terminal + Markdown output
```

The whole pipeline is one Opus 4.7 call with extended thinking — model extracts requirements, reads code, reasons about each verdict in thinking blocks, and emits structured JSON. No multi-step orchestration, no chain-of-prompts — extended thinking IS the orchestration.

## Supported languages

Scanner reads: `.py .js .ts .tsx .jsx .go .rs .java .kt .rb .php .c .cpp .h .hpp .cs .sql .graphql .proto .yaml .yml .json .toml`

Add more by editing `scanner.py:_CODE_EXTENSIONS`.

## License

MIT © [bhupendra05](https://github.com/bhupendra05)

---

*Built because every "is this done?" review meeting wastes an hour. Now you get the answer in 30 seconds — with evidence.*
