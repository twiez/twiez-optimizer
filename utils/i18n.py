import os
import json
from utils.settings_manager import get_setting

class TranslationManager:
    _instance = None
    _translations = {}
    _current_lang = "tr"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TranslationManager, cls).__new__(cls)
            cls._instance.load_language()
        return cls._instance

    def load_language(self):
        # Ayarlardan dili çek, yoksa varsayılan en
        lang = get_setting("language", "en")
        self._current_lang = lang
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        locale_path = os.path.join(base_dir, "locales", f"{lang}.json")
        
        if os.path.exists(locale_path):
            try:
                with open(locale_path, "r", encoding="utf-8") as f:
                    self._translations = json.load(f)
            except Exception as e:
                print(f"Dil dosyası yüklenirken hata: {e}")
                self._translations = {}
        else:
            self._translations = {}

    def get(self, key, default=None):
        return self._translations.get(key, default if default else key)

def tr(key, default=None):
    """Kısa kullanım için çeviri fonksiyonu"""
    return TranslationManager().get(key, default)
