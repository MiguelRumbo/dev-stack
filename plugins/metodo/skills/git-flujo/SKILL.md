---
name: git-flujo
description: >
  Convenciones de git del stack: Conventional Commits con scope de módulo, commits
  atómicos por tarea del plan, ramas por tema, qué va en el cuerpo del commit, cuándo
  commitear, PRs y cierre de rama. Usar al hacer commit, crear rama, abrir PR, mergear,
  o cuando el usuario diga "commit", "sube esto", "guarda cambios", "rama", "PR",
  "merge", "historial". Git workflow, commit conventions, branching.
---

# Flujo de git

## Commits

Formato **Conventional Commits** con el módulo como scope:

```
<tipo>(<modulo>): <qué cambia, en imperativo, minúscula, sin punto>

<por qué, si no es obvio. 1–3 líneas.>

Refs: docs/adr/0003-postgres.md, docs/modulos/pagos.md
```

Tipos permitidos: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `build`, `ci`.
`BREAKING CHANGE:` en el pie cuando cambia un contrato de módulo de forma incompatible; en
ese caso también se sube la `version` del contrato en el mismo commit.

Scope = nombre del módulo (`pagos`, `auth`, `ui-pedidos`). Para el kernel: `kernel`. Para
docs globales: `docs`. Para varios módulos a la vez: revisar si el commit debería partirse;
si no, scope del módulo principal.

Ejemplos:

```
feat(pagos): cobrar con Stripe vía adaptador

Primer proveedor real. Contrato PagoService v1 sin cambios.

Refs: docs/modulos/pagos.md
```

```
refactor(envios): extraer Strategy para tarifas por transportista

Tres transportistas con fórmulas distintas; el switch ya tenía bugs.

Refs: docs/modulos/envios.md#decisiones-de-diseño
```

## Cuándo se commitea

- **Un commit por tarea del plan**, no por archivo ni por "fin del día".
- Solo con tests verdes **ejecutados**. Nunca `--no-verify`.
- El commit incluye: código + tests + el `.md` del módulo si cambió comportamiento/contrato.
  Documentación y código del mismo cambio van juntos, no en commits separados.
- La entrada de bitácora va en un commit propio al cerrar: `docs(bitacora): sesión 2026-11-09 —
  tarifas de envío`.
- Si una tarea se partió en dos commits porque creció, el segundo dice `(2/2)` al final del
  título.

Nunca se commitea: secretos, `.env`, binarios generados, `node_modules`, outputs de build,
archivos de IDE. `.gitignore` se configura en `/metodo:init`.

## Ramas

- `main`: siempre desplegable. Nadie hace commit directo salvo `docs(bitacora)` y `chore`
  triviales, y solo si el usuario lo permite en `CLAUDE.md`.
- Rama por tema: `<tipo>/<modulo>-<tema-corto>`, por ejemplo `feat/pagos-stripe`,
  `fix/auth-refresh-token`.
- Una rama = un plan de `docs/planes/`. Si el plan cambia de alcance, se cierra la rama y se
  abre otra.
- `superpowers:using-git-worktrees` cuando se trabaja en dos temas a la vez.

## Antes de pedir merge

Checklist de `metodo` Fase 5, más:

- `git log main..HEAD` se lee como la lista de tareas del plan.
- Ningún commit `wip`, `fix typo`, `oops`. Se hace `rebase -i` para limpiar **solo** si la rama
  no se ha compartido; si ya hay PR abierto, no se reescribe historia.
- Rama actualizada con `main` (rebase si es privada, merge si es compartida).

## PR

Título = título del commit principal o del plan. Cuerpo:

```
## Qué
2 líneas.

## Por qué
Enlace a plan y ADRs.

## Cómo probar
Comandos.

## Docs actualizados
- docs/modulos/<modulo>.md
- docs/adr/000N
```

## Cierre de rama

Sigue `superpowers:finishing-a-development-branch`: el usuario elige merge, PR o descartar.
Tras merge: borrar rama local y remota, entrada en bitácora si no se hizo, verificar que
`docs/README.md` refleja el estado.

## Relación con otras skills

- `metodo:seguridad`: antes de cada commit, revisar que el diff no lleva secretos. Si se
  filtró uno, rotarlo primero; reescribir historia no basta.
- `superpowers` decide *cuándo* se está listo para commitear (tests, verificación); esta skill
  decide *cómo* es el commit.
