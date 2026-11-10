#!/usr/bin/env python3
"""Validación estructural del marketplace. Solo stdlib. Sale con 1 si hay errores.

Comprueba: JSON válido, manifiestos, fuentes externas fijadas a sha, skills con frontmatter
correcto, rutas de hooks y plantillas, referencias metodo:<skill>, y que las skills y
plantillas no lleven nombres personales escritos a mano.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHA = re.compile(r"^[0-9a-f]{40}$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
errors = []
warnings = []


def err(msg):
    errors.append(msg)


def rel(p):
    return p.relative_to(ROOT).as_posix()


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        err(f"{rel(path)}: JSON inválido ({e})")
        return None


def frontmatter(text):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fields, key = {}, None
    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            key = m.group(1)
            value = m.group(2).strip()
            fields[key] = "" if value in (">", "|", ">-", "|-") else value
        elif key and line.startswith((" ", "\t")):
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields


def check_skills(plugin_dir):
    names = set()
    for skill_md in sorted(plugin_dir.glob("skills/*/SKILL.md")):
        fm = frontmatter(skill_md.read_text(encoding="utf-8"))
        folder = skill_md.parent.name
        if fm is None:
            err(f"{rel(skill_md)}: falta frontmatter YAML")
            continue
        if fm.get("name") != folder:
            err(f"{rel(skill_md)}: name '{fm.get('name')}' no coincide con la carpeta '{folder}'")
        desc = fm.get("description", "")
        if not desc:
            err(f"{rel(skill_md)}: falta description")
        elif len(desc) > 1024:
            err(f"{rel(skill_md)}: description de {len(desc)} caracteres (máximo 1024)")
        names.add(folder)
    return names


def check_hooks(plugin_dir, manifest):
    hooks_ref = manifest.get("hooks")
    if not hooks_ref:
        return
    hooks_file = (plugin_dir / hooks_ref).resolve()
    data = load_json(hooks_file) if hooks_file.exists() else None
    if data is None:
        if not hooks_file.exists():
            err(f"{rel(plugin_dir)}: hooks apunta a {hooks_ref}, que no existe")
        return
    for event, groups in data.get("hooks", {}).items():
        for group in groups:
            for hook in group.get("hooks", []):
                for ref in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\"'\s]+)", hook.get("command", "")):
                    if not (plugin_dir / ref).exists():
                        err(f"{rel(hooks_file)}: {event} usa {ref}, que no existe")


def personal_words():
    words = set()
    market = load_json(ROOT / ".claude-plugin" / "marketplace.json") or {}
    sources = [market.get("owner", {}).get("name", "")]
    for manifest in ROOT.glob("plugins/*/.claude-plugin/plugin.json"):
        author = (load_json(manifest) or {}).get("author", {})
        sources.append(author.get("name", "") if isinstance(author, dict) else str(author))
    for s in sources:
        for w in re.findall(r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{3,}", s):
            words.add(w)
    return words - {"Anthropic", "Emil", "Kowalski", "Claude"}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for path in ROOT.rglob("*.json"):
        if ".git" not in path.parts and "node_modules" not in path.parts:
            load_json(path)

    market = load_json(ROOT / ".claude-plugin" / "marketplace.json")
    if market is None:
        return report()
    for field in ("name", "owner", "plugins"):
        if field not in market:
            err(f"marketplace.json: falta '{field}'")
    seen = set()
    skills_by_plugin = {}
    for p in market.get("plugins", []):
        name = p.get("name", "?")
        if name in seen:
            err(f"marketplace.json: plugin duplicado '{name}'")
        seen.add(name)
        if not p.get("description"):
            err(f"marketplace.json: '{name}' sin description")
        src = p.get("source")
        if isinstance(src, str):
            pdir = (ROOT / src).resolve()
            manifest_path = pdir / ".claude-plugin" / "plugin.json"
            if not manifest_path.exists():
                err(f"marketplace.json: '{name}' apunta a {src} sin .claude-plugin/plugin.json")
                continue
            manifest = load_json(manifest_path) or {}
            if manifest.get("name") != name:
                err(f"{rel(manifest_path)}: name '{manifest.get('name')}' ≠ '{name}' del marketplace")
            if "version" in manifest and not SEMVER.match(manifest["version"]):
                err(f"{rel(manifest_path)}: version '{manifest['version']}' no es semver")
            for lic in ("LICENSE",):
                if not (pdir / lic).exists():
                    err(f"{rel(pdir)}: falta {lic}")
            skills_by_plugin[name] = check_skills(pdir)
            check_hooks(pdir, manifest)
        elif isinstance(src, dict):
            kind = src.get("source")
            if kind not in ("github", "git-subdir", "url"):
                err(f"marketplace.json: '{name}' con source desconocido '{kind}'")
            if not SHA.match(src.get("sha", "")):
                err(f"marketplace.json: '{name}' no está fijado a un sha de 40 caracteres (python scripts/update-pins.py --apply)")
        else:
            err(f"marketplace.json: '{name}' sin source")

    vendored = ROOT / "scripts" / "vendored.lock"
    if vendored.exists():
        for line in vendored.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                parts = line.split()
                if len(parts) != 2 or not SHA.match(parts[1]):
                    err(f"scripts/vendored.lock: línea inválida '{line}'")

    metodo = ROOT / "plugins" / "metodo"
    if metodo.exists():
        own = skills_by_plugin.get("metodo", set())
        texts = list(metodo.rglob("*.md")) + list(metodo.rglob("*.sh"))
        for f in texts:
            for ref in re.findall(r"metodo:([a-z][a-z0-9-]*)", f.read_text(encoding="utf-8")):
                if ref not in own:
                    err(f"{rel(f)}: referencia a metodo:{ref}, skill que no existe")
        init = metodo / "skills" / "init" / "SKILL.md"
        if init.exists():
            for ref in set(re.findall(r"`(templates/[^`\s]+)`", init.read_text(encoding="utf-8"))):
                if not (metodo / ref).exists():
                    err(f"{rel(init)}: plantilla {ref} no existe")
        words = personal_words()
        for f in list(metodo.glob("skills/**/*.md")) + list(metodo.glob("templates/**/*.md")) + list(metodo.glob("hooks/*")):
            content = f.read_text(encoding="utf-8")
            for w in words:
                if re.search(rf"\b{re.escape(w)}\b", content):
                    err(f"{rel(f)}: contiene el nombre personal '{w}'; usa {{{{USUARIO}}}} o [nombre]")

    return report()


def report():
    for w in warnings:
        print(f"AVISO  {w}")
    for e in errors:
        print(f"ERROR  {e}")
    print(f"validate.py: {len(errors)} error(es), {len(warnings)} aviso(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
