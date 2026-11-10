# dev-stack

Marketplace personal de plugins para Claude Code. Junta las skills de terceros que uso con
un plugin propio (`metodo`) que dice cómo trabajamos: fases, arquitectura modular por
contratos, patrones, documentación en `docs/` con bitácora, convenciones de git y seguridad
(OWASP, ISO 27001, IA).

## Instalar

```bash
# 1. Registrar el marketplace (una vez por máquina)
claude plugin marketplace add <tu-usuario>/dev-stack

# 2. Núcleo (siempre)
claude plugin install metodo@dev-stack
claude plugin install superpowers@dev-stack
claude plugin install ponytail@dev-stack

# 3. Diseño (si el proyecto tiene UI)
claude plugin install frontend-design@dev-stack     # landing, marketing, sitios
claude plugin install interface-design@dev-stack    # dashboards, apps de producto
claude plugin install ui-ux-pro-max@dev-stack       # catálogo de estilos/paletas/fuentes
claude plugin install impeccable@dev-stack          # auditoría de diseño

# 4. Opcionales
claude plugin install emil-design-eng@dev-stack     # animación, Expo/React Native
claude plugin install c4-skills@dev-stack           # C4 + ADR, por proyecto facturable
```

Dentro de una sesión funciona igual con `/plugin marketplace add …` e `/plugin install …`.

Para que un proyecto registre el marketplace solo, en `.claude/settings.json` del proyecto:

```json
{
  "extraKnownMarketplaces": {
    "dev-stack": { "source": { "source": "github", "repo": "<tu-usuario>/dev-stack" } }
  },
  "enabledPlugins": {
    "metodo@dev-stack": true,
    "superpowers@dev-stack": true,
    "ponytail@dev-stack": true
  }
}
```

## Empezar un proyecto

```
/metodo:init
```

Crea `CLAUDE.md`, `docs/` (índice, arquitectura, bitácora, ADRs, plantilla de módulo,
`seguridad.md`), `.gitignore` y, si eliges arquitectura modular, la regla de lint contra imports cruzados.
Después, cualquier tarea no trivial pasa por `metodo:metodo`.

## Qué hace cada pieza

| Plugin | Rol en el flujo | Fase |
|---|---|---|
| **metodo** (propio) | Árbitro. Fases, qué skill cuándo, arquitectura modular, patrones, docs, git, seguridad | Todas |
| **superpowers** | Brainstorm, plan, TDD, debugging, verificación, cierre de rama | 1–6 |
| **ponytail** | Código mínimo que funciona; revisión de bloat; respuestas compactas | 4–5 |
| **ui-ux-pro-max** | Propone estilos, paletas, fuentes, guías por stack | 2 |
| **frontend-design** | Decide dirección visual en landing/marketing | 2 |
| **interface-design** | Decide dirección y tokens en producto; persiste en `.interface-design/system.md` | 2, 5 |
| **impeccable** | Audita y pule lo construido. No decide dirección | 5 |
| **emil-design-eng** | Animación y microinteracciones, incl. Expo | 2, 4 |
| **c4-skills** | Diagramas C4 (`c4-model`) y ADRs (`adr-scribe`) | 2, 6 |

El detalle de fases, reparto y arbitraje está en
[`plugins/metodo/skills/metodo/SKILL.md`](plugins/metodo/skills/metodo/SKILL.md).

## Dónde va cada instrucción

| Quiero que Claude… | Va en |
|---|---|
| …siga el mismo método en **todos** mis proyectos | `plugins/metodo/skills/*` (este repo) |
| …sepa cosas de **un** proyecto (stack, comandos, reglas propias) | `CLAUDE.md` del proyecto (plantilla en `plugins/metodo/templates/CLAUDE.md`) |
| …recuerde qué se hizo y qué se decidió | `docs/BITACORA.md` del proyecto |
| …entienda un módulo sin leer el código | `docs/modulos/<modulo>.md` |
| …sepa por qué se eligió X y no Y | `docs/adr/` |
| …sepa qué datos son sensibles y qué amenazas hay | `docs/seguridad.md` |
| …siga un plan de implementación | `docs/planes/` |
| …use una regla de diseño visual del proyecto | `.interface-design/system.md` (y `DESIGN.md` si usas impeccable) |

Regla práctica: si una instrucción la repetirías en dos proyectos, es del stack; si no, del
`CLAUDE.md`. `CLAUDE.md` se mantiene corto porque las reglas gordas viven en las skills.

## Mantener el marketplace

Requisitos locales: Git Bash (en Windows), Python 3.8+ y, para la validación oficial, Node.

### CI: local y en GitHub

```bash
bash scripts/ci.sh            # validación propia + tests de hooks + shellcheck si está instalado
bash scripts/ci.sh --claude   # además `claude plugin validate` (usa npx si no hay claude)
```

