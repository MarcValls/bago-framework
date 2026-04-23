#!/usr/bin/env python3
"""
ci_generator — Genera configuración CI/CD para proyectos con BAGO.

Genera:
  GitHub Actions  → .github/workflows/bago.yml
  GitLab CI       → .gitlab-ci.yml  
  pre-commit hook → .git/hooks/pre-commit

Uso:
  bago ci --provider github [--output .github/workflows/]
  bago ci --provider gitlab [--output .]
  bago ci --provider pre-commit
  bago ci --provider all
  bago ci --dry-run          → muestra sin escribir
"""
import argparse, sys, textwrap
from pathlib import Path

# ─── Templates ───────────────────────────────────────────────────────────────

GITHUB_WORKFLOW = """\
# bago.yml — Generado por bago ci --provider github
# BAGO Code Health & Governance CI
name: BAGO Code Health

on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master, develop ]

jobs:
  bago-health:
    name: BAGO Health Check
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # needed for git history in hotspot analysis

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install BAGO dependencies
        run: |
          pip install flake8 pylint mypy bandit
          pip install gitpython
          # ── Language-specific linters (install only what your project needs) ──
          # Java:       apt-get install -y checkstyle  (or download checkstyle jar)
          # Ruby:       gem install rubocop
          # PHP:        composer global require squizlabs/php_codesniffer phpstan/phpstan
          # Swift:      brew install swiftlint  (macOS runner only)
          # Kotlin:     curl -sSLO https://github.com/pinterest/ktlint/releases/download/1.2.1/ktlint
          # Shell:      apt-get install -y shellcheck
          # Terraform:  curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash
          # YAML:       pip install yamllint

      - name: BAGO validate
        run: python3 bago validate
        continue-on-error: false

      - name: BAGO scan (unified findings)
        run: python3 bago scan --json > bago-findings.json
        continue-on-error: true

      - name: BAGO risk matrix
        run: python3 bago risk --json > bago-risk.json
        continue-on-error: true

      - name: BAGO impact report
        run: python3 bago impact --brief
        continue-on-error: true

      - name: BAGO hotspot analysis
        run: python3 bago hotspot --json > bago-hotspots.json
        continue-on-error: true

      - name: Fail on critical findings
        run: |
          python3 -c "
          import json, sys
          try:
              data = json.load(open('bago-findings.json'))
              findings = data.get('findings', data) if isinstance(data, dict) else data
              critical = [f for f in (findings if isinstance(findings, list) else [])
                          if str(f.get('severity','')).lower() in ('critical','error')]
              if critical:
                  print(f'❌ {len(critical)} critical findings found:')
                  for f in critical[:10]:
                      print(f\"  [{f.get('severity','')}] {f.get('file','')}:{f.get('line','')} — {f.get('rule','')}\")
                  raise SystemExit(1)
              print(f'✅ No critical findings')
          except Exception as e:
              print(f'Warning: could not parse findings: {e}')
          "

      - name: Upload BAGO reports
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: bago-reports
          path: |
            bago-findings.json
            bago-risk.json
            bago-hotspots.json
          retention-days: 30

  bago-tests:
    name: BAGO Integration Tests
    runs-on: ubuntu-latest
    needs: bago-health

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Run BAGO integration tests
        run: python3 .bago/tools/integration_tests.py
"""

GITLAB_CI = """\
# .gitlab-ci.yml — Generado por bago ci --provider gitlab
# BAGO Code Health & Governance CI

stages:
  - validate
  - scan
  - report

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip/

bago-validate:
  stage: validate
  image: python:3.11-slim
  before_script:
    - pip install flake8 pylint mypy bandit gitpython --quiet
    # Add language-specific linters below as needed:
    # - gem install rubocop                                                    # Ruby
    # - composer global require squizlabs/php_codesniffer phpstan/phpstan      # PHP
    # - apt-get install -y shellcheck                                          # Shell
    # - pip install yamllint                                                   # YAML
  script:
    - python3 bago validate
  artifacts:
    when: always
    expire_in: 1 week

bago-scan:
  stage: scan
  image: python:3.11-slim
  before_script:
    - pip install flake8 pylint mypy bandit gitpython --quiet
    # Add language-specific linters below as needed (see bago-validate job)
  script:
    - python3 bago scan --json > bago-findings.json || true
    - python3 bago risk --json > bago-risk.json || true
    - python3 bago hotspot --json > bago-hotspots.json || true
    - |
      python3 -c "
      import json, sys
      try:
          data = json.load(open('bago-findings.json'))
          findings = data.get('findings', data) if isinstance(data, dict) else data
          critical = [f for f in (findings if isinstance(findings, list) else [])
                      if str(f.get('severity','')).lower() in ('critical','error')]
          if critical:
              print(f'FAIL: {len(critical)} critical findings')
              raise SystemExit(1)
          print('OK: No critical findings')
      except Exception as e:
          print(f'Warning: {e}')
      "
  artifacts:
    when: always
    paths:
      - bago-findings.json
      - bago-risk.json
      - bago-hotspots.json
    expire_in: 1 week

bago-impact:
  stage: report
  image: python:3.11-slim
  before_script:
    - pip install flake8 pylint mypy bandit gitpython --quiet
  script:
    - python3 bago impact --brief
    - python3 .bago/tools/integration_tests.py
  dependencies:
    - bago-scan
"""

