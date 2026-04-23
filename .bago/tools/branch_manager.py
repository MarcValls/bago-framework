#!/usr/bin/env python3
"""branch_manager.py — Herramienta #136: Gestión integral de ramas git.

Permite listar, crear, cambiar, renombrar y eliminar ramas git desde
el entorno BAGO, con validación de nomenclatura integrada y datos de
comparación (ahead/behind) respecto a la rama base.

Uso:
    bago branches                       → lista todas las ramas locales
    bago branches list [--remote]       → lista ramas (--remote incluye remotas)
    bago branches create <nombre>       → crea y cambia a nueva rama
    bago branches switch <nombre>       → cambia a una rama existente
    bago branches rename <viejo> <nuevo>→ renombra una rama local
    bago branches delete <nombre>       → elimina rama (pide confirmación)
    bago branches delete <nombre> -f   → elimina rama sin confirmación
    bago branches info [<nombre>]       → info detallada de una rama
    bago branches compare <a> <b>       → compara dos ramas (ahead/behind)
    bago branches --json                → output JSON de la lista
    bago branches --test                → self-tests

Opciones globales:
    --style STYLE   Estilo para validar nombres (gitflow|simple|jira|numeric|bago)
    --json          Output en JSON donde aplique
    --test          Ejecutar self-tests
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Colores ───────────────────────────────────────────────────────────────────
_RED  = "\033[0;31m"
_GRN  = "\033[0;32m"
_YEL  = "\033[0;33m"
_CYN  = "\033[0;36m"
_RST  = "\033[0m"
_BOLD = "\033[1m"

# ── Estilos de nomenclatura (mismos que branch_check.py) ─────────────────────
STYLES: dict[str, str] = {
    "gitflow": r'^(feature|bugfix|hotfix|release)/[\w\-\.]+$|^(develop|main|master|HEAD)$',
    "simple":  r'^(feat|fix|docs|chore|refactor|test|perf|ci|style|revert)/[\w\-\.]+$|^(main|master|develop|HEAD)$',
    "jira":    r'^[A-Z][A-Z0-9]+-\d+(/[\w\-\.]+)?$|^(main|master|develop|HEAD)$',
    "numeric": r'^(task|issue|sprint|ticket)/\d+(-[\w\-\.]+)?$|^(main|master|develop|HEAD)$',
    "bago":    r'^(S\d+|W\d+)/[\w\-\.]+$|^bago-[\w\-\.]+$|^(main|master|develop|HEAD)$',
    "copilot": r'^copilot/[\w\-\.]+$|^(main|master|develop|HEAD)$',
}


# ── Helpers git ───────────────────────────────────────────────────────────────

def _run(cmd: list[str], cwd: Optional[str] = None) -> tuple[int, str, str]:
    """Ejecuta un comando git; devuelve (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=15
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except FileNotFoundError:
        return 127, "", "git no encontrado en PATH"
    except subprocess.TimeoutExpired:
        return 1, "", "timeout ejecutando git"


def _find_git_root(start: Optional[str] = None) -> Optional[Path]:
    cwd = Path(start) if start else Path.cwd()
    current = cwd
    while True:
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def _current_branch(git_root: Path) -> str:
    _, out, _ = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(git_root))
    return out or "HEAD"


def _branch_exists(git_root: Path, name: str, remote: bool = False) -> bool:
    if remote:
        _, out, _ = _run(["git", "branch", "-r"], cwd=str(git_root))
        return any(name in line.strip() for line in out.splitlines())
    _, out, _ = _run(["git", "branch", "--list", name], cwd=str(git_root))
    return bool(out.strip())


def _validate_name(name: str, style: str) -> tuple[bool, str]:
    pattern = STYLES.get(style)
    if not pattern:
        return True, ""
    if re.match(pattern, name):
        return True, ""
    return False, f"No cumple el estilo '{style}'"


# ── Operaciones de rama ───────────────────────────────────────────────────────

