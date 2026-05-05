# Reglas de sincronizacion Git para BAGO

Objetivo: no publicar un BAGO roto al remoto.

## Regla 1 - No push sin gate local

Antes de publicar:

```bash
python3 bago pre-push --remote
```

El gate bloquea si el arbol esta sucio, si la rama local esta por detras del upstream o si falla cualquier validador requerido.

## Regla 2 - Instalar hook versionado

En cada clon activo:

```bash
git config core.hooksPath .githooks
```

Desde ese momento `git push` ejecuta `python3 bago pre-push` antes de publicar.

## Regla 3 - Primer push con upstream

Si `main` no tiene upstream:

```bash
git push -u origin main
```

Despues de eso, el gate compara `HEAD...@{u}` para detectar ramas por detras o divergidas.

## Regla 4 - CI repite el gate

GitHub Actions ejecuta `python3 bago pre-push` para que el remoto verifique lo mismo que el entorno local.

## Regla 5 - No versionar runtime

Metadatos del volumen, modelos, binarios, snapshots, research y sesiones privadas deben permanecer ignorados. Si aparece un untracked nuevo, clasificarlo antes de commitear.
