#!/usr/bin/env bash
# CI del marketplace. El mismo script corre en local y en GitHub Actions.
# Uso: bash scripts/ci.sh            # validación propia + tests de hooks + shellcheck si está
#      bash scripts/ci.sh --claude   # además `claude plugin validate .` (usa npx si no hay claude)
set -uo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root" || exit 1

with_claude=0
[ "${1:-}" = "--claude" ] && with_claude=1

PY=""
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(sys.version_info < (3, 8))' >/dev/null 2>&1; then
    PY=$c; break
  fi
done
[ -n "$PY" ] || { echo "Falta Python 3.8+"; exit 1; }
export PY

failed=()
group() { if [ -n "${GITHUB_ACTIONS:-}" ]; then echo "::group::$1"; else echo; echo "== $1"; fi; }
endgroup() { [ -n "${GITHUB_ACTIONS:-}" ] && echo "::endgroup::"; return 0; }
step() {
  local name=$1; shift
  group "$name"
  if "$@"; then endgroup; echo "OK     $name"
  else endgroup; echo "FALLO  $name"; failed+=("$name"); fi
}
skip() { echo; echo "SALTO  $1"; }

step "Estructura del marketplace" "$PY" scripts/checks/validate.py
step "Versión de plugins cambiados" "$PY" scripts/checks/versions.py
step "Tests de hooks" bash scripts/tests/hooks.sh
step "Sintaxis bash" bash -c 'for f in $(find . -name "*.sh" -not -path "./.git/*"); do bash -n "$f" || exit 1; done'

if command -v shellcheck >/dev/null 2>&1; then
  step "shellcheck" bash -c 'find . -name "*.sh" -not -path "./.git/*" -print0 | xargs -0 shellcheck -S warning'
else
  skip "shellcheck (no instalado; en GitHub Actions sí corre)"
fi

if [ "$with_claude" = 1 ]; then
  if command -v claude >/dev/null 2>&1; then
    claude_cmd=(claude)
  elif command -v npx >/dev/null 2>&1; then
    claude_cmd=(npx -y @anthropic-ai/claude-code)
  else
    claude_cmd=()
    echo "FALLO  claude plugin validate: no hay claude ni npx"; failed+=("claude plugin validate")
  fi
  if [ ${#claude_cmd[@]} -gt 0 ]; then
    step "claude plugin validate (marketplace)" "${claude_cmd[@]}" plugin validate .
    for p in plugins/*/; do
      step "claude plugin validate ($p)" "${claude_cmd[@]}" plugin validate "$p"
    done
  fi
else
  skip "claude plugin validate (usa --claude)"
fi

echo
if [ ${#failed[@]} -eq 0 ]; then echo "CI OK"; exit 0; fi
echo "CI FALLÓ: ${failed[*]}"
exit 1
