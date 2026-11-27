#!/usr/bin/env python3
"""Fija y actualiza las versiones (sha) de los plugins de terceros y de las copias vendorizadas.

Uso (desde la raíz del repo):
  python scripts/update-pins.py                 # solo informa qué se puede actualizar
  python scripts/update-pins.py --apply         # escribe los sha nuevos
  python scripts/update-pins.py --apply --report informe.md

Después de --apply: `bash scripts/sync-vendored.sh` (si cambió algo vendorizado) y
`bash scripts/ci.sh`. El informe lista, por cada dependencia que cambia, archivos con riesgo
(hooks, scripts, MCP, package.json), líneas añadidas sospechosas y skills nuevas o quitadas.
Es para que una persona decida el merge; no aprueba nada por sí solo.
"""
import argparse
import datetime
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
VENDORED = ROOT / "scripts" / "vendored.lock"
PINS_DOC = ROOT / "docs" / "PINS.md"

IGNORED_PATH = re.compile(
    r"(^|/)(tests?|__tests__|\.github|docs|examples?)/"
    r"|^\.(?!claude-plugin/|mcp\.json$)[^/]+/"
)
AUTO_RUN_PATH = re.compile(r"(^|/)(hooks/|\.claude-plugin/|\.mcp\.json$|settings\.json$)")
RISKY_PATH = re.compile(
    r"(^|/)(hooks/|bin/|scripts/|\.mcp\.json$|package\.json$|plugin\.json$|settings\.json$)"
    r"|\.(sh|bash|js|mjs|cjs|ts|py|ps1|exe|bat|cmd)$"
)
SUSPICIOUS_CODE = re.compile(
    r"curl |wget |Invoke-WebRequest|Invoke-RestMethod|fetch\(|https?://|base64|eval\(|exec\("
    r"|child_process|subprocess|os\.system|rm -rf|chmod \+x|\.ssh|webhook"
    # En mayúsculas: "token" en minúsculas es casi siempre un design token y llenaba el informe.
    r"|(?-i:API_KEY|TOKEN|SECRET)",
    re.IGNORECASE,
)
# Campos de un hook "type": "command" que Claude Code reconoce (https://code.claude.com/docs/en/hooks).
# Los demás (env, windows, powershell… de otros agentes) los ignora y claude.ai avisa al sincronizar.
COMMAND_HOOK_FIELDS = {"type", "command", "args", "async", "asyncRewake", "shell", "onFailure",
                       "if", "timeout", "statusMessage", "once"}
COMPONENT_FIELDS = {"commands", "agents", "skills", "hooks", "outputStyles", "themes",
                    "mcpServers", "lspServers"}
# Repo vendorizado -> plugin de este repo que lo copia (scripts/sync-vendored.sh). El informe
# solo mira las skills que de verdad se copian; el resto del repo no llega a nadie.
VENDORED_INTO = {"anthropics/skills": "frontend-design", "emilkowalski/skill": "emil-design-eng"}
SUSPICIOUS_PROMPT = re.compile(
    r"ignore (all |any )?(previous|prior) instructions|ignora (las )?instrucciones"
    r"|do not (tell|inform) the user|no (le )?digas al usuario|without (asking|telling)"
    r"|exfiltrat|send .{0,40}(to|a) https?://",
    re.IGNORECASE,
)


def git(*args, cwd=None):
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    ).stdout


def repo_url(spec):
    return spec if "://" in spec else f"https://github.com/{spec}"


def remote_head(url):
    return git("ls-remote", url, "HEAD").split()[0]


def latest_tag_at(clone, sha):
    try:
        return git("describe", "--tags", "--abbrev=0", sha, cwd=clone).strip()
    except subprocess.CalledProcessError:
        return ""


def external_plugins(market):
    for p in market["plugins"]:
        src = p["source"]
        if isinstance(src, dict) and src.get("source") in ("github", "git-subdir", "url"):
            spec = src.get("repo") or src.get("url")
            yield p, src, spec, src.get("path", "")


def vendored_scope(repo):
    """Rutas upstream que sync-vendored.sh copia: las skills que tiene el plugin local + LICENSE."""
    plugin = VENDORED_INTO.get(repo)
    skills = ROOT / "plugins" / plugin / "skills" if plugin else None
    if not skills or not skills.is_dir():
        return []
    return ["LICENSE"] + [f"skills/{d.name}" for d in sorted(skills.iterdir()) if d.is_dir()]


