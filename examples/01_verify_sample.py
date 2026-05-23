"""Example: verify the intentionally-incomplete sample impl against the spec."""
from pathlib import Path
import anthropic

from reqcheck import verify, scan_codebase, format_codebase
from reqcheck.report import print_terminal

HERE = Path(__file__).parent

spec = (HERE / "spec.md").read_text()
files = scan_codebase(str(HERE / "sample_impl"))
codebase = format_codebase(files)

client = anthropic.Anthropic()
report = verify(spec, codebase, client, thinking_budget=10000)

print_terminal(report)
