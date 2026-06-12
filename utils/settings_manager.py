import os
import json

# Store settings.json in LocalAppData for persistence across pyinstaller --onefile builds
_APP_DATA_DIR = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'TwiezOptimizer')
if not os.path.exists(_APP_DATA_DIR):
    os.makedirs(_APP_DATA_DIR, exist_ok=True)
SETTINGS_FILE = os.path.join(_APP_DATA_DIR, "settings.json")

_cache: dict = None


def _load() -> dict:
    global _cache
    if _cache is None:
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    _cache = json.load(f)
            except Exception:
                _cache = {}
        else:
            _cache = {}
    return _cache


def _save():
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(_cache, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[SettingsManager] Save error: {e}")


# ── Section-based API (used for toggle persistence) ──────────────────────────

def get(section: str, key: str, default=None):
    """Return saved value for section → key, or default."""
    return _load().get(section, {}).get(key, default)


def set_value(section: str, key: str, value):
    """Persist section → key = value immediately to disk."""
    data = _load()
    if section not in data:
        data[section] = {}
    data[section][key] = value
    _save()


def get_section(section: str) -> dict:
    """Return all saved keys for a section as a dict."""
    return dict(_load().get(section, {}))


# ── Flat API (legacy compat) ──────────────────────────────────────────────────

def load_settings() -> dict:
    return _load()


def save_settings(settings: dict):
    global _cache
    _cache = settings
    _save()


def get_setting(key, default=None):
    return _load().get(key, default)


def set_setting(key, value):
    _load()[key] = value
    _save()
