---
name: metodo
description: >
  Metodología de trabajo y orquestación del stack. Define las fases de todo trabajo
  (entender, diseñar, planear, ejecutar, verificar, cerrar), qué skill se usa en cada
  fase y cómo se resuelven los conflictos entre skills. Usar al inicio de cualquier
  tarea no trivial, cuando el usuario diga "metodo", "cómo trabajamos", "flujo de
  trabajo", "qué skill uso", o cuando dos skills parezcan aplicar a la vez.
  Use at the start of any non-trivial task; also when asked about workflow,
  methodology, orchestration or which skill applies.
---

# Método de trabajo

Este stack combina varias skills de terceros. Esta skill es el árbitro: dice **qué se usa
cuándo** y qué gana cuando dos skills se solapan. Si hay duda entre esta skill y la de un
tercero sobre *proceso*, gana esta. Sobre *contenido técnico* (cómo escribir un test, cómo
elegir una paleta), gana la skill especializada.

## Principios

1. **Primero entender, luego diseñar, luego codear.** Nunca se escribe código de producción
   sin un plan aprobado para tareas que tocan más de un archivo o más de un módulo.
2. **Lo pequeño que funciona.** Ponytail manda en ejecución: la solución más corta correcta.
   Las abstracciones se justifican con duplicación real o un punto de variación real,
   nunca con "por si acaso".
3. **Todo queda documentado.** El diseño y los porqués viven en `docs/`; la historia en
   `docs/BITACORA.md`. Cuánto se comenta el código lo fija el **modo de comentarios** del
   proyecto en `CLAUDE.md` (ver `documentacion`); si no está, se pregunta antes de codear.
4. **Módulos por contrato.** Un módulo no importa a otro; habla por su contrato. Ver
   `arquitectura-modular`.
5. **Commits atómicos, convencionales, con scope de módulo.** Ver `git-flujo`.
6. **El usuario decide; Claude propone y registra.** Toda decisión (de quien sea) queda en la
   bitácora, y las estructurales también en un ADR.

## Fases

### Fase 0 — Inicio de sesión (siempre, automático)

Antes de tocar nada:
- Leer `CLAUDE.md` del proyecto, incluido el modo de comentarios.
- Leer `docs/README.md` (índice) y las últimas 3 entradas de `docs/BITACORA.md`.
- Leer `docs/modulos/<modulo>.md` de cada módulo que se vaya a tocar.
- Si falta `docs/`, proponer `/metodo:init` antes de seguir.

### Fase 1 — Entender

Skill: `superpowers:brainstorming`.

Salida: un párrafo de entendimiento compartido y la lista de preguntas resueltas. No se
avanza mientras haya ambigüedad que cambie el diseño. Si el usuario pide "hazlo rápido",
se hace la versión mínima de esta fase (3 preguntas máximo), no se salta.

### Fase 2 — Diseñar

Se activa solo si la tarea crea un módulo, cambia un contrato, agrega una dependencia,
cambia estructura de datos o toca UI nueva. Un bugfix o cambio local salta a Fase 3.

| Qué se diseña | Skill | Salida |
|---|---|---|
| Estructura, módulos, contratos | `metodo:arquitectura-modular` | Lista de módulos, contratos y quién los consume |
| Decisión estructural (BD, framework, patrón de integración) | `c4-skills:adr-scribe` si está instalada; si no, plantilla `docs/adr/0000-plantilla.md` | ADR en `docs/adr/` |
| Diagrama de contexto/contenedores | `c4-skills:c4-model` si está instalada | Mermaid en `docs/arquitectura.md` |
| Necesidad de un patrón | `metodo:patrones-diseno` | Patrón elegido y por qué, en el doc del módulo |
| Auth, datos personales, entrada externa, pagos, LLM | `metodo:seguridad` | Amenazas y controles en `docs/seguridad.md` |
| UI nueva — opciones | `ui-ux-pro-max` | 2–3 direcciones candidatas |
| UI nueva — compromiso | `frontend-design` (landing, marketing, sitio) o `interface-design` (dashboard, admin, app de producto) | Dirección visual elegida, tokens |
| Animación | `emil-design-eng` (opcional) | Decisión de qué se anima y cómo |

Regla de reparto en diseño visual: **ui-ux-pro-max propone, frontend-design o interface-design
deciden, impeccable audita después.** Nunca los tres deciden.

