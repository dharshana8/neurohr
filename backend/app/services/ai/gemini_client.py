"""
Google Gemini AI Client integration module for NeuroHR X.
Supports OpenAI-compatible Gemini 2.0 Flash endpoint.
"""
from app.services.ai.grok_client import GrokClient, GrokClient as GeminiClient, grok_client, grok_client as gemini_client

__all__ = ["GeminiClient", "gemini_client", "GrokClient", "grok_client"]

