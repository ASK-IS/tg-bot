set -euo pipefail

REQ="/app/requirements.txt"
MAIN="/app/bot.py"

if [ "${SKIP_PIP_INSTALL:-0}" != "1" ]; then
  if [ -f "$REQ" ]; then
    echo "[entrypoint] Ensuring deps..."
    python -m pip install --upgrade pip
    python -m pip install --no-cache-dir -r "$REQ"
  fi
fi

echo "[entrypoint] Starting bot..."
exec python -u "$MAIN"
