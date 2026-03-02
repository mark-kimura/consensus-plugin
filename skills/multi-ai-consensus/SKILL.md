---
description: >
  When the user wants to cross-check ideas across multiple AI providers — look for phrases like
  "consensus", "multiple perspectives", "what do other AIs think", "cross-check", "second opinion",
  "ask other models", or "get diverse perspectives". This skill queries GPT-5, Gemini, and
  Perplexity concurrently and synthesizes their responses. NOTE: This calls external paid APIs
  using the user's own API keys, so only trigger when the user clearly intends it.
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
---

# Multi-AI Consensus

The user wants perspectives from multiple AI providers. You will craft a focused prompt based on the conversation context, query the providers, and synthesize the results.

## Steps

1. **Identify the question**: Based on the current conversation, determine what the user wants other AIs to weigh in on. Keep it focused — extract the core question or problem.

2. **Craft a prompt**: Write a clear, self-contained prompt that includes enough context for an external AI to give a useful answer. Include:
   - The core question or problem
   - Relevant technical context
   - What has been tried (if applicable)
   - A note that the provider must give a direct answer with no follow-up questions

3. **Save and execute**:

```bash
mkdir -p consensus_docs
```

Save the prompt to `consensus_docs/prompt-{timestamp}.md`, then run:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/consensus.py consensus_docs/prompt-{timestamp}.md --plugin-root "${CLAUDE_PLUGIN_ROOT}"
```

4. **Synthesize**: Read the consolidated output and present:
   - Where providers agree
   - Unique or contrasting perspectives
   - Actionable takeaways
