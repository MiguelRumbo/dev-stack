# Módulo `<nombre>`

- Estado: planeado | activo | apagado | deprecado
- Contrato: `src/modules/<nombre>/contract.<ext>` · versión 1.0.0
- Responsable de la decisión de crearlo: [quién], AAAA-MM-DD

## Propósito

<!-- 2 líneas: qué problema resuelve y para quién -->

## Contrato

### Servicios que expone
| Servicio | Método | Entrada | Salida | Errores |
|---|---|---|---|---|

### Eventos que emite
| Evento | Payload | Cuándo |
|---|---|---|

### Puertos que necesita (quién los implementa)
| Puerto | Lo implementa |
|---|---|

## Dependencias

- Del kernel: <!-- config, eventos, logger... -->
- De otros contratos: <!-- `pagos` v1 (solo `cobrar`) -->

## Cómo apagarlo

- Flag: `modules.<nombre>.enabled = false`
- Comportamiento apagado: <!-- Null Object | ModuleDisabledError -->
- UI: <!-- qué se oculta -->

## Flujo principal

1.
2.
3.

## Decisiones de diseño

<!-- - Patrón X en Y: por qué. (fecha, [quién]) -->

## Cómo probarlo

```
<comando>
```
Cubre: <!-- contrato con consumidor falso, casos de uso, adaptadores con dobles -->

## Pendientes y riesgos

<!-- enlazan a BITACORA.md -->
