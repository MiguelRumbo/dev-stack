#!/usr/bin/env python3
"""Sube la `version` de un plugin local en su plugin.json, sin tocar el resto del formato.

Uso (desde cualquier carpeta):
  python scripts/bump-version.py <plugin> [patch|minor|major]   # por defecto patch
  python scripts/bump-version.py <plugin> --if-changed

--if-changed (lo usa sync-vendored.sh): sube patch solo si el plugin difiere de HEAD y su
version sigue igual que en HEAD. Así se puede repetir sin subir dos veces.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = re.compile(r'("version"\s*:\s*")(\d+)\.(\d+)\.(\d+)(")')


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("-") or len(args) > 2:
        print(__doc__.strip())
        return 2
    name, mode = args[0], (args[1] if len(args) > 1 else "patch")
    if mode not in ("patch", "minor", "major", "--if-changed"):
        print(f"Modo desconocido: {mode}")
        return 2
    rel = f"plugins/{name}/.claude-plugin/plugin.json"
    manifest = ROOT / rel
    if not manifest.exists():
        print(f"No existe {rel}")
        return 1
    text = manifest.read_bytes().decode("utf-8")
    m = VERSION.search(text)
    if not m:
        print(f"{rel}: sin \"version\": \"X.Y.Z\"")
        return 1
    major, minor, patch = (int(m.group(i)) for i in (2, 3, 4))
    current = f"{major}.{minor}.{patch}"

    if mode == "--if-changed":
        dirty = git("status", "--porcelain", "--", f"plugins/{name}").stdout.strip()
        head = VERSION.search(git("show", f"HEAD:{rel}").stdout or "")
        head_version = ".".join(head.group(i) for i in (2, 3, 4)) if head else None
        if not dirty or head_version != current:
            print(f"{name}: {current} (sin cambios que versionar)")
            return 0
        mode = "patch"

    if mode == "major":
        major, minor, patch = major + 1, 0, 0
    elif mode == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    new = f"{major}.{minor}.{patch}"
    text = text[:m.start()] + f"{m.group(1)}{new}{m.group(5)}" + text[m.end():]
    manifest.write_bytes(text.encode("utf-8"))
    print(f"{name}: {current} -> {new}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
