"""Output formatters — terminal + Markdown."""
from __future__ import annotations

from reqcheck.types import Status, VerificationReport

_STATUS_EMOJI = {
    Status.satisfied: "✅",
    Status.partial: "🟡",
    Status.not_satisfied: "❌",
    Status.contradicted: "⛔",
    Status.untestable: "❓",
}

_STATUS_COLOR = {
    Status.satisfied: "green",
    Status.partial: "yellow",
    Status.not_satisfied: "red",
    Status.contradicted: "bold red",
    Status.untestable: "dim",
}


def print_terminal(r: VerificationReport) -> None:
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich import box
        console = Console()
    except ImportError:
        print(to_markdown(r))
        return

    cov_color = "green" if r.overall_coverage >= 0.8 else "yellow" if r.overall_coverage >= 0.5 else "red"

    summary = (
        f"[bold]{r.spec_summary}[/bold]\n\n"
        f"[bold]Coverage:[/bold] [{cov_color}]{r.overall_coverage:.0%}[/{cov_color}] "
        f"({r.satisfied}/{r.total_requirements} requirements satisfied)\n\n"
        f"  ✅ Satisfied:     {r.satisfied}\n"
        f"  🟡 Partial:       {r.partial}\n"
        f"  ❌ Missing:       {r.not_satisfied}\n"
        f"  ⛔ Contradicted:  {r.contradicted}\n"
        f"  ❓ Untestable:    {r.untestable}"
    )
    console.print()
    console.print(Panel(summary, title="[bold blue]📋 REQ-CHECK REPORT[/bold blue]", border_style="blue", padding=(1, 2)))

    # Findings table
    t = Table(show_header=True, box=box.SIMPLE, header_style="bold blue", title="\nFindings")
    t.add_column("ID", width=8, style="dim")
    t.add_column("Status", width=8)
    t.add_column("Conf.", width=6)
    t.add_column("Requirement", width=40)
    t.add_column("Why", width=50)

    for f in r.findings:
        emoji = _STATUS_EMOJI.get(f.status, "?")
        color = _STATUS_COLOR.get(f.status, "white")
        t.add_row(
            f.requirement.id,
            f"[{color}]{emoji} {f.status.value[:8]}[/{color}]",
            f"{f.confidence:.0%}",
            f.requirement.text[:80],
            f"[dim]{f.reasoning[:100]}[/dim]",
        )
    console.print(t)

    # Detail blocks for gaps
    has_gaps = [f for f in r.findings if f.status in (Status.partial, Status.not_satisfied, Status.contradicted)]
    if has_gaps:
        console.print("\n[bold red]🔴 Gap Details[/bold red]\n")
        for f in has_gaps:
            color = _STATUS_COLOR.get(f.status, "white")
            lines = [f"[bold {color}]{f.requirement.id}[/bold {color}]: {f.requirement.text}"]
            if f.evidence:
                lines.append("\n[bold]Evidence:[/bold]")
                for ev in f.evidence:
                    lines.append(f"  → {ev}")
            if f.gaps:
                lines.append("\n[bold yellow]Gaps:[/bold yellow]")
                for g in f.gaps:
                    lines.append(f"  • {g}")
            if f.suggestions:
                lines.append("\n[bold green]Suggestions:[/bold green]")
                for s in f.suggestions:
                    lines.append(f"  ✚ {s}")
            console.print(Panel("\n".join(lines), border_style=color, padding=(1, 2)))

    if r.critical_gaps:
        console.print(Panel(
            "\n".join(f"  • {g}" for g in r.critical_gaps),
            title="[bold red]🚨 Critical Gaps[/bold red]",
            border_style="red", padding=(1, 2),
        ))

    if r.thinking_excerpt:
        console.print(Panel(
            f"[dim italic]{r.thinking_excerpt}[/dim italic]",
            title="[dim]🧠 Extended Thinking Excerpt[/dim]",
            border_style="dim", padding=(0, 1),
        ))
    console.print()


def to_markdown(r: VerificationReport) -> str:
    lines = [
        f"# req-check Report",
        f"\n{r.spec_summary}",
        f"\n**Coverage:** {r.overall_coverage:.0%} ({r.satisfied}/{r.total_requirements} satisfied)",
        f"\n| Status | Count |",
        f"|--------|-------|",
        f"| ✅ Satisfied | {r.satisfied} |",
        f"| 🟡 Partial | {r.partial} |",
        f"| ❌ Not satisfied | {r.not_satisfied} |",
        f"| ⛔ Contradicted | {r.contradicted} |",
        f"| ❓ Untestable | {r.untestable} |",
        f"\n## Findings\n",
    ]
    for f in r.findings:
        emoji = _STATUS_EMOJI.get(f.status, "?")
        lines.append(f"### {emoji} {f.requirement.id} — {f.requirement.text}")
        lines.append(f"\n**Status:** `{f.status.value}` · **Confidence:** {f.confidence:.0%}")
        lines.append(f"\n{f.reasoning}")
        if f.evidence:
            lines.append("\n**Evidence:**")
            for ev in f.evidence:
                lines.append(f"- {ev}")
        if f.gaps:
            lines.append("\n**Gaps:**")
            for g in f.gaps:
                lines.append(f"- {g}")
        if f.suggestions:
            lines.append("\n**Suggestions:**")
            for s in f.suggestions:
                lines.append(f"- {s}")

    if r.critical_gaps:
        lines.append("\n## 🚨 Critical Gaps\n")
        for g in r.critical_gaps:
            lines.append(f"- {g}")

    return "\n".join(lines)
