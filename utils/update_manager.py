import os, sys, time, subprocess, shutil, psutil, GPUtil, platform, winreg, json, ctypes, requests
from zipfile import ZipFile
from io import BytesIO
from pypresence import Presence
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtChart import *
from config import *
from ui.custom_dialogs import CustomNotification

# ======================= GÜNCELLEME KONTROLÜ =======================
class UpdateChecker(QThread):
    update_available = pyqtSignal(str, str)  

    def __init__(self, current_version, repo_url):
        super().__init__()
        self.current_version = current_version
        self.repo_url = repo_url

    def run(self):
        try:
            api_url = "https://api.github.com/repos/twiez/twiez-optimizer/releases/latest"
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                latest_release = response.json()
                latest_version = latest_release["tag_name"]
                download_url = latest_release["assets"][0]["browser_download_url"]
                if self.is_new_version(latest_version):
                    self.update_available.emit(latest_version, download_url)
        except Exception as e:
            pass 

    def is_new_version(self, latest_version):
        
        current_parts = list(map(int, self.current_version.split(".")))
        latest_parts = list(map(int, latest_version.lstrip('v').split(".")))
        return latest_parts > current_parts

# ======================= GÜNCELLEME YÖNETİCİSİ =======================
class UpdateManager:
    def __init__(self, parent, download_url):
        self.parent = parent
        self.download_url = download_url

    def download_and_install_update(self):
        try:
            response = requests.get(self.download_url, stream=True, timeout=30)
            if response.status_code == 200:
                zip_file = ZipFile(BytesIO(response.content))
                # Path traversal koruması: zararlı dosya yollarını kontrol et
                target_dir = os.getcwd()
                for member in zip_file.namelist():
                    member_path = os.path.realpath(os.path.join(target_dir, member))
                    if not member_path.startswith(os.path.realpath(target_dir)):
                        CustomNotification("⛔ Güncelleme dosyası güvenlik kontrolünden geçemedi!", duration=3000, parent=self.parent).show_notification()
                        return
                zip_file.extractall(target_dir)
                CustomNotification("✅ Uygulama başarıyla güncellendi! Lütfen uygulamayı yeniden başlatın.", duration=3000, parent=self.parent).show_notification()
                sys.exit()  
            else:
                CustomNotification("⛔ Güncelleme indirilemedi!", duration=3000, parent=self.parent).show_notification()
        except Exception as e:
            CustomNotification(f"⛔ Güncelleme sırasında hata oluştu:\n{str(e)}", duration=3000, parent=self.parent).show_notification()

