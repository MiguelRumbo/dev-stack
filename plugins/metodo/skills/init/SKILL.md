---
name: init
description: >
  Inicializa un proyecto con la estructura del stack: CLAUDE.md, carpeta docs/ (índice,
  arquitectura, bitácora, ADRs, plantilla de módulo), .gitignore básico y, si el usuario
  quiere, regla de lint contra imports cruzados entre módulos. Usar en proyectos nuevos o
  al adoptar el stack en uno existente, cuando falte docs/ o CLAUDE.md, o cuando el usuario
  diga "/metodo:init", "inicializa el proyecto", "prepara el repo", "adopta el stack".
---

# /metodo:init — preparar un proyecto

Las plantillas están en `${CLAUDE_PLUGIN_ROOT}/templates/`. Este archivo está en
`<plugin>/skills/init/SKILL.md`, así que `templates/` está dos niveles arriba.

## Pasos

1. **Detectar estado.** ¿Hay `CLAUDE.md`? ¿Hay `docs/`? ¿Hay git? ¿Qué lenguaje/stack?
   (buscar `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `app.json` de Expo,
   `*.csproj`…). No sobrescribir nada existente sin preguntar.

2. **Preguntar lo mínimo** (una sola ronda, con AskUserQuestion si está disponible):
   - Nombre del proyecto y una línea de propósito.
   - ¿Arquitectura modular por contratos? (ver `arquitectura-modular` → regla de decisión;
     proponer la respuesta según el tamaño detectado).
   - ¿Tipo de UI? (ninguna / web marketing / app de producto / ambas / móvil).
   - ¿Puede Claude commitear directo en `main` para `docs(bitacora)` y `chore`? Sí/No.
   - ¿Modo de comentarios en código? `sin-comentarios` / `minimos` / `completos` (ver
     `documentacion`; recomendar según el código existente, o `minimos` si no hay).
   - ¿Instalar c4-skills para este proyecto? (recomendar sí si es para cliente/entregable).
   - ¿Maneja datos personales o exige algún marco (ISO 27001, RGPD, LFPDPPP)? Va a
     `docs/seguridad.md` → Cumplimiento.

3. **Copiar y rellenar plantillas**:
   - `templates/CLAUDE.md` → `./CLAUDE.md` (si ya existe, proponer **añadir** la sección
     "Método de trabajo" al final, no reemplazar).
   - `templates/docs/README.md` → `docs/README.md`
   - `templates/docs/arquitectura.md` → `docs/arquitectura.md`
   - `templates/docs/BITACORA.md` → `docs/BITACORA.md` con la primera entrada: la
     inicialización, fecha de hoy, decisiones de este paso con `[{{USUARIO}}]`.
   - `templates/docs/adr/0000-plantilla.md` → `docs/adr/0000-plantilla.md`
   - `templates/docs/adr/0001-adoptar-stack.md` → `docs/adr/0001-adoptar-stack.md` rellenado
     con las respuestas (arquitectura modular sí/no y por qué).
   - `templates/docs/modulos/_plantilla.md` → `docs/modulos/_plantilla.md`
   - `templates/docs/seguridad.md` → `docs/seguridad.md`
   - Crear `docs/planes/.gitkeep`.
   Reemplazar `{{PROYECTO}}`, `{{PROPOSITO}}`, `{{FECHA}}`, `{{USUARIO}}`, `{{ARQUITECTURA}}`,
   `{{COMENTARIOS}}`, `{{MAIN_DIRECTO}}` en todas. `{{USUARIO}}` = `git config user.name`; si
   está vacío, preguntarlo en la ronda del paso 2.

4. **`.gitignore`**: si no existe, crear uno mínimo para el stack detectado más
   `.env*` (con excepción `!.env.example`), `.interface-design/cache/` (si aplica), `*.local`,
   `*.pem`, `*.key`. Proponer (sin instalar) un pre-commit con `gitleaks`.

5. **Regla de lint de imports cruzados** (solo si eligió arquitectura modular):
   - JS/TS: proponer `eslint-plugin-import` con `import/no-restricted-paths` o
     `dependency-cruiser`. Escribir la config, no instalar sin aprobación (requiere ADR corto
     de dependencia según `metodo`).
   - Python: `import-linter` con contratos `independence` entre `src/modules/*`.
   - Otros: anotar en `docs/arquitectura.md` que la regla se vigila por revisión y grep.

6. **Esqueleto de código** (solo si eligió modular y el repo está vacío o casi): crear
   `src/kernel/` con registro mínimo, bus de eventos mínimo y config, en el lenguaje
   detectado, siguiendo ponytail: lo más corto que funcione. Nada de módulos de ejemplo
   salvo que el usuario lo pida.

7. **Cerrar**: mostrar árbol resultante, recordar los próximos pasos:
   - `/plugin install c4-skills@dev-stack` si dijo que sí.
   - Primera sesión de trabajo: `metodo` Fase 1.
   - Commit: `chore(docs): inicializar estructura del stack`.

## Qué no hace

- No instala plugins (no tiene permiso); solo indica el comando.
- No borra ni mueve código existente.
- No crea módulos de negocio; eso es Fase 2 de `metodo`.
