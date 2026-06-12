import os, sys, time, subprocess, shutil, psutil, GPUtil, platform, winreg, json, ctypes, requests
from zipfile import ZipFile
from io import BytesIO
from pypresence import Presence
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtChart import *
from config import *

from utils.i18n import tr

# ======================= HOME (🏠 Ev) WIDGET =======================
class HomeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.start_status_timer()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        # Kişiye Özel Selamlama
        greeting = QLabel(tr("home_greeting", "Merhaba, {}!").format(platform.node()))
        greeting.setAlignment(Qt.AlignCenter)
        greeting.setStyleSheet(f"color: {STYLE_CONFIG['dark']['primary']}; font: bold 24px;")
        main_layout.addWidget(greeting)
        # Sistem Durum Özeti Paneli
        status_panel = self.create_system_status_panel()
        main_layout.addWidget(status_panel)
        # Kısayol Butonları
        shortcuts = self.create_shortcut_buttons()
        main_layout.addLayout(shortcuts)
        # Son Güncellemeler / Duyurular
        announcements = self.create_announcements_panel()
        main_layout.addWidget(announcements)
        # Rastgele İpucu / İstatistik
        tip = QLabel(f"{tr('home_tip_prefix', 'İpucu')}: {self.get_random_tip()}")
        tip.setAlignment(Qt.AlignCenter)
        tip.setStyleSheet(f"color: {STYLE_CONFIG['dark']['text']}; font: italic 12px;")
        main_layout.addWidget(tip)
        # Ekstra bilgi
        content_label = QLabel(tr("home_footer", "Twiez Optimizer ile sisteminizi optimize edin ve hızlandırın!"))
        content_label.setAlignment(Qt.AlignCenter)
        content_label.setStyleSheet(f"color: {STYLE_CONFIG['dark']['text']}; font: 13px '{STYLE_CONFIG['font']['content'][0]}'; padding-top: 10px;")
        main_layout.addWidget(content_label)
        style_all_buttons(self)

    def create_system_status_panel(self):
        frame = QFrame()
        frame.setStyleSheet(f"background: {STYLE_CONFIG['dark']['card_bg']}; border-radius: 10px; padding: 10px;")
        layout = QGridLayout(frame)
        layout.setSpacing(10)
        self.lbl_cpu_status = QLabel(f"{tr('home_cpu', 'CPU')}: N/A")
        self.lbl_ram_status = QLabel(f"{tr('home_ram', 'RAM')}: N/A")
        self.lbl_disk_status = QLabel(f"{tr('home_disk', 'Disk')}: N/A")
        self.lbl_os_info = QLabel(f"{tr('home_os', 'OS')}: {platform.system()} {platform.release()}")
        self.lbl_computer_name = QLabel(f"{tr('home_pc', 'Bilgisayar')}: {platform.node()}")
        last_opt = self.get_antivirus_status()
        self.lbl_last_opt = QLabel(f"{tr('home_av_status', 'Antivirüs Durumu:')} {last_opt}")
        for lbl in [self.lbl_cpu_status, self.lbl_ram_status, self.lbl_disk_status, self.lbl_os_info, self.lbl_computer_name, self.lbl_last_opt]:
            lbl.setStyleSheet(f"color: {STYLE_CONFIG['dark']['text']}; font: 12px '{STYLE_CONFIG['font']['content'][0]}';")
        layout.addWidget(self.lbl_cpu_status, 0, 0)
        layout.addWidget(self.lbl_ram_status, 0, 1)
        layout.addWidget(self.lbl_disk_status, 0, 2)
        layout.addWidget(self.lbl_os_info, 1, 0)
        layout.addWidget(self.lbl_computer_name, 1, 1)
        layout.addWidget(self.lbl_last_opt, 1, 2)
        return frame

    def get_antivirus_status(self):
        try:
            # Windows Defender durumunu kontrol et
            cmd = 'powershell "Get-MpComputerStatus | Select-Object RealTimeProtectionEnabled"'
            result = subprocess.check_output(cmd, shell=True).decode()
            if "True" in result:
                return tr("home_av_protected", "✅ Korumalı")
            else:
                return tr("home_av_unprotected", "⚠️ Koruma Kapalı")
        except Exception:
            return tr("home_av_unknown", "⚠️ Durum Bilinmiyor")

    def get_system_health(self):
        try:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage(os.getenv('SystemDrive') + "\\").percent
            return f"{tr('home_cpu', 'CPU')}: {cpu}% | {tr('home_ram', 'RAM')}: {mem}% | {tr('home_disk', 'Disk')}: {disk}%"
        except Exception:
            return "Bilinmiyor"

    def create_shortcut_buttons(self):
        layout = QHBoxLayout()
        layout.setSpacing(20)
        btn_rapid_clean = QPushButton(tr("home_quick_clean", "Hızlı Temizlik"))
        btn_rapid_clean.setCursor(Qt.PointingHandCursor)
        btn_rapid_clean.clicked.connect(self.go_to_cleaner)
        btn_startup = QPushButton(tr("home_startup_mgr", "Başlangıç Programlarını Yönet"))
        btn_startup.setCursor(Qt.PointingHandCursor)
        btn_startup.clicked.connect(self.go_to_startup)
        btn_hardware = QPushButton(tr("home_hw_info", "Donanım Bilgisi"))
        btn_hardware.setCursor(Qt.PointingHandCursor)
        btn_hardware.clicked.connect(self.go_to_hardware)
        layout.addWidget(btn_rapid_clean)
        layout.addWidget(btn_startup)
        layout.addWidget(btn_hardware)
        return layout

    def create_announcements_panel(self):
        frame = QFrame()
        frame.setStyleSheet(f"background: {STYLE_CONFIG['dark']['list_bg']}; border-radius: 10px; padding: 10px;")
        layout = QVBoxLayout(frame)
        title = QLabel(tr("home_announcements_title", "Son Güncellemeler / Duyurular"))
        title.setStyleSheet(f"color: {STYLE_CONFIG['dark']['primary']}; font: bold 14px;")
        layout.addWidget(title)
        announcement_text = self.load_announcements()
        announcement = QLabel(announcement_text)
        announcement.setStyleSheet(f"color: {STYLE_CONFIG['dark']['text']}; font: 12px '{STYLE_CONFIG['font']['content'][0]}';")
        announcement.setWordWrap(True)
        layout.addWidget(announcement)
        return frame

    def load_announcements(self):
        return tr("home_announcements_text", "🎉 v1.4.0 Massive Network & Privacy Update!\n\n• 🧽 Debloater: Remove pre-installed Microsoft bloatware and disable background telemetry tracking with a single click.\n• 🌐 Network Optimizer: Switch to fast DNS servers like Cloudflare or Google to lower your ping and improve connection speed.\n• 🛡️ Safe Execution: The app now automatically creates a 'System Restore Point' before applying deep system changes.\n• 🛠️ Quick Tools: Easily flush your DNS cache or perform a Winsock reset when experiencing connection issues.\n• ✨ UI Enhancements: Sleeker info tooltips, elegant notification pop-ups, and polished button designs.")

    def get_random_tip(self):
        tips = tr("tips", [
            "Disk temizliği yapmadan önce yedekleme yapın.",
            "Arka planda çalışan gereksiz programları kapatın.",
            "Sistem güncellemelerini düzenli olarak kontrol edin.",
            "Performansı artırmak için başlangıç programlarını yönetin.",
            "Donanım verilerini izleyerek olası arızaları önleyin.",
            "Güvenlik duvarı ayarlarınızı düzenli olarak kontrol edin.",
            "Windows Defender'ı güncel tutun ve düzenli tarama yapın.",
            "Sistem geri yükleme noktaları oluşturmayı unutmayın.",
            "DNS önbelleğini düzenli olarak temizleyin.",
            "Prefetch dosyalarını ayda bir temizleyin.",
            "Gereksiz Windows hizmetlerini devre dışı bırakın.",
            "Disk birleştirme işlemini düzenli olarak yapın.",
            "Sistem sürücülerinizi güncel tutun.",
            "Güç planınızı kullanım amacınıza göre ayarlayın.",
            "Tarayıcı önbelleğini düzenli olarak temizleyin.",
            "Sistem kaynaklarını izleyerek performans sorunlarını tespit edin.",
            "Windows güncelleme geçmişini düzenli olarak temizleyin.",
            "Bellek dökümleri ve hata raporlarını temizleyin.",
            "Thumbnail önbelleğini düzenli olarak temizleyin.",
            "Gereksiz başlangıç programlarını devre dışı bırakın.",
            "Şifrelerinizi Dikkatli Seçin!"
        ])
        import random
        return random.choice(tips)

    def start_status_timer(self):
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_system_status)
        self.status_timer.start(1000)

    def update_system_status(self):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage(os.getenv('SystemDrive') + "\\").percent
        self.lbl_cpu_status.setText(f"CPU: {cpu}%")
        self.lbl_ram_status.setText(f"RAM: {mem}%")
        self.lbl_disk_status.setText(f"Disk: {disk}%")

    def go_to_cleaner(self):
        main_window = self.window()
        if hasattr(main_window, "show_cleaner"):
            main_window.show_cleaner()

    def go_to_startup(self):
        main_window = self.window()
        if hasattr(main_window, "show_startup"):
            main_window.show_startup()

    def go_to_hardware(self):
        main_window = self.window()
        if hasattr(main_window, "show_hardware"):
            main_window.show_hardware()
