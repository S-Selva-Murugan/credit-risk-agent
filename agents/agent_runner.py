"""
Agent Runner
============
Base class for all Claude SDK agents.

Reads the agent's .md file (frontmatter = config, body = system prompt),
then calls the Claude API with that system prompt.
Every subagent is just an instantiation of this class pointed at its .md file.
"""

import os
import re
import json
import anthropic

# Parse YAML frontmatter without requiring the yaml package
def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split ---frontmatter--- from body. Returns (meta_dict, body_str)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end == -1:
        return {}, text
    front = text[3:end].strip()
    body  = text[end + 3:].strip()
    meta  = {}
    for line in front.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta, body


class AgentRunner:
    """
    Reads an agent .md file and executes it via the Claude API.
    The .md frontmatter supplies the model; the body is the system prompt.
    """

    DEFAULT_MODEL = "claude-haiku-4-5-20251001"

    def __init__(self, md_path: str, tracer=None, metrics=None):
        self.md_path = md_path
        self.tracer   = tracer
        self.metrics  = metrics

        # Load and parse the .md definition
        with open(md_path, "r", encoding="utf-8") as f:
            raw = f.read()
        self.meta, self.system_prompt = _parse_frontmatter(raw)
        self.name  = self.meta.get("name", os.path.basename(md_path))
        self.model = self.meta.get("model", self.DEFAULT_MODEL)

        # Initialise Anthropic client — supports OpenRouter via ANTHROPIC_BASE_URL
        client_kwargs = {"api_key": os.environ.get("ANTHROPIC_API_KEY", "")}
        base_url = os.environ.get("ANTHROPIC_BASE_URL")
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = anthropic.Anthropic(**client_kwargs)

    def run(self, user_message: str, max_tokens: int = 2048) -> str:
        """
        Send user_message to Claude with this agent's system prompt.
        Returns the raw text response.
        """
        if self.tracer:
            self.tracer.log(agent=self.name, message=f"Calling Claude ({self.model})")

        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )

        response = message.content[0].text

        if self.metrics and hasattr(message, "usage") and message.usage:
            self.metrics.record_tokens(
                self.name,
                message.usage.input_tokens,
                message.usage.output_tokens,
            )

        if self.tracer:
            self.tracer.log(agent=self.name, message=f"Response received ({len(response)} chars)")

        return response

    def run_json(self, user_message: str, max_tokens: int = 2048) -> dict:
        """
        Like run() but extracts and parses the first JSON object in the response.
        Handles all Claude output patterns:
          - bare JSON
          - ```json ... ``` fenced block
          - JSON followed by extra explanation text
        """
        raw = self.run(user_message, max_tokens)

        # 1. Try a fenced ```json ... ``` block first
        fence_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw, re.IGNORECASE)
        if fence_match:
            candidate = fence_match.group(1)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        # 2. Extract the first { ... } block by brace counting
        start = raw.find("{")
        if start != -1:
            depth = 0
            for i, ch in enumerate(raw[start:], start):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = raw[start:i + 1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            break

        # 3. Last resort — try the whole stripped response
        stripped = raw.strip()
        try:
            return json.loads(stripped)
        except json.JSONDecodeError as e:
            if self.tracer:
                self.tracer.log(agent=self.name, message=f"JSON parse error: {e}", level="ERROR")
            raise ValueError(f"[{self.name}] Claude returned invalid JSON: {e}\nRaw: {raw[:300]}")
