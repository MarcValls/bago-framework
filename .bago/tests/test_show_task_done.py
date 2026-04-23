#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_show_task_done.py — Tests para show_task --done + session_close_generator.

Ejecutar:
  python3 .bago/tests/test_show_task_done.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_module(name: str, rel_path: str):
    path = ROOT / ".bago" / "tools" / rel_path
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)   # type: ignore[arg-type]
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)                   # type: ignore[union-attr]
    return mod


def _sample_task(tmp: Path) -> dict:
    task = {
        "idea_index": 1,
        "idea_title": "Cierre automático de sesión",
        "priority": 90,
        "workflow": "W7_FOCO_SESION",
        "accepted_at": "2026-04-23T00:00:00+00:00",
        "objetivo": "Generar artefacto de cierre al marcar done",
        "alcance": "show_task.py + session_close_generator.py",
        "no_alcance": "cosecha completa",
        "archivos_candidatos": [".bago/tools/show_task.py"],
        "validacion_minima": ["artefacto creado en sessions/"],
        "metric": "SESSION_CLOSE_*.md existe",
        "siguiente_paso": "Ejecutar show_task --done",
        "status": "pending",
    }
    task_file = tmp / "pending_w2_task.json"
    task_file.write_text(json.dumps(task, ensure_ascii=False, indent=2))
    return task


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

passed = 0
failed = 0


def ok(name: str) -> None:
    global passed
    passed += 1
    print(f"  ✅ PASS  {name}")


def fail(name: str, reason: str) -> None:
    global failed
    failed += 1
    print(f"  ❌ FAIL  {name}: {reason}")


# --- Test 1: session_close_generator.generate() crea el artefacto ----------
def test_generate_creates_file():
    gen = _load_module("session_close_generator", "session_close_generator.py")
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        task = _sample_task(tmp)
        out  = tmp / "SESSION_CLOSE_test.md"
        result = gen.generate(task=task, out_path=out)
        if not result.exists():
            fail("generate_creates_file", "archivo no creado")
            return
        content = result.read_text(encoding="utf-8")
        if "Cierre automático de sesión" not in content:
            fail("generate_creates_file", "idea_title no aparece en el contenido")
            return
        ok("generate_creates_file")


# --- Test 2: artefacto contiene secciones clave ----------------------------
def test_generate_content_sections():
    gen = _load_module("session_close_generator", "session_close_generator.py")
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        task = _sample_task(tmp)
        out  = tmp / "SESSION_CLOSE_sections.md"
        gen.generate(task=task, out_path=out)
        content = out.read_text(encoding="utf-8")
        required = [
            "## Tarea completada",
            "## Resumen de cambios",
            "## Estado del sistema al cierre",
        ]
        missing = [s for s in required if s not in content]
        if missing:
            fail("generate_content_sections", f"faltan secciones: {missing}")
        else:
            ok("generate_content_sections")


# --- Test 3: _register_implemented() registra el título --------------------
def test_register_implemented():
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        # patch IMPLEMENTED_FILE via monkey-patch
        st = _load_module("show_task_test3", "show_task.py")
        impl_file = tmp / "implemented_ideas.json"
        st.IMPLEMENTED_FILE = impl_file

        task = {"idea_title": "Mi idea de prueba", "idea_index": 42}
        st._register_implemented(task)

        if not impl_file.exists():
            fail("register_implemented", "implemented_ideas.json no creado")
            return
        data = json.loads(impl_file.read_text())
        titles = [e["title"] for e in data.get("implemented", [])]
        if "Mi idea de prueba" not in titles:
            fail("register_implemented", f"título no registrado; encontrado: {titles}")
        else:
            ok("register_implemented")


# --- Test 4: _generate_close_artifact() no rompe con task vacío ------------
def test_generate_close_artifact_no_crash():
    st = _load_module("show_task_test4", "show_task.py")
    try:
        # with empty task — should not raise, just warn
        st._generate_close_artifact({})
        ok("generate_close_artifact_no_crash")
    except Exception as exc:
        fail("generate_close_artifact_no_crash", str(exc))


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print()
    print("  ┌─────────────────────────────────────────┐")
    print("  │  test_show_task_done.py                 │")
    print("  └─────────────────────────────────────────┘")
    print()
    test_generate_creates_file()
    test_generate_content_sections()
    test_register_implemented()
    test_generate_close_artifact_no_crash()
    print()
    total = passed + failed
    print(f"  Resultado: {passed}/{total} tests pasados")
    print()
    sys.exit(0 if failed == 0 else 1)
