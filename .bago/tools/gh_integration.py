#!/usr/bin/env python3
"""
bago gh — integración con GitHub: check runs y comentarios inline en PRs.

Usa la GitHub API (via token o gh CLI si disponible) para:
  - Publicar hallazgos del scan como GitHub Check Run con anotaciones
  - Publicar comentarios inline en PRs con hallazgos por archivo/línea
  - Filtrar por severidad antes de publicar

Uso:
    bago gh status                         → estado de integración (token, repo)
    bago gh checks                         → crea/actualiza Check Run con último scan
    bago gh checks --scan SCAN-20260421    → usa scan específico
    bago gh checks --severity warning      → solo errores y warnings
    bago gh pr <número>                    → comenta hallazgos en PR (inline review)
    bago gh pr <número> --dry-run          → preview sin publicar
    bago gh config --token TOKEN           → guarda token GitHub
    bago gh config --repo owner/repo       → guarda repo destino
    bago gh --test                         → tests integrados
"""
import argparse, json, os, sys, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

TOOLS_DIR = Path(__file__).parent
sys.path.insert(0, str(TOOLS_DIR))
import findings_engine as fe

BAGO_ROOT  = Path(__file__).parent.parent
CONFIG_DIR = BAGO_ROOT / "state" / "gh_config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = CONFIG_DIR / "config.json"

BOLD="\033[1m"; DIM="\033[2m"; RESET="\033[0m"
RED="\033[31m"; GREEN="\033[32m"; YELLOW="\033[33m"; CYAN="\033[36m"

SEV_TO_ANNOTATION = {"error": "failure", "warning": "warning", "info": "notice", "hint": "notice"}
SEV_ORD = {"error": 0, "warning": 1, "info": 2, "hint": 3}


# ─── Config ──────────────────────────────────────────────────────────────────

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            pass
    return {}


def save_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2) + "\n")


def get_token(cfg: dict) -> str | None:
    return cfg.get("token") or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def get_repo(cfg: dict) -> str | None:
    """Returns 'owner/repo' string or None."""
    if cfg.get("repo"):
        return cfg["repo"]
    # Try to detect from git remote
    try:
        import subprocess
        r = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, cwd=str(BAGO_ROOT.parent)
        )
        url = r.stdout.strip()
        import re
        m = re.search(r"github\.com[:/](.+?/[^.]+?)(?:\.git)?$", url)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


def get_head_sha(cfg: dict) -> str | None:
    """Get current HEAD commit SHA."""
    try:
        import subprocess
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=str(BAGO_ROOT.parent)
        )
        return r.stdout.strip() or None
    except Exception:
        return None


# ─── GitHub API ──────────────────────────────────────────────────────────────

class GitHubAPI:
    BASE = "https://api.github.com"

    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo  = repo

    def _request(self, method: str, path: str, body: dict | None = None) -> tuple:
        """Returns (status_code, response_dict)."""
        url  = f"{self.BASE}{path}"
        data = json.dumps(body).encode() if body else None
        req  = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            try:
                body_err = json.loads(e.read())
            except Exception:
                body_err = {"message": str(e)}
            return e.code, body_err
        except Exception as e:
            return 0, {"message": str(e)}

    def create_check_run(self, name: str, head_sha: str, title: str,
                         summary: str, annotations: list, conclusion: str) -> tuple:
        """Create a GitHub Check Run with annotations."""
        # GitHub limits 50 annotations per request
        chunks = [annotations[i:i+50] for i in range(0, max(1, len(annotations)), 50)]
        first_chunk = chunks[0] if chunks else []

        body = {
            "name":       name,
            "head_sha":   head_sha,
            "status":     "completed",
            "conclusion": conclusion,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "output": {
                "title":       title,
                "summary":     summary,
                "annotations": first_chunk,
            },
        }
        status, resp = self._request("POST", f"/repos/{self.repo}/check-runs", body)

        # Add remaining annotations in batches via PATCH
        if status in (200, 201) and len(chunks) > 1:
            check_id = resp.get("id")
            for chunk in chunks[1:]:
                patch_body = {"output": {"title": title, "summary": summary,
                                         "annotations": chunk}}
                self._request("PATCH", f"/repos/{self.repo}/check-runs/{check_id}", patch_body)

        return status, resp

    def create_pr_review(self, pr_number: int, body: str, comments: list) -> tuple:
        """Create a PR review with inline comments."""
        # Get PR head SHA first
        status, pr_data = self._request("GET", f"/repos/{self.repo}/pulls/{pr_number}")
        if status != 200:
            return status, pr_data
        commit_id = pr_data.get("head", {}).get("sha", "")

        review_body = {
            "commit_id": commit_id,
            "body":      body,
            "event":     "COMMENT",
            "comments":  comments[:50],  # GitHub limit
        }
        return self._request("POST",
                              f"/repos/{self.repo}/pulls/{pr_number}/reviews",
                              review_body)

    def test_auth(self) -> tuple:
        return self._request("GET", "/user")


