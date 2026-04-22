# BAGO-CHG-003 · Cierre Sprint 1b Compras + cierre de worktrees swarm

- **Fecha:** 2026-04-10
- **Ámbito:** TPV_Contabilidad 2 / Sprint 1b Compras
- **Estado:** aceptado

## Resumen

Se ejecutó el cierre técnico de Sprint 1b de Compras sobre la rama `codex/full-app-base`, corrigiendo la desalineación entre frontend y backend de `purchaseOrders`, validando gates del sprint y cerrando los worktrees del swarm `compras-mvp-sprint-1a`.

## Cambios estructurales aceptados

1. El modal de Compras deja de depender de un shape frontend ad hoc y consume el contrato real de `purchaseOrders`.
2. El selector de proveedores reutiliza el catálogo local de `entities` en vez de requerir una API nueva de suppliers para el sprint.
3. Los documentos de Sprint 1a con referencias temporales a “mañana 9 abril” pasan a histórico/contextual.
4. El cierre del swarm se ejecuta sobre worktrees limpios; las ramas permanecen existentes a la espera de la decisión de consolidación/borrado.

## Evidencia ejecutada

- `pnpm bago:start:check`
- `pnpm lint`
- `pnpm typecheck`
- `pnpm --filter @tpv/server test`
- `pnpm --filter @tpv/app-core test`
- `pnpm build:web`
- `pnpm agents:swarm:scaffold-bridge -- --check`
- `pnpm agents:swarm:check-bridge-drift`
- `pnpm agents:swarm:check-model`
- `pnpm agents:orchestrator:validate-schemas`
- `pnpm agents:orchestrator:check-drift`
- `pnpm agents:orchestrator:coverage`
- `pnpm agents:orchestrator:smoke-fixture`
- `pnpm audit:a11y`
- `pnpm audit:perf`
- `pnpm agents:swarm:close -- --feature compras-mvp-sprint-1a`
- `pnpm agents:swarm:close -- --feature compras-mvp-sprint-1a --apply`

## Riesgos residuales

- Accesibilidad: 7 violaciones activas (4 serious, 3 moderate).
- Rendimiento: Lighthouse performance 28, LCP 10.7 s, TBT 5,330 ms.
- Las ramas swarm siguen presentes aunque las worktrees ya fueron cerradas.
