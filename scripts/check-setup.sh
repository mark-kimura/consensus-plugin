#!/usr/bin/env bash
# Check consensus plugin prerequisites: uv binary and API keys.
# Outputs JSON for SessionStart hook consumption.
# Never exits non-zero — informational only.

set -euo pipefail

uv_ok="false"
uv_msg=""
if command -v uv &>/dev/null; then
  uv_ok="true"
else
  uv_msg="uv not found. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

check_key() {
  local name="$1" var="$2"
  if [ -n "${!var:-}" ]; then
    echo "\"$name\": true"
  else
    echo "\"$name\": false"
  fi
}

openai_status=$(check_key "openai" "OPENAI_API_KEY")
gemini_status=$(check_key "gemini" "GEMINI_API_KEY")
openrouter_status=$(check_key "openrouter" "OPENROUTER_API_KEY")

# Build provider summary line for display
providers=""
if [ -n "${OPENAI_API_KEY:-}" ]; then
  providers="${providers}OpenAI OK, "
else
  providers="${providers}OpenAI missing, "
fi
if [ -n "${GEMINI_API_KEY:-}" ]; then
  providers="${providers}Gemini OK, "
else
  providers="${providers}Gemini missing, "
fi
if [ -n "${OPENROUTER_API_KEY:-}" ]; then
  providers="${providers}OpenRouter OK"
else
  providers="${providers}OpenRouter missing"
fi

# Count available providers
count=0
[ -n "${OPENAI_API_KEY:-}" ] && count=$((count + 1))
[ -n "${GEMINI_API_KEY:-}" ] && count=$((count + 1))
[ -n "${OPENROUTER_API_KEY:-}" ] && count=$((count + 1))

# Output JSON
cat <<EOF
{
  "uv_available": $uv_ok,
  "uv_message": "$uv_msg",
  "api_keys": { $openai_status, $gemini_status, $openrouter_status },
  "providers_available": $count,
  "summary": "$providers"
}
EOF

# Print human-readable status
if [ "$uv_ok" = "true" ]; then
  echo "[Consensus] uv: ready" >&2
else
  echo "[Consensus] WARNING: $uv_msg" >&2
fi

if [ "$count" -eq 0 ]; then
  echo "[Consensus] WARNING: No API keys set. Set OPENAI_API_KEY, GEMINI_API_KEY, or OPENROUTER_API_KEY." >&2
else
  echo "[Consensus] Providers: $providers" >&2
fi
