# Matriz de compatibilidad del stack

Revisado el 2026-11-09 clonando cada repo e instalando los plugins desde este marketplace
con Claude Code 2.1.321. Los números de skills y tokens salen de `claude plugin details`.

2026-11-10: `metodo` suma la skill `seguridad`. 2026-11-27: medido de nuevo con Claude Code
2.1.332 (~1.65k).

## Inventario real

| Plugin | Origen | Formato upstream | Skills | Agents | Hooks | Siempre-en-contexto | Licencia |
|---|---|---|---|---|---|---|---|
| metodo | este repo | plugin | 7 | 0 | SessionStart, Stop | ~1.65k tok | MIT |
| superpowers | obra/superpowers | plugin | 15 | 0 | SessionStart | ~0.85k | MIT |
| ponytail | DietrichGebert/ponytail | plugin | 6 | 0 | SessionStart, SubagentStart, UserPromptSubmit | ~0.64k | MIT |
| frontend-design | anthropics/skills → vendorizado aquí | skill suelta dentro de un plugin de 19 | 1 | 0 | — | ~0.08k | Apache-2.0 |
| ui-ux-pro-max | nextlevelbuilder/ui-ux-pro-max-skill | plugin | 7 | 0 | — | ~1.1k | MIT |
| impeccable | pbakaus/impeccable (`plugin/`) | plugin en subcarpeta (`git-subdir`) | 1 | 4 | SessionStart, PostToolUse(Edit\|Write), Stop | ~0.3k | Apache-2.0 |
| interface-design | Dammyjay93/interface-design | plugin | 3 | 0 | — | ~0.3k | MIT |
| emil-design-eng | emilkowalski/skill → vendorizado aquí | 18 skills sin plugin.json | 8 (subconjunto) | 0 | — | ~1.4k | MIT |
| c4-skills | muthub-ai/c4-skills | 2 skills sin plugin.json (la entrada del marketplace es el manifiesto) | 2 | 0 | — | ~0.5k | MIT |

Total si instalas los 9: **~6.8k tokens** siempre en contexto. Stack recomendado (sin emil):
**~5.4k**.

## Por qué dos están vendorizados

Claude Code autodescubre `skills/` en la raíz de un repo. Si el repo trae 19 skills y la
entrada del marketplace lista solo una, el resultado es **19 + 1**, no 1 (se comprobó:
frontend-design instalado desde `anthropics/skills` cargaba 19 skills). Por eso frontend-design
y el subconjunto de Emil se copian a `plugins/` de este repo. Se refrescan con
`scripts/sync-vendored.sh`. Ambas licencias lo permiten; se conserva LICENSE y NOTICE.

c4-skills no tiene `skills/` en raíz (sus carpetas son `c4designer/` y `adr-scribe/`), así
que la entrada con `skills: [...]` funciona sin vendorizar. Como tampoco trae `plugin.json`,
la entrada lleva `"strict": false` (ver abajo).

## Avisos al sincronizar en claude.ai

claude.ai valida el marketplace con su propio esquema al sincronizarlo, más estricto que
Claude Code en algunos puntos. Lo que pasa `claude plugin validate --strict` puede salir allí
como omitido o con avisos.

| Aviso | Causa | Qué se hizo |
|---|---|---|
| c4-skills omitido: *requires .claude-plugin/plugin.json …* | Upstream no trae `plugin.json`; la entrada es el manifiesto | `"strict": false` en la entrada. Claude Code ya la usaba así (con o sin `strict`). `validate.py` lo exige y `update-pins.py` avisa 🚨 si upstream añade un `plugin.json`, porque entonces `strict: false` + `skills` es un conflicto y el plugin no carga |
| metodo: *unrecognized key 'icon'* | `icon` no está en el esquema de claude.ai | Quitado de `plugin.json`. El icono sigue en `.claude-plugin/icon.png`, ruta que se detecta sin declararla. `validate.py` falla con campos desconocidos |
| superpowers: campo `powershell` en el hook SessionStart | Campo para otros agentes; en Claude Code la variante Windows es `"shell": "powershell"` | Nada que hacer aquí: el hook corre con `command`. Es upstream |
| impeccable: campos `env` y `windows` en SessionStart, PostToolUse y Stop | Campos para otros agentes (VS Code, Windows sin Git Bash) | Igual: el hook corre con `command`, sin la variable `IMPECCABLE_HOOK_HARNESS=vscode` de `env` (pensada para VS Code). Su versión siguiente añade `commandWindows`, que dará un aviso más por hook |

