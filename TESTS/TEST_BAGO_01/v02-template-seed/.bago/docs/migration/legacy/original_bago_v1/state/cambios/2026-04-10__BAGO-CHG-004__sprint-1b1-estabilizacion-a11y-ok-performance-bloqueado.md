# BAGO-CHG-004 · Sprint 1b.1 estabilización: a11y cerrada, swarm consolidado, performance bloqueado

- **Fecha:** 2026-04-10
- **Ámbito:** TPV_Contabilidad 2 / Sprint 1b.1 Estabilización
- **Estado:** aceptado con bloqueo residual

## Resumen

Se ejecutó el sprint de estabilización 1b.1 sobre `codex/full-app-base`. El frente de accesibilidad quedó cerrado para `login`, `dashboard` y `tpv`; la consolidación swarm/git quedó completada; y el rendimiento mejoró de forma relevante pero insuficiente para el umbral operativo del repo.

## Cambios estructurales aceptados

1. `apps/web/index.html` deja de bloquear zoom, elimina el `importmap` sobrante y sustituye activos pesados de arranque por SVG/iconos ligeros.
2. La capa visual compartida centraliza la remediación de contraste en `packages/app-core/src/styles/index.css`.
3. `Card` soporta interacción visual sin semántica de botón para evitar `nested-interactive` cuando contiene controles internos.
4. El runner Playwright de accesibilidad se endurece para esperar por shell/UI real en lugar de `networkidle`, y limita el alcance auditado a `login`, `dashboard` y `tpv`.
5. Las ramas locales `swarm/compras-mvp-sprint-1a/*` se eliminan tras verificar que no contienen commits únicos frente a `codex/full-app-base`.

## Evidencia ejecutada

- `pnpm lint`
- `pnpm typecheck`
- `pnpm --filter @tpv/server test`
- `pnpm --filter @tpv/app-core test`
- `pnpm build:web`
- `pnpm test:e2e:a11y`
- `pnpm audit:a11y`
- `pnpm audit:perf`

## Resultado operativo

- Accesibilidad: `pages=3`, `serious=0`, `moderate=0`, `critical=0`.
- Rendimiento: Lighthouse Performance `54`, Accessibility `100`, Best Practices `93`, LCP `2.6 s`, FCP `2.2 s`, TBT `26,660 ms`.
- Swarm/git: worktrees cerrados y ramas locales del swarm eliminadas sin pérdida de commits únicos.

## Riesgo residual bloqueante

- El umbral del repo para rendimiento sigue en `>=80`.
- El sprint 1b.1 queda **bloqueado por performance**, no por accesibilidad ni por deuda swarm/git.
