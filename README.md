# Consensus — Multi-AI Provider Plugin for Claude Code

Get unstuck by querying multiple AI providers (GPT-5.2, Gemini, etc.) for diverse perspectives, right from within Claude Code.

## How It Works

When you're stuck on a problem, Consensus queries multiple AI providers concurrently — GPT-5.2 and Gemini 3.1 Pro by default — then synthesizes their responses to surface common themes, unique insights, and actionable takeaways.

## Installation

### 1. Install `uv` (Python package runner)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Set API Keys

Set one or more of these environment variables (you only need the providers you want to use):

```bash
export OPENROUTER_API_KEY="sk-or-..."   # OpenRouter — routes GPT-5.2 and Gemini (recommended)
export OPENAI_API_KEY="sk-..."          # OpenAI direct API (optional, if not using OpenRouter)
export GEMINI_API_KEY="AI..."           # Google Gemini direct API (optional, if not using OpenRouter)
```

Add them to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) to persist across sessions.

### 3. Install the Plugin

```bash
claude plugin add /path/to/consensus-plugin
```

Or run Claude Code with the plugin directory:

```bash
claude --plugin-dir /path/to/consensus-plugin
```

## Usage

### Slash Commands

**Ask for consensus:**

```
/consensus:ask help me optimize the SSE connection handling
```

Or without arguments (Claude infers from conversation context):

```
/consensus:ask
```

**Update provider models:**

```
/consensus:update              # Update all providers to latest models
/consensus:update openai       # Update only OpenAI
/consensus:update check        # Dry-run: show current vs. latest without changes
```

### Natural Language (Skill)

The plugin also triggers when you say things like:

- "What do other AIs think about this approach?"
- "Can I get a consensus on this?"
- "Cross-check this with other models"
- "I want multiple perspectives on this"

### What Happens

1. Claude Code analyzes your request and conversation context
2. Crafts a comprehensive prompt with technical details
3. Queries all available providers concurrently
4. Reads the consolidated responses
5. Synthesizes findings: agreements, unique perspectives, and takeaways

All intermediate files (prompts, raw responses) go to a temp directory — nothing is written to your project.

## Configuration

The plugin works out of the box with environment variables. For advanced configuration, copy `consensus_config.json` to your project root and customize:

- **Provider routing**: Toggle `use_openrouter` per provider to route through OpenRouter or call APIs directly
- **Models**: Change which model each provider uses
- **Search modes**: Set default to `"web"` (includes web search) or `"none"` (faster, no web)
- **Token limits**: Adjust `max_tokens` per provider

### Config Resolution Order

1. `./consensus_config.json` (your project root)
2. Plugin's built-in `consensus_config.json`
3. Hardcoded defaults

## API Key Management

| Variable | Provider | Notes |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI GPT-5.2 | Direct API access |
| `GEMINI_API_KEY` | Google Gemini | Direct API access |
| `OPENROUTER_API_KEY` | OpenRouter | Routes GPT-5.2, Gemini, and others (recommended) |

- Keys are **never** stored in plugin files
- Providers with missing keys are silently skipped
- Having just **one** key is enough
- The SessionStart hook reports which providers are available

## Search Modes

- **`web`** (default): Providers include current web information. Good for recent technologies.
- **`none`**: Fast responses without web search. Good for coding questions.

## Project Structure

```
consensus-plugin/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── commands/
│   └── update.md                # /consensus:update command
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
- At least one API key (OpenAI, Gemini, or OpenRouter)
- Claude Code

## License

MIT