Los avisos de hooks de terceros son inofensivos y solo se quitan cambiando el repo upstream.
El informe de `update-pins.py` marca con ℹ️ los campos de hook nuevos de este tipo.

## Solapes detectados y cómo se resuelven

| Solape | Entre | Resolución (en `metodo:metodo`) |
|---|---|---|
| Revisión de código | superpowers requesting-code-review vs ponytail-review vs `/security-review` | superpowers decide *cuándo*; ponytail-review audita *bloat*; `/security-review` + `metodo:seguridad` auditan seguridad. |
| Código mínimo vs controles de seguridad | ponytail vs metodo:seguridad | **Seguridad.** Validación, permisos y manejo de errores no son bloat. |
| Definir tokens/dirección visual | frontend-design vs interface-design vs impeccable | Por superficie: landing/marketing → frontend-design; producto → interface-design. **Impeccable nunca define, solo audita.** |
| Archivo de diseño persistente | impeccable (lee/escribe `DESIGN.md`, `PRODUCT.md`) vs interface-design (`.interface-design/system.md`) | Dos archivos distintos, no chocan. Convención: `system.md` es la fuente de tokens; `DESIGN.md` lo puede referenciar. |
| Catálogos de estilo | ui-ux-pro-max (design-system, ui-styling) vs theme-factory (no instalada) | ui-ux-pro-max. |
| Skills fuera de alcance | ui-ux-pro-max: banner-design, brand, slides | Se ignoran salvo petición. |
| Diseño pre-código | superpowers brainstorming vs c4-skills c4-model | Fases distintas: brainstorming entiende, c4-model documenta. |
| ADRs | c4-skills adr-scribe vs plantilla propia `docs/adr/0000-plantilla.md` | Mismo formato MADR. Con c4-skills instalada, adr-scribe redacta; sin ella, la plantilla. |
| Hook Stop | metodo (aviso de docs) vs impeccable (design deep pass) | Ambos corren; metodo solo emite `systemMessage`, no bloquea. Sin conflicto. |
| Hook SessionStart | metodo, superpowers, ponytail, impeccable | Cuatro inyecciones de contexto al arrancar. Es el costo "siempre-en-contexto" de la tabla. Aceptable. |

## Riesgos de seguridad revisados

- **impeccable** descarga un binario en su primer uso (`scripts/impeccable` es un launcher).
  Su hook `PostToolUse` corre tras cada `Edit|Write`. Es el plugin con más superficie. Si no
  confías, quítalo y usa solo frontend-design/interface-design, que son solo texto.
- **ponytail** tiene `userConfig` con webhook opcional (`webhookUrl`). Por defecto vacío: nada
  sale de la máquina. Escribe un CSV local en `~/.config/ponytail/band/`. Se puede apagar con
  `/plugin configure ponytail@dev-stack` → `ledger=false`.
- **superpowers**: hook SessionStart en bash puro, solo inyecta texto. Sin riesgo observado.
- **interface-design, ui-ux-pro-max, c4-skills, frontend-design, emil**: solo Markdown y
  scripts de consulta locales. Sin hooks de red.

Ningún `SKILL.md` revisado contenía instrucciones de prompt injection evidentes (exfiltrar,
ignorar reglas, ocultar acciones). Revisión manual del 2026-11-09; repetir al actualizar.

## Versiones fijadas

Desde 2026-11-10 todas las fuentes externas llevan `sha` y el CI falla si alguna no lo tiene.
Estado actual en [`PINS.md`](PINS.md); cómo actualizar en el README ("Versiones fijadas y cómo
actualizarlas"). Cuando el informe de `update-pins` marque 🚨, repetir la revisión de esta
página para esa dependencia antes de mergear.

Versiones vistas el 2026-11-09: superpowers 7.0.2 · ponytail 5.3.3 ·
impeccable 4.8.2 · interface-design 2026.6.20.1332 · ui-ux-pro-max 2.15.0 · c4-skills 1.2.0.
