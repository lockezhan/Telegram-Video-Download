#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_ACTIVATE="$WORKSPACE_DIR/venv/bin/activate"

if [[ ! -f "$VENV_ACTIVATE" ]]; then
  echo "❌ 未找到虚拟环境: $VENV_ACTIVATE"
  echo "请先在 /home/elite/BJUT_LAB 下创建 venv"
  exit 1
fi

source "$VENV_ACTIVATE"
cd "$SCRIPT_DIR"

python3 download_by_links.py "$@"
