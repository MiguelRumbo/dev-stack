#!/usr/bin/env bash
# Stop: si hay cambios en codigo pero ni la bitacora ni ningun doc de modulo cambiaron,
# avisa. Solo informa (systemMessage); nunca bloquea.

set -u

command -v git >/dev/null 2>&1 || exit 0
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0
[ -f "docs/BITACORA.md" ] || exit 0

# Evitar bucle: si Claude ya fue avisado en esta parada, salir.
input=$(cat 2>/dev/null || true)
case "$input" in *'"stop_hook_active":true'*) exit 0 ;; esac

changed=$(git status --porcelain 2>/dev/null | cut -c4- | sed 's/.* -> //; s/^"//; s/"$//')
[ -n "$changed" ] || exit 0

code_changed=$(printf '%s\n' "$changed" | grep -v '^docs/' | grep -v -E '\.(md|txt|json|ya?ml|lock)$' | head -n 1)
[ -n "$code_changed" ] || exit 0

docs_changed=$(printf '%s\n' "$changed" | grep -E '^docs/(BITACORA\.md|modulos/)' | head -n 1)
[ -z "$docs_changed" ] || exit 0

msg="metodo: hay cambios en codigo sin cambios en docs/BITACORA.md ni en docs/modulos/. Antes de cerrar: actualiza el .md del modulo tocado y anade la entrada de bitacora (metodo:documentacion)."
esc=${msg//\"/\\\"}
printf '{"systemMessage":"%s"}\n' "$esc"
exit 0
