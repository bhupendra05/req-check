"""CLI — `req-check verify --spec spec.md --code ./src`."""
from __future__ import annotations

import sys
from pathlib import Path

import click


@click.group()
def main():
    """req-check — verify that your codebase implements your spec.

    Uses Claude Opus 4.7 extended thinking to extract requirements
    from a spec, then check each one against the actual code.
    """


@main.command()
@click.option("--spec", "-s", required=True, type=click.Path(exists=True), help="Specification file (markdown, txt, PDF text)")
@click.option("--code", "-c", required=True, type=click.Path(exists=True, file_okay=False), help="Codebase directory")
@click.option("--output", "-o", type=click.Choice(["terminal", "markdown", "json"]), default="terminal")
@click.option("--max-code-chars", default=50_000, show_default=True, help="Max chars of codebase to read")
@click.option("--thinking-budget", default=12000, show_default=True, help="Extended thinking token budget")
@click.option("--model", default="claude-opus-4-7", show_default=True)
@click.option("--strict", is_flag=True, help="Exit non-zero if any requirement is not_satisfied or contradicted (for CI)")
@click.option("--api-key", envvar="ANTHROPIC_API_KEY", help="Anthropic API key")
def verify(spec, code, output, max_code_chars, thinking_budget, model, strict, api_key):
    """Verify a codebase against a spec.

    \b
    Examples:
      req-check verify --spec spec.md --code ./src
      req-check verify -s PRD.md -c . --output markdown > coverage.md
      req-check verify -s spec.md -c ./src --strict   # for CI
    """
    if not api_key:
        click.echo("Error: ANTHROPIC_API_KEY not set", err=True)
        sys.exit(1)

    spec_text = Path(spec).read_text(errors="replace")

    click.echo(f"📂 Scanning codebase: {code}", err=True)
    from reqcheck.scanner import scan_codebase, format_codebase
    files = scan_codebase(code, max_chars=max_code_chars)
    click.echo(f"   Found {len(files)} code files", err=True)

    if not files:
        click.echo("Error: no code files found in codebase", err=True)
        sys.exit(1)

    codebase_text = format_codebase(files)

    click.echo("🔍 Verifying requirements with extended thinking...", err=True)

    import anthropic
    from reqcheck.verifier import verify as _verify
    from reqcheck.report import print_terminal, to_markdown

    client = anthropic.Anthropic(api_key=api_key)

    try:
        report = _verify(spec_text, codebase_text, client, thinking_budget=thinking_budget, model=model)
    except Exception as e:
        click.echo(f"Error during verification: {e}", err=True)
        sys.exit(1)

    if output == "terminal":
        print_terminal(report)
    elif output == "markdown":
        click.echo(to_markdown(report))
    elif output == "json":
        click.echo(report.model_dump_json(indent=2))

    if strict and (report.not_satisfied > 0 or report.contradicted > 0):
        sys.exit(1)


if __name__ == "__main__":
    main()
