import os, sys, time, subprocess, shutil, psutil, GPUtil, platform, winreg, json, ctypes, requests
from zipfile import ZipFile
from io import BytesIO
from pypresence import Presence
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtChart import *
from config import *

# ======================= CLEANER THREAD =======================
class CleanerThread(QThread):
    update_status = pyqtSignal(str)
    complete_signal = pyqtSignal(int)
    
    def __init__(self, directories):
        super().__init__()
        self.directories = directories
        self._is_running = True
    
    def run(self):
        total_deleted = 0
        for dir_path, label in self.directories:
            if dir_path and os.path.exists(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        if not self._is_running:
                            return
                        file_path = os.path.join(root, file)
                        try:
                            os.remove(file_path)
                            total_deleted += 1
                            self.update_status.emit(str(total_deleted))
                        except Exception:
                            pass
                        time.sleep(0.01)
        self.complete_signal.emit(total_deleted)
    
    def stop(self):
        self._is_running = False

