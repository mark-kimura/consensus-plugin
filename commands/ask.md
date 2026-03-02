---
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
description: Query multiple AI providers concurrently for expert advice with comprehensive prompts
argument-hint: "[optional: specific focus area or leave empty for context-based]"
---

# Consensus — Query Multiple AIs

You will analyze the user's request and current context, craft a comprehensive prompt, then query multiple AI providers concurrently (GPT-5.2, Gemini 3.1 Pro, Perplexity via OpenRouter) and consolidate their responses.

Arguments provided: $ARGUMENTS

## Workflow

### 1. Analyze the Request

Determine what problem to focus on based on:
- Explicit instructions from $ARGUMENTS (if provided)
- Recent conversation context and issues the user has been working on
- Current codebase state, recent errors, or challenges

### 2. Craft a Comprehensive Prompt

Create a detailed prompt including:
- **Problem statement** with full technical context
- **What has been tried** and the outcomes
- **Relevant code snippets**, configurations, and error messages
- **Specific questions** for the AI providers to address
- **Decision criteria** (performance vs simplicity, short-term vs long-term, etc.)
- **Response requirements**: Providers must give direct answers — no follow-up questions allowed. If information is incomplete, they should state assumptions and proceed.

### 3. Save Prompt to File

```bash
mkdir -p consensus_docs
```

Save the crafted prompt as `consensus_docs/prompt-{timestamp}.md`.

### 4. Execute Concurrent Queries

Run the consensus engine and wait for completion:

```bash
# Default: uses config's default search mode (usually "web")
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/consensus.py consensus_docs/prompt-{timestamp}.md --plugin-root "${CLAUDE_PLUGIN_ROOT}"

# Explicit no-web mode only when requested
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/consensus.py consensus_docs/prompt-{timestamp}.md --search-mode none --plugin-root "${CLAUDE_PLUGIN_ROOT}"
```

### 5. Analyze and Present Consensus

Read the output file `consensus_docs/consolidated-{timestamp}.md` and synthesize findings:

- **Common themes**: Areas where multiple providers agree
- **Unique perspectives**: Insights mentioned by only one provider
- **Consensus summary**: Overall agreement or majority opinion
- **Minority viewpoints**: Dissenting opinions or alternative approaches
- **Key takeaways**: Actionable insights synthesized from all responses

## Context Gathering (when no specific focus provided)

When $ARGUMENTS is empty, gather context by:
1. Reviewing recent error messages and debugging attempts
2. Analyzing current git changes and recent commits
3. Checking for failing tests or build issues
4. Considering conversation history for recurring problems

## Search Modes

- **web**: Include current web information (default — good for recent technologies)
- **none**: Fast responses without web search (good for coding questions)

## AI Providers

Queries these providers concurrently:
- **OpenAI GPT-5.2**: Responses API with reasoning capabilities
- **Google Gemini 3.1 Pro**: Large context with thinking capabilities
- **Perplexity Sonar**: Built-in web search and research capabilities

Providers with missing API keys are silently skipped. At least one key is required.
