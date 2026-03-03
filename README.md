# Consensus — Multi-AI Provider Plugin for Claude Code

Get unstuck by querying multiple AI providers (GPT-5.2, Gemini, Kimi K2.5) for diverse perspectives, right from within Claude Code.

## How It Works

When you're stuck on a problem, Consensus queries multiple AI providers concurrently — GPT-5.2, Gemini 3.1 Pro, and Kimi K2.5 via OpenRouter by default — then synthesizes their responses to surface common themes, unique insights, and actionable takeaways.

## Installation

### 1. Install `uv` (Python package runner)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Set API Keys

Only one key is needed for the default setup:

```bash
export OPENROUTER_API_KEY="sk-or-..."   # Routes all three default providers
```

Optional, for direct API access (bypassing OpenRouter):

```bash
export OPENAI_API_KEY="sk-..."          # OpenAI direct API
export GEMINI_API_KEY="AI..."           # Google Gemini direct API
```

Add them to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) to persist across sessions.

### 3. Install the Plugin

In Claude Code, run these two commands:

```
/plugin marketplace add mark-kimura/kahidreamers-marketplace
/plugin install consensus@kahidreamers-marketplace
```

### 4. Enable Auto-Update (Recommended)

By default, third-party plugins don't auto-update. To get new versions automatically on session start:

1. Run `/plugin` in Claude Code
2. Go to **Marketplaces**
3. Select **kahidreamers-marketplace**
4. Choose **Enable auto-update**

Without this, you'll need to run `/plugin update consensus@kahidreamers-marketplace` manually after each release.

## Usage

### `/consensus:ask`

```
/consensus:ask help me optimize the SSE connection handling
```

Or without arguments — Claude infers from conversation context:

```
/consensus:ask
```

This also auto-triggers when you say things like:
- "What do other AIs think about this approach?"
- "Can I get a consensus on this?"
- "Cross-check this with other models"

### `/consensus:config`

```
/consensus:config              # Show current providers (same as check)
/consensus:config check        # Show current providers
/consensus:config update       # Update all providers to latest models
/consensus:config add llama 4  # Add a new provider via OpenRouter
/consensus:config remove kimi  # Remove a provider
/consensus:config openai       # Interactively configure OpenAI (model + routing)
```

### What Happens

1. Claude analyzes your request and conversation context
2. Crafts a comprehensive prompt with technical details
3. Queries all available providers concurrently
4. Synthesizes findings: agreements, unique perspectives, and takeaways

All intermediate files go to a temp directory — nothing is written to your project.

## Configuration

The plugin works out of the box with just `OPENROUTER_API_KEY`. For advanced configuration, copy `consensus_config.json` to your project root and customize:

- **Provider routing**: Toggle `use_openrouter` per provider to route through OpenRouter or call APIs directly
- **Models**: Change which model each provider uses
- **Search modes**: Set default to `"web"` (includes web search) or `"none"` (faster, no web)
- **Token limits**: Adjust `max_tokens` per provider

### Config Resolution Order

1. `./consensus_config.json` (your project root)
2. Plugin's built-in `consensus_config.json`
3. Hardcoded defaults

## Search Modes

- **`web`** (default): Providers include current web information. Good for recent technologies.
- **`none`**: Fast responses without web search. Good for coding questions.

## Project Structure

```
consensus-plugin/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── commands/
│   └── config.md                # /consensus:config command
├── skills/
│   └── ask/
│       └── SKILL.md             # /consensus:ask skill (also auto-triggers)
├── hooks/
│   └── hooks.json               # SessionStart: checks API keys + uv
├── scripts/
│   ├── consensus.py             # Core engine (uv run auto-resolves deps)
│   └── check-setup.sh           # Setup validator
├── consensus_config.json        # Default config template
├── .gitignore
├── LICENSE
└── README.md
```

## Requirements

- [uv](https://docs.astral.sh/uv/) — auto-installs Python dependencies on first run
- At least one API key (`OPENROUTER_API_KEY` recommended)
- Claude Code

## License

MIT
