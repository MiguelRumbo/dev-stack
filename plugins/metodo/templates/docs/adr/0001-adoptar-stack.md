# 0001 — Adoptar el stack dev-stack y su método de trabajo

- Estado: aceptado
- Fecha: {{FECHA}}
- Decisores: [{{USUARIO}}]
- Afecta a: todo el proyecto

## Contexto y problema

El proyecto lo construye Claude Code en muchas sesiones. Sin método, cada sesión reinventa
estructura, pierde decisiones y deja código sin documentar.

## Opciones consideradas

1. Sin método: CLAUDE.md libre, documentación cuando se acuerde.
2. Stack dev-stack con arquitectura modular por contratos.
3. Stack dev-stack con carpeta plana (proyecto pequeño).

## Decisión

<!-- Opción 2 o 3 y por qué, usando la regla de decisión de metodo:arquitectura-modular -->

## Consecuencias

### Positivas
- Contexto acotado por módulo para cada sesión.
- Toda decisión queda registrada.

### Negativas
- Sobrecarga inicial de docs y contratos.
- Indirección entre módulos (si opción 2).

## Enlaces

- docs/arquitectura.md
- Entrada de bitácora: {{FECHA}}
