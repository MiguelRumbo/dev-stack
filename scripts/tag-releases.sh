#!/usr/bin/env bash
# Crea un tag <plugin>--v<version> por cada plugin de este repo cuya versión aún no tiene tag.
# Deja registrado qué commit es cada versión publicada, y es la convención con la que Claude Code
# resuelve rangos de versión cuando otro plugin depende de uno de estos.
# Uso: bash scripts/tag-releases.sh          # solo muestra qué tags faltan
#      bash scripts/tag-releases.sh --push   # los crea en HEAD (debe ser origin/main) y los sube
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"

push=0
[ "${1:-}" = "--push" ] && push=1

py=$(command -v python3 || command -v python || command -v py) || { echo "Falta Python" >&2; exit 1; }

if [ "$push" = 1 ]; then
  git fetch -q --tags origin main
  if [ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]; then
    echo "HEAD no es origin/main: los tags solo se crean sobre lo publicado." >&2
    exit 1
  fi
fi

missing=()
for manifest in plugins/*/.claude-plugin/plugin.json; do
  read -r name version < <("$py" -c 'import json,sys; m=json.load(open(sys.argv[1],encoding="utf-8")); print(m["name"], m.get("version",""))' "$manifest")
  if [ -z "$version" ]; then
    echo "sin version  $name (no se etiqueta)"
    continue
  fi
  tag="$name--v$version"
  if git rev-parse -q --verify "refs/tags/$tag" >/dev/null; then
    echo "existe       $tag"
  else
    echo "falta        $tag"
    missing+=("$tag")
  fi
done

[ ${#missing[@]} -eq 0 ] && { echo "Nada que etiquetar."; exit 0; }
[ "$push" = 1 ] || { echo "Ejecuta con --push para crearlos en HEAD."; exit 0; }

for tag in "${missing[@]}"; do
  git tag -a "$tag" -m "${tag/--v/ }"
done
git push -q origin "${missing[@]/#/refs/tags/}"
echo "Creados y subidos: ${missing[*]}"
