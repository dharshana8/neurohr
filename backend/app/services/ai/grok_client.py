import json
import logging
import re
from typing import List, Dict, Optional, Any
from openai import AsyncOpenAI, RateLimitError, APITimeoutError, APIError

from app.core.config import settings
from app.services.ai.exceptions import (
    AIServiceError,
    AIConfigurationError,
    AIRateLimitError,
    AITimeoutError,
    AIResponseParseError,
)

logger = logging.getLogger("neurohr.ai.grok")

class GrokClient:
    """
    Reusable asynchronous xAI Grok client using OpenAI-compatible API protocol.
    Maintains a persistent client instance and enforces safe error handling.
    """
    _instance: Optional["GrokClient"] = None

    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None
        self._is_configured_override: Optional[bool] = None
        self._init_client()

    def _init_client(self):
        api_key = settings.XAI_API_KEY.strip() if settings.XAI_API_KEY else ""
        if api_key:
            self._client = AsyncOpenAI(
                api_key=api_key,
                base_url=settings.XAI_BASE_URL,
                timeout=30.0,
                max_retries=2
            )
        else:
            self._client = None

    @classmethod
    def get_instance(cls) -> "GrokClient":
        if cls._instance is None:
            cls._instance = GrokClient()
        return cls._instance

    @property
    def is_configured(self) -> bool:
        if self._is_configured_override is not None:
            return self._is_configured_override
        return bool(settings.XAI_API_KEY and settings.XAI_API_KEY.strip())

    @is_configured.setter
    def is_configured(self, value: Optional[bool]):
        self._is_configured_override = value

    @is_configured.deleter
    def is_configured(self):
        self._is_configured_override = None

    @property
    def model(self) -> str:
        return settings.XAI_MODEL or "grok-4.6"

    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 1200
    ) -> str:
        """
        Generate completion from chat messages history.
        """
        if not self.is_configured:
            raise AIConfigurationError("Generative AI is not configured. Please configure XAI_API_KEY.")

        if self._client is None:
            self._init_client()
            if self._client is None:
                raise AIConfigurationError("Failed to initialize Grok client.")

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content or ""
        except RateLimitError as e:
            logger.warning("Grok API rate limit exceeded")
            raise AIRateLimitError("Grok AI service is experiencing high traffic. Please try again shortly.")
        except APITimeoutError as e:
            logger.error("Grok API request timed out")
            raise AITimeoutError("AI service request timed out. Please try again.")
        except APIError as e:
            # Sanitize error message to prevent secret leaking
            sanitized_msg = re.sub(r'Bearer\s+[A-Za-z0-9_\-\.]+', 'Bearer [REDACTED]', str(e))
            logger.error("Grok API error: %s", sanitized_msg)
            raise AIServiceError("AI service returned an error. Please try again later.")
        except Exception as e:
            logger.error("Unexpected error calling Grok API: %s", type(e).__name__)
            raise AIServiceError("Unexpected error communicating with AI service.")

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1200
    ) -> str:
        """
        Generate completion for a prompt with an optional system prompt.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return await self.generate_chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output and safely parse it.
        """
        raw_text = await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature
        )

        # Clean potential markdown fences ```json ... ```
        cleaned = raw_text.strip()
        if "```" in cleaned:
            # Extract content between markdown code blocks
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned)
            if match:
                cleaned = match.group(1).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response from Grok: %s", str(e))
            raise AIResponseParseError(f"Grok response was not valid JSON: {cleaned[:100]}...")

grok_client = GrokClient.get_instance()
