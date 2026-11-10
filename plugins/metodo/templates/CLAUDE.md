# {{PROYECTO}}

{{PROPOSITO}}

## Lee esto primero

1. `docs/README.md` — índice y estado de los módulos.
2. Últimas 3 entradas de `docs/BITACORA.md` — qué se hizo y qué quedó pendiente.
3. `docs/modulos/<modulo>.md` de cada módulo que vayas a tocar.

## Método de trabajo

Este proyecto usa el stack `dev-stack`. La skill `metodo:metodo` manda sobre el proceso.
Resumen:

- **Fases:** entender → diseñar → planear → ejecutar → verificar → cerrar. No se codea sin
  plan aprobado si la tarea toca más de un archivo o algún contrato.
- **Código:** ponytail. La solución más corta que funciona. Sin abstracciones no pedidas.
- **Arquitectura:** {{ARQUITECTURA}}  <!-- "modular por contratos (ver docs/arquitectura.md)" o "carpeta plana; proyecto pequeño" -->
- **Comentarios en código:** {{COMENTARIOS}}  <!-- sin-comentarios | minimos | completos. Ver metodo:documentacion -->
- **Docs:** diseño, porqués e historia en `docs/`. Ver `metodo:documentacion`.
- **Un .md por módulo** en `docs/modulos/`. Se actualiza en el mismo commit que el cambio.
- **Bitácora:** `docs/BITACORA.md`, append-only, toda decisión con `[quién]`.
- **ADR** para: dependencias nuevas, cambios de contrato, elección de framework/BD/proveedor.
- **Commits:** Conventional Commits con scope de módulo, uno por tarea del plan, tests verdes
  ejecutados. Ver `metodo:git-flujo`.
- **Seguridad:** sin secretos en código ni en el chat; amenazas y controles en
  `docs/seguridad.md`. Ver `metodo:seguridad`.
- **Commit directo en main:** {{MAIN_DIRECTO}}  <!-- "solo docs(bitacora) y chore" o "nunca" -->

## Stack técnico

<!-- lenguaje, framework, gestor de paquetes, comandos: instalar, test, lint, dev, build -->

## UI

<!-- "no aplica" | "marketing → frontend-design" | "producto → interface-design" | "ambas" -->
<!-- Tokens compartidos en .interface-design/system.md -->

## Reglas propias del proyecto

<!-- cosas que solo aplican aquí -->
