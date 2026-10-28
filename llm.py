"""LLM backend abstraction.

Supports two real backends (Amazon Bedrock via boto3, or the Anthropic API directly)
and a deterministic DEMO_MODE fallback so the whole graph can be exercised end-to-end
with zero credentials and zero network calls. This mirrors a real production concern:
agent systems need to degrade predictably, not silently, when a backend is unavailable.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class LLMResponse:
    text: str
    demo_mode: bool


class LLMClient:
    """A thin, swappable wrapper. Each agent calls `client.generate(system, user)`
    and gets back text plus a flag indicating whether this was a live model call.
    """

    def __init__(self) -> None:
        self.backend, self.demo_mode = self._detect_backend()

    def _detect_backend(self) -> tuple[str, bool]:
        if os.getenv("FORCE_DEMO_MODE", "false").lower() == "true":
            return "demo", True
        if os.getenv("ANTHROPIC_API_KEY"):
            return "anthropic", False
        if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
            return "bedrock", False
        return "demo", True

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        if self.backend == "anthropic":
            return self._generate_anthropic(system_prompt, user_prompt)
        if self.backend == "bedrock":
            return self._generate_bedrock(system_prompt, user_prompt)
        return self._generate_demo(system_prompt, user_prompt)

    # --- real backends ---

    def _generate_anthropic(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        import anthropic

        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(block.text for block in msg.content if block.type == "text")
        return LLMResponse(text=text, demo_mode=False)

    def _generate_bedrock(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        import json

        import boto3

        client = boto3.client(
            "bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        model_id = os.getenv(
            "BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0"
        )
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 600,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        resp = client.invoke_model(modelId=model_id, body=json.dumps(body))
        payload = json.loads(resp["body"].read())
        text = "".join(
            block["text"] for block in payload.get("content", []) if block.get("type") == "text"
        )
        return LLMResponse(text=text, demo_mode=False)

    # --- demo fallback ---

    def _generate_demo(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Deterministic, clearly-labeled mock output.

        This is NOT a model call. It exists so the agent graph, the retrieval step, and
        the control flow can all be exercised without any credentials. Real reasoning
        text is produced by the live backends above.
        """
        return LLMResponse(
            text=(
                "[DEMO MODE: deterministic mock response, not a live model generation. "
                "Set AWS or Anthropic credentials in .env to see real LLM reasoning here.]"
            ),
            demo_mode=True,
        )


_default_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client
