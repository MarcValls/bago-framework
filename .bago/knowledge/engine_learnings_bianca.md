# BAGO — Conocimiento del Engine BIANCA
_Aprendido en sesión 2026-05-04 — Actualizado por agente de soporte BAGO 2026-05-04_

---

## 📋 Inventario FX por escena (sprints 197-260)

> Fuente canónica: `.bago/knowledge/fx_inventory.md` (catálogo completo con estado en código)

| Escena | FX count | Sprints |
|--------|----------|---------|
| TorreBabelScene | 11 | 197,200,205,208,212,217,236,242,245,250,258 |
| BosqueInconclusasScene | 8 | 202,209,213,218,237,246,252,257 |
| LlanurasParrafoScene | 7 | 198,207,211,216,239,248,256 |
| PaginaEnBlancaScene | 5 | 201,210,244,249,260 |
| PrologueScene | 4 | 206,215,241,255 |
| CreditsScene | 4 | 203,240,251,259 |
| SegundoActoScene | 4 | 204,238,247,254 |
| SettingsScene | 4 | 199,214,243,253 |
| **TOTAL** | **47** | **sprints 197-260** |

**⚠️ Gap sprint 219-235**: No registrados en `completed_sprints`. El agente `bago-sprints-219` ejecutó 236-247 directamente. Verificar si se implementaron.

### FX nuevos confirmados en código (sprints 248-260)

Comentarios `// Sprint NNN` verificados en archivos `.ts`:

| Sprint | Escena | Efecto | Líneas en código |
|--------|--------|--------|-----------------|
| 248 | LlanurasParrafoScene | `punctuationRain` — lluvia de puntuación | L89, L501, L899 |
| 249 | PaginaEnBlancaScene | `writePulseRings` — anillos de pulso escritura | L129, L502, L704 |
| 250 | TorreBabelScene | `vocabLightning` — relámpagos vocabulario | L365, L826, L899 |
| 251 | CreditsScene | `orbitLetterRings` — anillos letras orbitando | L113, L255, L558 |
| 252 | BosqueInconclusasScene | `bioSpores` — esporas bioluminiscentes | L99, L523, L668 |
| 253 | SettingsScene | `audioEqualizer` — ecualizador ondas | L43, L231 |
| 254 | SegundoActoScene | `auroraBorealis` — aurora boreal pulsante | L50, L168 |
| 255 | PrologueScene | `pageShards` — fragmentos página volando | L160, L289, L556 |
| 256 | LlanurasParrafoScene | `glyphStream` — corriente glifos en río | L92, L521, L914 |
| 257 | BosqueInconclusasScene | `earthVeins` — venas bioluminiscentes tierra | L102, L533, L646 |
| 258 | TorreBabelScene | `inkTides` — mareas de tinta suelo | L368, L850, L1161 |
| 259 | CreditsScene | `letterConstellations` — constelaciones letras | L116, L581 |
| 260 | PaginaEnBlancaScene | `inkSpillBloom` — derrame tinta bloom tiles | L132 |

---

## 🔇 GAP CRÍTICO: AudioManager SFX sin conectar

El `AudioManager` tenía 9 funciones SFX implementadas que no estaban conectadas desde escenas en la revisión documentada:

| Función | Cuándo debería llamarse |
|---------|------------------------|
| `playFootstep()` | Cada paso de Bianca (onMove en todas las escenas) |
| `playWordPickup()` | En `_checkWordPickups()` de TorreBabelScene |
| `playBorradorTouch()` | En `onTouchBianca` de todas las escenas |
| `playBossBeat()` | Al golpear al boss / al recibir hit |
| `playResonimoLand()` | Al pisar tile resonimo (id=4/5) |
| `playInktramaSolve()` | Al resolver puzzle inktrama |
| `playDialogueBlip(pitch)` | Por cada carácter renderizado en diálogos |
| `playPerspectiveShift()` | En `onAngleChange` de BosqueInconclusasScene |
| `playMenuSelect()` | Al seleccionar opción en Settings |

