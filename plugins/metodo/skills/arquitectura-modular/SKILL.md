---
name: arquitectura-modular
description: >
  Arquitectura desacoplada por módulos y contratos (estilo "cada servicio independiente,
  apagable, que habla por su interfaz"). Define cuándo conviene y cuándo no, cómo se
  estructura un módulo, qué es un contrato, cómo se registran y apagan módulos, y qué
  está prohibido. Usar al crear un proyecto, al agregar un módulo o feature, al decidir
  si algo va en un módulo existente o uno nuevo, al revisar imports cruzados, o cuando el
  usuario hable de módulos, contratos, desacoplamiento, feature flags, plugin architecture,
  modular monolith, hexagonal, ports and adapters.
---

# Arquitectura modular por contratos

## El modelo

Un sistema es un conjunto de **módulos** que:

1. No se importan entre sí. Cada uno solo importa su propio código y el **núcleo** (kernel).
2. Exponen un **contrato**: tipos, interfaces y eventos que otros pueden consumir.
3. Se **registran** en el núcleo al arrancar y pueden **apagarse** sin romper a los demás.
4. Tienen su **propio doc** en `docs/modulos/<modulo>.md`.

Es la misma idea con la que un proveedor cloud ofrece servicios: cada uno tiene una API
pública, no sabe cómo está hecho el de al lado, y puedes no contratarlo. En un solo
repositorio esto se llama **monolito modular** o **arquitectura de plugins**; en el borde
de cada módulo se aplica **puertos y adaptadores** (hexagonal).

## Análisis: ¿conviene?

### Lo que da

- **Contexto pequeño para Claude.** Un módulo cabe en una sesión; el agente lee su doc y su
  contrato, no todo el repo. Esto es la ventaja más grande para trabajar con IA.
- **Documentación natural por módulo.** Un `.md` por módulo mapea 1:1 con la regla del stack.
- **Cambios acotados.** Un bug en `pagos` no obliga a leer `notificaciones`.
- **Reemplazable.** Cambiar el proveedor de email es cambiar un adaptador, no tocar 14 archivos.
- **Entregable a cliente.** Un módulo apagable es una feature vendible por separado.
- **Pruebas por módulo** con dobles del contrato, sin levantar todo.

### Lo que cuesta

- **Indirección.** Cada llamada cruzada pasa por un contrato. Para leer el flujo completo hay
  que seguir dos saltos.
- **Versionado de contratos.** Cambiar un contrato obliga a actualizar consumidores. Esto es
  trabajo real y hay que hacerlo explícito (ADR).
- **Duplicación controlada.** Dos módulos pueden tener un `formatearFecha` cada uno. Es
  aceptable hasta que se repite 3 veces; entonces va al núcleo.
- **Transversales** (auth, logging, errores, configuración, i18n) necesitan un lugar: el
  núcleo. Si el núcleo crece demasiado, el desacoplamiento es falso.
- **Sobrecarga en proyectos chicos.** Un script, un prototipo de fin de semana o una landing
  no lo necesitan.

### Regla de decisión

Usar arquitectura modular cuando se cumple **al menos dos**:

- El proyecto tendrá 3 o más features con ciclos de vida distintos.
- Es para un cliente o lo va a mantener alguien más (o tú dentro de 6 meses).
- Habrá integraciones externas reemplazables (pagos, email, storage, auth de terceros).
- Se prevé apagar o vender partes por separado.
- Lo va a construir una IA en muchas sesiones, con contexto que se pierde entre ellas.

No usarla cuando: es un script, una prueba de concepto desechable, una landing estática, o
el usuario dijo explícitamente que es temporal. En esos casos: carpeta plana, ponytail manda.

**Punto medio recomendado para proyectos de cliente:** empezar con dos o tres módulos gordos (por
ejemplo `auth`, `core-negocio`, `ui`) y dividir cuando un módulo pase de ~15 archivos o
cuando dos personas/sesiones lo toquen a la vez. Dividir tarde es barato si los imports ya
son limpios; dividir temprano es caro porque los contratos cambian cada semana.

## Estructura de un módulo

```
src/
  kernel/                  # núcleo: registro de módulos, bus de eventos, config, errores, logger
    registry.<ext>
    events.<ext>
    config.<ext>
  modules/
    <modulo>/
      contract.<ext>       # ÚNICO archivo que otros módulos pueden importar
      index.<ext>          # registra el módulo en el kernel; exporta implementación del contrato
      domain/              # lógica pura, sin framework
      application/         # casos de uso; orquesta domain + puertos
      adapters/            # implementaciones concretas: BD, HTTP, UI, SDKs externos
      __tests__/
docs/
  modulos/<modulo>.md
```

Ajustar nombres al lenguaje (`mod.rs`, `__init__.py`, `index.ts`, `module.kt`), pero mantener
el **contrato como archivo único y explícito**.

## Qué es un contrato

Un contrato tiene **solo**:

- Tipos de datos de entrada y salida (DTOs). Nunca entidades internas del módulo.
- Interfaces de los servicios que el módulo ofrece (puertos de entrada).
- Interfaces de lo que el módulo necesita del exterior (puertos de salida), que el kernel o
  los adaptadores satisfacen.
- Eventos que emite, con su payload tipado.
- Un `id` de módulo y una `version` de contrato (semver simple).

Un contrato **no** tiene: implementación, imports de frameworks, imports de otros módulos
(solo del kernel), lógica.

Cambiar un contrato = ADR corto + actualizar `docs/modulos/<modulo>.md` + buscar consumidores
(grep del import) + subir `version`.

## Comunicación entre módulos

Dos formas, y solo dos:

1. **Llamada por contrato** (síncrona): `kernel.get<ContratoPagos>('pagos').cobrar(...)`.
   Para cuando B necesita la respuesta de A ahora.
2. **Evento** (asíncrono): `kernel.events.emit(PedidoCreado, {...})`. Para cuando A no debe
   saber quién escucha. Si el módulo que escucha está apagado, el evento se pierde o se
   encola según decida el kernel; nunca rompe al emisor.

Prohibido: importar `modules/a/...` desde `modules/b/...`. Se vigila con una regla de lint
(`no-restricted-imports`, `import/no-restricted-paths`, `dependency-cruiser`, `archunit`,
`import-linter` según lenguaje). Configurarla en `/metodo:init`.

## Apagar un módulo

Un módulo se apaga en configuración (`config.modules.pagos = false` o variable de entorno).
Consecuencias que el kernel debe garantizar:

- `kernel.get('pagos')` devuelve un **Null Object** que implementa el contrato y responde de
  forma inerte (o lanza `ModuleDisabledError` tipado, según decida el ADR del proyecto).
- Los eventos que emitía ya no se emiten; los que escuchaba se ignoran.
- La UI consulta `kernel.isEnabled('pagos')` para ocultar sus pantallas.
- Los tests del módulo se saltan, no fallan.

## Relación con otras skills

- **ponytail**: dentro de un módulo, manda ponytail. La estructura domain/application/adapters
  se crea solo cuando el módulo tiene lógica que justifique separar; un módulo de 3 archivos
  puede ser `contract`, `index`, `impl`. El contrato sí es obligatorio siempre.
- **patrones-diseno**: los patrones que más aparecen aquí son Adapter (en `adapters/`),
  Strategy (implementaciones intercambiables de un puerto), Null Object (módulo apagado),
  Observer/Pub-Sub (eventos), Facade (el `index` del módulo), Registry (kernel).
- **c4-skills**: cada módulo es un *Component* (nivel 3) dentro del *Container* app. El
  kernel y los módulos se listan en `docs/arquitectura.md`.
- **documentacion**: cada módulo tiene su `.md` con propósito, contrato, eventos, dependencias
  del kernel, cómo apagarlo y decisiones propias.

## Checklist al crear un módulo

- [ ] Nombre en singular, kebab-case, sin prefijos técnicos (`pagos`, no `pagos-service`).
- [ ] `contract.<ext>` escrito **antes** que la implementación y revisado con el usuario.
- [ ] Registro en el kernel con `id`, `version`, `enabled` por config.
- [ ] Null Object o error tipado para estado apagado.
- [ ] Test del contrato (un consumidor falso lo usa) y tests de la implementación.
- [ ] `docs/modulos/<modulo>.md` creado desde `docs/modulos/_plantilla.md`.
- [ ] Entrada en `docs/README.md` y en `docs/BITACORA.md`.
- [ ] Regla de lint actualizada si el proyecto usa listas explícitas.