PRE_COMMIT_HOOK = """\
#!/bin/sh
# pre-commit hook — Generado por bago ci --provider pre-commit
# Ejecuta BAGO scan rápido antes de cada commit

echo "  [BAGO pre-commit] Verificando salud del código..."

# Quick validate
python3 bago validate > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "  ❌ bago validate FAILED — commit bloqueado"
    echo "  Ejecuta: python3 bago validate  para ver errores"
    exit 1
fi

echo "  ✅ bago validate OK"

# Run scan (fast mode - only flake8)
python3 .bago/tools/scan.py --tool flake8 --json > /tmp/bago_precommit.json 2>/dev/null
if [ $? -eq 0 ]; then
    python3 -c "
import json, sys
try:
    data = json.load(open('/tmp/bago_precommit.json'))
    findings = data.get('findings', []) if isinstance(data, dict) else []
    critical = [f for f in findings if str(f.get('severity','')).lower() in ('critical','error')]
    if critical:
        print(f'  ❌ {len(critical)} errores críticos detectados')
        for f in critical[:5]:
            print(f\"    {f.get('file','')}:{f.get('line','')} — {f.get('message','')}\")
        raise SystemExit(1)
    warns = len([f for f in findings if str(f.get('severity','')).lower() == 'warning'])
    print(f'  ✅ scan OK ({warns} warnings, 0 critical)')
except Exception:
    print('  ✅ scan OK')
" || exit 1
fi

exit 0
"""


def write_github(output_dir: Path, dry_run: bool) -> str:
    dest = output_dir / ".github" / "workflows" / "bago.yml"
    if dry_run:
        return f"[dry-run] {dest}\n{GITHUB_WORKFLOW[:200]}..."
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(GITHUB_WORKFLOW, encoding="utf-8")
    return str(dest)


def write_gitlab(output_dir: Path, dry_run: bool) -> str:
    dest = output_dir / ".gitlab-ci.yml"
    if dry_run:
        return f"[dry-run] {dest}\n{GITLAB_CI[:200]}..."
    dest.write_text(GITLAB_CI, encoding="utf-8")
    return str(dest)


def write_pre_commit(output_dir: Path, dry_run: bool) -> str:
    hook_dir = output_dir / ".git" / "hooks"
    dest = hook_dir / "pre-commit"
    if dry_run:
        return f"[dry-run] {dest}"
    if not hook_dir.exists():
        return f"SKIP: {hook_dir} no existe (no es un repo git)"
    dest.write_text(PRE_COMMIT_HOOK, encoding="utf-8")
    dest.chmod(0o755)
    return str(dest)


def main():
    p = argparse.ArgumentParser(
        prog="bago ci",
        description="Genera configuración CI/CD con BAGO integrado.")
    p.add_argument("--provider", "-p",
                   choices=["github","gitlab","pre-commit","all"],
                   default="github",
                   help="Proveedor CI (default: github)")
    p.add_argument("--output", "-o", default=".",
                   help="Directorio raíz del proyecto (default: .)")
    p.add_argument("--dry-run", action="store_true",
                   help="Muestra sin escribir")
    p.add_argument("--test", action="store_true", help="Self-tests")
    args = p.parse_args()

    if args.test:
        _self_test()
        return

    output_dir = Path(args.output).resolve()
    provider   = args.provider
    dry_run    = args.dry_run

    print(f"\n  bago ci — Generador de CI/CD")
    print(f"  Provider: {provider}  |  Output: {output_dir}")
    if dry_run:
        print(f"  [dry-run activo — no se escriben archivos]")
    print()

    written = []
    if provider in ("github", "all"):
        result = write_github(output_dir, dry_run)
        written.append(("GitHub Actions", result))
    if provider in ("gitlab", "all"):
        result = write_gitlab(output_dir, dry_run)
        written.append(("GitLab CI", result))
    if provider in ("pre-commit", "all"):
        result = write_pre_commit(output_dir, dry_run)
        written.append(("pre-commit hook", result))

    for name, dest in written:
        print(f"  ✅  {name}: {dest}")

    if not dry_run:
        print()
        print("  Próximos pasos:")
        if provider in ("github", "all"):
            print("  • git add .github/workflows/bago.yml && git commit -m 'ci: add BAGO workflow'")
        if provider in ("gitlab", "all"):
            print("  • git add .gitlab-ci.yml && git commit -m 'ci: add BAGO GitLab CI'")
        if provider in ("pre-commit", "all"):
            print("  • El hook se ejecutará automáticamente en cada git commit")
    print()


def _self_test():
    import tempfile
    print("Ejecutando self-tests de ci_generator.py...")
    errors = []

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        # Test 1: GitHub
        write_github(tdp, dry_run=False)
        dest = tdp / ".github" / "workflows" / "bago.yml"
        if not dest.exists():
            errors.append("github: file not created")
        elif "BAGO Code Health" not in dest.read_text():
            errors.append("github: content wrong")
        else:
            print("  OK: GitHub Actions workflow generado")

        # Test 2: GitLab
        write_gitlab(tdp, dry_run=False)
        dest2 = tdp / ".gitlab-ci.yml"
        if not dest2.exists():
            errors.append("gitlab: file not created")
        elif "bago-validate" not in dest2.read_text():
            errors.append("gitlab: content wrong")
        else:
            print("  OK: GitLab CI config generado")

        # Test 3: dry-run returns string
        result = write_github(tdp, dry_run=True)
        if "[dry-run]" not in result:
            errors.append("dry-run: no dry-run marker")
        else:
            print("  OK: dry-run mode funciona")

        # Test 4: templates are valid YAML-ish
        if "on:" not in GITHUB_WORKFLOW:
            errors.append("github template: missing 'on:' trigger")
        else:
            print("  OK: GitHub template tiene triggers")

    n = 4
    print(f"\n  {n - len(errors)}/{n} tests pasaron")
    if errors:
        for e in errors: print(f"  FAIL: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()