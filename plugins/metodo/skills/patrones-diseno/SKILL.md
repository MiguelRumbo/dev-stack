---
name: patrones-diseno
description: >
  Guía de patrones de diseño: cuándo usar cada uno, cuándo NO, qué síntoma del código lo
  pide, cómo se combina con YAGNI/ponytail y cómo documentarlo. Usar cuando el usuario
  pregunte qué patrón aplicar, mencione un patrón por nombre (factory, strategy, observer,
  repository, adapter, decorator, facade, command, state, builder, singleton, CQRS, etc.),
  cuando haya duplicación, condicionales por tipo, acoplamiento a librerías externas, o
  al diseñar un módulo nuevo. Design patterns: when to use, when not to, smell-to-pattern.
---

# Patrones de diseño: cuándo sí, cuándo no

## Regla cero (compatibilidad con ponytail)

Un patrón se introduce **solo** si resuelve un problema que ya existe en el código o en el
diseño aprobado. Nunca "por si crece". Señales válidas:

- Duplicación en 3 lugares o más.
- Un `switch`/`if` sobre un tipo o modo que ya tiene 3 ramas y va a tener más.
- Una librería externa importada desde más de un archivo del módulo.
- Un constructor con más de 4 parámetros opcionales.
- Un objeto con estados que cambian su comportamiento y ya hay bugs por estados inválidos.
- Un contrato de módulo que exige intercambiar implementaciones (ver `arquitectura-modular`).

Si la señal no está, se escribe la función directa y se anota en el doc del módulo:
"Candidato a Strategy si aparece un tercer proveedor". Eso es documentación, no deuda.

Todo patrón aplicado se **nombra** en `docs/modulos/<modulo>.md`, sección "Decisiones de
diseño", con una línea de por qué. El nombre del tipo ya lo dice (`PagoStripeAdapter`,
`NotificadorNull`, `PedidoRepository`); en el código solo se comenta si el modo de
comentarios del proyecto lo pide.

## Del síntoma al patrón

| Síntoma | Patrón | Alternativa más simple primero |
|---|---|---|
| Mismo algoritmo con variaciones por proveedor/modo | **Strategy** | Una función con un parámetro, si son 2 variantes |
| Hablamos con una librería/API externa en varios sitios | **Adapter** (puerto + adaptador) | Un solo wrapper-función si es una llamada |
| Un módulo apagado o una dependencia opcional | **Null Object** | `if (modulo)` si hay un solo uso |
| Varios módulos reaccionan a algo que pasó | **Observer / Pub-Sub** (eventos del kernel) | Llamada directa si solo reacciona uno y es síncrono |
| Crear objetos cuya clase concreta depende de config | **Factory (función)** | `new X()` directo; una factory es una función, no una clase, hasta que haga falta más |
| Construir objeto con muchas opciones | **Builder** o **objeto de opciones con defaults** | Objeto de opciones casi siempre basta |
| Añadir comportamiento (caché, log, retry) sin tocar la clase | **Decorator** | Middleware del framework si existe |
| Fachada simple sobre un subsistema complejo | **Facade** (el `index` del módulo) | Nada; es casi gratis |
| Acceso a datos acoplado a la BD | **Repository** | Funciones de consulta en un archivo `queries` si no hay dominio rico |
| Deshacer, colas, reintentos, auditoría de acciones | **Command** | Función + log si no hay undo ni cola |
| Comportamiento según estado y transiciones con reglas | **State** (máquina de estados explícita) | Enum + switch si son 3 estados sin reglas de transición |
| Recorrer estructura compleja con operaciones distintas | **Visitor** | Método polimórfico o `match`; Visitor casi nunca en apps |
| Instancia única global | **Singleton** | Inyección por el kernel. Singleton se evita: rompe tests |
| Lecturas y escrituras con formas muy distintas y carga alta | **CQRS** | Un repositorio normal. CQRS solo con evidencia de carga o de modelos realmente distintos |
| Unidad de trabajo transaccional sobre varios repos | **Unit of Work** | Transacción del ORM |
| Dependencias que cambian por entorno/test | **Inyección de dependencias** (por constructor o por el kernel) | Siempre sí; es la base de lo demás, pero sin contenedor mágico |

## Patrones que este stack usa por defecto

Por la arquitectura modular, estos aparecen sin discutirse:

- **Ports & Adapters** en el borde de cada módulo.
- **Registry** (el kernel) para ubicar módulos por contrato.
- **Null Object** para módulos apagados.
- **Pub-Sub** para eventos entre módulos.
- **Facade** como `index` de cada módulo.
- **Inyección por constructor** dentro del módulo.

Todo lo demás requiere la señal de la Regla cero.

## Patrones por capa (dentro de un módulo)

- **domain/**: Value Object, Entity, State si hay máquina de estados, Specification solo si
  las reglas se combinan dinámicamente. Sin frameworks.
- **application/**: casos de uso como funciones o clases con un método; Command si hay cola o
  undo; Unit of Work si hay transacción multi-repo.
- **adapters/**: Adapter, Repository, Decorator (caché/retry/log), Anti-Corruption Layer
  cuando el modelo externo es muy distinto al nuestro.
- **UI**: Container/Presenter (o hooks + componentes tontos), Observer vía estado reactivo del
  framework. No se reimplementa lo que el framework ya da.

## Antipatrones a vigilar

- **Patronitis**: clase `AbstractFactoryProvider` para dos valores. Ponytail lo rechaza.
- **Anémico + servicios dios**: entidades sin comportamiento y un `Service` de 800 líneas.
  Mover reglas al dominio.
- **Singleton de conveniencia**: `Config.getInstance()` por todos lados. Inyectar.
- **Repositorio que filtra todo**: `findByXAndYAndZ` x 20. Usar Specification o query object
  solo si el crecimiento es real; si no, consultas nombradas por caso de uso.
- **Eventos para todo**: usar evento donde una llamada síncrona era clara. Evento solo cuando
  el emisor no debe conocer al receptor.
- **Adapter que filtra el modelo externo**: devolver el objeto del SDK tal cual. El adaptador
  traduce a tipos del contrato.

## Cómo documentar un patrón

En `docs/modulos/<modulo>.md`, sección "Decisiones de diseño":

```
- Strategy en `calculoEnvio`: tres transportistas con tarifas distintas; se añade uno al mes.
  Interfaz `TarifaEnvio`, implementaciones en `adapters/tarifas/`. (2026-11-09, [Claude→nombre])
```

Si el patrón cruza módulos o cambia un contrato, además ADR en `docs/adr/`.