def list_branches(git_root: Path, include_remote: bool = False,
                  as_json: bool = False) -> int:
    """Lista ramas locales (y remotas si se pide)."""
    current = _current_branch(git_root)

    # Ramas locales
    _, local_out, _ = _run(
        ["git", "branch", "--format=%(refname:short)|%(objectname:short)|%(subject)|%(authordate:short)"],
        cwd=str(git_root)
    )
    local_branches = []
    for line in local_out.splitlines():
        parts = line.split("|", 3)
        if not parts:
            continue
        bname = parts[0].strip()
        if not bname:
            continue
        sha   = parts[1].strip() if len(parts) > 1 else ""
        subj  = parts[2].strip() if len(parts) > 2 else ""
        date  = parts[3].strip() if len(parts) > 3 else ""

        # Ahead / behind vs default branch (main o master)
        ahead, behind = _ahead_behind(git_root, bname)

        local_branches.append({
            "name": bname,
            "sha": sha,
            "last_commit": subj[:60],
            "date": date,
            "current": bname == current,
            "ahead": ahead,
            "behind": behind,
            "type": "local",
        })

    # Ramas remotas
    remote_branches: list[dict] = []
    if include_remote:
        _, rem_out, _ = _run(
            ["git", "branch", "-r", "--format=%(refname:short)|%(objectname:short)|%(subject)|%(authordate:short)"],
            cwd=str(git_root)
        )
        for line in rem_out.splitlines():
            parts = line.split("|", 3)
            bname = parts[0].strip()
            if not bname or "HEAD" in bname:
                continue
            remote_branches.append({
                "name": bname,
                "sha": parts[1].strip() if len(parts) > 1 else "",
                "last_commit": (parts[2].strip() if len(parts) > 2 else "")[:60],
                "date": parts[3].strip() if len(parts) > 3 else "",
                "current": False,
                "type": "remote",
            })

    all_branches = local_branches + remote_branches

    if as_json:
        print(json.dumps(all_branches, indent=2, ensure_ascii=False))
        return 0

    print(f"\n{_BOLD}  Ramas{_RST} — {git_root.name}\n")
    for b in local_branches:
        marker   = f"{_GRN}*{_RST}" if b["current"] else " "
        sync_str = ""
        if b["ahead"] or b["behind"]:
            sync_str = f"  {_YEL}↑{b['ahead']} ↓{b['behind']}{_RST}"
        date_str = f"  {_CYN}{b['date']}{_RST}" if b["date"] else ""
        print(f"  {marker} {_BOLD}{b['name']}{_RST}{date_str}{sync_str}")
        if b["last_commit"]:
            print(f"      {b['last_commit']}")

    if remote_branches:
        print(f"\n{_BOLD}  Remotas:{_RST}")
        for b in remote_branches:
            date_str = f"  {_CYN}{b['date']}{_RST}" if b["date"] else ""
            print(f"    {b['name']}{date_str}")
            if b["last_commit"]:
                print(f"      {b['last_commit']}")
    print()
    return 0


def _default_base(git_root: Path) -> str:
    """Detecta la rama base por defecto (main o master)."""
    for base in ("main", "master"):
        if _branch_exists(git_root, base):
            return base
    return "HEAD"


def _ahead_behind(git_root: Path, branch: str) -> tuple[int, int]:
    """Devuelve (ahead, behind) respecto a la rama base."""
    base = _default_base(git_root)
    if branch == base:
        return 0, 0
    _, out, err = _run(
        ["git", "rev-list", "--left-right", "--count", f"{base}...{branch}"],
        cwd=str(git_root)
    )
    if not out or err:
        return 0, 0
    parts = out.split()
    if len(parts) == 2:
        try:
            return int(parts[1]), int(parts[0])  # ahead, behind
        except ValueError:
            return 0, 0
    return 0, 0


def create_branch(git_root: Path, name: str, style: str = "gitflow") -> int:
    """Crea una nueva rama y cambia a ella."""
    # Validar nombre
    ok, reason = _validate_name(name, style)
    if not ok:
        print(f"{_YEL}⚠  Nombre de rama '{name}' no válido ({reason}){_RST}")
        print(f"   Continúa bajo tu responsabilidad.")

    if _branch_exists(git_root, name):
        print(f"{_RED}✗ La rama '{name}' ya existe{_RST}")
        return 1

    rc, _, err = _run(["git", "checkout", "-b", name], cwd=str(git_root))
    if rc != 0:
        print(f"{_RED}✗ Error al crear la rama: {err}{_RST}")
        return rc

    print(f"{_GRN}✔ Rama '{name}' creada y activa{_RST}")
    return 0