GitHub Actions corre el mismo script en cada push a `main` y en cada PR, en Linux y Windows
(`.github/workflows/ci.yml`). Es el doble check: lo que pasa en local pasa allí.

Qué se comprueba: JSON y manifiestos válidos, plugins de terceros fijados a un `sha`, skills con
frontmatter correcto, rutas de hooks y plantillas, referencias `metodo:<skill>` existentes,
ningún nombre personal en skills/plantillas, 14 pruebas de los hooks y la validación oficial
de Claude Code.

### Versiones fijadas y cómo actualizarlas

Cada plugin de terceros está fijado a un commit (`sha` en `marketplace.json`) y las copias
vendorizadas a `scripts/vendored.lock`. Así un cambio upstream no te cambia el comportamiento.
Estado actual en [`docs/PINS.md`](docs/PINS.md).

- **Automático:** el día 1 de cada mes `update-pins.yml` busca versiones nuevas, corre el CI completo
  con ellas y abre un PR con un informe de riesgo por dependencia (🚨 hooks/manifiesto/MCP que
  se ejecutan solos, ⚠️ scripts, ➕ skills nuevas, 🔎 líneas sospechosas). El PR **nunca se
  mergea solo**: lo revisas y decides. También se lanza a mano desde Actions → "Actualizar
  versiones fijadas" (opcionalmente para una sola dependencia).
- **Manual:**
  ```bash
  python scripts/update-pins.py                       # qué hay nuevo
  python scripts/update-pins.py --apply --report r.md # fijar lo nuevo + informe
  bash scripts/sync-vendored.sh                       # traer copias vendorizadas al sha fijado
  bash scripts/ci.sh --claude
  ```

Configuración necesaria en GitHub (una vez): Settings → Actions → General → "Allow GitHub
Actions to create and approve pull requests". Los PR creados por el bot no disparan
`ci.yml` (límite de GitHub con `GITHUB_TOKEN`); por eso `update-pins.yml` corre el CI él mismo
y pone el resultado en el PR. Si quieres el check también en el PR, ejecútalo a mano desde
Actions → CI sobre la rama.

### Versión de los plugins de este repo

Claude Code solo entrega una copia nueva de un plugin cuando cambia su `version` en
`plugin.json`. Por eso `metodo`, `frontend-design` y `emil-design-eng` llevan `version`, y el CI
(`scripts/checks/versions.py`) falla si un PR cambia algo dentro de `plugins/<x>/` sin subirla.
Así cada versión corresponde a un solo contenido y los usuarios solo reciben lo que publicas
a propósito, aunque `main` siga avanzando.

```bash
python scripts/bump-version.py metodo patch   # o minor / major
```

- **patch:** arreglos y ajustes de texto. **minor:** skill, hook o plantilla nuevos.
  **major:** cambio que obliga a tocar proyectos ya inicializados.
- `sync-vendored.sh` sube patch en las copias vendorizadas cuando su contenido cambia, así que
  el PR mensual de `update-pins.yml` ya sale versionado.
- En local, `versions.py` compara con `origin/main`; en GitHub, con la base del PR o con el
  commit anterior del push.

### Otras notas

- `docs/COMPATIBILIDAD.md` tiene la matriz de solapes y la revisión de seguridad; repasarla
  cuando el informe de actualización marque 🚨.
- Los hooks de `metodo` son bash: en Windows necesitan Git Bash en el PATH.
- `.gitattributes` fuerza saltos LF: con CRLF los `.sh` fallan en Linux.

## Estructura

```
dev-stack/
  .claude-plugin/marketplace.json
  plugins/
    metodo/                 # plugin propio
      skills/{metodo,arquitectura-modular,patrones-diseno,documentacion,git-flujo,seguridad,init}/
      hooks/                # SessionStart: inyecta método + estado; Stop: avisa docs pendientes
      templates/            # CLAUDE.md y docs/ que copia /metodo:init
    frontend-design/        # vendorizado de anthropics/skills
    emil-design-eng/        # vendorizado (subconjunto) de emilkowalski/skill
  .github/workflows/        # ci.yml (cada push/PR) y update-pins.yml (mensual)
  scripts/
    ci.sh                   # CI local = CI en GitHub
    update-pins.py          # buscar/fijar versiones nuevas + informe de riesgo
    sync-vendored.sh        # copias vendorizadas al sha de vendored.lock (sube su version si cambian)
    bump-version.py         # subir version de un plugin de este repo
    vendored.lock
    checks/validate.py      # validación estructural
    checks/versions.py      # plugin cambiado => version subida
    tests/hooks.sh          # pruebas de los hooks
  docs/COMPATIBILIDAD.md
  docs/PINS.md              # versiones fijadas (generado)
```

## Licencias

`metodo` es MIT. Los plugins vendorizados conservan su licencia original (Apache-2.0 para
frontend-design, MIT para Emil) con sus `LICENSE` y `NOTICE`. Los demás se descargan de sus
repos y no se redistribuyen aquí.
