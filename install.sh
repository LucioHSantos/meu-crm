#!/bin/bash
set -euo pipefail
# ============================================================
#  CRM Premium - One-Command Installer
#  Usage: bash install.sh
#  Or:    curl -sL https://raw.githubusercontent.com/LucioHSantos/meu-crm/main/install.sh | bash
# ============================================================
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}   CRM PREMIUM - ONE-CLICK INSTALLER${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Execute como root: sudo bash install.sh${NC}"
    exit 1
fi

if ! command -v git &>/dev/null; then
    apt update && apt install -y git
fi

TMP_DIR=$(mktemp -d)
git clone --depth=1 https://github.com/LucioHSantos/meu-crm.git "$TMP_DIR" 2>/dev/null || {
    echo -e "${YELLOW}Repositório privado. Use o comando com GITHUB_TOKEN:${NC}"
    echo "  GITHUB_TOKEN=seu_token bash install.sh"
    echo ""
    read -rsp "GitHub Token: " GITHUB_TOKEN
    echo ""
    git clone --depth=1 "https://${GITHUB_TOKEN}@github.com/LucioHSantos/meu-crm.git" "$TMP_DIR"
}

cd "$TMP_DIR"
bash deploy/setup-vps.sh
rm -rf "$TMP_DIR"