def switch_branch(git_root: Path, name: str) -> int:
    """Cambia a una rama existente."""
    if not _branch_exists(git_root, name):
        # Intentar desde remote
        if _branch_exists(git_root, name, remote=True):
            rc, _, err = _run(["git", "checkout", "--track", f"origin/{name}"], cwd=str(git_root))
        else:
            print(f"{_RED}✗ La rama '{name}' no existe{_RST}")
            return 1
    else:
        rc, _, err = _run(["git", "checkout", name], cwd=str(git_root))

    if rc != 0:
        print(f"{_RED}✗ Error al cambiar de rama: {err}{_RST}")
        return rc

    print(f"{_GRN}✔ Cambiado a '{name}'{_RST}")
    return 0


def rename_branch(git_root: Path, old_name: str, new_name: str, style: str = "gitflow") -> int:
    """Renombra una rama local."""
    if not _branch_exists(git_root, old_name):
        print(f"{_RED}✗ La rama '{old_name}' no existe{_RST}")
        return 1

    ok, reason = _validate_name(new_name, style)
    if not ok:
        print(f"{_YEL}⚠  Nombre '{new_name}' no válido ({reason}){_RST}")

    rc, _, err = _run(["git", "branch", "-m", old_name, new_name], cwd=str(git_root))
    if rc != 0:
        print(f"{_RED}✗ Error al renombrar: {err}{_RST}")
        return rc

    print(f"{_GRN}✔ Rama renombrada: '{old_name}' → '{new_name}'{_RST}")
    return 0


def delete_branch(git_root: Path, name: str, force: bool = False) -> int:
    """Elimina una rama local (con confirmación si no forzado)."""
    if not _branch_exists(git_root, name):
        print(f"{_RED}✗ La rama '{name}' no existe{_RST}")
        return 1

    current = _current_branch(git_root)
    if name == current:
        print(f"{_RED}✗ No se puede eliminar la rama activa '{name}'{_RST}")
        return 1

    if not force:
        answer = input(f"  ¿Eliminar la rama '{name}'? [s/N]: ").strip().lower()
        if answer not in ("s", "si", "sí", "y", "yes"):
            print("  Cancelado.")
            return 0

    flag = "-D" if force else "-d"
    rc, _, err = _run(["git", "branch", flag, name], cwd=str(git_root))
    if rc != 0:
        print(f"{_RED}✗ Error al eliminar: {err}")
        print(f"  Usa -f para forzar (rama no fusionada){_RST}")
        return rc

    print(f"{_GRN}✔ Rama '{name}' eliminada{_RST}")
    return 0


def branch_info(git_root: Path, name: Optional[str] = None) -> int:
    """Muestra información detallada de una rama."""
    if name is None:
        name = _current_branch(git_root)

    if not _branch_exists(git_root, name):
        print(f"{_RED}✗ La rama '{name}' no existe{_RST}")
        return 1

    ahead, behind = _ahead_behind(git_root, name)

    _, log_out, _ = _run(
        ["git", "log", "--oneline", "-10", name],
        cwd=str(git_root)
    )
    _, created_out, _ = _run(
        ["git", "log", "--format=%ad", "--date=short", name],
        cwd=str(git_root)
    )
    dates = [l.strip() for l in created_out.splitlines() if l.strip()]
    first_date = dates[-1] if dates else "—"
    last_date  = dates[0]  if dates else "—"

    _, sha_out, _ = _run(["git", "rev-parse", "--short", name], cwd=str(git_root))
    base = _default_base(git_root)

    print(f"\n{_BOLD}  Rama: {name}{_RST}")
    print(f"  SHA         : {sha_out}")
    print(f"  Primer commit: {first_date}")
    print(f"  Último commit: {last_date}")
    print(f"  Base         : {base}")
    print(f"  Adelante     : {ahead} commit(s)")
    print(f"  Atrás        : {behind} commit(s)")
    print(f"\n{_BOLD}  Últimos 10 commits:{_RST}")
    for line in log_out.splitlines():
        print(f"    {line}")
    print()
    return 0


