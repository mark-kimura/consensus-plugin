---
allowed-tools:
  - WebSearch
  - Read
  - Write
  - Bash
  - Glob
description: Update AI provider model versions by searching for the latest available models
argument-hint: "[optional: openai|gemini|kimi|all|check] [--local]"
---

# Consensus — Update Provider Models

You will check current model versions, search for the latest available models, and update the configuration interactively.

Arguments provided: $ARGUMENTS

## Workflow

### 1. Parse Arguments

Determine the scope and target from `$ARGUMENTS`:

**Provider scope:**
- **`openai`** — Update only the OpenAI provider
- **`gemini`** — Update only the Gemini provider
- **`kimi`** — Update only the Kimi provider
- **`all`** or empty — Update all providers (default)
- **`check`** — Dry-run: show current vs. latest versions without making changes

**Target flag:**
- **`--local`** — Update only `./consensus_config.json` (current project). Creates it from the plugin template if it doesn't exist.
- **Default (no flag)** — Update the plugin template at `${CLAUDE_PLUGIN_ROOT}/consensus_config.json` (affects all projects that don't have a local override)

### 2. Read Current Configuration

Load the active configuration:

1. Check for a project-local config at `./consensus_config.json`
2. If not found, fall back to the plugin template at `${CLAUDE_PLUGIN_ROOT}/consensus_config.json`

Display the current model versions in a table:

| Provider | Field | Current Value |
|----------|-------|---------------|
| OpenAI | `model` | (value) |
| OpenAI | `openrouter_model.none` | (value) |
| OpenAI | `openrouter_model.web` | (value) |
| Gemini | `model` | (value) |
| Gemini | `openrouter_model.none` | (value) |
| Gemini | `openrouter_model.web` | (value) |
| Kimi | `model` | (value) |
| Kimi | `openrouter_model.none` | (value) |
| Kimi | `openrouter_model.web` | (value) |

### 3. Search for Latest Models

Use WebSearch to find the latest stable/GA model versions for each in-scope provider. Run targeted queries:

- **OpenAI**: Search for the latest GPT model available via the OpenAI API and on OpenRouter. Look for the current flagship model name.
- **Gemini**: Search for the latest Google Gemini model available via the Gemini API and on OpenRouter. Look for the current flagship model name.
- **Kimi**: Search for the latest Moonshot Kimi model available on OpenRouter. Look for the current flagship model name.

Prefer stable/GA releases over preview or experimental models unless the user explicitly requests otherwise.

### 4. Model ID Convention Reference

When determining the correct config values, follow these naming conventions:

| Provider | `model` field | `openrouter_model.none` | `openrouter_model.web` |
|----------|--------------|------------------------|----------------------|
| OpenAI | Bare model name (e.g. `gpt-5.2`) | `openai/<model>` (e.g. `openai/gpt-5.2`) | `openai/<model>:online` (e.g. `openai/gpt-5.2:online`) |
| Gemini | Bare model name (e.g. `gemini-3.1-pro`) | `google/<model>` (e.g. `google/gemini-3.1-pro`) | `google/<model>:online` (e.g. `google/gemini-3.1-pro:online`) |
| Kimi | Bare model name (e.g. `kimi-k2.5`) | `moonshotai/<model>` (e.g. `moonshotai/kimi-k2.5`) | `moonshotai/<model>` (same — no `:online` variant) |

### 5. Present Comparison

Show a comparison table of current vs. latest versions:

| Provider | Field | Current | Latest | Changed? |
|----------|-------|---------|--------|----------|
| OpenAI | `model` | ... | ... | ... |
| OpenAI | `openrouter_model.none` | ... | ... | ... |
| OpenAI | `openrouter_model.web` | ... | ... | ... |
| Gemini | `model` | ... | ... | ... |
| Gemini | `openrouter_model.none` | ... | ... | ... |
| Gemini | `openrouter_model.web` | ... | ... | ... |
| Kimi | `model` | ... | ... | ... |
| Kimi | `openrouter_model.none` | ... | ... | ... |
| Kimi | `openrouter_model.web` | ... | ... | ... |

If running in **`check` mode**, stop here — display the table and exit without making changes.

If all models are already up to date, report that and exit.

### 6. Confirm with User

Before applying any changes, clearly list what will be modified and ask the user for confirmation. Do not proceed without explicit approval.

### 7. Update Configuration

Determine the target file based on the `--local` flag:

- **Default (global)**: Write to `${CLAUDE_PLUGIN_ROOT}/consensus_config.json`
- **`--local`**: Write to `./consensus_config.json`. If it doesn't exist, copy the full template from `${CLAUDE_PLUGIN_ROOT}/consensus_config.json` first, then apply model updates on top.

Apply changes following these rules:

- **Only modify model-related fields**: `model`, `openrouter_model.none`, `openrouter_model.web`
- **Never touch**: `api_keys`, `enabled`, `use_openrouter`, `endpoint`, `endpoints`, or `settings`
- **Preserve `api_keys` as `null`** in the config file — keys come from environment variables
- **Write format**: 2-space JSON indentation with a trailing newline

### 8. Verify

Read back the target config file and display the final model versions to confirm the update was applied correctly.

## Notes

- At least one provider must be in scope. If the argument doesn't match a known provider name, treat it as `all`.
- If a WebSearch returns ambiguous results, prefer the model that appears in official documentation or API changelogs.
- When multiple stable versions exist (e.g. `gemini-3.1-pro` and `gemini-3.0-pro`), prefer the newest stable release.