# ─── Finding → GitHub annotation ────────────────────────────────────────────

def finding_to_annotation(f: fe.Finding, repo_root: str = "") -> dict:
    """Convert a Finding to a GitHub annotation dict."""
    path = f.file
    if repo_root and path.startswith(repo_root):
        path = path[len(repo_root):].lstrip("/")

    message = f.message
    if f.fix_suggestion:
        message += f"\n\n**Fix sugerido:** {f.fix_suggestion}"
    if f.autofixable:
        message += "\n\n✅ *Autofixable con `bago fix --apply`*"

    return {
        "path":             path,
        "start_line":       f.line,
        "end_line":         f.line,
        "annotation_level": SEV_TO_ANNOTATION.get(f.severity, "notice"),
        "message":          message,
        "title":            f"[{f.rule}] {f.source}",
    }


def finding_to_pr_comment(f: fe.Finding, repo_root: str = "") -> dict:
    """Convert a Finding to a GitHub PR review comment."""
    path = f.file
    if repo_root and path.startswith(repo_root):
        path = path[len(repo_root):].lstrip("/")

    body = f"`{f.rule}` **{f.severity}**: {f.message}"
    if f.fix_suggestion:
        body += f"\n> **Fix:** {f.fix_suggestion}"
    if f.autofixable:
        body += "\n> ✅ Autofixable con `bago fix --apply`"

    return {
        "path":      path,
        "line":      f.line,
        "side":      "RIGHT",
        "body":      body,
    }


# ─── Commands ────────────────────────────────────────────────────────────────

def cmd_status(cfg: dict):
    token = get_token(cfg)
    repo  = get_repo(cfg)
    sha   = get_head_sha(cfg)
    db    = fe.FindingsDB.latest()

    print(f"\n  {BOLD}BAGO GitHub Integration{RESET}\n")
    print(f"  Token:    {'✅ configurado' if token else '❌ no configurado'}")
    print(f"  Repo:     {repo or '❌ no detectado'}")
    print(f"  HEAD SHA: {sha[:12] if sha else '❌'}")
    print(f"  Último scan: {db.scan_id if db else '❌ sin scans'}")

    if token:
        api    = GitHubAPI(token, repo or "")
        status, resp = api.test_auth()
        if status == 200:
            print(f"  Auth:     {GREEN}✅ OK como {resp.get('login','?')}{RESET}")
        else:
            print(f"  Auth:     {RED}❌ Error {status}: {resp.get('message','')}{RESET}")
    print()