def compare_branches(git_root: Path, branch_a: str, branch_b: str) -> int:
    """Compara dos ramas mostrando ahead/behind y commits distintos."""
    for name in (branch_a, branch_b):
        if not _branch_exists(git_root, name):
            print(f"{_RED}✗ La rama '{name}' no existe{_RST}")
            return 1

    _, out, _ = _run(
        ["git", "rev-list", "--left-right", "--count", f"{branch_a}...{branch_b}"],
        cwd=str(git_root)
    )
    parts = out.split() if out else []
    behind_a = int(parts[0]) if len(parts) == 2 else 0
    ahead_a  = int(parts[1]) if len(parts) == 2 else 0

    _, commits_out, _ = _run(
        ["git", "log", "--oneline", f"{branch_a}..{branch_b}"],
        cwd=str(git_root)
    )
    commits_in_b = commits_out.splitlines()

    _, commits_out2, _ = _run(
        ["git", "log", "--oneline", f"{branch_b}..{branch_a}"],
        cwd=str(git_root)
    )
    commits_in_a = commits_out2.splitlines()

    print(f"\n{_BOLD}  Comparando: {branch_a} ↔ {branch_b}{_RST}\n")
    print(f"  {branch_b} tiene {ahead_a} commit(s) que {branch_a} no tiene")
    print(f"  {branch_a} tiene {behind_a} commit(s) que {branch_b} no tiene")

    if commits_in_b:
        print(f"\n{_BOLD}  Solo en {branch_b}:{_RST}")
        for c in commits_in_b[:10]:
            print(f"    {c}")
    if commits_in_a:
        print(f"\n{_BOLD}  Solo en {branch_a}:{_RST}")
        for c in commits_in_a[:10]:
            print(f"    {c}")
    print()
    return 0


# ── CLI ───────────────────────────────────────────────────────────────────────

def _usage() -> None:
    print(f"""
{_BOLD}branch_manager.py{_RST} — Gestión de ramas git

Uso:
  bago branches                        → listar ramas locales
  bago branches list [--remote]        → listar (--remote incluye remotas)
  bago branches create <nombre>        → crear y cambiar a nueva rama
  bago branches switch <nombre>        → cambiar a una rama
  bago branches rename <viejo> <nuevo> → renombrar rama local
  bago branches delete <nombre> [-f]  → eliminar rama (-f fuerza)
  bago branches info [<nombre>]        → info detallada
  bago branches compare <a> <b>        → comparar dos ramas
  bago branches --json                 → output JSON de la lista

Opciones:
  --style  STYLE  Estilo de nomenclatura: gitflow|simple|jira|numeric|bago|copilot
  --json          Output JSON
  --test          Self-tests
""")


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        _usage()
        return 0

    if "--test" in argv:
        return _run_tests()

    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]

    style = "gitflow"
    if "--style" in argv:
        idx = argv.index("--style")
        if idx + 1 < len(argv):
            style = argv[idx + 1]
            argv = argv[:idx] + argv[idx + 2:]

    git_root = _find_git_root()
    if git_root is None:
        print(f"{_RED}✗ No se encontró repositorio git{_RST}")
        return 1

    sub = argv[0] if argv else "list"

    if sub in ("list", "ls"):
        include_remote = "--remote" in argv or "-r" in argv
        return list_branches(git_root, include_remote=include_remote, as_json=as_json)

    elif sub == "create":
        if len(argv) < 2:
            print(f"{_RED}✗ Falta el nombre de la rama{_RST}"); return 1
        return create_branch(git_root, argv[1], style=style)

    elif sub in ("switch", "checkout", "sw"):
        if len(argv) < 2:
            print(f"{_RED}✗ Falta el nombre de la rama{_RST}"); return 1
        return switch_branch(git_root, argv[1])

    elif sub == "rename":
        if len(argv) < 3:
            print(f"{_RED}✗ Uso: bago branches rename <viejo> <nuevo>{_RST}"); return 1
        return rename_branch(git_root, argv[1], argv[2], style=style)

    elif sub in ("delete", "del", "rm"):
        if len(argv) < 2:
            print(f"{_RED}✗ Falta el nombre de la rama{_RST}"); return 1
        force = "-f" in argv or "--force" in argv
        return delete_branch(git_root, argv[1], force=force)

    elif sub == "info":
        name = argv[1] if len(argv) >= 2 else None
        return branch_info(git_root, name)

    elif sub == "compare":
        if len(argv) < 3:
            print(f"{_RED}✗ Uso: bago branches compare <a> <b>{_RST}"); return 1
        return compare_branches(git_root, argv[1], argv[2])

    else:
        # Argumento desconocido: tratar como lista si no parece un subcomando
        if sub.startswith("-") or not sub.isalpha():
            return list_branches(git_root, as_json=as_json)
        print(f"{_RED}✗ Subcomando desconocido: '{sub}'{_RST}")
        _usage()
        return 1


