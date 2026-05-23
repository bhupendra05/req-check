"""Codebase scanner — collects relevant source files for verification."""
from __future__ import annotations

import os
from pathlib import Path

# Files to include — code we want the model to read
_CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".go", ".rs", ".java", ".kt", ".rb", ".php",
    ".c", ".cpp", ".h", ".hpp", ".cs",
    ".sql", ".graphql", ".proto",
    ".yaml", ".yml", ".json", ".toml",
}

# Directories to skip
_SKIP_DIRS = {
    "node_modules", ".git", "venv", ".venv", "__pycache__",
    "dist", "build", "target", ".next", ".pytest_cache",
    "site-packages", ".tox", "coverage", "htmlcov",
}

# Files to skip
_SKIP_FILES = {".DS_Store", "package-lock.json", "yarn.lock", "Cargo.lock", "poetry.lock"}


def scan_codebase(root: str, max_chars: int = 50_000) -> dict[str, str]:
    """Walk a codebase and return {relative_path: content}.

    Caps total characters so we stay within context limits.
    """
    root_path = Path(root).resolve()
    files: dict[str, str] = {}
    total = 0

    for dirpath, dirnames, filenames in os.walk(root_path):
        # In-place filter of subdirs
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]

        for fname in sorted(filenames):
            if fname in _SKIP_FILES:
                continue
            if fname.startswith("."):
                continue
            ext = Path(fname).suffix.lower()
            if ext not in _CODE_EXTENSIONS:
                continue

            fpath = Path(dirpath) / fname
            try:
                content = fpath.read_text(errors="replace")
            except (OSError, UnicodeDecodeError):
                continue

            # Cap per-file size
            if len(content) > 8000:
                content = content[:8000] + "\n... [truncated]"

            rel = str(fpath.relative_to(root_path))
            files[rel] = content
            total += len(content)

            if total >= max_chars:
                return files

    return files


def format_codebase(files: dict[str, str]) -> str:
    """Format the scanned files into a string for the prompt."""
    parts = []
    for path, content in sorted(files.items()):
        parts.append(f"--- {path} ---\n{content}\n")
    return "\n".join(parts)
