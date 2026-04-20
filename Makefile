# ─────────────────────────────────────────────────────────────────────────────
# Makefile BAGO — empaquetado, instalación y validación
# Uso desde la carpeta que contiene .bago/ y el script bago
# ─────────────────────────────────────────────────────────────────────────────

BAGO_DIR   := .bago
TOOLS      := $(BAGO_DIR)/tools
DIST       := $(BAGO_DIR)/dist
VERSION    := $(shell python3 -c "import json; print(json.loads(open('$(BAGO_DIR)/pack.json').read())['version'])" 2>/dev/null || echo "unknown")
TIMESTAMP  := $(shell date +%Y%m%d_%H%M%S)
PACK_NAME  := BAGO_$(VERSION)_$(TIMESTAMP)

# Shell (detecta zsh o bash)
SHELL_RC   := $(shell [ -f ~/.zshrc ] && echo ~/.zshrc || echo ~/.bashrc)
BAGO_PATH  := $(shell pwd)/bago

.PHONY: help banner validate check-pure pack deploy install uninstall clean

# ─── Ayuda ────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  BAGO · Sistema de empaquetado"
	@echo "  ─────────────────────────────"
	@echo "  make banner     → muestra el cartel BAGO ACTIVO"
	@echo "  make validate   → valida manifest + state + pack"
	@echo "  make pack       → crea zip con timestamp en dist/"
	@echo "  make deploy     → crea zip limpio sin historial (para nuevos proyectos)"
	@echo "  make install    → instala alias 'bago' en $(SHELL_RC)"
	@echo "  make uninstall  → elimina alias 'bago' de $(SHELL_RC)"
	@echo "  make clean      → limpia __pycache__ del pack"
	@echo ""

# ─── Banner ───────────────────────────────────────────────────────────────────
banner:
	@python3 $(TOOLS)/bago_banner.py

# ─── Validación ───────────────────────────────────────────────────────────────
validate:
	@python3 $(TOOLS)/validate_pack.py

# ─── Pureza de validación/reporting ───────────────────────────────────────────
check-pure:
	@git diff --quiet || (echo "KO: working tree is dirty before checks"; git diff --stat; exit 1)
	@python3 bago validate
	@python3 bago health
	@git diff --quiet || (echo "KO: validate/health introduced changes"; git diff --stat; git diff; exit 1)
	@echo "OK: validate and health are side-effect free"

# ─── Pack: regenera TREE+CHECKSUMS y crea zip ─────────────────────────────────
pack:
	@echo ""
	@echo "  📦 Paso 1/4: sincronizando TREE.txt y CHECKSUMS.sha256..."
	@python3 -c "from pathlib import Path; import hashlib; root = Path('.bago'); entries = sorted(str(p.relative_to(root)) + ('/' if p.is_dir() else '') for p in root.rglob('*')); (root/'TREE.txt').write_text('\n'.join(entries)+'\n'); lines = [f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root)}' for p in sorted(root.rglob('*')) if p.is_file() and p.name != 'CHECKSUMS.sha256']; (root/'CHECKSUMS.sha256').write_text('\n'.join(lines)+'\n'); print('  OK')"
	@echo "  📋 Paso 2/4: validando pack..."
	@python3 $(TOOLS)/validate_pack.py
	@mkdir -p $(DIST)/source
	@echo "  🗜  Paso 3/4: creando zip ..."
	@cd .. && zip -r "$(shell pwd)/$(DIST)/source/$(PACK_NAME).zip" "$(notdir $(shell pwd))/.bago" "$(notdir $(shell pwd))/bago" "$(notdir $(shell pwd))/Makefile" --exclude "**/__pycache__/*" --exclude "**/*.pyc" -q
	@echo "  🔄 Paso 4/4: actualizando TREE con el nuevo zip..."
	@python3 -c "from pathlib import Path; import hashlib; root = Path('.bago'); entries = sorted(str(p.relative_to(root)) + ('/' if p.is_dir() else '') for p in root.rglob('*')); (root/'TREE.txt').write_text('\n'.join(entries)+'\n'); lines = [f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root)}' for p in sorted(root.rglob('*')) if p.is_file() and p.name != 'CHECKSUMS.sha256']; (root/'CHECKSUMS.sha256').write_text('\n'.join(lines)+'\n'); print('  OK')"
	@echo "  ✅ Pack creado: $(DIST)/source/$(PACK_NAME).zip"
	@ls -lh "$(DIST)/source/$(PACK_NAME).zip"
	@echo ""

# ─── Instalar alias global ────────────────────────────────────────────────────
install:
	@echo ""
	@echo "  📌 Instalando alias 'bago' en $(SHELL_RC) ..."
	@grep -q "alias bago=" $(SHELL_RC) && \
		echo "  ⚠️  Alias ya existe. Actualizado." && \
		sed -i.bak '/alias bago=/d' $(SHELL_RC) || true
	@echo "alias bago='python3 $(BAGO_PATH)'" >> $(SHELL_RC)
	@echo "  ✅ Añadido: alias bago='python3 $(BAGO_PATH)'"
	@echo "  ℹ️  Ejecuta: source $(SHELL_RC)"
	@echo "  ℹ️  Luego: bago  (desde cualquier carpeta)"
	@echo ""

# ─── Desinstalar alias ────────────────────────────────────────────────────────
uninstall:
	@echo ""
	@sed -i.bak '/alias bago=/d' $(SHELL_RC) && \
		echo "  ✅ Alias eliminado de $(SHELL_RC)" || \
		echo "  ⚠️  No se encontró alias bago en $(SHELL_RC)"
	@echo ""

# ─── Limpiar __pycache__ ──────────────────────────────────────────────────────
clean:
	@find $(BAGO_DIR) -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "  ✅ __pycache__ limpiado"

# ─── Deploy: zip limpio sin historial ─────────────────────────────────────────
deploy:
	@echo ""
	@echo "  🚀 Generando ZIP de arranque limpio (sin historial)..."
	@python3 $(DIST)/source/make_clean_pack.py
	@echo ""
