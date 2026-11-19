import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import context_packer as cp


def make(tmp_path):
    (tmp_path / "a.py").write_text("print('a')\n")
    (tmp_path / "b.md").write_text("# doc\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "x.js").write_text("x")
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "c.py").write_text("c = 1\n")
    (tmp_path / "img.png").write_bytes(b"\x89PNG")


def test_collect_ignores_defaults(tmp_path):
    make(tmp_path)
    assert cp.collect_files(str(tmp_path)) == ["a.py", "b.md", os.path.join("pkg", "c.py")]


def test_extension_filter(tmp_path):
    make(tmp_path)
    assert cp.collect_files(str(tmp_path), extensions=[".py"]) == ["a.py", os.path.join("pkg", "c.py")]


def test_pack_format_and_tokens(tmp_path):
    make(tmp_path)
    text, tokens, skipped = cp.pack(str(tmp_path), extensions=[".py"])
    assert "=== a.py ===\nprint('a')\n" in text
    assert tokens == cp.estimate_tokens(text) and skipped == []


def test_budget_skips_files(tmp_path):
    make(tmp_path)
    _, _, skipped = cp.pack(str(tmp_path), extensions=[".py"], max_tokens=8)
    assert skipped


def test_binary_file_skipped(tmp_path):
    (tmp_path / "bin.dat").write_bytes(b"\xff\xfe\x00\x81")
    _, _, skipped = cp.pack(str(tmp_path))
    assert skipped == ["bin.dat"]