Regla de reparto frontend-design vs interface-design: por tipo de superficie, no por gusto.
Landing, sitio, marketing, portafolio → frontend-design. Dashboard, panel, settings, app de
producto, herramienta interna → interface-design. Un proyecto con ambas superficies usa ambas,
cada una en su superficie, y los tokens compartidos se guardan en `.interface-design/system.md`.

### Fase 3 — Planear

Skill: `superpowers:writing-plans`.

El plan se guarda en `docs/planes/<fecha>-<tema>.md`. Cada tarea del plan nombra el módulo,
el contrato que toca (si alguno), el test que la valida y el doc que actualiza.

El usuario aprueba el plan.

### Fase 4 — Ejecutar

Skills activas a la vez: `superpowers:executing-plans` (o `subagent-driven-development`),
`superpowers:test-driven-development`, `ponytail` (modo full), y las reglas de código de
`metodo:seguridad` siempre.

Ciclo por tarea del plan:
1. Test que falla.
2. Código mínimo que lo pasa (ponytail).
3. Actualizar `docs/modulos/<modulo>.md` si cambió comportamiento, API o contrato.
4. Commit (`git-flujo`). Un commit por tarea del plan, no por archivo.

Reglas:
- Comentarios según el modo del proyecto (`sin-comentarios`, `minimos`, `completos`). Si no
  está definido en `CLAUDE.md`, se pregunta antes del primer código y se guarda.
- Si en medio de la ejecución aparece una decisión no prevista, se **detiene**, se anota en
  la bitácora como decisión, y si es estructural se abre ADR. No se improvisa en silencio.
- Si una tarea del plan resulta mal definida, se vuelve a Fase 3 para esa tarea, no se
  adivina.

### Fase 5 — Verificar

Skills: `superpowers:verification-before-completion`, `ponytail:ponytail-review`,
`impeccable` (modo audit/critique) si hubo UI, `superpowers:requesting-code-review` para
cambios grandes, `metodo:seguridad` (checklist) y `/security-review` de Claude Code si el
cambio toca auth, datos, entrada externa, dependencias o LLM.

Checklist mínimo:
- Tests verdes, ejecutados de verdad (no "deberían pasar").
- Sin secretos en el diff; dependencias nuevas auditadas.
- Ningún módulo importa a otro fuera de su contrato (grep de imports cruzados).
- Cada módulo tocado tiene su `docs/modulos/<modulo>.md` al día.
- Comentarios nuevos coherentes con el modo del proyecto y al día con el código.
- Lint y formato limpios.

### Fase 6 — Cerrar

Skills: `metodo:documentacion` (bitácora), `superpowers:finishing-a-development-branch`.

- Entrada en `docs/BITACORA.md`: qué se hizo, decisiones tomadas y por quién, pendientes.
- ADRs nuevos enlazados desde `docs/README.md`.
- Rama cerrada según `git-flujo` (merge, PR o descarte, según decida el usuario).

## Tabla de arbitraje

Cuando dos skills se solapan, esto decide:

| Conflicto | Gana | Por qué |
|---|---|---|
| Superpowers quiere diseñar en texto vs c4-skills quiere diagrama | Las dos, en orden: brainstorming → c4-model | Son fases distintas |
| Ponytail dice "no abstraigas" vs patrones-diseno sugiere patrón | Ponytail, salvo que el patrón elimine duplicación existente o un punto de variación real ya presente | YAGNI |
| Ponytail quiere quitar validación, manejo de errores o chequeos de permisos por "bloat" | Seguridad | Un control de seguridad no es abstracción especulativa |
| Impeccable y interface-design quieren ambos definir tokens | interface-design define, impeccable audita | Reparto fijo |
| Una skill de terceros comenta (o deja de comentar) distinto al modo del proyecto | El modo de `CLAUDE.md` | Regla del proyecto |
| ui-ux-pro-max incluye skills de brand, slides, banner | Ignorar salvo que el usuario las pida | Fuera del alcance del stack |

## Qué NO se hace

- No se empieza a codear "para ver cómo queda" en tareas que tocan contratos.
- No se instalan dependencias sin ADR corto (puede ser de 5 líneas) y entrada en bitácora.
- No se dejan TODOs en código. Van a `docs/BITACORA.md` sección Pendientes.
- No se reescribe un módulo entero cuando el plan decía cambiar una función.