def cmd_checks(cfg: dict, scan_id: str | None, min_severity: str, dry_run: bool):
    token = get_token(cfg)
    repo  = get_repo(cfg)
    sha   = get_head_sha(cfg)

    if not token:
        print(f"{RED}✗ Sin token. Usa: bago gh config --token TOKEN{RESET}")
        sys.exit(1)
    if not repo:
        print(f"{RED}✗ Sin repo. Usa: bago gh config --repo owner/repo{RESET}")
        sys.exit(1)
    if not sha:
        print(f"{RED}✗ No se puede obtener el SHA del HEAD{RESET}")
        sys.exit(1)

    db = fe.FindingsDB.load(scan_id) if scan_id else fe.FindingsDB.latest()
    if db is None:
        print(f"{RED}✗ Sin scan disponible. Ejecuta 'bago scan' primero.{RESET}")
        sys.exit(1)

    sev_ord = SEV_ORD.get(min_severity, 3)
    findings = [f for f in db.findings if SEV_ORD.get(f.severity, 3) <= sev_ord]
    repo_root = str(BAGO_ROOT.parent) + "/"

    annotations = [finding_to_annotation(f, repo_root) for f in findings[:100]]
    summary_data = db._summary()
    errs  = summary_data["by_severity"].get("error", 0)
    warns = summary_data["by_severity"].get("warning", 0)
    conclusion = "failure" if errs > 0 else "warning" if warns > 0 else "success"

    title   = f"BAGO Scan — {len(findings)} hallazgos"
    summary = (f"**{errs} errores**, {warns} warnings, "
               f"{summary_data['autofixable']} autofixables.\n\n"
               f"Ejecuta `bago fix --apply` para corregir automáticamente.")

    if dry_run:
        print(f"\n  {DIM}[DRY-RUN]{RESET} Check Run que se publicaría:")
        print(f"  Repo:        {repo}")
        print(f"  SHA:         {sha[:12]}")
        print(f"  Conclusion:  {conclusion}")
        print(f"  Annotations: {len(annotations)}")
        print(f"  Title:       {title}\n")
        return

    api = GitHubAPI(token, repo)
    status, resp = api.create_check_run(
        name="BAGO Code Analysis", head_sha=sha,
        title=title, summary=summary,
        annotations=annotations, conclusion=conclusion
    )

    if status in (200, 201):
        url = resp.get("html_url", "")
        print(f"\n  {GREEN}✅ Check Run creado:{RESET} {url}\n")
    else:
        print(f"\n  {RED}✗ Error {status}:{RESET} {resp.get('message','')}\n")


def cmd_pr(cfg: dict, pr_number: int, min_severity: str, dry_run: bool):
    token = get_token(cfg)
    repo  = get_repo(cfg)

    if not token:
        print(f"{RED}✗ Sin token. Usa: bago gh config --token TOKEN{RESET}")
        sys.exit(1)
    if not repo:
        print(f"{RED}✗ Sin repo. Usa: bago gh config --repo owner/repo{RESET}")
        sys.exit(1)

    db = fe.FindingsDB.latest()
    if db is None:
        print(f"{RED}✗ Sin scan. Ejecuta 'bago scan' primero.{RESET}")
        sys.exit(1)

    sev_ord  = SEV_ORD.get(min_severity, 1)  # default: warnings+errors only
    findings = [f for f in db.findings if SEV_ORD.get(f.severity, 3) <= sev_ord]
    repo_root = str(BAGO_ROOT.parent) + "/"
    comments = [finding_to_pr_comment(f, repo_root) for f in findings[:50]]

    s = db._summary()
    review_body = (
        f"## BAGO Code Analysis — {db.scan_id}\n\n"
        f"| Severidad | Cantidad |\n|-----------|----------|\n"
        f"| 🔴 Errors  | {s['by_severity'].get('error',0)} |\n"
        f"| 🟡 Warnings | {s['by_severity'].get('warning',0)} |\n"
        f"| 🔵 Info    | {s['by_severity'].get('info',0)} |\n\n"
        f"**{s['autofixable']} hallazgos autofixables** — ejecuta `bago fix --apply`"
    )

    if dry_run:
        print(f"\n  {DIM}[DRY-RUN]{RESET} Review que se publicaría en PR #{pr_number}:")
        print(f"  Comentarios inline: {len(comments)}")
        print(f"  Body preview:\n{review_body[:300]}\n")
        return

    api = GitHubAPI(token, repo)
    status, resp = api.create_pr_review(pr_number, review_body, comments)

    if status in (200, 201):
        print(f"\n  {GREEN}✅ Review publicado en PR #{pr_number}{RESET}\n")
    else:
        print(f"\n  {RED}✗ Error {status}:{RESET} {resp.get('message','')}\n")


