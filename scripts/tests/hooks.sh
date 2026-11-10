#!/usr/bin/env bash
# Pruebas de los hooks de metodo en repos temporales. Uso: bash scripts/tests/hooks.sh
set -u
root=$(cd "$(dirname "$0")/../.." && pwd)
hooks="$root/plugins/metodo/hooks"
py=${PY:-python3}
pass=0
fail=0

check() {
  local name=$1 cond=$2
  if [ "$cond" = 0 ]; then pass=$((pass + 1)); echo "  ok    $name"
  else fail=$((fail + 1)); echo "  FALLO $name"; fi
}

valid_json() { printf '%s' "$1" | "$py" -c 'import json,sys; json.load(sys.stdin)' 2>/dev/null; }
contains() { case "$1" in *"$2"*) return 0 ;; *) return 1 ;; esac; }
empty() { [ -z "$1" ]; }

new_repo() {
  local d
  d=$(mktemp -d)
  git -C "$d" init -q
  git -C "$d" config user.name ci
  git -C "$d" config user.email ci@example.com
  git -C "$d" config core.autocrlf false
  echo "$d"
}

echo "session-start.sh"
d=$(mktemp -d)
out=$(cd "$d" && bash "$hooks/session-start.sh")
valid_json "$out"; check "sin docs: JSON válido" $?
contains "$out" "/metodo:init"; check "sin docs: propone /metodo:init" $?
contains "$out" "sin definir"; check "sin CLAUDE.md: pide modo de comentarios" $?

mkdir -p "$d/docs"
printf '# B\n\n## 2026-01-01 — uno\n\n## 2026-01-02 — dos "con comillas"\n' > "$d/docs/BITACORA.md"
printf '# P\nUsa dev-stack.\n- **Comentarios en código:** completos\n' > "$d/CLAUDE.md"
out=$(cd "$d" && bash "$hooks/session-start.sh")
valid_json "$out"; check "con bitácora y comillas: JSON válido" $?
contains "$out" "dos"; check "con bitácora: incluye últimas entradas" $?
contains "$out" "comentarios en codigo: completos"; check "lee el modo de comentarios de CLAUDE.md" $?

printf '# B\n\n## Índice\n\n## 2026-01-01 — uno\n\n## 2026-01-02 — dos\n\n## Archivo histórico\n\n- 2025-Q4\n' > "$d/docs/BITACORA.md"
out=$(cd "$d" && bash "$hooks/session-start.sh")
contains "$out" "uno" && contains "$out" "dos"; check "bitácora: toma las 2 últimas entradas con fecha" $?
! contains "$out" "Archivo" && ! contains "$out" "Índice"; check "bitácora: ignora títulos ## sin fecha" $?
rm -rf "$d"

echo "stop-check.sh"
d=$(mktemp -d)
out=$(cd "$d" && echo '{}' | bash "$hooks/stop-check.sh")
empty "$out"; check "fuera de git: silencio" $?
rm -rf "$d"

d=$(new_repo)
mkdir -p "$d/docs/modulos" "$d/src"
echo x > "$d/docs/BITACORA.md"; echo a > "$d/src/mi archivo.ts"
git -C "$d" add -A && git -C "$d" commit -qm init

echo b >> "$d/src/mi archivo.ts"
out=$(cd "$d" && echo '{}' | bash "$hooks/stop-check.sh")
valid_json "$out" && contains "$out" "systemMessage"; check "código sin docs: avisa" $?

out=$(cd "$d" && echo '{"stop_hook_active":true}' | bash "$hooks/stop-check.sh")
empty "$out"; check "stop_hook_active: no repite el aviso" $?

echo y >> "$d/docs/BITACORA.md"
out=$(cd "$d" && echo '{}' | bash "$hooks/stop-check.sh")
empty "$out"; check "código con bitácora: silencio" $?

git -C "$d" checkout -q -- . && git -C "$d" mv "src/mi archivo.ts" "src/otro nombre.ts"
out=$(cd "$d" && echo '{}' | bash "$hooks/stop-check.sh")
contains "$out" "systemMessage"; check "renombre con espacios: avisa" $?

git -C "$d" reset -q --hard && echo z >> "$d/README.md"
out=$(cd "$d" && echo '{}' | bash "$hooks/stop-check.sh")
empty "$out"; check "solo .md cambiado: silencio" $?
rm -rf "$d"

echo "hooks.sh: $pass ok, $fail fallo(s)"
[ "$fail" = 0 ]
