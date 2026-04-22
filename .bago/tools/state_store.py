#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
state_store.py — Capa de abstracción de estado BAGO
====================================================

Desacopla las herramientas del backend concreto de almacenamiento.
Backend activo: JSON (un fichero por registro).
Backend futuro:  SQLite (skeleton listo; activar cuando todas las herramientas
                 estén migradas).

USO BÁSICO
----------
    from state_store import StateStore

    store = StateStore()                     # auto-detecta bago_root
    store = StateStore("/ruta/al/proyecto")  # ruta explícita

    # ── Colecciones ────────────────────────────────────────────────────────
    session = store.sessions.get("SES-W1-2026-04-21-001")
    closed  = store.sessions.list({"status": "closed"},
                                   sort_by="updated_at", limit=10)
    session["status"] = "closed"
    store.sessions.save(session)              # ID ya asignado

    # changes y evidences: create() auto-asigna ID secuencial
    chg = store.changes.create({"title": "...", "type": "governance"})
    # → chg["change_id"] == "BAGO-CHG-068"

    # ── Singletons ─────────────────────────────────────────────────────────
    gs = store.global_state.get()
    store.global_state.patch({"updated_at": "..."})
    # ADVERTENCIA patch(): reemplaza claves de primer nivel completas.
    # Para objetos anidados usar el patrón: get → mutar → set

    # ── Batch-write (best-effort) ──────────────────────────────────────────
    with store.transaction() as txn:
        txn.sessions.save(session)
        txn.changes.save(chg)
        txn.evidences.save(evd)
        txn.global_state.patch(updates)

    # ── Inventario ─────────────────────────────────────────────────────────
    inv = store.inventory()
    # → {"sessions": 50, "changes": 53, "evidences": 50, "evaluations": 6}

MIGRACIÓN PENDIENTE
-------------------
Migrar estas herramientas antes de activar el backend SQLite:

  MIGRADAS
  ✅ generate_task_closure.py
  ✅ cosecha.py  (delegado a generate_task_closure)

  PENDIENTES
  ⏳ pack_dashboard.py         ⏳ audit_v2.py
  ⏳ auto_mode.py              ⏳ efficiency_meter.py
  ⏳ stale_detector.py         ⏳ validate_state.py
  ⏳ session_preflight.py      ⏳ session_opener.py
  ⏳ bago_debug.py             ⏳ show_task.py
  ⏳ context_map.py            ⏳ repo_context_guard.py
  ⏳ bago_on.py / repo_on.py   ⏳ reconcile_state.py
  ⏳ session_stats.py          ⏳ personality_panel.py
  ⏳ v2_close_checklist.py     ⏳ workflow_selector.py
  ⏳ vertice_activator.py      ⏳ emit_ideas.py
"""

from __future__ import annotations

import json
import threading
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── Excepciones ───────────────────────────────────────────────────────────────

class StateStoreError(Exception):
    """Error base de StateStore."""

class RecordNotFoundError(StateStoreError):
    """El registro solicitado no existe."""

class DuplicateIdError(StateStoreError):
    """Intento de crear un registro con ID ya existente."""

class BackendNotEnabledError(StateStoreError):
    """El backend solicitado no está habilitado todavía."""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _atomic_write(path: Path, content: str) -> None:
    """Escribe content en path de forma atómica (tmp → rename)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(path)
    except Exception:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _apply_filters(records: list, filters: dict | None) -> list:
    if not filters:
        return records
    return [r for r in records if all(r.get(k) == v for k, v in filters.items())]


def _apply_sort_limit(records: list, sort_by: str, descending: bool,
                      limit: int | None) -> list:
    records = sorted(records, key=lambda r: r.get(sort_by) or "", reverse=descending)
    if limit is not None:
        records = records[:limit]
    return records


# ══════════════════════════════════════════════════════════════════════════════
# BACKENDS DE COLECCIÓN
# ══════════════════════════════════════════════════════════════════════════════

