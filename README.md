# Consensus — Multi-AI Provider Plugin for Claude Code

Get unstuck by querying multiple AI providers (GPT-5.2, Gemini, DeepSeek V3.2) for diverse perspectives, right from within Claude Code.

## How It Works

When you're stuck on a problem, Consensus queries multiple AI providers concurrently — GPT-5.2, Gemini 3.1 Pro, and DeepSeek V3.2 via OpenRouter by default — then synthesizes their responses to surface common themes, unique insights, and actionable takeaways.

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

**Option A — KahiDreamers Marketplace**:

```
/plugin marketplace add mark-kimura/kahidreamers-marketplace
/plugin install consensus@kahidreamers-marketplace
```

**Option B — Official Plugin Directory** (submitted, under review by Anthropic):

```
/plugin install consensus@claude-plugin-directory
```

### 4. Enable Auto-Update (Recommended)

For the official directory, auto-update is enabled by default. For third-party marketplaces, enable it manually:

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
/consensus:config update       # Update all providers to latest models
/consensus:config add llama 4  # Add a new provider via OpenRouter
/consensus:config remove deepseek  # Remove a provider
/consensus:config openai       # Interactively configure OpenAI (model + routing)
/consensus:config --reset      # Reset all providers to plugin defaults
```

### What Happens

1. Claude analyzes your request and conversation context
2. Crafts a comprehensive prompt with technical details
3. Queries all available providers concurrently
4. Synthesizes findings: agreements, unique perspectives, and takeaways

All intermediate files go to a temp directory — nothing is written to your project.

## Configuration

The plugin works out of the box with just `OPENROUTER_API_KEY`. Use `/consensus:config` to manage providers interactively, or customize `consensus_config.json` directly:

- **Provider routing**: Route through OpenRouter or call APIs directly (`/consensus:config openai`)
- **Models**: Add, remove, or update providers (`/consensus:config add llama 4`)
- **Search modes**: Set default to `"web"` (includes web search) or `"none"` (faster, no web)
- **Token limits**: Adjust `max_tokens` per provider

### Config Resolution Order

1. `./consensus_config.json` (project root — for project-specific overrides)
2. `~/.claude/consensus_config.json` (user config — written by `/consensus:config`, survives plugin updates)
3. Plugin's built-in `consensus_config.json`
4. Hardcoded defaults

## Search Modes

By default, providers include current web information in their responses. If you'd rather get purely model-based perspectives without web search, just say so naturally:

- "Get a consensus on this, no web search"
- "What do other models think — don't use the web"
- "/consensus:ask without web search, compare approaches to caching"

Claude will detect your intent and run in the appropriate mode:

- **`web`** (default): Providers include current web information. Good for questions about recent technologies or current best practices.
- **`none`**: Pure model knowledge, no web search. Faster responses. Good for coding questions, architecture decisions, or when you want unbiased model perspectives.

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