def show(clone, sha, path):
    r = subprocess.run(["git", "show", f"{sha}:{path}"], cwd=clone, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else None


def unknown_hook_fields(clone, sha, base):
    raw = show(clone, sha, f"{base}hooks/hooks.json")
    if raw is None:
        return set()
    try:
        events = json.loads(raw).get("hooks", {})
    except (ValueError, AttributeError):
        return {"(hooks.json no es JSON válido)"}
    return {key for groups in events.values() for group in groups
            for hook in group.get("hooks", []) if hook.get("type") == "command"
            for key in set(hook) - COMMAND_HOOK_FIELDS}


def sync_checks(clone, old, new, subpath, entry):
    """Lo que la versión nueva rompe o hace avisar al cargarla en Claude Code o claude.ai."""
    out = []
    base = f"{subpath.strip('/')}/" if subpath else ""
    inline = sorted(COMPONENT_FIELDS & set(entry))
    if inline and entry.get("strict") is False and show(clone, new, f"{base}.claude-plugin/plugin.json") is not None:
        out.append(f"- 🚨 Upstream ya trae `.claude-plugin/plugin.json` y la entrada declara "
                   f"{', '.join(inline)} con `\"strict\": false`: el plugin no cargará (manifiestos "
                   "en conflicto). Quita esos campos y `strict` de la entrada.")
    added = unknown_hook_fields(clone, new, base) - (unknown_hook_fields(clone, old, base) if old else set())
    if added:
        out.append("- ℹ️ Campos de hook que Claude Code ignora y claude.ai marca al sincronizar "
                   f"(el hook corre igual con `command`): {', '.join(f'`{k}`' for k in sorted(added))}")
    return out


def read_vendored():
    if not VENDORED.exists():
        return {}
    pins = {}
    for line in VENDORED.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            repo, sha = line.split()
            pins[repo] = sha
    return pins


def write_vendored(pins):
    lines = ["# repo sha  (lo escribe scripts/update-pins.py; lo lee scripts/sync-vendored.sh)"]
    lines += [f"{repo} {sha}" for repo, sha in pins.items()]
    VENDORED.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def analyze(url, old, new, paths, entry=None, subpath=""):
    """Clona sin blobs y compara old..new dentro de `paths` (vacío = todo el repo).

    `entry` es la entrada del marketplace (None para un repo vendorizado). Devuelve
    (tag, líneas de informe).
    """
    out = []
    with tempfile.TemporaryDirectory() as tmp:
        git("clone", "-q", "--filter=blob:none", "--no-checkout", url, tmp)
        tag = latest_tag_at(tmp, new)
        if entry is not None:
            out += sync_checks(tmp, old, new, subpath, entry)
        if not old:
            out.append("- Primera fijación: no hay versión anterior con la que comparar.")
            return tag, out
        scope = ["--", *paths] if paths else []
        try:
            changed = git("diff", "--name-status", old, new, *scope, cwd=tmp).splitlines()
        except subprocess.CalledProcessError:
            out.append(f"- ⚠️ No se pudo comparar {old[:7]}..{new[:7]} (¿historia reescrita upstream?). Revisar a mano.")
            return tag, out
        n = len(paths) - 1
        where = f" en lo vendorizado ({n} skill{'s' if n != 1 else ''} + LICENSE)" if entry is None and paths else ""
        out.append(f"- Archivos cambiados{where}: {len(changed)} · comparación: {url}/compare/{old[:12]}...{new[:12]}")
        if entry is None and paths:
            upstream = git("diff", "--name-status", "--diff-filter=A", old, new, "--",
                           "skills/*/SKILL.md", cwd=tmp).splitlines()
            for c in upstream:
                path = c.split(maxsplit=1)[1]
                if path.rsplit("/", 1)[0] not in paths:
                    out.append(f"- ℹ️ Skill nueva upstream, no vendorizada (añádela a "
                               f"`scripts/sync-vendored.sh` si la quieres): `{path}`")
        skills_added = [c for c in changed if c.startswith("A") and c.endswith("SKILL.md")]
        skills_removed = [c for c in changed if c.startswith("D") and c.endswith("SKILL.md")]
        for c in skills_added:
            out.append(f"- ➕ Skill nueva (más tokens en contexto): `{c.split(maxsplit=1)[1]}`")
        for c in skills_removed:
            out.append(f"- ➖ Skill quitada: `{c.split(maxsplit=1)[1]}`")
        paths = [c.split()[-1] for c in changed]
        relevant = [p for p in paths if not IGNORED_PATH.search(p)]
        auto = [p for p in relevant if AUTO_RUN_PATH.search(p)]
        risky = [p for p in relevant if RISKY_PATH.search(p) and p not in auto]
        for path in auto:
            out.append(f"- 🚨 Se ejecuta solo en Claude Code (hook/manifiesto/MCP): `{path}`")
        for path in risky[:20]:
            out.append(f"- ⚠️ Script o dependencia cambiada: `{path}`")
        if len(risky) > 20:
            out.append(f"- ⚠️ … y {len(risky) - 20} scripts más (ver comparación)")
        risky = auto + risky
        diff = git("diff", "--unified=0", old, new, *scope, cwd=tmp)
        current = ""
        hits = 0
        for line in diff.splitlines():
            if line.startswith("+++ "):
                current = line[6:]
                continue
            if not line.startswith("+") or hits >= 40:
                continue
            text = line[1:].strip()
            if IGNORED_PATH.search(current):
                continue
            is_md = current.endswith(".md")
            pattern = SUSPICIOUS_PROMPT if is_md else SUSPICIOUS_CODE
            if (is_md or RISKY_PATH.search(current)) and pattern.search(text):
                out.append(f"  - 🔎 `{current}`: `{text[:160]}`")
                hits += 1
        if not risky and not skills_added and hits == 0:
            out.append("- Sin cambios en hooks, scripts ni skills nuevas. Riesgo bajo.")
    return tag, out


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="escribir los sha nuevos")
    ap.add_argument("--report", help="ruta del informe Markdown")
    ap.add_argument("--only", help="actualizar solo esta dependencia (nombre de plugin o repo)")
    args = ap.parse_args()

    market = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    vendored = read_vendored()
    report = ["# Actualización de versiones fijadas", ""]
    rows = []
    changes = 0

    targets = [(p["name"], s, spec, sub, "plugin", p) for p, s, spec, sub in external_plugins(market)]
    targets += [(repo, None, repo, "", "vendorizado", None) for repo in vendored]

    for name, src, spec, subpath, kind, entry in targets:
        url = repo_url(spec)
        old = src.get("sha", "") if src is not None else vendored[name]
        try:
            new = remote_head(url)
        except subprocess.CalledProcessError as e:
            print(f"ERROR {name}: no se pudo leer {url}: {e.stderr.strip()}", file=sys.stderr)
            return 2
        wanted = args.only is None or args.only in (name, spec)
        if old == new or not wanted:
            print(f"= {name:18} {old[:12] or '(sin fijar)'}")
            rows.append((name, spec, kind, old, ""))
            continue
        changes += 1
        print(f"↑ {name:18} {old[:12] or '(sin fijar)'} -> {new[:12]}")
        paths = vendored_scope(name) if entry is None else ([subpath] if subpath else [])
        tag, lines = analyze(url, old, new, paths, entry, subpath)
        report += [f"## {name} ({kind})", f"`{old[:12] or '—'}` → `{new[:12]}` {tag}".rstrip(), ""] + lines + [""]
        rows.append((name, spec, kind, new if args.apply else old, tag))
        if args.apply:
            if src is not None:
                src["sha"] = new
            else:
                vendored[name] = new

    if changes == 0:
        report.append("Todo al día. Nada que actualizar.")

    if args.apply and changes:
        MARKETPLACE.write_text(json.dumps(market, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        write_vendored(vendored)
        today = datetime.date.today().isoformat()
        doc = [
            "# Versiones fijadas",
            "",
            f"Generado por `scripts/update-pins.py` el {today}. No editar a mano.",
            "",
            "| Dependencia | Repo | Tipo | sha | Tag |",
            "|---|---|---|---|---|",
        ]
        doc += [f"| {n} | {s} | {k} | `{sha[:12]}` | {t} |" for n, s, k, sha, t in rows]
        PINS_DOC.write_text("\n".join(doc) + "\n", encoding="utf-8", newline="\n")

    if args.report:
        Path(args.report).write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"{changes} dependencia(s) con versión nueva." + ("" if args.apply or not changes else " Usa --apply para escribirlas."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