class CollectionBackend(ABC):
    """Protocolo de backend para una colección de registros."""

    @abstractmethod
    def get(self, record_id: str) -> "dict | None": ...

    @abstractmethod
    def list_all(self) -> list: ...

    @abstractmethod
    def save(self, record: dict, id_field: str) -> None: ...

    @abstractmethod
    def delete(self, record_id: str, id_field: str) -> bool: ...

    @abstractmethod
    def all_ids(self) -> list: ...


class JsonCollectionBackend(CollectionBackend):
    """
    Backend JSON: un fichero por registro en un directorio.
    Actualmente en producción.
    """

    _SKIP = {"README", ".DS_Store"}

    def __init__(self, directory: Path, id_field: str) -> None:
        self._dir = directory
        self._id_field = id_field

    def _path(self, record_id: str) -> Path:
        return self._dir / f"{record_id}.json"

    def get(self, record_id: str) -> "dict | None":
        p = self._path(record_id)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def list_all(self) -> list:
        result = []
        for f in self._dir.glob("*.json"):
            if f.stem in self._SKIP or f.stem.startswith("."):
                continue
            try:
                result.append(json.loads(f.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                pass
        return result

    def save(self, record: dict, id_field: str) -> None:
        record_id = record.get(id_field)
        if not record_id:
            raise StateStoreError(f"Record missing required field '{id_field}'")
        _atomic_write(
            self._path(record_id),
            json.dumps(record, indent=2, ensure_ascii=False),
        )

    def delete(self, record_id: str, id_field: str) -> bool:
        p = self._path(record_id)
        if p.exists():
            p.unlink()
            return True
        return False

    def all_ids(self) -> list:
        return [
            f.stem for f in self._dir.glob("*.json")
            if f.stem not in self._SKIP and not f.stem.startswith(".")
        ]


class SqliteCollectionBackend(CollectionBackend):
    """
    Backend SQLite — SKELETON (no activado).

    Esquema de tabla híbrido propuesto (columnas indexadas + blob raw):
        CREATE TABLE <collection> (
            id          TEXT PRIMARY KEY,
            status      TEXT,
            task_type   TEXT,
            type        TEXT,
            created_at  TEXT,
            updated_at  TEXT,
            raw_json    TEXT NOT NULL
        );

    PARA ACTIVAR:
        1. Migrar todas las herramientas de la lista PENDIENTES al StateStore.
        2. Añadir "sqlite" a _VALID_BACKENDS en este fichero.
        3. Cambiar state/store_config.json → {"backend": "sqlite"}.
        4. Ejecutar: python3 state_store.py --migrate-to-sqlite
    """

    def __init__(self, db_path: Path, table: str, id_field: str) -> None:
        raise BackendNotEnabledError(
            "SQLite backend no habilitado. "
            "Migra todas las herramientas a StateStore antes de activarlo. "
            "Ver lista PENDIENTES en el docstring de state_store.py."
        )

    def get(self, record_id: str):
        raise BackendNotEnabledError("SQLite backend no habilitado.")

    def list_all(self):
        raise BackendNotEnabledError("SQLite backend no habilitado.")

    def save(self, record, id_field):
        raise BackendNotEnabledError("SQLite backend no habilitado.")

    def delete(self, record_id, id_field):
        raise BackendNotEnabledError("SQLite backend no habilitado.")

    def all_ids(self):
        raise BackendNotEnabledError("SQLite backend no habilitado.")


# ══════════════════════════════════════════════════════════════════════════════
# COLLECTION STORE (fachada pública)
# ══════════════════════════════════════════════════════════════════════════════

class CollectionStore:
    """
    API pública para una colección (sessions, changes, evidences).

    Parámetros:
        backend     — implementación de CollectionBackend
        id_field    — nombre del campo ID ("session_id", "change_id", …)
        id_prefix   — prefijo para IDs secuenciales ("BAGO-CHG", "BAGO-EVD")
        sequential  — True si create() puede auto-asignar IDs numéricos
    """

    def __init__(self, backend: CollectionBackend, id_field: str,
                 id_prefix: str = "", sequential: bool = True) -> None:
        self._backend    = backend
        self._id_field   = id_field
        self._id_prefix  = id_prefix
        self._sequential = sequential
        self._lock       = threading.Lock()

    # ── Lectura ───────────────────────────────────────────────────────────

    def get(self, record_id: str) -> "dict | None":
        """Devuelve el registro con ese ID, o None si no existe."""
        return self._backend.get(record_id)

    def list(self, filters: "dict | None" = None, *,
             sort_by: str = "updated_at", descending: bool = True,
             limit: "int | None" = None) -> list:
        """
        Devuelve registros filtrados, ordenados y limitados.

        filters   — dict de igualdad exacta, p.ej. {"status": "closed"}
        sort_by   — campo por el que ordenar
        descending — True = más reciente primero
        limit     — número máximo de resultados
        """
        records = _apply_filters(self._backend.list_all(), filters)
        return _apply_sort_limit(records, sort_by, descending, limit)

    def count(self, filters: "dict | None" = None) -> int:
        """Cuenta registros, opcionalmente filtrados."""
        if filters:
            return len(_apply_filters(self._backend.list_all(), filters))
        return len(self._backend.all_ids())

    # ── Escritura ─────────────────────────────────────────────────────────

    def save(self, record: dict) -> None:
        """
        Persiste un registro con ID ya asignado (insert o update).
        Para sessions (IDs contextuales SES-W1-…), usar siempre este método.
        """
        self._backend.save(record, self._id_field)

    def create(self, record: dict) -> dict:
        """
        Auto-asigna el siguiente ID secuencial y persiste el registro.
        Devuelve el registro con el ID asignado.

        Solo válido para colecciones secuenciales (changes, evidences).
        Para sessions, usar save() con ID pre-asignado.
        """
        if not self._sequential:
            raise StateStoreError(
                f"La colección '{self._id_field}' usa IDs asignados por el caller. "
                "Usa save() con el ID ya establecido en el registro."
            )
        record = dict(record)
        with self._lock:
            num = self._next_num()
            record[self._id_field] = f"{self._id_prefix}-{num:03d}"
            self._backend.save(record, self._id_field)
        return record

    def delete(self, record_id: str) -> bool:
        """Elimina el registro. Devuelve True si existía."""
        return self._backend.delete(record_id, self._id_field)

    def next_num(self) -> int:
        """
        Devuelve el próximo número secuencial disponible.
        Útil para callers que construyen IDs complejos (p.ej. SES-W2-2026-04-21-001)
        antes de llamar a save().
        """
        return self._next_num()

    def _next_num(self) -> int:
        nums = []
        for id_str in self._backend.all_ids():
            parts = id_str.split("-")
            if parts[-1].isdigit():
                nums.append(int(parts[-1]))
        return max(nums, default=0) + 1


# ══════════════════════════════════════════════════════════════════════════════
# SINGLETON STORE (fachada pública)
# ══════════════════════════════════════════════════════════════════════════════

class SingletonStore:
    """
    API pública para un fichero JSON singleton
    (global_state, repo_context, pending_task, user_profile…).
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    def get(self) -> dict:
        """Devuelve el contenido del fichero, o {} si no existe."""
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def set(self, data: dict) -> None:
        """Sobreescribe el fichero de forma atómica."""
        _atomic_write(
            self._path,
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        )

    def patch(self, updates: dict) -> dict:
        """
        Fusión shallow: actualiza claves de primer nivel y persiste.
        Devuelve el dict resultante.

        ADVERTENCIA: los valores de primer nivel se reemplazan en bloque.
        Para objetos anidados (inventory, sprint_status, last_validation)
        usa el patrón: get → mutar → set.
        """
        current = self.get()
        current.update(updates)
        self.set(current)
        return current

    def exists(self) -> bool:
        return self._path.exists()

    def clear(self) -> None:
        """Elimina el fichero (útil para pending_task tras completar)."""
        if self._path.exists():
            self._path.unlink()


# ══════════════════════════════════════════════════════════════════════════════
# TRANSACTION (batch-write best-effort)
# ══════════════════════════════════════════════════════════════════════════════

class _WriteOp:
    __slots__ = ("kind", "target", "data", "id_field")

    def __init__(self, kind: str, target: Any, data: Any, id_field: str = "") -> None:
        self.kind     = kind
        self.target   = target
        self.data     = data
        self.id_field = id_field


class Transaction:
    """
    Contexto de batch-write best-effort.

    Acumula operaciones de escritura y las ejecuta todas al salir del bloque
    `with`. Si alguna falla, las anteriores ya se habrán persistido (no hay
    rollback), pero el error se propaga para que el caller lo detecte.

    Uso:
        with store.transaction() as txn:
            txn.sessions.save(session)
            txn.changes.save(chg)
            txn.global_state.patch(updates)
    """

    def __init__(self, store: "StateStore") -> None:
        self._store = store
        self._ops: list = []
        self.sessions     = _CollectionProxy(store.sessions,    self._ops)
        self.changes      = _CollectionProxy(store.changes,     self._ops)
        self.evidences    = _CollectionProxy(store.evidences,   self._ops)
        self.global_state = _SingletonProxy(store.global_state, self._ops)
        self.repo_context = _SingletonProxy(store.repo_context, self._ops)
        self.pending_task = _SingletonProxy(store.pending_task, self._ops)
        self.user_profile = _SingletonProxy(store.user_profile, self._ops)

    def __enter__(self) -> "Transaction":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is None:
            self._flush()
        return False

    def _flush(self) -> None:
        for op in self._ops:
            if op.kind == "collection_save":
                op.target.save(op.data, op.id_field)
            elif op.kind == "singleton_set":
                op.target.set(op.data)
            elif op.kind == "singleton_patch":
                op.target.patch(op.data)


class _CollectionProxy:
    def __init__(self, store: CollectionStore, ops: list) -> None:
        self._store = store
        self._ops   = ops

    def save(self, record: dict) -> None:
        self._ops.append(
            _WriteOp("collection_save", self._store._backend, record,
                     self._store._id_field)
        )

    def create(self, record: dict) -> dict:
        # create() necesita el lock y el ID inmediatamente
        return self._store.create(record)

    def get(self, record_id: str) -> "dict | None":
        return self._store.get(record_id)

    def list(self, *args, **kwargs) -> list:
        return self._store.list(*args, **kwargs)

    def count(self, *args, **kwargs) -> int:
        return self._store.count(*args, **kwargs)


class _SingletonProxy:
    def __init__(self, store: SingletonStore, ops: list) -> None:
        self._store = store
        self._ops   = ops

    def set(self, data: dict) -> None:
        self._ops.append(_WriteOp("singleton_set", self._store, data))

    def patch(self, updates: dict) -> None:
        self._ops.append(_WriteOp("singleton_patch", self._store, updates))

    def get(self) -> dict:
        return self._store.get()

    def exists(self) -> bool:
        return self._store.exists()

    def clear(self) -> None:
        self._store.clear()


# ══════════════════════════════════════════════════════════════════════════════
# STATE STORE (punto de entrada)
# ══════════════════════════════════════════════════════════════════════════════

_VALID_BACKENDS = {"json"}   # añadir "sqlite" aquí cuando esté listo


class StateStore:
    """
    Punto de entrada único para todo el estado BAGO.
    Auto-detecta el bago_root desde la ubicación de este fichero
    si no se especifica explícitamente.
    """

    def __init__(self, bago_root: "str | Path | None" = None) -> None:
        if bago_root is None:
            bago_root = Path(__file__).resolve().parents[2]
        self._root      = Path(bago_root).resolve()
        self._bago_dir  = self._root / ".bago"
        self._state_dir = self._bago_dir / "state"

        backend_name = self._read_backend_config()
        self._build_stores(backend_name)

    def _read_backend_config(self) -> str:
        cfg = self._state_dir / "store_config.json"
        if cfg.exists():
            try:
                name = json.loads(cfg.read_text(encoding="utf-8")).get("backend", "json")
                if name not in _VALID_BACKENDS:
                    raise StateStoreError(
                        f"Backend '{name}' no válido o no habilitado todavía. "
                        f"Backends disponibles: {sorted(_VALID_BACKENDS)}"
                    )
                return name
            except (json.JSONDecodeError, OSError):
                pass
        return "json"

    def _build_stores(self, backend_name: str) -> None:
        sd = self._state_dir
        if backend_name == "json":
            self.sessions = CollectionStore(
                JsonCollectionBackend(sd / "sessions",  "session_id"),
                id_field="session_id", id_prefix="SES", sequential=False,
            )
            self.changes = CollectionStore(
                JsonCollectionBackend(sd / "changes",   "change_id"),
                id_field="change_id", id_prefix="BAGO-CHG", sequential=True,
            )
            self.evidences = CollectionStore(
                JsonCollectionBackend(sd / "evidences", "evidence_id"),
                id_field="evidence_id", id_prefix="BAGO-EVD", sequential=True,
            )
        else:
            raise BackendNotEnabledError(f"Backend '{backend_name}' no implementado.")

        self.global_state  = SingletonStore(sd / "global_state.json")
        self.repo_context  = SingletonStore(sd / "repo_context.json")
        self.pending_task  = SingletonStore(sd / "pending_w2_task.json")
        self.user_profile  = SingletonStore(sd / "user_personality_profile.json")

    def inventory(self) -> dict:
        """
        Devuelve los contadores reales del estado (sin depender del campo
        'inventory' manual de global_state.json).
        """
        evaluations = 0
        eval_dir = self._state_dir / "evaluations"
        if eval_dir.exists():
            evaluations = len(list(eval_dir.glob("*.md")))
        return {
            "sessions":    self.sessions.count(),
            "changes":     self.changes.count(),
            "evidences":   self.evidences.count(),
            "evaluations": evaluations,
        }

    def transaction(self) -> Transaction:
        """Devuelve un contexto de batch-write. Ver clase Transaction."""
        return Transaction(self)


# ══════════════════════════════════════════════════════════════════════════════
# CLI DE UTILIDAD
# ══════════════════════════════════════════════════════════════════════════════

def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="state_store.py — utilidades de estado BAGO"
    )
    parser.add_argument("--inventory", action="store_true",
                        help="Muestra el inventario real del estado")
    parser.add_argument("--list", metavar="COLLECTION",
                        help="Lista registros de una colección (sessions|changes|evidences)")
    parser.add_argument("--filter", metavar="KEY=VALUE", action="append",
                        help="Filtro de igualdad para --list (repetible)")
    parser.add_argument("--limit", type=int, default=10,
                        help="Límite de resultados para --list (default: 10)")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="Output JSON")
    args = parser.parse_args()

    store = StateStore()

    if args.inventory:
        inv = store.inventory()
        if args.as_json:
            print(json.dumps(inv, indent=2, ensure_ascii=False))
        else:
            print("  Inventario BAGO:")
            for k, v in inv.items():
                print(f"    {k:<12} {v}")
        return

    if args.list:
        col_map = {
            "sessions":  store.sessions,
            "changes":   store.changes,
            "evidences": store.evidences,
        }
        col = col_map.get(args.list)
        if col is None:
            print(f"Colección desconocida: {args.list}. Usar: sessions|changes|evidences")
            return
        filters = {}
        for f in (args.filter or []):
            if "=" in f:
                k, v = f.split("=", 1)
                filters[k] = v
        records = col.list(filters or None, limit=args.limit)
        if args.as_json:
            print(json.dumps(records, indent=2, ensure_ascii=False))
        else:
            for r in records:
                id_val  = r.get(col._id_field, "?")
                status  = r.get("status", r.get("normalized_status", "—"))
                updated = (r.get("updated_at") or r.get("recorded_at") or "")[:10]
                title   = r.get("title") or r.get("user_goal") or r.get("summary") or ""
                print(f"  {id_val:<30} {status:<12} {updated}  {title[:50]}")
        return

    parser.print_help()


if __name__ == "__main__":
    _cli()
