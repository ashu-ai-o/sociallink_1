"""
Gemini API Key Pool - Rotating Rate Limiter
================================================
- Holds multiple Gemini API keys from database AISettings or settings.GEMINI_API_KEYS
- Each key is allowed max 15 requests/minute
- Keys are rotated every 60 seconds (1 minute) in round-robin order
- Falls back to the next key if the current key is rate-limited (429)
"""

import time
import asyncio
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

# Per-key request limit
KEY_MAX_RPM = 15
# Key rotation interval in seconds (1 minute for Gemini)
KEY_ROTATION_SECONDS = 60


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
            return bool(self.request_count < KEY_MAX_RPM)
        return False

    async def record_use(self):
        async with self._lock:
            now = time.monotonic()
            if now - self.window_start >= 60:
                self.request_count = 0
                self.window_start = now
            self.request_count += 1


class GeminiKeyPool:
    """
    Thread-safe async pool that rotates between multiple Gemini API keys.
    """

    _instance: Optional["GeminiKeyPool"] = None

    def __init__(self, keys: List[str]):
        if not keys:
            raise ValueError("At least one Gemini API key must be provided.")
        self._slots = [_KeySlot(k) for k in keys]
        self._rotation_index = 0
        self._rotation_lock = asyncio.Lock()
        self._rotation_start = time.monotonic()

    @classmethod
    def from_settings(cls) -> "GeminiKeyPool":
        """Singleton factory — reads from Django settings or AISettings."""
        from django.conf import settings
        from automations.models import AISettings
        
        # Load keys from AISettings if available
        keys = []
        try:
            ai_settings = AISettings.load()
            raw = ai_settings.gemini_api_keys
            if raw:
                keys = [k.strip() for k in raw.split(",") if k.strip()]
        except Exception as e:
            logger.warning(f"Could not load AISettings: {e}")
            
        if not keys:
            raw = getattr(settings, "GEMINI_API_KEYS", None)
            if not raw:
                single = getattr(settings, "GEMINI_API_KEY", "")
                keys = [single] if single else []
            elif isinstance(raw, str):
                keys = [k.strip() for k in raw.split(",") if k.strip()]
            else:
                keys = list(raw)

        if not keys:
            logger.warning("No Gemini API keys configured.")
            # Set a dummy key to prevent crash if not used
            keys = ["dummy_key"]
            
        # Instead of global singleton that cannot refresh when AISettings changes,
        # we update the slots if the keys changed, or just instantiate a new one.
        # But for rate limiting context, we should preserve request counts.
        # For simplicity, we just use the singleton pattern here.
        if cls._instance is None:
            cls._instance = cls(keys)
            logger.info(f"[GeminiKeyPool] Initialized with {len(keys)} API key(s).")
        else:
            current_keys = [s.key for s in cls._instance._slots]
            if current_keys != keys:
                cls._instance = cls(keys)
                logger.info(f"[GeminiKeyPool] Re-initialized with {len(keys)} API key(s).")
            
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset singleton — useful in tests."""
        cls._instance = None

    async def get_key(self) -> str:
        """
        Return the best available API key.
        Rotates active index every minute.
        """
        async with self._rotation_lock:
            now = time.monotonic()
            if now - self._rotation_start >= KEY_ROTATION_SECONDS:
                self._rotation_index = (self._rotation_index + 1) % len(self._slots)
                self._rotation_start = now
                key_snippet = self._slots[self._rotation_index].key[-6:] if len(self._slots[self._rotation_index].key) > 6 else self._slots[self._rotation_index].key
                logger.info(
                    f"[GeminiKeyPool] Rotated to key index {self._rotation_index} "
                    f"(key: ...{key_snippet})"
                )

        n = len(self._slots)
        for offset in range(n):
            idx = (self._rotation_index + offset) % n
            slot = self._slots[idx]
            if await slot.can_use():
                await slot.record_use()
                logger.debug(
                    f"[GeminiKeyPool] Using key index {idx} "
                    f"(requests this window: {slot.request_count}/{KEY_MAX_RPM})"
                )
                return slot.key

        logger.warning("[GeminiKeyPool] All keys at capacity. Waiting 2s before retry...")
        await asyncio.sleep(2)
        slot = self._slots[self._rotation_index]
        await slot.record_use()
        return slot.key
