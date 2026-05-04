# BAGO-CHG-005

- **Fecha:** 2026-04-11
- **Ámbito:** Sprint 1b.1 estabilización web
- **Tipo:** cierre de remediación no funcional

## Resultado

Se cerró el bloque corto y exclusivo de optimización de rendimiento web. El repo pasó de un estado bloqueado por Lighthouse Performance `54` a un estado validado con `Performance 90`, `Accessibility 100`, `Best Practices 96`, `LCP 1.2 s` y `TBT 420 ms` en `docs/status/perf-audit-latest.md`.

## Cambios aplicados

1. Migración de Tailwind desde runtime (`tailwindcss-cdn.js`) a build-time con `postcss.config.cjs` y `tailwind.config.cjs`.
2. Eliminación del coste de main thread asociado al bootstrap CSS runtime.
3. Reparto de carga inicial mediante `React.lazy` en `App`, `AppMainContent` y `AppModals`, evitando importar pantallas/modales cerrados en el primer render.
4. Ajuste de chunking en Vite para dejar de forzar un chunk global de `lucide-react`.
5. Revalidación de accesibilidad tras la migración CSS y corrección final de contraste en tema claro.
6. Parametrización del puerto del runner Playwright a11y mediante `PLAYWRIGHT_A11Y_PORT` para permitir validaciones limpias sin depender de un dev server previo en `4173`.

## Verificación ejecutada

1. `pnpm --filter @tpv/web build`
2. `pnpm typecheck`
3. `pnpm audit:perf`
4. `pnpm lint`
5. `pnpm --filter @tpv/app-core test`
6. `CI=1 PLAYWRIGHT_A11Y_PORT=4175 pnpm audit:a11y`

## Decisión

Sprint 1b.1 deja de estar bloqueado por performance. El bloque de estabilización no funcional queda operativo y listo para cierre en la rama canónica.
