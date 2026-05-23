"""Tests for the codebase scanner — no API key needed."""
import tempfile
from pathlib import Path

from reqcheck.scanner import scan_codebase, format_codebase


def test_scanner_finds_python_files():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a.py").write_text("def hello(): return 1\n")
        (root / "b.py").write_text("def world(): return 2\n")
        files = scan_codebase(str(root))
        assert "a.py" in files
        assert "b.py" in files
        assert "def hello" in files["a.py"]


def test_scanner_skips_node_modules():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "src").mkdir()
        (root / "src" / "main.py").write_text("# real code\n")
        (root / "node_modules").mkdir()
        (root / "node_modules" / "lib.js").write_text("// junk\n")
        files = scan_codebase(str(root))
        assert any("src/main.py" in k or "src\\main.py" in k for k in files)
        assert not any("node_modules" in k for k in files)


def test_scanner_skips_dot_files():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".env").write_text("SECRET=abc\n")
        (root / "main.py").write_text("# real\n")
        files = scan_codebase(str(root))
        assert "main.py" in files
        assert ".env" not in files


def test_format_codebase_includes_filenames():
    files = {"a.py": "x = 1", "b.py": "y = 2"}
    out = format_codebase(files)
    assert "--- a.py ---" in out
    assert "--- b.py ---" in out
    assert "x = 1" in out


def test_scanner_caps_total_chars():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        big_content = "x" * 5000
        for i in range(20):
            (root / f"file{i}.py").write_text(big_content)
        files = scan_codebase(str(root), max_chars=10_000)
        # should have stopped early
        assert len(files) < 20