def cmd_config(cfg: dict, token: str | None, repo: str | None):
    if token:
        cfg["token"] = token
        print(f"  {GREEN}✓ Token guardado{RESET}")
    if repo:
        cfg["repo"] = repo
        print(f"  {GREEN}✓ Repo configurado: {repo}{RESET}")
    if token or repo:
        save_config(cfg)
    else:
        print(f"  Usa --token TOKEN y/o --repo owner/repo")


def run_tests():
    print("Ejecutando tests de gh_integration.py...")
    errors = 0
    def ok(n): print(f"  OK: {n}")
    def fail(n, m):
        nonlocal errors; errors += 1; print(f"  FAIL: {n} — {m}")

    # T1: finding_to_annotation path stripping
    f = fe.Finding(id="A",severity="error",file="/repo/src/main.py",line=5,col=0,
                   rule="E001",source="flake8",message="test error",
                   fix_suggestion="fix it",autofixable=True)
    ann = finding_to_annotation(f, "/repo/")
    if ann["path"] == "src/main.py" and ann["annotation_level"] == "failure":
        ok("gh:annotation_path_strip")
    else:
        fail("gh:annotation_path_strip", str(ann))

    # T2: finding_to_annotation contains fix suggestion
    if "fix it" in ann["message"] and "Autofixable" in ann["message"]:
        ok("gh:annotation_fix_in_message")
    else:
        fail("gh:annotation_fix_in_message", ann["message"])

    # T3: finding_to_pr_comment structure
    cmt = finding_to_pr_comment(f, "/repo/")
    if cmt["path"] == "src/main.py" and cmt["line"] == 5 and "E001" in cmt["body"]:
        ok("gh:pr_comment_structure")
    else:
        fail("gh:pr_comment_structure", str(cmt))

    # T4: load_config returns dict
    cfg = load_config()
    if isinstance(cfg, dict):
        ok("gh:load_config_dict")
    else:
        fail("gh:load_config_dict", str(type(cfg)))

    # T5: get_repo detects from git remote (or None gracefully)
    cfg2 = {}
    repo = get_repo(cfg2)  # may be None if no git remote, should not crash
    if repo is None or "/" in str(repo):
        ok("gh:get_repo_graceful")
    else:
        fail("gh:get_repo_graceful", str(repo))

    # T6: SEV_TO_ANNOTATION mapping completeness
    for sev in ("error","warning","info","hint"):
        if sev not in SEV_TO_ANNOTATION:
            fail("gh:sev_mapping", f"missing {sev}"); break
    else:
        ok("gh:sev_mapping")

    total=6; passed=total-errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors: sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="bago gh", add_help=False)
    sub = parser.add_subparsers(dest="subcmd")

    sub.add_parser("status")

    p_checks = sub.add_parser("checks")
    p_checks.add_argument("--scan",     default=None)
    p_checks.add_argument("--severity", default="warning")
    p_checks.add_argument("--dry-run",  action="store_true")

    p_pr = sub.add_parser("pr")
    p_pr.add_argument("pr_number", type=int)
    p_pr.add_argument("--severity", default="warning")
    p_pr.add_argument("--dry-run",  action="store_true")

    p_cfg = sub.add_parser("config")
    p_cfg.add_argument("--token", default=None)
    p_cfg.add_argument("--repo",  default=None)

    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    if args.test:
        run_tests(); return

    cfg = load_config()
    if args.subcmd == "status" or not args.subcmd:
        cmd_status(cfg)
    elif args.subcmd == "checks":
        cmd_checks(cfg, args.scan, args.severity, args.dry_run)
    elif args.subcmd == "pr":
        cmd_pr(cfg, args.pr_number, args.severity, args.dry_run)
    elif args.subcmd == "config":
        cmd_config(cfg, args.token, args.repo)

if __name__ == "__main__":
    main()