**El AudioManager sí se inicializa** (main.ts línea 1727) y las zonas ambientales SÍ cambian (SceneManager.ts línea 99 con `zoneMap`). Solo faltan los SFX de eventos.

---

## 🥁 BeatTimer.onBeat nunca usado

`ResonimoMechanic.BeatTimer` tiene un callback `onBeat(beat: number)` que dispara en cada beat. Ninguna escena lo hookea. Potencial para:
- Pulsos visuales sincronizados con la música
- Spawn de partículas on-beat
- Flash de elementos HUD al ritmo

BPMs por zona: PEB=72, LP=90, BI=108, TB=140.

---

## 📦 ParticleSystem — Detalles internos

- **Shapes válidos**: `'letter' | 'word' | 'dot' | 'glyph'`  ← NUNCA usar `'circle'`
- **Glyph pool**: `✦✧✴✵✶✷✸✹⊕⊗◈` (12 chars, aleatorio)
- **Dot**: siempre renderiza `•`
- **Alpha curve**: fade-in 0→20% vida, estable 20→85%, fade-out 85→100%
- **Font**: `${size}px serif` (no monospace!)
- **Rotation**: cada partícula tiene `rotation` + `rotSpeed` (±0.5 rad/s aleatorio)
- **SpawnArea**: área de spawn alrededor del punto (wx, wy) en píxeles

---

## 👾 ElBorrador — Estados y callbacks

- **Estados**: `'patrol' | 'alert' | 'chase' | 'retreat' | 'stunned'`
- `DETECT_RADIUS = 4` tiles, `CHASE_RADIUS = 6` tiles
- `PATROL_SPEED = 1.4` tiles/s, `CHASE_SPEED = 2.2` tiles/s
- `STUN_TIME = 3.0` segundos
- **Callback**: `onTouchBianca: (() => void) | null` — hookado en PE, LP, BI, Torre
- **Método**: `stun()` — fuerza estado stunned
- **Visual alert**: `tentacleCount = 8` en alert/chase (vs 5 normal), muestra `!` flotante

---

## ✨ BrillitoEntity — Internals

- Orbita a `ORBIT_RADIUS = 28px`, `ORBIT_SPEED = 1.8 rad/s`
- **Trail propio**: 3 partículas orbitales built-in en `renderAt()` (no necesita nuestro array externo, pero nuestros arrays en escenas añaden efecto adicional)
- `getScreenPosition(biancaScreenX, biancaScreenY)` → coords reales del núcleo orbital
- `queueDialogue(id, callback)` + `checkProximityTrigger()` para diálogos por proximidad

---

## 🎵 ResonimoMechanic — Detalles

- `BeatTimer.beatDuration` = `60/bpm` segundos
- `BeatTimer.isOnBeat(tolerance=0.15)` → true si estamos a ±15% del beat
- `ResonimoManager.renderBeatHUD(ctx, x, y, w, h)` — HUD de metrónomo ya implementado
- `ResonimoInstance.isWalkable()` → solo si `state === 'solid'`
- Visual: líneas de onda animadas DENTRO del tile cuando está sólido

---

## 🔤 SimemorfMechanic — Palabras y perspectivas

- **5 Simemorfos predefinidos**: BANCO, CARA, PALO, COPA, SIERRA
- `PerspectiveManager.onAngleChange` → hookado en BosqueInconclusasScene línea 200
- `PerspectiveManager.renderPerspectiveHUD(ctx, W-84, H-84)` — ya en HUD
- `[Q]/[E]` para rotar perspectiva

---

## 🪢 TactrioRope — Física Verlet

- **Estados**: `'idle' | 'aiming' | 'flying' | 'attached' | 'retracting'`
- `config.segmentCount = 12` nodos, `segmentLength = 16px`
- **Letras del `wordLabel` escritas a lo largo de la cuerda** (cosmético)
- `[T]` para lanzar, `←→` para apuntar, `[T]` de nuevo para retraer
- `rope.canTraverse` → true cuando attached y dist > 30px
- Usado en TorreBabelScene

