# Instalación · BAGO AMTEC V2.2.2 Revisión Canónica

## Naturaleza del paquete

`.bago/` es una capa de operación cognitiva pensada para vivir dentro de la raíz de un repositorio real.

## Instalación recomendada

```text
mi-repo/
├── .bago/
├── src/
├── docs/
└── ...
```

## Regla de portabilidad

Esta guía vive dentro de `.bago/` para que la carpeta sea autocontenida. La copia de `README_INSTALACION.md` en la raíz del zip es solo una comodidad para distribución.

## Pasos

1. Descomprimir el zip en la raíz del repositorio.
2. Confirmar que existe `.bago/pack.json`.
3. Leer `AGENT_START.md`.
4. Si trabajas sobre el repo real, usar `workflow_bootstrap_repo_first`.
5. Ejecutar:
   - `python3 .bago/tools/validate_manifest.py`
   - `python3 .bago/tools/validate_state.py`
   - `python3 .bago/tools/validate_pack.py`

## Criterio de instalación correcta

La instalación es correcta si:

- `.bago/` puede moverse como carpeta completa sin depender de rutas `../`,
- el manifiesto resuelve todas sus rutas,
- los validadores pasan,
- el arranque repo-first funciona como ruta oficial.

## Replicar el trigger conversacional `.bago/`

Copiar `.bago/` dentro de un repo no basta por sí solo para que el agente interprete `.bago/` como comando de arranque.
Ese comportamiento debe quedar declarado en las instrucciones del propio repo.

### Patrón recomendado

1. Copiar `.bago/` en la raíz del repo.
2. Confirmar que existe `.bago/AGENT_START.md`.
3. Crear o actualizar `AGENTS.md` en la raíz del repo.
4. Añadir una regla explícita para que `.bago/` signifique:
   - leer `.bago/AGENT_START.md`,
   - seguir la ruta oficial de arranque,
   - no listar la carpeta salvo petición explícita.

### Plantilla mínima de `AGENTS.md`

```md
# AGENTS

## BAGO Trigger

Si el usuario escribe `.bago/`, interprétalo como comando de arranque de BAGO en este repositorio.

Pasos obligatorios:

1. Leer `.bago/AGENT_START.md`.
2. Seguir la ruta oficial indicada en ese archivo.
3. No responder listando la carpeta `.bago/` salvo que el usuario pida inspección explícita del contenido.

## Compatibilidad

- `.bago/START_AGENT.md` es solo alias de compatibilidad.
- La entrada oficial es `.bago/AGENT_START.md`.
```

### Refuerzo opcional

Si el entorno soporta skills locales, se puede añadir además una skill `bago-start` con estas reglas:

- trigger: `.bago/`, `iniciar BAGO`, `activar BAGO`
- acción principal: abrir `.bago/AGENT_START.md`
- guardrail: no tratar `.bago/` como path literal por defecto

### Criterio de replicación correcta

El patrón queda bien replicado cuando, en una sesión nueva sobre el repo:

- el usuario escribe `.bago/`,
- el agente abre `.bago/AGENT_START.md`,
- el arranque sigue la ruta canónica,
- y no se responde con un simple listado del directorio.
