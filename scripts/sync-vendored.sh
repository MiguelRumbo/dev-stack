#!/usr/bin/env bash
# Copia frontend-design y el subconjunto de emil-design-eng desde el sha fijado en
# scripts/vendored.lock. Para mover a una versión nueva: python scripts/update-pins.py --apply
# Uso: bash scripts/sync-vendored.sh   (desde cualquier carpeta)
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
lock="$root/scripts/vendored.lock"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

fetch_pinned() {
  local repo=$1 dest=$2 sha
  sha=$(awk -v r="$repo" '$1 == r { print $2 }' "$lock")
  [ -n "$sha" ] || { echo "Falta $repo en $lock" >&2; exit 1; }
  git init -q "$dest"
  git -C "$dest" config core.autocrlf false
  git -C "$dest" fetch -q --depth=1 "https://github.com/$repo" "$sha"
  git -C "$dest" -c advice.detachedHead=false checkout -q FETCH_HEAD
  echo "$repo @ ${sha:0:12}"
}

fetch_pinned anthropics/skills "$tmp/anthropics"
rm -rf "$root/plugins/frontend-design/skills/frontend-design"
cp -r "$tmp/anthropics/skills/frontend-design" "$root/plugins/frontend-design/skills/"
cp "$tmp/anthropics/skills/frontend-design/LICENSE.txt" "$root/plugins/frontend-design/LICENSE"

fetch_pinned emilkowalski/skill "$tmp/emil"
for s in emil-design-eng animate animate-expo animation-vocabulary review-animations improve-animations choreograph gestures; do
  rm -rf "$root/plugins/emil-design-eng/skills/$s"
  cp -r "$tmp/emil/skills/$s" "$root/plugins/emil-design-eng/skills/"
done
cp "$tmp/emil/LICENSE" "$root/plugins/emil-design-eng/LICENSE"

# Un cambio de contenido sin subir version no llega a quien ya tiene el plugin instalado.
py=$(command -v python3 || command -v python || command -v py) || { echo "Falta Python" >&2; exit 1; }
for p in frontend-design emil-design-eng; do
  "$py" "$root/scripts/bump-version.py" "$p" --if-changed
done

echo "Sincronizado. Corre bash scripts/ci.sh y revisa el diff antes de commitear."