---

## 📖 NarrativeState — Flags persistentes

- Clave storage: `bianca_narrative_state_v1`
- API: `get/set/is/toggle/increment/reset/exportAll/importAll`
- Flags de diálogo: `dialogue_seen_${id}` → `true` (evita repetición)

---

## 🏆 AchievementSystem — 13 logros

| ID | Descripción |
|----|-------------|
| `boss_defeated` | Derrotar al Gran Borrador |
| `all_zones` | Completar Acto I |
| `all_collectibles` | Todos los coleccionables |
| `all_pliegos` | 13 pliegos reunidos |
| `full_inventory` | 22 palabras |
| `first_word` | Primera palabra recogida |
| `first_inktrama` | Primera inktrama resuelta |
| `survive_enrage` | Sobrevivir al enrage |
| `prologue_read` | Leer el prólogo |
| `no_damage_boss` | Boss sin recibir daño |
| `all_bonus` | Los 4 coleccionables bonus |
| `high_combo` | 6+ golpes seguidos |
| `all_ecos` | Todos los ecos respondidos |

Toast via: `window.game.ui.showNotification()`

---

## 🗺️ Mapa de tiles

- **id=3**: Inktrama tile
- **id=4**: Resonimo tile  
- **id=5**: Siemorf/resonimo tile
- `isoToScreen(tx, ty)` → función de **módulo** (no método de clase)
- `TILE_W = 64`, `TILE_H = 32` (estándar isométrico)

---

## 📁 Archivos TS con macOS resource forks

Hay archivos `._*.ts` (macOS resource forks) en `src/engine/`. Son invisibles para el build pero ensucian el directorio. Candidatos a limpiar.

---

## ✨ Patrones FX nuevos (sprints 236-260)

### Aurora Pattern (SegundoActoScene — Sprint 254)

```typescript
// Declaración:
private auroraTime = 0;

// En update(dt):
this.auroraTime += dt;

// En render() — fondo, antes de entidades:
const aW = W * 1.2;
for (let i = 0; i < 4; i++) {
  const phase = this.auroraTime * 0.4 + i * Math.PI * 0.5;
  const yBase = H * 0.2 + Math.sin(phase) * 40;
  const aurora = ctx.createLinearGradient(0, yBase - 60, 0, yBase + 60);
  const hue = 160 + i * 30 + Math.sin(this.auroraTime * 0.3) * 20;
  aurora.addColorStop(0, 'rgba(0,0,0,0)');
  aurora.addColorStop(0.5, `hsla(${hue}, 80%, 60%, 0.12)`);
  aurora.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = aurora;
  ctx.fillRect(-aW * 0.1, yBase - 60, aW, 120);
}
ctx.globalAlpha = 1;
```

### Equalizer Pattern (SettingsScene — Sprint 253)

```typescript
// Declaración:
private eqTime = 0;
private eqBars = Array.from({length: 12}, () => 0.3 + Math.random() * 0.7);

// En update(dt):
this.eqTime += dt;
this.eqBars = this.eqBars.map((b, i) =>
  0.2 + 0.8 * Math.abs(Math.sin(this.eqTime * (1.5 + i * 0.3) + i)));

// En render() — detrás del panel de opciones:
const barW = 8, gap = 4;
const totalW = (barW + gap) * this.eqBars.length;
const startX = W / 2 - totalW / 2;
this.eqBars.forEach((h, i) => {
  const barH = h * 60;
  const x = startX + i * (barW + gap);
  ctx.globalAlpha = 0.12;
  ctx.fillStyle = '#a0d8ff';
  ctx.fillRect(x, H / 2 - barH / 2, barW, barH);
});
ctx.globalAlpha = 1;
```

### Spore Particles Pattern (BosqueInconclusasScene — Sprint 252)

