---
name: documentacion
description: >
  Reglas de documentación del proyecto: carpeta docs/ con un .md por módulo o feature,
  índice, ADRs, planes, la bitácora de trabajo (docs/BITACORA.md) donde se registra
  todo lo hecho, cambiado y decidido, y el modo de comentarios en código del proyecto
  (sin-comentarios, minimos o completos). Usar al terminar cualquier tarea, al crear o
  cambiar un módulo, antes de escribir código si el modo de comentarios no está definido,
  cuando el usuario diga "documenta", "bitácora", "anota esto", "registra la decisión",
  "qué hicimos", "comentarios", "docstrings", o al final de cada sesión. Documentation
  rules, code comments policy, module docs, work log, decision log.
---

# Documentación

## Regla principal

**La documentación de diseño, contexto e historia vive en `docs/`.** Cuánto se explica
*dentro* del código lo decide cada proyecto con su **modo de comentarios**.

## Modo de comentarios

| Modo | En el código | En `docs/` | Cuándo conviene |
|---|---|---|---|
| `sin-comentarios` | Nada. Nombres que se explican solos. | Todo: comportamiento, porqués, decisiones | Proyectos donde Claude escribe casi todo y el contexto se lee desde `docs/` |
| `minimos` | Solo el **porqué** que el código no puede decir (workaround, invariante, límite externo, enlace a ADR/issue) y docstrings de la API pública | Lo demás | Equipo mixto; punto medio recomendado si no hay preferencia |
| `completos` | Docstrings en toda función/clase/módulo público con el estándar del lenguaje (JSDoc/TSDoc, PEP 257, rustdoc, KDoc, XML doc) y comentarios en lógica no trivial | Arquitectura, contratos, decisiones; enlaza al código en vez de repetirlo | Librerías y SDK, equipos que lo exigen, código que se entrega a un cliente que mantendrá sin `docs/`, proyectos de aprendizaje |

Reglas en **todos** los modos:
- Primero se mejora el nombre; el comentario nunca sustituye un mal nombre.
- Un comentario explica el **porqué** o el **contrato**, nunca repite el **qué** (`i++ // suma 1`).
- Un comentario desactualizado es un bug: se corrige en el mismo commit que el código.
- Directivas de herramientas (`// eslint-disable-next-line`, `# type: ignore`, `# nosec`) y
  cabeceras de licencia siempre están permitidas.
- `TODO`, `FIXME`, `HACK` no se quedan en código: van a `docs/BITACORA.md` → Pendientes.
  En `completos` se permite `TODO(<enlace a issue>)` si el proyecto usa issues.
- Las decisiones con alternativas descartadas van a `docs/adr/`, no a un comentario.

### Cómo se elige y dónde se guarda

1. **Leer** `CLAUDE.md` del proyecto: línea `- **Comentarios en código:** <modo>`.
2. Si no está, **preguntar una sola vez** antes de escribir el primer código del proyecto (con
   AskUserQuestion si está disponible). Recomendar según lo que ya hay: si el código existente
   tiene docstrings, `completos`; si no hay comentarios, `sin-comentarios`; si no hay código,
   `minimos`.
3. **Guardar** la respuesta en `CLAUDE.md` (sección "Método de trabajo"), que es la memoria
   versionada del proyecto y la ve todo el equipo. Si el usuario no quiere tocar `CLAUDE.md`,
   guardarla en la memoria de Claude para ese proyecto y decírselo.
4. Anotar la decisión en `docs/BITACORA.md` con `[quién]`.
5. Cambiar de modo después es una decisión nueva: se actualiza `CLAUDE.md` y se anota en la
   bitácora. No se reescriben comentarios de código existente salvo que el usuario lo pida.

## Estructura de `docs/`

```
docs/
  README.md              # índice: qué hay, enlaces, estado de cada módulo
  arquitectura.md        # visión general: módulos, kernel, diagrama C4 L1/L2 (Mermaid)
  BITACORA.md            # bitácora de trabajo, cronológica, append-only
  seguridad.md           # datos, amenazas, controles, riesgos aceptados (metodo:seguridad)
  adr/
    0000-plantilla.md
    0001-<titulo>.md
  modulos/
    _plantilla.md
    <modulo>.md          # uno por módulo o feature importante
  planes/
    <fecha>-<tema>.md    # planes de superpowers:writing-plans
  guias/                 # opcional: setup local, despliegue, cómo probar
```

