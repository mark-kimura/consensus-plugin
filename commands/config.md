---
allowed-tools:
  - WebSearch
  - Read
  - Write
  - Bash
  - Glob
description: Manage provider configuration — check status, update models, add/remove/configure providers
argument-hint: "[check|update|add <model>|remove <provider>|<provider>] [--local]"
---

# Consensus — Provider Configuration

Manage the consensus provider configuration: check current providers, update model versions, add new providers, or remove existing ones.

Arguments provided: $ARGUMENTS

## Workflow

### 1. Parse Arguments

Parse `$ARGUMENTS` to determine the subcommand and target:

**Subcommands:**
- **`check`** — Show current provider configuration (read-only). This is the **default** when no subcommand is given.
- **`update [provider]`** — Update models to latest versions (existing behavior)
- **`add <model>`** — Add a new provider via OpenRouter
- **`remove <provider>`** — Remove an existing provider
- **`<provider>`** — Interactive configuration for an existing provider (e.g. `openai`, `gemini`, `kimi`). Detected when the first argument matches an existing provider key in config and is not one of the subcommand keywords above.

**Target flag (applies to all subcommands):**
- **`--local`** — Operate on `./consensus_config.json` (current project). Creates it from the plugin template if it doesn't exist.
- **Default (no flag)** — Operate on the plugin template at `${CLAUDE_PLUGIN_ROOT}/consensus_config.json` (affects all projects that don't have a local override)

### 2. Route to Subcommand

Based on the parsed subcommand, follow the appropriate section below.

---

## Subcommand: `check`

Display the current provider configuration in a table.

### Read Current Configuration

Load the active configuration:

1. If `--local`: read `./consensus_config.json` (report if missing)
2. Otherwise: read `${CLAUDE_PLUGIN_ROOT}/consensus_config.json`

### Display Provider Table

| Provider | Enabled | OpenRouter? | Model | OpenRouter none | OpenRouter web |
|----------|---------|-------------|-------|-----------------|----------------|
| (name) | (yes/no) | (yes/no) | (value) | (value) | (value) |

For each provider in `providers`, show one row. Done — no changes made.

---

## Subcommand: `update [provider]`

Check and update model versions, searching for the latest available models.

### Parse Provider Scope

- **`openai`** — Update only the OpenAI provider
- **`gemini`** — Update only the Gemini provider
- **`kimi`** — Update only the Kimi provider
- **`all`** or empty — Update all providers (default)

### Read Current Configuration

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

### Search for Latest Models

Use WebSearch to find the latest stable/GA model versions for each in-scope provider. Run targeted queries:

- **OpenAI**: Search for the latest GPT model available via the OpenAI API and on OpenRouter. Look for the current flagship model name.
- **Gemini**: Search for the latest Google Gemini model available via the Gemini API and on OpenRouter. Look for the current flagship model name.
- **Kimi**: Search for the latest Moonshot Kimi model available on OpenRouter. Look for the current flagship model name.

Prefer stable/GA releases over preview or experimental models unless the user explicitly requests otherwise.

### Model ID Convention Reference

When determining the correct config values, follow these naming conventions:

| Provider | `model` field | `openrouter_model.none` | `openrouter_model.web` |
|----------|--------------|------------------------|----------------------|
| OpenAI | Bare model name (e.g. `gpt-5.2`) | `openai/<model>` (e.g. `openai/gpt-5.2`) | `openai/<model>:online` (e.g. `openai/gpt-5.2:online`) |
| Gemini | Bare model name (e.g. `gemini-3.1-pro`) | `google/<model>` (e.g. `google/gemini-3.1-pro`) | `google/<model>:online` (e.g. `google/gemini-3.1-pro:online`) |
| Kimi | Bare model name (e.g. `kimi-k2.5`) | `moonshotai/<model>` (e.g. `moonshotai/kimi-k2.5`) | `moonshotai/<model>` (same — no `:online` variant) |

### Present Comparison

Show a comparison table of current vs. latest versions:

| Provider | Field | Current | Latest | Changed? |
|----------|-------|---------|--------|----------|
| ... | ... | ... | ... | ... |

If all models are already up to date, report that and exit.

### Confirm with User

Before applying any changes, clearly list what will be modified and ask the user for confirmation. Do not proceed without explicit approval.

### Update Configuration

Determine the target file based on the `--local` flag:

- **Default (global)**: Write to `${CLAUDE_PLUGIN_ROOT}/consensus_config.json`
- **`--local`**: Write to `./consensus_config.json`. If it doesn't exist, copy the full template from `${CLAUDE_PLUGIN_ROOT}/consensus_config.json` first, then apply model updates on top.

Apply changes following these rules:

- **Only modify model-related fields**: `model`, `openrouter_model.none`, `openrouter_model.web`
- **Never touch**: `api_keys`, `enabled`, `use_openrouter`, `endpoint`, `endpoints`, or `settings`
- **Preserve `api_keys` as `null`** in the config file — keys come from environment variables
- **Write format**: 2-space JSON indentation with a trailing newline

### Verify

Read back the target config file and display the final model versions to confirm the update was applied correctly.

---

## Subcommand: `add <model>`

Add a new AI provider to the configuration via OpenRouter.

### Parse Model Name

Extract the user's fuzzy model name from `$ARGUMENTS` (everything after `add`). Examples: "llama 4", "deepseek", "grok", "command r+", "mistral large".

### Search OpenRouter for the Model

Use WebSearch to find the correct model on OpenRouter:

1. Search for: `site:openrouter.ai <model name>` to find the model page
2. Determine the exact **OpenRouter model ID** (e.g. `meta-llama/llama-4-maverick`, `deepseek/deepseek-r1`)
3. Extract the **provider prefix** from the model ID (the part before `/`, e.g. `meta-llama`, `deepseek`)
4. Check if an **`:online` variant** exists by searching for `<model-id>:online` on OpenRouter

### Build Provider Config Entry

Construct the provider configuration entry:

```json
{
  "<provider-key>": {
    "enabled": true,
    "use_openrouter": true,
    "model": "<bare-model-name>",
    "openrouter_model": {
      "none": "<provider-prefix>/<bare-model-name>",
      "web": "<provider-prefix>/<bare-model-name>:online"
    }
  }
}
```

Rules for the provider key:
- Use a short, recognizable name (e.g. `llama`, `deepseek`, `grok`, `mistral`, `command-r`)
- Lowercase, no spaces
- If the provider key already exists in config, warn the user and ask how to proceed

If no `:online` variant exists, set `web` to the same value as `none` (same pattern as Kimi).

### Confirm with User

Present the proposed config entry clearly and ask for confirmation before writing. Show:
- Provider key name
- Full config entry that will be added
- Which config file will be modified

### Write to Config

1. Read the target config file (based on `--local` flag)
2. Add the new provider entry under `providers`
3. Write back with 2-space JSON indentation and trailing newline
4. **Preserve `api_keys` as `null`** — never write actual key values

### Verify

Read back the config file and display the updated provider table to confirm the addition.

---

## Subcommand: `remove <provider>`

Remove or disable an existing provider from the configuration.

### Parse Provider Name

Extract the user's fuzzy provider name from `$ARGUMENTS` (everything after `remove`). Examples: "kimi", "moonshot", "that k2.5 model", "deepseek", "llama".

### Match Against Existing Providers

Read the current config and find the matching provider:

1. Try exact match on provider key (e.g. `kimi`, `openai`, `gemini`)
2. Try fuzzy match on model name (e.g. "k2.5" → kimi, "gpt" → openai)
3. Try fuzzy match on openrouter model IDs (e.g. "moonshot" → kimi via `moonshotai/...`)

If no match is found, show the available providers and ask the user to clarify.
If multiple matches are found, list them and ask the user to pick one.

### Confirm with User

Show the provider that will be removed, including its full config entry, and ask for confirmation:
- Provider key name
- Current model configuration
- Which config file will be modified

**Important**: Warn if removing would leave fewer than 2 providers enabled — consensus works best with multiple perspectives.

### Remove from Config

1. Read the target config file (based on `--local` flag)
2. Delete the provider entry entirely from `providers`
3. Write back with 2-space JSON indentation and trailing newline
4. **Preserve `api_keys` as `null`** — never write actual key values

### Verify

Read back the config file and display the updated provider table to confirm the removal.

---

## Subcommand: `<provider>` (Interactive Provider Config)

Interactively configure an existing provider — choose the model and routing method.

Triggered when `$ARGUMENTS` starts with an existing provider key (e.g. `openai`, `gemini`, `kimi`) that isn't one of the keyword subcommands (`check`, `update`, `add`, `remove`).

### Show Current Config

Read the active config and display the current settings for this provider:

- **Provider key**: (e.g. `openai`)
- **Enabled**: yes/no
- **Routing**: OpenRouter / Direct API
- **Model**: (current model name)
- **OpenRouter model (none)**: (value)
- **OpenRouter model (web)**: (value)

### Ask: Routing

Ask the user how they want to route this provider:

1. **OpenRouter** (recommended) — Routes through OpenRouter. Only needs `OPENROUTER_API_KEY`.
2. **Direct API** — Calls the provider's API directly. Needs the provider-specific key (e.g. `OPENAI_API_KEY`, `GEMINI_API_KEY`).

If the user picks Direct API, check if the corresponding environment variable is set. If not, warn them which key they'll need to set (but do not block — they may set it later).

### Ask: Model

Search for available models for this provider and present choices:

1. Use WebSearch to find the latest models available for this provider (on OpenRouter if routing via OpenRouter, or via the provider's own API if direct).
2. Present the top 2–3 model options to the user. Include the current model as one of the choices (marked as current). Prefer stable/GA releases.
3. Let the user pick, or type a custom model name.

### Build Updated Config

Based on the user's choices, update the provider config entry:

- Set `use_openrouter` to `true` or `false` based on routing choice
- Set `model` to the bare model name
- Set `openrouter_model.none` and `openrouter_model.web` following the naming conventions (see Model ID Convention Reference in the `update` section)
- If no `:online` variant exists for the chosen model, set `web` to the same value as `none`

### Confirm and Write

Present the full updated config entry and ask for confirmation. Then:

1. Read the target config file (based on `--local` flag)
2. Update the provider entry under `providers`
3. Write back with 2-space JSON indentation and trailing newline
4. **Preserve `api_keys` as `null`** — never write actual key values

### Verify

Read back the config file and display the updated provider settings to confirm.

---

## Notes

- At least one provider must remain enabled. Refuse to remove the last provider.
- If a WebSearch returns ambiguous results, prefer the model that appears in official documentation or API changelogs.
- When multiple stable versions exist, prefer the newest stable release.
- The `check` subcommand is always safe — it never modifies any files.
- For `add`, the provider is always configured with `use_openrouter: true` since we're discovering it via OpenRouter.
