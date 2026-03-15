"""
OpenRouter API Key Pool - Rotating Rate Limiter
================================================
- Holds multiple OpenRouter API keys from settings.OPENROUTER_API_KEYS
- Each key is allowed max 15 requests/minute (capped below the 20 req/min limit for safety)
- Keys are rotated every 5 minutes in round-robin order
- Falls back to the next key if the current key is rate-limited (429)
"""

import time
import asyncio
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

# Per-key request limit (safe buffer below OpenRouter's 20/min limit)
KEY_MAX_RPM = 15
# Key rotation interval in seconds
KEY_ROTATION_SECONDS = 300  # 5 minutes


class _KeySlot:
    """Tracks usage stats for a single API key."""

    def __init__(self, key: str):
        self.key = key
        self.request_count = 0       # Requests sent this minute window
        self.window_start = time.monotonic()  # Start of current 1-min window
        self._lock = asyncio.Lock()

    async def can_use(self) -> bool:
        async with self._lock:
            now = time.monotonic()
            # Reset window every 60 seconds
            if now - self.window_start >= 60:
                self.request_count = 0
                self.window_start = now
            return self.request_count < KEY_MAX_RPM

    async def record_use(self):
        async with self._lock:
            now = time.monotonic()
            if now - self.window_start >= 60:
                self.request_count = 0
                self.window_start = now
            self.request_count += 1


class OpenRouterKeyPool:
    """
    Thread-safe async pool that rotates between multiple OpenRouter API keys.

    Usage:
        pool = OpenRouterKeyPool.from_settings()
        async with pool.acquire() as key:
            # use key for one AI request
    """

    _instance: Optional["OpenRouterKeyPool"] = None

    def __init__(self, keys: List[str]):
        if not keys:
            raise ValueError("At least one OpenRouter API key must be provided.")
        self._slots = [_KeySlot(k) for k in keys]
        self._rotation_index = 0
        self._rotation_lock = asyncio.Lock()
        self._rotation_start = time.monotonic()

    @classmethod
    def from_settings(cls) -> "OpenRouterKeyPool":
        """Singleton factory — reads from Django settings."""
        if cls._instance is None:
            from django.conf import settings
            # Support comma-separated or list
            raw = getattr(settings, "OPENROUTER_API_KEYS", None)
            if not raw:
                # Fallback: single key
                single = getattr(settings, "OPENROUTER_API_KEY", "")
                keys = [single] if single else []
            elif isinstance(raw, str):
                keys = [k.strip() for k in raw.split(",") if k.strip()]
            else:
                keys = list(raw)

            if not keys:
                raise RuntimeError(
                    "No OpenRouter API keys configured. "
                    "Set OPENROUTER_API_KEYS (comma-separated) or OPENROUTER_API_KEY in settings/.env"
                )
            cls._instance = cls(keys)
            logger.info(f"[KeyPool] Initialized with {len(keys)} API key(s).")
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset singleton — useful in tests."""
        cls._instance = None

    async def get_key(self) -> str:
        """
        Return the best available API key.
        Rotates active index every 5 minutes.
        Skips rate-limited keys and falls back to others.
        """
        async with self._rotation_lock:
            # Time-based rotation: every KEY_ROTATION_SECONDS, advance the index
            now = time.monotonic()
            if now - self._rotation_start >= KEY_ROTATION_SECONDS:
                self._rotation_index = (self._rotation_index + 1) % len(self._slots)
                self._rotation_start = now
                logger.info(
                    f"[KeyPool] Rotated to key index {self._rotation_index} "
                    f"(key: ...{self._slots[self._rotation_index].key[-6:]})"
                )

        # Try from the current rotation index, then fall back through all keys
        n = len(self._slots)
        for offset in range(n):
            idx = (self._rotation_index + offset) % n
            slot = self._slots[idx]
            if await slot.can_use():
                await slot.record_use()
                logger.debug(
                    f"[KeyPool] Using key index {idx} "
                    f"(requests this window: {slot.request_count}/{KEY_MAX_RPM})"
                )
                return slot.key

        # All keys exhausted — wait 2s and try again (simple back-off)
        logger.warning("[KeyPool] All keys at capacity. Waiting 2s before retry...")
        await asyncio.sleep(2)
        # Return the current slot key regardless — the retryable 429 handler will catch it
        slot = self._slots[self._rotation_index]
        await slot.record_use()
        return slot.key
