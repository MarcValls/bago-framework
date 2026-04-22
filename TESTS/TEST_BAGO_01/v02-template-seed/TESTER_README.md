# BAGO 2.4-v2rc · Guía para el Tester

Gracias por probar BAGO. Este paquete contiene el framework listo para usar.

---

## Requisitos

- Python 3.9+
- Terminal con color (iTerm2, Terminal.app, Windows Terminal, etc.)

---

## Primer arranque

```bash
# 1. Descomprime el paquete en cualquier directorio
unzip BAGO_v02-template-seed_tester.zip
cd v02-template-seed

# 2. Da permiso de ejecución (solo la primera vez en macOS/Linux)
chmod +x bago

# 3. Arranca
python3 bago
```

Al ejecutar por primera vez verás:

```
┌─────────────────────────────────────────────┐
│  BAGO · Primera ejecución                   │
├─────────────────────────────────────────────┤
│  [1] Evolucionar el framework BAGO          │
│  [2] Iniciar un proyecto nuevo              │
└─────────────────────────────────────────────┘
```

- **[1]** → Usa este directorio para trabajar/evolucionar el propio framework BAGO.
- **[2]** → Introduce una ruta de destino (o pulsa Enter para usar este mismo directorio)
  y BAGO copiará el pack allí, listo para tu proyecto.

---

## Comandos disponibles

```bash
python3 bago                 # banner + estado del pack
python3 bago setup           # sincroniza contexto del repositorio
python3 bago health          # puntuación de salud del pack
python3 bago audit           # auditoría completa
python3 bago validate        # valida integridad del pack
python3 bago workflow        # selector de workflow interactivo
python3 bago dashboard       # dashboard completo
python3 bago versions        # lista cleanversions disponibles
python3 bago help            # ayuda rápida
```

---

## Qué testear

Por favor prueba y anota:

1. **Prompt de primera ejecución** — ¿aparece correctamente? ¿opciones claras?
2. **Opción [1] framework** — ¿muestra el banner sin errores?
3. **Opción [2] proyecto nuevo** — ¿copia el pack correctamente al destino elegido?
4. **Opción [2] con Enter** — ¿inicializa en el directorio actual sin errores?
5. **`bago health`** — ¿puntuación coherente?
6. **`bago workflow`** — ¿selector interactivo funciona?
7. **Segunda ejecución** — tras elegir [1] o [2], ¿ya no vuelve a preguntar?

---

## Reportar problemas

Indica:
- Sistema operativo y versión de Python (`python3 --version`)
- Comando ejecutado
- Output completo (copia/pega del terminal)
- Comportamiento esperado vs obtenido

---

*BAGO 2.4-v2rc · cleanversion v02-template-seed · 2026-04-19*
