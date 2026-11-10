#!/usr/bin/env python3
"""Exige subir `version` en plugin.json cuando cambia un plugin local del marketplace.

Claude Code solo entrega una copia nueva de un plugin cuando cambia su `version`. Un cambio sin
subirla no llega a quien ya lo tiene instalado, y quien instala de cero recibe otro contenido
con la misma etiqueta.

Compara el árbol de trabajo (incluye cambios sin commitear) con una base:
  1. el argumento, si se pasa;
  2. la variable VERSION_BASE (la define ci.yml: base del PR o commit anterior del push);
  3. si no, el merge-base de HEAD con origin/main.

Uso: python scripts/checks/versions.py [base]
Para subir una versión: python scripts/bump-version.py <plugin> [patch|minor|major]
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
errors = []


def git(*args, check=True):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r


def resolve_base():
    for candidate in (sys.argv[1] if len(sys.argv) > 1 else "", os.environ.get("VERSION_BASE", "")):
        candidate = candidate.strip()
        if candidate and set(candidate) != {"0"}:
            return candidate
    r = git("merge-base", "HEAD", "origin/main", check=False)
    return r.stdout.strip() if r.returncode == 0 else ""


def local_plugins():
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    for p in market.get("plugins", []):
        if isinstance(p.get("source"), str):
            yield p["name"], strip_prefix(p["source"], "./").rstrip("/")


def strip_prefix(text, prefix):
    return text[len(prefix):] if text.startswith(prefix) else text


def parse(version):
    m = SEMVER.match(version or "")
    return tuple(int(x) for x in m.groups()) if m else None


def changed(base, path):
    diff = git("diff", "--name-only", base, "--", path).stdout.splitlines()
    untracked = git("ls-files", "--others", "--exclude-standard", "--", path).stdout.splitlines()
    return diff + untracked


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    base = resolve_base()
    if not base or git("cat-file", "-e", f"{base}^{{commit}}", check=False).returncode != 0:
        print(f"versions.py: sin base para comparar ({base or 'no hay origin/main'}); se omite")
        return 0
    short = git("rev-parse", "--short", base).stdout.strip()

    for name, path in local_plugins():
        manifest = f"{path}/.claude-plugin/plugin.json"
        now = json.loads((ROOT / manifest).read_text(encoding="utf-8")).get("version")
        if parse(now) is None:
            errors.append(f"{name}: plugin.json sin version semver ('{now}'); sin ella cada push "
                          "llega a todos los usuarios")
            continue
        old_raw = git("show", f"{base}:{manifest}", check=False)
        if old_raw.returncode != 0:
            continue  # plugin nuevo respecto a la base
        before = json.loads(old_raw.stdout).get("version")
        files = changed(base, path)
        if not files:
            continue
        if parse(before) is not None and parse(now) <= parse(before):
            sample = ", ".join(strip_prefix(f, path + "/") for f in files[:3])
            more = f" y {len(files) - 3} más" if len(files) > 3 else ""
            errors.append(f"{name}: cambió ({sample}{more}) y su version {now} no es mayor que "
                          f"la de la base {short} ({before}). Súbela: "
                          f"python scripts/bump-version.py {name} patch")
        else:
            print(f"ok     {name}: {before} -> {now}")

    for e in errors:
        print(f"ERROR  {e}")
    print(f"versions.py: base {short}, {len(errors)} error(es)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
