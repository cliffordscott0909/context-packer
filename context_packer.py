"""Pack a project's source files into one LLM-ready prompt with a size estimate."""
import argparse
import fnmatch
import os
import sys

DEFAULT_IGNORES = [".git", "node_modules", "__pycache__", "*.pyc", "*.png", "*.jpg",
                   "*.zip", ".venv", "venv", "dist", "build", "*.lock"]


def is_ignored(rel_path, ignores):
    parts = rel_path.split(os.sep)
    return any(fnmatch.fnmatch(p, pat) for p in parts for pat in ignores)


def load_gitignore(root):
    """Read simple patterns from root/.gitignore (no negation or ** support)."""
    path = os.path.join(root, ".gitignore")
    if not os.path.isfile(path):
        return []
    pats = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith(("#", "!")):
                pats.append(line.strip("/"))
    return pats


def collect_files(root, ignores=None, extensions=None):
    """Return sorted relative paths of text files under root."""
    ignores = DEFAULT_IGNORES if ignores is None else ignores
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        dirnames[:] = [d for d in dirnames
                       if not is_ignored(os.path.join(rel_dir, d) if rel_dir != "." else d, ignores)]
        for name in filenames:
            rel = os.path.join(rel_dir, name) if rel_dir != "." else name
            if is_ignored(rel, ignores):
                continue
            if extensions and not any(name.endswith(e) for e in extensions):
                continue
            found.append(rel)
    return sorted(found)


def estimate_tokens(text):
    """Rough estimate: ~4 characters per token."""
    return (len(text) + 3) // 4


def pack(root, ignores=None, extensions=None, max_tokens=None, fmt="plain"):
    """Build the prompt text. Files that would exceed max_tokens are skipped."""
    chunks, skipped, used = [], [], 0
    for rel in collect_files(root, ignores, extensions):
        try:
            with open(os.path.join(root, rel), encoding="utf-8") as f:
                body = f.read()
        except (UnicodeDecodeError, OSError):
            skipped.append(rel)
            continue
        if fmt == "markdown":
            lang = os.path.splitext(rel)[1].lstrip(".")
            chunk = f"## {rel}\n\n```{lang}\n{body.rstrip(chr(10))}\n```\n\n"
        else:
            chunk = f"=== {rel} ===\n{body}\n"
        cost = estimate_tokens(chunk)
        if max_tokens is not None and used + cost > max_tokens:
            skipped.append(rel)
            continue
        used += cost
        chunks.append(chunk)
    return "".join(chunks), used, skipped


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", nargs="?", default=".")
    p.add_argument("-e", "--ext", action="append", help="only include this extension, e.g. .py")
    p.add_argument("-m", "--max-tokens", type=int, help="token budget")
    p.add_argument("-g", "--gitignore", action="store_true", help="also honor patterns in root .gitignore")
    p.add_argument("-f", "--format", choices=["plain", "markdown"], default="plain")
    p.add_argument("-o", "--output", help="write to file instead of stdout")
    a = p.parse_args(argv)
    ignores = DEFAULT_IGNORES + (load_gitignore(a.root) if a.gitignore else [])
    text, tokens, skipped = pack(a.root, ignores=ignores, extensions=a.ext,
                                 max_tokens=a.max_tokens, fmt=a.format)
    if a.output:
        with open(a.output, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        sys.stdout.write(text)
    print(f"~{tokens} tokens, {len(skipped)} file(s) skipped", file=sys.stderr)


if __name__ == "__main__":
    main()
