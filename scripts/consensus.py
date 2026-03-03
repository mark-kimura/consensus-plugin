#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp>=3.8.0"]
# ///
"""
AI consensus engine — queries multiple AI providers concurrently and consolidates responses.
Supports OpenAI and Gemini via OpenRouter with configurable web search modes.

Designed to be run via `uv run consensus.py` which auto-resolves dependencies.

Setup:
  Set API keys as environment variables (only the ones you need):
    export OPENAI_API_KEY="sk-..."
    export GEMINI_API_KEY="AI..."
    export OPENROUTER_API_KEY="sk-or-..."

Usage:
  uv run consensus.py <markdown_file> [--search-mode {web|none}] [--output-dir DIR] [--config CONFIG] [--plugin-root DIR]
  Output goes to a temp directory by default. Use --output-dir to persist files.
"""

import sys
import os
import argparse
import asyncio
import aiohttp
import json
import time
import tempfile
from datetime import datetime
from typing import List, Dict, Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "api_keys": {
        "openai": None,
        "gemini": None,
        "openrouter": None,
    },
    "providers": {
        "openai": {
            "enabled": True,
            "use_openrouter": True,
            "model": "gpt-5.2",
            "endpoint": "https://api.openai.com/v1",
            "openrouter_model": {
                "none": "openai/gpt-5.2",
                "web": "openai/gpt-5.2:online",
            },
        },
        "gemini": {
            "enabled": True,
            "use_openrouter": True,
            "model": "gemini-3.1-pro-preview",
            "endpoint": "https://generativelanguage.googleapis.com/v1beta",
            "openrouter_model": {
                "none": "google/gemini-3.1-pro-preview",
                "web": "google/gemini-3.1-pro-preview:online",
            },
        },
        "kimi": {
            "enabled": True,
            "use_openrouter": True,
            "model": "kimi-k2.5",
            "openrouter_model": {
                "none": "moonshotai/kimi-k2.5",
                "web": "moonshotai/kimi-k2.5",
            },
        },
    },
    "settings": {
        "default_search_mode": "web",
        "max_tokens": 32768,
        "max_tokens_gemini": 32768,
        "temperature": 0.7,
        "concurrent_requests": True,
    },
    "endpoints": {
        "openai": "https://api.openai.com/v1",
        "gemini": "https://generativelanguage.googleapis.com/v1beta",
        "openrouter": "https://openrouter.ai/api/v1",
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge *override* into a copy of *base*."""
    merged = base.copy()
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(config_path: Optional[str] = None, plugin_root: Optional[str] = None) -> Dict:
    """Load configuration with resolution order:
    1. Explicit --config path
    2. ./consensus_config.json (project-local)
    3. ~/.claude/consensus_config.json (user config)
    4. <plugin_root>/consensus_config.json (plugin default)
    5. Built-in DEFAULT_CONFIG
    """
    config = None

    # Try explicit path first
    if config_path and os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = _deep_merge(DEFAULT_CONFIG, json.load(f))

    # Try project-local
    if config is None and os.path.exists("consensus_config.json"):
        with open("consensus_config.json", "r", encoding="utf-8") as f:
            config = _deep_merge(DEFAULT_CONFIG, json.load(f))

    # Try user config
    if config is None:
        user_cfg = os.path.join(os.path.expanduser("~"), ".claude", "consensus_config.json")
        if os.path.exists(user_cfg):
            with open(user_cfg, "r", encoding="utf-8") as f:
                config = _deep_merge(DEFAULT_CONFIG, json.load(f))

    # Try plugin root
    if config is None and plugin_root:
        plugin_cfg = os.path.join(plugin_root, "consensus_config.json")
        if os.path.exists(plugin_cfg):
            with open(plugin_cfg, "r", encoding="utf-8") as f:
                config = _deep_merge(DEFAULT_CONFIG, json.load(f))

    # Fallback to built-in defaults
    if config is None:
        config = DEFAULT_CONFIG.copy()

    # Always override API keys from environment variables
    if os.getenv("OPENAI_API_KEY"):
        config["api_keys"]["openai"] = os.getenv("OPENAI_API_KEY")
    if os.getenv("GEMINI_API_KEY"):
        config["api_keys"]["gemini"] = os.getenv("GEMINI_API_KEY")
    if os.getenv("OPENROUTER_API_KEY"):
        config["api_keys"]["openrouter"] = os.getenv("OPENROUTER_API_KEY")
    return config


# ---------------------------------------------------------------------------
# Provider classes
# ---------------------------------------------------------------------------

class AIProvider:
    """Base class for AI providers."""

    def __init__(self, name: str, api_key: str, config: Dict):
        self.name = name
        self.api_key = api_key
        self.available = bool(api_key)
        self.config = config

    def get_model_for_mode(self, search_mode: str) -> str:
        return ""

    async def query(self, session: aiohttp.ClientSession, prompt: str, search_mode: str) -> Optional[str]:
        raise NotImplementedError


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: str, config: Dict):
        super().__init__("OpenAI", api_key, config)
        self.base_url = config["endpoints"]["openai"]

    def get_model_for_mode(self, search_mode: str) -> str:
        return self.config["providers"]["openai"]["model"]

    async def query(self, session: aiohttp.ClientSession, prompt: str, search_mode: str) -> Optional[str]:
        if not self.available:
            return None

        enhanced_prompt = self._enhance_prompt(prompt, search_mode)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        model = self.config["providers"]["openai"]["model"]
        if model.startswith("gpt-5"):
            reasoning_effort = "low" if search_mode == "none" else "medium"
            data = {
                "model": model,
                "input": enhanced_prompt,
                "reasoning": {"effort": reasoning_effort},
                "text": {"verbosity": "medium"},
            }
            endpoint = f"{self.base_url}/responses"
        else:
            data = {
                "model": model,
                "messages": [{"role": "user", "content": enhanced_prompt}],
                "max_tokens": self.config["settings"]["max_tokens"],
            }
            endpoint = f"{self.base_url}/chat/completions"

        try:
            async with session.post(endpoint, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if model.startswith("gpt-5"):
                        return self._parse_gpt5_response(result)
                    else:
                        return result["choices"][0]["message"]["content"]
                else:
                    print(f"OpenAI API error: {response.status}")
                    return None
        except Exception as e:
            print(f"Error querying OpenAI: {e}")
            return None

    def _parse_gpt5_response(self, result: dict) -> Optional[str]:
        try:
            for field in ("text", "output"):
                items = result.get(field)
                if isinstance(items, list):
                    for item in items:
                        if item.get("type") == "message" and item.get("status") == "completed" and "content" in item:
                            for c in item["content"]:
                                if c.get("type") == "output_text":
                                    return c.get("text", "")
            if "output" in result:
                return str(result["output"])
            print("Could not extract text from GPT-5.2 response structure")
            return None
        except Exception as e:
            print(f"Error parsing GPT-5.2 response: {e}")
            return None

    def _enhance_prompt(self, prompt: str, search_mode: str) -> str:
        if search_mode == "web":
            return f"Please provide a comprehensive answer using current web information when relevant:\n\n{prompt}"
        elif search_mode == "deep":
            return f"Please provide a deep, analytical response with thorough research and multiple perspectives:\n\n{prompt}"
        return prompt


class GeminiProvider(AIProvider):
    """Google Gemini provider."""

    def __init__(self, api_key: str, config: Dict):
        super().__init__("Gemini", api_key, config)
        self.base_url = config["endpoints"]["gemini"]

    def get_model_for_mode(self, search_mode: str) -> str:
        return self.config["providers"]["gemini"]["model"]

    async def query(self, session: aiohttp.ClientSession, prompt: str, search_mode: str) -> Optional[str]:
        if not self.available:
            return None

        enhanced_prompt = self._enhance_prompt(prompt, search_mode)
        params = {"key": self.api_key}
        max_tokens = self.config["settings"].get("max_tokens_gemini", self.config["settings"]["max_tokens"])

        data = {
            "contents": [{"parts": [{"text": enhanced_prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": self.config["settings"]["temperature"],
            },
        }

        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries + 1):
            try:
                model = self.config["providers"]["gemini"]["model"]
                url = f"{self.base_url}/models/{model}:generateContent"
                async with session.post(url, params=params, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if "candidates" in result and len(result["candidates"]) > 0:
                            candidate = result["candidates"][0]
                            if "content" in candidate and "parts" in candidate["content"]:
                                text = candidate["content"]["parts"][0]["text"]
                                if candidate.get("finishReason") == "MAX_TOKENS":
                                    print("  Warning: Gemini response truncated (MAX_TOKENS)")
                                return text
                        return None
                    elif response.status >= 500 and attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        print(f"  Gemini server error {response.status}, retrying in {delay}s ({attempt + 1}/{max_retries})")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        print(f"Gemini API error: {response.status}")
                        return None
            except Exception as e:
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    print(f"  Gemini connection error, retrying in {delay}s ({attempt + 1}/{max_retries}): {e}")
                    await asyncio.sleep(delay)
                    continue
                print(f"Error querying Gemini after {max_retries} retries: {e}")
                return None
        return None

    def _enhance_prompt(self, prompt: str, search_mode: str) -> str:
        if search_mode == "web":
            return f"Please search for current information and provide a comprehensive answer:\n\n{prompt}"
        elif search_mode == "deep":
            return f"Please provide a thorough, in-depth analysis with multiple angles and detailed research:\n\n{prompt}"
        return prompt


class OpenRouterProvider(AIProvider):
    """Generic OpenRouter provider for any model."""

    def __init__(self, api_key: str, model_config, provider_name: str, config: Dict):
        super().__init__(provider_name, api_key, config)
        self.model_config = model_config
        self.base_url = config["endpoints"]["openrouter"]

    def get_model_for_mode(self, search_mode: str) -> str:
        if isinstance(self.model_config, dict):
            return self.model_config.get(search_mode, self.model_config.get("none", ""))
        return self.model_config

    async def query(self, session: aiohttp.ClientSession, prompt: str, search_mode: str) -> Optional[str]:
        if not self.available:
            return None

        model = self.get_model_for_mode(search_mode)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/mark-kimura/consensus-plugin",
            "X-Title": "Consensus Multi-Provider Query Tool",
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.config["settings"]["max_tokens"],
        }

        if search_mode == "web" and not model.endswith(":online"):
            data["plugins"] = [{"id": "web", "max_results": 5, "search_prompt": "Relevant web results:"}]

        try:
            async with session.post(f"{self.base_url}/chat/completions", headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    print(f"{self.name} (OpenRouter) API error: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"Error querying {self.name} via OpenRouter: {e}")
            return None


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

async def query_all_providers(providers: List[AIProvider], prompt: str, search_mode: str) -> Dict[str, str]:
    """Query all available providers concurrently."""
    responses = {}

    async def query_with_progress(provider: AIProvider, session: aiohttp.ClientSession):
        model_name = provider.get_model_for_mode(search_mode)

        print(f"  * {provider.name} ({model_name}): Starting...", flush=True)
        start_time = time.time()
        try:
            resp = await provider.query(session, prompt, search_mode)
            elapsed = time.time() - start_time
            if resp:
                print(f"  + {provider.name} ({model_name}): Completed in {elapsed:.1f}s", flush=True)
            else:
                print(f"  x {provider.name} ({model_name}): No response received", flush=True)
            return provider.name, resp
        except Exception as e:
            print(f"  x {provider.name} ({model_name}): Error - {e}", flush=True)
            return provider.name, None

    async with aiohttp.ClientSession() as session:
        tasks = [
            asyncio.create_task(query_with_progress(p, session))
            for p in providers
            if p.available
        ]
        for completed in asyncio.as_completed(tasks):
            name, resp = await completed
            if resp:
                responses[name] = resp

    return responses


def consolidate_responses(responses: Dict[str, str], prompt: str) -> str:
    """Consolidate responses from multiple providers into a markdown document."""
    if not responses:
        return "No responses received from any provider."

    lines = [
        f"# Consolidated AI Response - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"**Query:** {prompt[:200]}{'...' if len(prompt) > 200 else ''}",
        "",
        f"**Providers Used:** {', '.join(responses.keys())}",
        "",
    ]

    for provider_name, response in responses.items():
        lines.append(f"## {provider_name} Response")
        lines.append("")
        lines.append(response.strip() if isinstance(response, str) else str(response))
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def setup_providers(config: Dict) -> List[AIProvider]:
    """Initialize AI providers based on configuration."""
    providers = []

    for provider_name, provider_config in config["providers"].items():
        if not provider_config["enabled"]:
            continue

        if provider_config["use_openrouter"]:
            openrouter_key = config["api_keys"].get("openrouter")
            if not openrouter_key:
                print(f"Warning: {provider_name} configured for OpenRouter but no key found, skipping...", flush=True)
                continue
            providers.append(OpenRouterProvider(openrouter_key, provider_config["openrouter_model"], provider_name, config))
        else:
            api_key = config["api_keys"].get(provider_name)
            if not api_key:
                print(f"Warning: {provider_name} direct API enabled but no key found, skipping...", flush=True)
                continue
            if provider_name == "openai":
                providers.append(OpenAIProvider(api_key, config))
            elif provider_name == "gemini":
                providers.append(GeminiProvider(api_key, config))

    return providers


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser(description="Query multiple AI providers concurrently")
    parser.add_argument("markdown_file", help="Path to the markdown file containing the prompt")
    parser.add_argument("--search-mode", choices=["web", "none"], help="Search mode: web or none")
    parser.add_argument("--output-dir", default=None, help="Output directory for responses (default: temp directory)")
    parser.add_argument("--config", default=None, help="Path to configuration file")
    parser.add_argument("--plugin-root", default=None, help="Path to plugin root directory")

    args = parser.parse_args()

    config = load_config(config_path=args.config, plugin_root=args.plugin_root)

    if not args.search_mode:
        args.search_mode = config["settings"]["default_search_mode"]

    if not os.path.exists(args.markdown_file):
        print(f"Error: File '{args.markdown_file}' not found")
        sys.exit(1)

    with open(args.markdown_file, "r", encoding="utf-8") as f:
        prompt = f.read()

    providers = setup_providers(config)
    available = [p for p in providers if p.available]

    if not available:
        print("Error: No API keys found. Please set environment variables:")
        print("  export OPENAI_API_KEY='sk-...'")
        print("  export GEMINI_API_KEY='AI...'")
        print("  export OPENROUTER_API_KEY='sk-or-...'")
        sys.exit(1)

    print(f"Available providers: {', '.join(p.name for p in available)}")
    print(f"Search mode: {args.search_mode}")
    print("Querying providers...", flush=True)

    responses = await query_all_providers(available, prompt, args.search_mode)

    if not responses:
        print("Error: No responses received from any provider")
        sys.exit(1)

    consolidated = consolidate_responses(responses, prompt)

    # Use explicit output dir if provided, otherwise use temp directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        output_file = os.path.join(args.output_dir, f"consolidated-{timestamp}.md")
    else:
        tmp_dir = tempfile.mkdtemp(prefix="consensus-")
        output_file = os.path.join(tmp_dir, f"consolidated-{timestamp}.md")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(consolidated)

    print(f"Output saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
