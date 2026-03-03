# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Consensus is a Claude Code plugin that queries multiple AI providers (GPT-5.2, Gemini, and Kimi K2.5 via OpenRouter by default) concurrently via async Python, then synthesizes their responses. Additional providers can be enabled in config. It has no build system — pure Python 3.11+ with `uv` for dependency resolution via PEP 723 inline script metadata.

## Running the Core Engine

```bash
# Standard invocation (from project using the plugin)
uv run scripts/consensus.py <prompt-file.md> --plugin-root . [--search-mode web|none] [--output-dir DIR] [--config CONFIG]

# Validate prerequisites (SessionStart hook)
bash scripts/check-setup.sh
```

There are no tests, linter, or build commands. The only runtime dependency is `aiohttp>=3.8.0`, auto-resolved by `uv`.

## Architecture

### Plugin Components

- **`.claude-plugin/plugin.json`** — Plugin manifest (name: `consensus`, v1.0.0)
- **`skills/ask/SKILL.md`** — `/consensus:ask` skill; orchestrates the full workflow (analyze context → craft prompt → run engine → synthesize results). Also auto-triggers on phrases like "consensus", "second opinion", "cross-check"
- **`hooks/hooks.json`** — SessionStart hook runs `check-setup.sh` to validate `uv` and API key availability (informational only, never fails)
- **`consensus_config.json`** — Default configuration template; users can copy to project root to override

### Core Engine (`scripts/consensus.py`)

Single-file async Python engine (~560 lines). Key flow:

1. `load_config()` — 4-tier config resolution: CLI `--config` → `./consensus_config.json` → `<plugin-root>/consensus_config.json` → built-in `DEFAULT_CONFIG`. Environment variables always override API keys.
2. `setup_providers()` — Dynamically initializes providers based on config `enabled`/`use_openrouter` flags and available API keys. Missing keys cause skip, not failure.
3. `query_all_providers()` — Fires all provider queries concurrently via `asyncio.create_task` + `asyncio.as_completed`.
4. `consolidate_responses()` — Writes markdown with per-provider sections to a temp directory (or `--output-dir` if specified).

### Provider Class Hierarchy

- `AIProvider` — Abstract base with `name`, `api_key`, `available`, `config`
- `OpenAIProvider` — Direct API; GPT-5.2 uses Responses API with reasoning effort levels, older models use chat completions
- `GeminiProvider` — Direct Gemini API with exponential backoff retry (3 retries, 1s→2s→4s); 32768 token limit
- `OpenRouterProvider` — Generic OpenRouter proxy; model selected by search mode from `openrouter_model` config map; adds web plugin when model doesn't end with `:online`

### Search Modes

- **`web`** (default) — Providers include web search; models use `:online` variants or web plugins
- **`none`** — No web search; faster responses; lower reasoning effort for GPT-5.2

### Key Environment Variables

- `OPENROUTER_API_KEY` — Routes GPT-5.2 and Gemini by default; only key needed for default setup
- `OPENAI_API_KEY`, `GEMINI_API_KEY` — Optional; for direct API access when `use_openrouter` is false
- `CLAUDE_PLUGIN_ROOT` — Injected by Claude Code; used in command/skill markdown templates

## Conventions

- API keys come exclusively from environment variables, never stored in config files
- `_deep_merge()` is used for config layering — override dicts merge recursively, other values replace
- Output files go to a temp directory by default; use `--output-dir` to persist to a specific location
- Command and skill markdown files use YAML frontmatter for `allowed-tools`, `description`, and `argument-hint`
- The `check-setup.sh` hook outputs both JSON (for structured consumption) and human-readable warnings to stderr