Un `.md` por módulo evita el documento único gigante. El índice (`README.md`) es la única
vista global y debe caber en una pantalla.

## `docs/modulos/<modulo>.md`

Secciones fijas (ver `_plantilla.md`):

1. **Propósito** — 2 líneas. Qué problema resuelve, para quién.
2. **Contrato** — qué expone (servicios, tipos, eventos) y versión. Enlace al archivo.
3. **Dependencias** — qué necesita del kernel y de qué contratos ajenos consume.
4. **Cómo apagarlo** — flag y comportamiento cuando está apagado.
5. **Flujo principal** — pasos del caso de uso central, en prosa o lista. Opcional: Mermaid.
6. **Decisiones de diseño** — patrones aplicados y por qué, con fecha y quién decidió.
7. **Cómo probarlo** — comando, fixtures, qué cubre.
8. **Pendientes y riesgos** — enlazan a la bitácora.

Se actualiza **en el mismo commit** que cambia el comportamiento. Un commit que cambia el
contrato sin tocar este archivo está incompleto.

## `docs/BITACORA.md`

Bitácora cronológica. **Append-only**: no se editan entradas pasadas; si algo cambió, se
agrega una entrada nueva que lo diga.

Formato de entrada:

```markdown
## 2026-11-09 — <tema corto de la sesión>

**Contexto:** una línea sobre qué se quería lograr.

**Hecho:**
- <módulo>: qué cambió (enlace a commit o rango si aplica)
- …

**Decisiones:**
- [usuario] Usar PostgreSQL en vez de SQLite para producción. → ADR 0003
- [Claude] Strategy para tarifas de envío; había tres transportistas. → docs/modulos/envios.md
- [usuario] Posponer módulo de facturación a la siguiente iteración.

**Descartado:**
- Caché en memoria para catálogo: la API ya responde en 40 ms.

**Pendientes:**
- [ ] Añadir test de contrato a `notificaciones`
- [ ] Revisar límite de reintentos en `pagos` (riesgo: cobros duplicados)

**Siguiente paso sugerido:** …
```

Reglas:
- Toda decisión lleva quién la tomó entre corchetes: el nombre de la persona o `[Claude]`.
  Si Claude propuso y la persona aprobó: `[Claude→nombre]`. El nombre sale de
  `git config user.name`; si está vacío, se pregunta una vez y se usa el mismo siempre.
- Las decisiones estructurales enlazan a su ADR. Las locales, al doc del módulo.
- Una entrada por sesión de trabajo como mínimo. Si la sesión es larga y cambia de tema, una
  entrada por tema.
- Se escribe al **cerrar** (Fase 6 de `metodo`), pero las decisiones se van anotando en
  cuanto ocurren, aunque la entrada se complete al final.
- Al inicio de sesión se leen las últimas 3 entradas. Si la bitácora supera ~2000 líneas, se
  archiva en `docs/bitacora/2026-Q4.md` y `BITACORA.md` queda con un índice + las últimas
  entradas.

## ADRs (`docs/adr/`)

Formato MADR corto (compatible con `c4-skills:adr-scribe` si está instalada):

```markdown
# 0003 — Título en forma de decisión

- Estado: propuesto | aceptado | reemplazado por 0007
- Fecha: 2026-11-09
- Decisores: <nombre> (Claude propuso)

## Contexto y problema
## Opciones consideradas
## Decisión
## Consecuencias
- Positivas
- Negativas (obligatorio; un ADR sin negativas está incompleto)
```

Cuándo hay ADR: nueva dependencia, cambio de contrato, elección de framework/BD/proveedor,
patrón que cruza módulos, cualquier cosa que cueste más de un día deshacer.

## Qué documenta Claude sin que se lo pidan

- Al crear un módulo: su `.md`, línea en `README.md`, entrada en bitácora.
- Al cambiar un contrato: `.md` del módulo, ADR, bitácora.
- Al tomar cualquier decisión en Fase 4 que no estaba en el plan: bitácora inmediatamente.
- Al cerrar sesión: entrada de bitácora completa.
- Al descartar una opción que el usuario propuso: bitácora, sección Descartado, con el motivo.

## Qué NO se documenta

- Lo obvio desde el código bien nombrado (en ningún modo).
- En `docs/`, lo que ya dice un docstring (modo `completos`): se enlaza, no se copia.
- Cómo funciona una librería externa (se enlaza a su doc).
- Historias de "intenté X y falló" salvo que la lección cambie una decisión; entonces va a
  Descartado con una línea.