```typescript
// Declaración:
private bioSpores: Array<{x:number, y:number, vy:number, alpha:number, size:number}> = [];
private sporeTimer = 0;

// En update(dt):
this.sporeTimer += dt;
if (this.sporeTimer > 0.3) {
  this.sporeTimer = 0;
  const isoPos = isoToScreen(
    Math.floor(Math.random() * MAP_W),
    Math.floor(Math.random() * MAP_H)
  );
  this.bioSpores.push({
    x: isoPos.x + (Math.random() - 0.5) * 60,
    y: isoPos.y,
    vy: -18 - Math.random() * 20,
    alpha: 0.7 + Math.random() * 0.3,
    size: 2 + Math.random() * 3
  });
}
this.bioSpores.forEach(s => { s.y += s.vy * dt; s.alpha -= dt * 0.4; });
this.bioSpores = this.bioSpores.filter(s => s.alpha > 0);

// En render():
this.bioSpores.forEach(s => {
  ctx.globalAlpha = Math.max(0, s.alpha);
  ctx.beginPath();
  ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
  ctx.fillStyle = '#88ffcc';
  ctx.shadowColor = '#44ffaa';
  ctx.shadowBlur = 8;
  ctx.fill();
});
ctx.globalAlpha = 1;
ctx.shadowBlur = 0;
```

### Lightning Pattern (TorreBabelScene — Sprint 250)

```typescript
// Declaración:
private vocabBolts: Array<{
  x1:number, y1:number, x2:number, y2:number, alpha:number
}> = [];
private boltTimer = 0;

// En update(dt):
this.boltTimer += dt;
if (this.boltTimer > 0.8 && this.torrePositions.length >= 2) {
  this.boltTimer = 0;
  const a = this.torrePositions[Math.floor(Math.random() * this.torrePositions.length)];
  const b = this.torrePositions[Math.floor(Math.random() * this.torrePositions.length)];
  this.vocabBolts.push({x1: a.x, y1: a.y, x2: b.x, y2: b.y, alpha: 1.0});
}
this.vocabBolts.forEach(v => v.alpha -= dt * 3);
this.vocabBolts = this.vocabBolts.filter(v => v.alpha > 0);

// En render():
this.vocabBolts.forEach(v => {
  ctx.globalAlpha = Math.max(0, v.alpha) * 0.6;
  ctx.strokeStyle = '#ffffa0';
  ctx.lineWidth = 1.5;
  ctx.shadowColor = '#ffff00';
  ctx.shadowBlur = 6;
  ctx.beginPath();
  ctx.moveTo(v.x1, v.y1);
  // Zigzag simple (2-3 segmentos)
  const mx = (v.x1 + v.x2) / 2 + (Math.random() - 0.5) * 40;
  const my = (v.y1 + v.y2) / 2 + (Math.random() - 0.5) * 40;
  ctx.lineTo(mx, my);
  ctx.lineTo(v.x2, v.y2);
  ctx.stroke();
});
ctx.globalAlpha = 1;
ctx.shadowBlur = 0;
```

---

## 🔑 Reglas críticas actualizadas (sprint 197-260 validadas)

| Regla | Detalle |
|-------|---------|
| `ParticleShape` | Únicamente `'letter'|'word'|'dot'|'glyph'` — NUNCA `'circle'` |
| `isoToScreen` | Función de módulo, no método de clase. Importar, no llamar como `this.isoToScreen()` |
| Tiles resonimo | id=4 y id=5 ambos son walkable en resonimo (comprobar los dos) |
| `ctx.shadowBlur` | Siempre resetear a 0 después de usarlo (`ctx.shadowBlur = 0`) |
| `ctx.globalAlpha` | Siempre cerrar con `ctx.globalAlpha = 1` tras bloques FX |
| `ctx.save/restore` | Para FX con múltiples propiedades modificadas (transform, shadow, composite) |
| Audio import | `import { audioManager } from '../engine/AudioManager'` — es singleton exportado |
| Sprint size óptimo | 3-5 KB/sprint es ideal. Gap 248-260: ~0.35 KB/sprint (muy limpio) |

_Última actualización: 2026-05-04 (sprints 197-260 completos)_
