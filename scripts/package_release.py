"""Create a reviewed-source ZIP, excluding local credentials and run history."""

from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ("peerlab", "tests", "scripts", ".github", "examples", "docs")
FILES = ("README.md", "LICENSE", "CONTRIBUTING.md", "SECURITY.md", "pyproject.toml", ".gitignore", ".gitattributes", ".env.example")


def main():
    paths = [ROOT / name for name in FILES if (ROOT/name).is_file()]
    for name in DIRECTORIES:
        paths += [p for p in (ROOT/name).rglob("*") if p.is_file() and
                  not p.is_symlink() and "__pycache__" not in p.parts and
                  p.suffix not in (".pyc", ".pyo") and not p.name.startswith(".env")]
    secrets = []
    env = ROOT/".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8-sig").splitlines():
            key, _, value = line.partition("=")
            if key.strip().endswith("API_KEY") and value.strip() and not value.strip().startswith("your_"):
                secrets.append(value.strip().strip("\"'").encode())
    pattern = re.compile(rb"\bsk-[A-Za-z0-9_-]{20,}\b")
    for path in paths:
        if not path.resolve().is_relative_to(ROOT):
            raise SystemExit("Refusing a file outside the project.")
        raw = path.read_bytes()
        if pattern.search(raw) or any(secret in raw for secret in secrets):
            raise SystemExit(f"Possible API key in {path.relative_to(ROOT)}; packaging refused.")
    dest = ROOT/"dist"/"peerlab-ai-source.zip"
    dest.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(set(paths)):
            archive.write(path, Path("peerlab-ai")/path.relative_to(ROOT))
    print(f"Checked {len(set(paths))} source files. No API key detected.")
    print(f"Archive: {dest}")


if __name__ == "__main__":
    main()
