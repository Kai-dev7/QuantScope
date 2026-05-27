from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import os

from app.services.config_service import config_service


class ConfigProvider:
    """Effective configuration provider with simple env→DB merge and TTL cache.

    - Priority: ENV > DB
    - Cache TTL: configurable (default 60s)
    - Invalidate on writes: caller should invoke `invalidate()` after writes
    """

    def __init__(self, ttl_seconds: int = 60) -> None:
        self._ttl = timedelta(seconds=ttl_seconds)
        self._cache_settings: Dict[Optional[str], Dict[str, Any]] = {}
        self._cache_time: Dict[Optional[str], datetime] = {}

    def invalidate(self, user_id: Optional[str] = None) -> None:
        if user_id is None:
            self._cache_settings.clear()
            self._cache_time.clear()
            return
        self._cache_settings.pop(user_id, None)
        self._cache_time.pop(user_id, None)

    def _is_cache_valid(self, user_id: Optional[str] = None) -> bool:
        return (
            user_id in self._cache_settings
            and user_id in self._cache_time
            and __import__("datetime").datetime.now(__import__("datetime").timezone.utc) - self._cache_time[user_id] < self._ttl
        )

    async def get_effective_system_settings(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        if self._is_cache_valid(user_id):
            return dict(self._cache_settings.get(user_id) or {})

        # Load DB settings
        cfg = await config_service.get_system_config(user_id=user_id)
        base: Dict[str, Any] = {}
        if cfg and getattr(cfg, "system_settings", None):
            try:
                base = dict(cfg.system_settings)
            except Exception:
                base = {}

        # Merge ENV over DB (best-effort heuristics):
        # - if ENV with exact key exists -> override
        # - try uppercased and dot/space to underscore variants
        merged: Dict[str, Any] = dict(base)
        for k, v in list(base.items()):
            candidates = [
                k,
                k.upper(),
                str(k).replace(".", "_").replace(" ", "_").upper(),
            ]
            found = None
            for ek in candidates:
                if ek in os.environ:
                    found = os.environ.get(ek)
                    break
            if found is not None:
                merged[k] = found

        # Optionally: allow whitelisting additional env-only keys via prefix
        # For now, keep minimal behavior to avoid surprising surfaces.

        # Cache
        self._cache_settings[user_id] = dict(merged)
        self._cache_time[user_id] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        return dict(merged)
    async def get_system_settings_meta(self, user_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Return metadata for system settings keys including sensitivity, editability and source.
        Fields per key:
          - sensitive: bool (by keyword patterns)
          - editable: bool (False if sensitive or source is environment; True otherwise)
          - source: 'environment' | 'database' | 'default'
          - has_value: bool (effective value is not None/empty)
        """
        # Load DB settings raw
        cfg = await config_service.get_system_config(user_id=user_id)
        db_settings: Dict[str, Any] = {}
        if cfg and getattr(cfg, "system_settings", None):
            try:
                db_settings = dict(cfg.system_settings)
            except Exception:
                db_settings = {}

        def _env_override_for_key(key: str) -> Optional[Any]:
            candidates = [
                key,
                key.upper(),
                str(key).replace(".", "_").replace(" ", "_").upper(),
            ]
            for ek in candidates:
                if ek in os.environ:
                    return os.environ.get(ek)
            return None

        sens_patterns = ("key", "secret", "password", "token", "client_secret")
        meta: Dict[str, Dict[str, Any]] = {}
        for k, v in db_settings.items():
            env_v = _env_override_for_key(k)
            source = "environment" if env_v is not None else ("database" if v is not None else "default")
            sensitive = isinstance(k, str) and any(p in k.lower() for p in sens_patterns)
            editable = not sensitive and source != "environment"
            effective_val = env_v if env_v is not None else v
            has_value = effective_val not in (None, "")
            meta[k] = {
                "sensitive": bool(sensitive),
                "editable": bool(editable),
                "source": source,
                "has_value": bool(has_value),
            }
        return meta



# Module-level singleton
provider = ConfigProvider(ttl_seconds=60)
