import os, sys, time, subprocess, shutil, psutil, GPUtil, platform, winreg, json, ctypes, requests
from zipfile import ZipFile
from io import BytesIO
from pypresence import Presence
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtChart import *
from config import *

# ======================= RPC THREAD =======================
class RPCThread(QThread):
    def __init__(self):
        super().__init__()
        self.running = True
        self.client_id = "1361646178965389322"  
        self.RPC = Presence(self.client_id)

    def run(self):
        try:
            self.RPC.connect()
            self.RPC.update(
                state="Busy Speeding Up His Computer⚡",
                start=time.time(),
                large_image="twiez_optimizer_logo",
                large_text="Twiez Optimizer - Bilgisayarını hızlandır"
            )
            while self.running:
                time.sleep(15)
        except Exception as e:
            print(f"RPC Hatası: {str(e)}")

    def stop(self):
        self.running = False
        try:
            self.RPC.close()
        except Exception:
            pass

