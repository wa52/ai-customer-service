"""Persist admin settings locally, protecting the model key with Windows DPAPI."""

import base64
import ctypes
import json
import os
from pathlib import Path
from typing import Any

from app.config.settings import Settings


def _config_path() -> Path:
    app_data = os.getenv("LOCALAPPDATA")
    root = Path(app_data) if app_data else Path.home() / ".local" / "share"
    return root / "SmartCustomerService" / "admin-config.json"


class _DataBlob(ctypes.Structure):
    _fields_ = [("size", ctypes.c_uint32), ("data", ctypes.POINTER(ctypes.c_ubyte))]


def _protect_windows(value: bytes, *, decrypt: bool = False) -> bytes:
    if os.name != "nt":
        raise RuntimeError("Persistent API key storage requires Windows DPAPI; configure LLM_API_KEY in the environment on this platform")

    source_buffer = ctypes.create_string_buffer(value)
    source = _DataBlob(len(value), ctypes.cast(source_buffer, ctypes.POINTER(ctypes.c_ubyte)))
    target = _DataBlob()
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    crypt32.CryptProtectData.argtypes = [ctypes.POINTER(_DataBlob), ctypes.c_wchar_p, ctypes.POINTER(_DataBlob), ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(_DataBlob)]
    crypt32.CryptProtectData.restype = ctypes.c_int
    crypt32.CryptUnprotectData.argtypes = [ctypes.POINTER(_DataBlob), ctypes.POINTER(ctypes.c_wchar_p), ctypes.POINTER(_DataBlob), ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(_DataBlob)]
    crypt32.CryptUnprotectData.restype = ctypes.c_int
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    if decrypt:
        description = ctypes.c_wchar_p()
        success = crypt32.CryptUnprotectData(ctypes.byref(source), ctypes.byref(description), None, None, None, 0, ctypes.byref(target))
    else:
        # Machine scope keeps settings readable if the local backend is relaunched elevated.
        success = crypt32.CryptProtectData(ctypes.byref(source), "SmartCustomerService", None, None, None, 0x4, ctypes.byref(target))
    if not success:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        kernel32.LocalFree(target.data)
        if decrypt and description:
            kernel32.LocalFree(description)


def load_admin_settings(base: Settings) -> Settings:
    path = _config_path()
    if not path.exists():
        return base
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        updates = dict(payload.get("settings", {}))
        environment_names = {"llm_api_key": "LLM_API_KEY", "database_url": "DATABASE_URL", "redis_url": "REDIS_URL"}
        for field, encrypted in payload.get("protected_secrets", {}).items():
            environment_name = environment_names.get(field)
            if encrypted and os.name == "nt" and not (environment_name and os.getenv(environment_name)):
                updates[field] = _protect_windows(base64.b64decode(encrypted), decrypt=True).decode("utf-8")
        return base.model_copy(update=updates)
    except (OSError, ValueError, TypeError, json.JSONDecodeError, RuntimeError):
        return base


def save_admin_settings(settings: Settings) -> None:
    values: dict[str, Any] = settings.model_dump(exclude={"llm_api_key", "database_url", "redis_url"})
    protected_secrets = {}
    if os.name == "nt":
        for field in ("llm_api_key", "database_url", "redis_url"):
            value = getattr(settings, field)
            if value:
                protected_secrets[field] = base64.b64encode(_protect_windows(value.encode("utf-8"))).decode("ascii")
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"settings": values, "protected_secrets": protected_secrets}, ensure_ascii=False, indent=2), encoding="utf-8")