# ── Self-tests ────────────────────────────────────────────────────────────────

def _run_tests() -> int:
    import tempfile, os

    print("Tests de branch_manager.py...")
    fails: list[str] = []

    def ok(n: str) -> None:
        print(f"  OK: {n}")

    def fail(n: str, m: str) -> None:
        fails.append(n)
        print(f"  FAIL: {n}: {m}")

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        env = {**os.environ, "GIT_AUTHOR_NAME": "Tester",
               "GIT_AUTHOR_EMAIL": "t@t.com",
               "GIT_COMMITTER_NAME": "Tester",
               "GIT_COMMITTER_EMAIL": "t@t.com"}

        def git(*args: str) -> tuple[int, str]:
            r = subprocess.run(["git"] + list(args), cwd=str(root),
                               capture_output=True, text=True, env=env)
            return r.returncode, r.stdout.strip()

        # Setup minimal repo
        git("init")
        git("config", "user.email", "t@t.com")
        git("config", "user.name", "Tester")
        (root / "f.txt").write_text("hello\n")
        git("add", ".")
        git("commit", "-m", "init")
        # Rename to main if needed
        git("branch", "-M", "main")

        # T1 — validate_name gitflow valid
        v, r = _validate_name("feature/my-feature", "gitflow")
        if v:
            ok("validate:gitflow_valid")
        else:
            fail("validate:gitflow_valid", r)

        # T2 — validate_name gitflow invalid
        v, r = _validate_name("my-random-branch", "gitflow")
        if not v:
            ok("validate:gitflow_invalid")
        else:
            fail("validate:gitflow_invalid", "debería ser inválida")

        # T3 — create_branch
        rc = create_branch(root, "feature/test-branch")
        if rc == 0 and _branch_exists(root, "feature/test-branch"):
            ok("create_branch")
        else:
            fail("create_branch", f"rc={rc}")

        # T4 — switch_branch (back to main)
        rc = switch_branch(root, "main")
        if rc == 0:
            cur = _current_branch(root)
            if cur == "main":
                ok("switch_branch")
            else:
                fail("switch_branch", f"branch actual={cur}")
        else:
            fail("switch_branch", f"rc={rc}")

        # T5 — rename_branch
        rc = rename_branch(root, "feature/test-branch", "feature/renamed-branch")
        if rc == 0 and _branch_exists(root, "feature/renamed-branch"):
            ok("rename_branch")
        else:
            fail("rename_branch", f"rc={rc}")

        # T6 — branch_info (no crash)
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = branch_info(root, "main")
        if rc == 0 and "main" in buf.getvalue():
            ok("branch_info")
        else:
            fail("branch_info", f"rc={rc}")

        # T7 — ahead_behind same branch
        a, b = _ahead_behind(root, "main")
        if a == 0 and b == 0:
            ok("ahead_behind_same")
        else:
            fail("ahead_behind_same", f"ahead={a} behind={b}")

        # T8 — delete_branch (force)
        rc = delete_branch(root, "feature/renamed-branch", force=True)
        if rc == 0 and not _branch_exists(root, "feature/renamed-branch"):
            ok("delete_branch")
        else:
            fail("delete_branch", f"rc={rc}")

        # T9 — delete active branch should fail
        rc = delete_branch(root, "main", force=True)
        if rc != 0:
            ok("delete_active_branch_rejected")
        else:
            fail("delete_active_branch_rejected", "eliminó la rama activa")

        # T10 — _find_git_root
        subdir = root / "subdir"
        subdir.mkdir()
        found = _find_git_root(str(subdir))
        if found == root:
            ok("find_git_root")
        else:
            fail("find_git_root", f"encontrado={found}")

    total = 10
    passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails:
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
