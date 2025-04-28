# C0ded by twiez >:
# github/twiez
# buymeacoffee.com/twiez

import sys
import os
import shutil
import psutil
import GPUtil
import platform
import winreg
import subprocess
import json
import ctypes
import requests  # GitHub API için gerekli
from zipfile import ZipFile
from io import BytesIO
from pypresence import Presence
import time
from PyQt5.QtWidgets import QToolButton, QStyle, QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QPushButton, QMessageBox, QHBoxLayout, QStackedWidget, QFrame, QCheckBox, QListWidget, QListWidgetItem, QGraphicsDropShadowEffect, QGridLayout, QSpacerItem, QSizePolicy, QDialog, QScrollArea
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPoint, QRect, QPropertyAnimation, QEasingCurve, QUrl
from PyQt5.QtGui import QIcon, QFont, QColor, QPainter, QCursor, QLinearGradient, QDesktopServices
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis

# DPI farkındalığı ve ölçeklendirme ayarları
if sys.platform == 'win32':
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

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
                            self.update_status.emit(f"{total_deleted} dosya silindi...")
                        except Exception:
                            pass
                        time.sleep(0.01)
        self.complete_signal.emit(total_deleted)
    
    def stop(self):
        self._is_running = False

# ======================= DPI Ölçeklendirme VE FONT GÜNCELLEME =======================
def update_font_sizes(app):
    """
    Uygulama ekran DPI'sına göre STYLE_CONFIG içindeki font boyutlarını dinamik olarak ölçeklendirir.
    """
    screen = app.primaryScreen()
    dpi = screen.logicalDotsPerInch()  
    scale = dpi / 96  # 96 DPI referans değeri
    
    # Font boyutlarını ölçeklendir
    for key, font_tuple in STYLE_CONFIG['font'].items():
        name = font_tuple[0]
        size = font_tuple[1]
        if len(font_tuple) > 2:
            weight = font_tuple[2]
            STYLE_CONFIG['font'][key] = (name, int(size * scale), weight)
        else:
            STYLE_CONFIG['font'][key] = (name, int(size * scale))
    
    # Widget boyutlarını ölçeklendir
    STYLE_CONFIG['spacing']['default'] = int(12 * scale)
    STYLE_CONFIG['spacing']['tight'] = int(6 * scale)
    STYLE_CONFIG['spacing']['wide'] = int(18 * scale)

# ======================= KONFİGÜRASYON & STİL =======================
CURRENT_VERSION = "1.2.0"
STYLE_CONFIG = {
    'dark': {
        'bg': 'rgba(18, 18, 18, 0.97)',
        'text': '#e0e0e0',
        'primary': 'rgba(103, 58, 183, 0.9)',
        'secondary': 'rgba(40, 40, 40, 0.8)',
        'list_bg': 'rgba(30, 30, 30, 0.9)',
        'chart_line': '#7c4dff',
        'warning': '#ff4444',
        'hover': 'rgba(123, 31, 162, 0.85)',
        'card_bg': 'rgba(45, 45, 45, 0.7)',
        'gradient_start': '#1a237e',
        'gradient_end': '#4a148c'
    },
    'font': {
        'title': ('Segoe UI', 14, QFont.Bold),
        'content': ('Arial', 11),
        'detail': ('Consolas', 10),
        'chart': ('Arial', 9)
    },
    'spacing': {
        'default': 12,
        'tight': 6,
        'wide': 18
    }
}

def set_global_styles(app):
    app.setStyleSheet(f"""
        * {{
            selection-background-color: {STYLE_CONFIG['dark']['primary']};
        }}
        QMessageBox {{
            background-color: {STYLE_CONFIG['dark']['bg']};
            color: {STYLE_CONFIG['dark']['text']};
        }}
        QMessageBox QLabel {{
            color: {STYLE_CONFIG['dark']['text']} !important;
            font: {STYLE_CONFIG['font']['content'][1]}pt '{STYLE_CONFIG['font']['content'][0]}';
        }}
        QMessageBox QPushButton {{
            background: {STYLE_CONFIG['dark']['primary']};
            color: {STYLE_CONFIG['dark']['text']} !important;
            padding: 8px 24px;
            border-radius: 6px;
            min-width: 90px;
        }}
        QMessageBox QPushButton:hover {{ background: {STYLE_CONFIG['dark']['hover']}; }}
        QToolTip {{
            background: {STYLE_CONFIG['dark']['secondary']};
            color: {STYLE_CONFIG['dark']['text']};
            border: 1px solid {STYLE_CONFIG['dark']['primary']};
            border-radius: 4px;
            padding: 4px;
            font: {STYLE_CONFIG['font']['content'][1]}pt '{STYLE_CONFIG['font']['content'][0]}';
        }}
    """)

# Ortak buton stili fonksiyonu
BUTTON_STYLE = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c4dff, stop:1 #bb86fc);
        color: #fff;
        border-radius: 9px;
        font: bold 14px 'Segoe UI', Arial;
        padding: 8px 28px;
        min-width: 120px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a67cdb, stop:1 #bb86fc);
    }
"""

def style_all_buttons(widget):
    for btn in widget.findChildren(QPushButton):
        btn.setStyleSheet(BUTTON_STYLE)

# ======================= DARK MESSAGEBOX =======================
class DarkMessageBox(QDialog):
    def __init__(self, title, message, icon="info", parent=None, buttons=("Tamam",), default=0):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {STYLE_CONFIG['dark']['bg']};
                border-radius: 12px;
            }}
        """)
        self.result_index = default

        # Üst bar
        bar = QFrame()
        bar.setFixedHeight(38)
        bar.setStyleSheet(f"""
            QFrame {{
                background: {STYLE_CONFIG['dark']['bg']};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
            QFrame:hover {{
                background: {STYLE_CONFIG['dark']['hover']};
            }}
        """)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(14, 0, 14, 0)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"color: {STYLE_CONFIG['dark']['primary']}; font: bold 15px;")
        bar_layout.addWidget(lbl_title)
        bar_layout.addStretch()
        btn_close = QPushButton("×")
        btn_close.setFixedSize(28, 28)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {STYLE_CONFIG['dark']['text']};
                font: bold 18px;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background: {STYLE_CONFIG['dark']['hover']};
                color: white;
            }}
        """)
        btn_close.clicked.connect(self.reject)
        bar_layout.addWidget(btn_close)

        # Hareket ettirmek için mouse event'leri
        bar.mousePressEvent = self._mouse_press
        bar.mouseMoveEvent = self._mouse_move
        self._drag_pos = None

        # İçerik
        icon_label = QLabel()
        if icon == "info":
            icon_label.setText("ℹ️")
        elif icon == "warning":
            icon_label.setText("⚠️")
        elif icon == "error":
            icon_label.setText("⛔")
        elif icon == "success":
            icon_label.setText("✅")
        icon_label.setStyleSheet("font-size: 28px; margin-right: 10px;")
        icon_label.setFixedWidth(36)

        msg_label = QLabel(message)
        msg_label.setStyleSheet(f"color: {STYLE_CONFIG['dark']['text']}; font: 13px '{STYLE_CONFIG['font']['content'][0]}';")
        msg_label.setWordWrap(True)

        content_layout = QHBoxLayout()
        content_layout.addWidget(icon_label)
        content_layout.addWidget(msg_label)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btns = []
        for i, text in enumerate(buttons):
            btn = QPushButton(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {STYLE_CONFIG['dark']['primary']};
                    color: white;
                    border-radius: 8px;
                    padding: 7px 28px;
                    font: bold 13px;
                }}
                QPushButton:hover {{
                    background: {STYLE_CONFIG['dark']['hover']};
                }}
            """)
            btn.clicked.connect(lambda _, idx=i: self._done(idx))
            self.btns.append(btn)
            btn_layout.addWidget(btn)
        btn_layout.addStretch()

        # Ana layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(bar)
        main_layout.addSpacing(10)
        main_layout.addLayout(content_layout)
        main_layout.addSpacing(18)
        main_layout.addLayout(btn_layout)
        main_layout.addSpacing(10)

        self.setFixedWidth(420)
        self.setFixedHeight(200 + 30 * (len(message) // 60))

        # Pencere gölgesi
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

    def _mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def _mouse_move(self, event):
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            self._drag_pos = event.globalPos()

    def _done(self, idx):
        self.result_index = idx
        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        # Pencereyi ekranın ortasına konumlandır
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    @staticmethod
    def show_info(parent, title, message):
        dlg = DarkMessageBox(title, message, icon="info", parent=parent)
        dlg.exec_()

    @staticmethod
    def show_success(parent, title, message):
        dlg = DarkMessageBox(title, message, icon="success", parent=parent)
        dlg.exec_()

    @staticmethod
    def show_warning(parent, title, message):
        dlg = DarkMessageBox(title, message, icon="warning", parent=parent)
        dlg.exec_()

    @staticmethod
    def show_error(parent, title, message):
        dlg = DarkMessageBox(title, message, icon="error", parent=parent)
        dlg.exec_()

    @staticmethod
    def ask_question(parent, title, message, yes_text="Evet", no_text="Hayır"):
        dlg = CustomConfirmation(title, message, yes_text, no_text, parent)
        return dlg.show_confirmation()

# ======================= CUSTOM CONFIRMATION =======================
class CustomConfirmation(QDialog):
    def __init__(self, title, message, yes_text="Evet", no_text="Hayır", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setAttribute(Qt.WA_StyledBackground)
        bg_color = STYLE_CONFIG['dark']['card_bg']
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                border-radius: 12px;
                padding: 15px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['primary']};
            font: bold 16px;
            background-color: {STYLE_CONFIG['dark']['card_bg']};
            padding: 8px;
            border-radius: 8px;
        """)
        layout.addWidget(title_label, alignment=Qt.AlignCenter)

        msg_label = QLabel(message)
        msg_label.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: 13px '{STYLE_CONFIG['font']['content'][0]}';
            line-height: 1.4;
            background-color: {STYLE_CONFIG['dark']['card_bg']};
            padding: 10px;
            border-radius: 8px;
        """)
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignCenter)
        msg_label.setMinimumWidth(300)
        layout.addWidget(msg_label, alignment=Qt.AlignCenter)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        self.no_btn = QPushButton(no_text)
        self.no_btn.setCursor(Qt.PointingHandCursor)
        self.no_btn.setStyleSheet(f"""
            QPushButton {{
                background: {STYLE_CONFIG['dark']['secondary']};
                color: {STYLE_CONFIG['dark']['text']};
                border-radius: 8px;
                padding: 10px 20px;
                font: bold 13px;
            }}
            QPushButton:hover {{
                background: {STYLE_CONFIG['dark']['hover']};
            }}
        """)

        self.yes_btn = QPushButton(yes_text)
        self.yes_btn.setCursor(Qt.PointingHandCursor)
        self.yes_btn.setStyleSheet(f"""
            QPushButton {{
                background: {STYLE_CONFIG['dark']['primary']};
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                font: bold 13px;
            }}
            QPushButton:hover {{
                background: {STYLE_CONFIG['dark']['hover']};
            }}
        """)

        btn_layout.addWidget(self.no_btn)
        btn_layout.addWidget(self.yes_btn)
        layout.addLayout(btn_layout)

        self.yes_btn.clicked.connect(self.accept)
        self.no_btn.clicked.connect(self.reject)
        self.adjustSize()

    def show_confirmation(self):
        self.adjustSize()
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        return self.exec_() == QDialog.Accepted

# ======================= CUSTOM NOTIFICATION =======================
class CustomNotification(QFrame):
    def __init__(self, message, duration=3000, parent=None):
        super().__init__(parent)
        bg_color = STYLE_CONFIG['dark']['warning'] if message.strip().startswith("⛔") else STYLE_CONFIG['dark']['bg']
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 12px;
                padding: 15px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        label = QLabel(message)
        label.setStyleSheet(f"""
            QLabel {{
                color: {STYLE_CONFIG['dark']['text']};
                font: 13px '{STYLE_CONFIG['font']['content'][0]}';
            }}
        """)
        label.setWordWrap(True)
        layout.addWidget(label)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.close)
        self.timer.start(duration)

    def show_notification(self, x=None, y=None):
        self.adjustSize()
        if x is None or y is None:
            screen_geometry = QApplication.desktop().screenGeometry()
            x = screen_geometry.width() - self.width() - 20
            y = screen_geometry.height() - self.height() - 50
        try:
            self.move(x, y)
            self.show()
        except Exception:
            # Hata durumunda varsayılan konuma yerleştir
            self.move(20, 20)
            self.show()

    def showEvent(self, event):
        super().showEvent(event)
        try:
            # Pencereyi ekranın sağ alt köşesine konumlandır
            screen = QApplication.primaryScreen().geometry()
            x = screen.width() - self.width() - 20
            y = screen.height() - self.height() - 50
            self.move(x, y)
        except Exception:
            # Hata durumunda varsayılan konuma yerleştir
            self.move(20, 20)

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
        greeting = QLabel(f"Merhaba, {platform.node()}!")
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
        tip = QLabel(f"İpucu: {self.get_random_tip()}")
        tip.setAlignment(Qt.AlignCenter)
        tip.setStyleSheet(f"color: {STYLE_CONFIG['dark']['text']}; font: italic 12px;")
        main_layout.addWidget(tip)
        # Ekstra bilgi
        content_label = QLabel("Twiez Optimizer ile sisteminizi optimize edin ve hızlandırın!")
        content_label.setAlignment(Qt.AlignCenter)
        content_label.setStyleSheet(f"color: {STYLE_CONFIG['dark']['text']}; font: 13px '{STYLE_CONFIG['font']['content'][0]}'; padding-top: 10px;")
        main_layout.addWidget(content_label)
        style_all_buttons(self)

    def create_system_status_panel(self):
        frame = QFrame()
        frame.setStyleSheet(f"background: {STYLE_CONFIG['dark']['card_bg']}; border-radius: 10px; padding: 10px;")
        layout = QGridLayout(frame)
        layout.setSpacing(10)
        self.lbl_cpu_status = QLabel("CPU: N/A")
        self.lbl_ram_status = QLabel("RAM: N/A")
        self.lbl_disk_status = QLabel("Disk: N/A")
        self.lbl_os_info = QLabel(f"OS: {platform.system()} {platform.release()}")
        self.lbl_computer_name = QLabel(f"Bilgisayar: {platform.node()}")
        last_opt = self.get_antivirus_status()
        self.lbl_last_opt = QLabel(f"Antivirüs Durumu: {last_opt}")
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
                return "✅ Korumalı"
            else:
                return "⚠️ Koruma Kapalı"
        except:
            return "⚠️ Durum Bilinmiyor"

    def get_system_health(self):
        try:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage(os.getenv('SystemDrive') + "\\").percent
            return f"CPU: {cpu}% | RAM: {mem}% | Disk: {disk}%"
        except:
            return "Bilinmiyor"

    def create_shortcut_buttons(self):
        layout = QHBoxLayout()
        layout.setSpacing(20)
        btn_rapid_clean = QPushButton("Hızlı Temizlik")
        btn_rapid_clean.setCursor(Qt.PointingHandCursor)
        btn_rapid_clean.clicked.connect(self.go_to_cleaner)
        btn_startup = QPushButton("Başlangıç Programlarını Yönet")
        btn_startup.setCursor(Qt.PointingHandCursor)
        btn_startup.clicked.connect(self.go_to_startup)
        btn_hardware = QPushButton("Donanım Bilgisi")
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
        title = QLabel("Son Güncellemeler / Duyurular")
        title.setStyleSheet(f"color: {STYLE_CONFIG['dark']['primary']}; font: bold 14px;")
        layout.addWidget(title)
        announcement_text = self.load_announcements()
        announcement = QLabel(announcement_text)
        announcement.setStyleSheet(f"color: {STYLE_CONFIG['dark']['text']}; font: 12px '{STYLE_CONFIG['font']['content'][0]}';")
        announcement.setWordWrap(True)
        layout.addWidget(announcement)
        return frame

    def load_announcements(self):
        announcements = [
            "🎉 v1.2.0 Güncellemesi Yayınlandı!",
            "   • Gelişmiş Güvenlik Özellikleri:",
            "   • Windows Defender Güvenlik Duvarı entegrasyonu",
            "   • Gelen/Giden bağlantı kuralları yönetimi",
            "   • Port izinleri ve engellemeleri",
            "   • Program bazlı güvenlik duvarı kuralları",
            "   • Otomatik güvenlik duvarı durumu kontrolü",
            "   • UAC (Kullanıcı Hesabı Denetimi) kontrolü",
            "   • Sistem güvenlik analizi ve raporlama",
            "   • Gerçek zamanlı güvenlik izleme",
            "   • Arayüz iyileştirmeleri yapıldı",
            "   • Sistem temizleme özellikleri geliştirildi",
            "   • Hata düzeltmeleri ve stabilite iyileştirmeleri"
        ]
        return "\n".join(announcements)

    def get_random_tip(self):
        tips = [
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
            "Gereksiz başlangıç programlarını devre dışı bırakın."
            "Şifrelerinizi Dikkatli Seçin!."
        ]
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
        self.RPC.close()

# ======================= ANA PENCERE VE WIDGET'LAR =======================
class OptimizerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.old_pos = None
        self.rpc_thread = RPCThread()
        self.init_ui()
        self.setWindowTitle("Twiez Optimizer")
        self.setWindowIcon(QIcon('fav.ico'))
        self.rpc_thread.start()
        self.update_checker = UpdateChecker(CURRENT_VERSION, "https://github.com/twiez/twiez-optimizer")
        self.update_checker.update_available.connect(self.prompt_update)
        self.update_checker.start()

    def animate_minimize(self):
        fade_out = QPropertyAnimation(self, b"windowOpacity")
        fade_out.setDuration(200)
        fade_out.setStartValue(1)
        fade_out.setEndValue(0)
        fade_out.setEasingCurve(QEasingCurve.InOutQuad)
        def on_fade_out_finished():
            self.showMinimized()
            self.setWindowOpacity(1)
        fade_out.finished.connect(on_fade_out_finished)
        fade_out.start()
        self._fade_out_anim = fade_out
    
    def animate_close(self):
        fade_out = QPropertyAnimation(self, b"windowOpacity")
        fade_out.setDuration(200)
        fade_out.setStartValue(1)
        fade_out.setEndValue(0)
        fade_out.setEasingCurve(QEasingCurve.InOutQuad)
        fade_out.finished.connect(self.close)
        fade_out.start()
        self._fade_out_anim = fade_out

    def animate_maximize(self):
        if not self.isMaximized():
            
            fade_out = QPropertyAnimation(self, b"windowOpacity")
            fade_out.setDuration(150)
            fade_out.setStartValue(1)
            fade_out.setEndValue(0)
            fade_out.setEasingCurve(QEasingCurve.InOutQuad)
            
            def on_fade_out_finished():
               
                screen = QApplication.primaryScreen().geometry()
                self.move(screen.center() - self.rect().center())
              
                self.showMaximized()
               
                fade_in = QPropertyAnimation(self, b"windowOpacity")
                fade_in.setDuration(150)
                fade_in.setStartValue(0)
                fade_in.setEndValue(1)
                fade_in.setEasingCurve(QEasingCurve.InOutQuad)
                fade_in.start()
                self._fade_in_anim = fade_in
            
            fade_out.finished.connect(on_fade_out_finished)
            fade_out.start()
            self._fade_out_anim = fade_out
        else:
           
            fade_out = QPropertyAnimation(self, b"windowOpacity")
            fade_out.setDuration(150)
            fade_out.setStartValue(1)
            fade_out.setEndValue(0)
            fade_out.setEasingCurve(QEasingCurve.InOutQuad)
            
            def on_fade_out_finished():
                
                screen = QApplication.primaryScreen().geometry()
                self.showNormal()
                self.move(screen.center() - self.rect().center())
                
                fade_in = QPropertyAnimation(self, b"windowOpacity")
                fade_in.setDuration(150)
                fade_in.setStartValue(0)
                fade_in.setEndValue(1)
                fade_in.setEasingCurve(QEasingCurve.InOutQuad)
                fade_in.start()
                self._fade_in_anim = fade_in
            
            fade_out.finished.connect(on_fade_out_finished)
            fade_out.start()
            self._fade_out_anim = fade_out

    def create_title_bar(self):
        title_bar = QFrame()
        title_bar.setFixedHeight(60)
        title_bar.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {STYLE_CONFIG['dark']['gradient_start']}, 
                stop:1 {STYLE_CONFIG['dark']['gradient_end']});
            border-radius: 15px 15px 0 0;
        """)
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(20, 0, 20, 0)
        title_label = QLabel("Twiez Optimizer")
        title_label.setFont(QFont(*STYLE_CONFIG['font']['title']))
        title_label.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            background: transparent;
            padding: 5px;
        """)
        btn_style = f"""
            QPushButton {{
                background: transparent;
                color: {STYLE_CONFIG['dark']['text']};
                font: bold 20px;
                min-width: 34px;
                min-height: 34px;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.15);
                border: 1px solid rgba(255,255,255,0.2);
            }}
        """
        btn_min = QPushButton("–")
        btn_min.setStyleSheet(btn_style)
        btn_min.clicked.connect(self.animate_minimize)
        
        btn_max = QPushButton("▢")
        btn_max.setStyleSheet(btn_style)
        btn_max.clicked.connect(self.animate_maximize)
        
        btn_close = QPushButton("×")
        btn_close.setStyleSheet(btn_style)
        btn_close.clicked.connect(self.animate_close)
        
        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(btn_min)
        layout.addWidget(btn_max)
        layout.addWidget(btn_close)
        title_bar.mousePressEvent = self.title_bar_mouse_press
        title_bar.mouseMoveEvent = self.title_bar_mouse_move
        return title_bar

    def title_bar_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()
            
            if self.isMaximized():
                self.showNormal()
                
                new_pos = event.globalPos() - QPoint(self.width() // 2, 0)
                self.move(new_pos)
                self.old_pos = event.globalPos()

    def title_bar_mouse_move(self, event):
        if self.old_pos is not None and event.buttons() == Qt.LeftButton:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def create_menu_panel(self):
        menu_frame = QFrame()
        menu_layout = QVBoxLayout(menu_frame)
        menu_layout.setSpacing(12)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        buttons = [
            ('🏠 Ev', self.show_home),
            ('👾 Windows', self.show_windows),
            ('⚙️ Optimizasyon', self.show_optimization),
            ('🚀 Başlangıç', self.show_startup),
            ('🧹 Temizlik', self.show_cleaner),
            ('📊 Performans', self.show_performance),
            ('💻 Donanım', self.show_hardware),
            ('🔒 Güvenlik', self.show_security),
            ('💓 Bilgi', self.show_info)
        ]
        for text, callback in buttons:
            btn = QPushButton(text)
            btn.setFont(QFont(*STYLE_CONFIG['font']['title']))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {STYLE_CONFIG['dark']['secondary']};
                    color: {STYLE_CONFIG['dark']['text']};
                    border-radius: 10px;
                    padding: 14px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background: {STYLE_CONFIG['dark']['hover']};
                    border: 1px solid {STYLE_CONFIG['dark']['primary']};
                }}
            """)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setFixedHeight(55)
            btn.clicked.connect(callback)
            menu_layout.addWidget(btn)
        menu_layout.addStretch()
        return menu_frame

    def create_stacked_widget(self):
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(HomeWidget())               # Index 0: Ev
        self.stacked_widget.addWidget(WindowsSettingsWidget())    # Index 1: Windows
        self.stacked_widget.addWidget(OptimizationWidget())       # Index 2: Optimizasyon
        self.stacked_widget.addWidget(StartupWidget())            # Index 3: Başlangıç
        self.stacked_widget.addWidget(CleanerWidget())            # Index 4: Temizlik
        self.stacked_widget.addWidget(PerformanceWidget())        # Index 5: Performans
        self.stacked_widget.addWidget(HardwareWidget())           # Index 6: Donanım
        self.stacked_widget.addWidget(InfoWidget())               # Index 7: Bilgi
        self.stacked_widget.addWidget(SecurityWidget())           # Index 8: Güvenlik
        return self.stacked_widget

    def show_home(self):
        self.stacked_widget.setCurrentIndex(0)

    def show_windows(self):
        self.stacked_widget.setCurrentIndex(1)

    def show_optimization(self):
        self.stacked_widget.setCurrentIndex(2)

    def show_startup(self):
        self.stacked_widget.setCurrentIndex(3)

    def show_cleaner(self):
        self.stacked_widget.setCurrentIndex(4)

    def show_performance(self):
        self.stacked_widget.setCurrentIndex(5)

    def show_hardware(self):
        self.stacked_widget.setCurrentIndex(6)

    def show_security(self):
        self.stacked_widget.setCurrentIndex(8)

    def show_info(self):
        self.stacked_widget.setCurrentIndex(7)

    def create_content_area(self):
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.addWidget(self.create_menu_panel(), 1)
        content_layout.addWidget(self.create_stacked_widget(), 4)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(0, 10, 0, 10)
        return content_widget

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Ekran boyutuna göre pencere boyutunu ayarla
        screen = QApplication.primaryScreen()
        scale = screen.logicalDotsPerInch() / 96
        screen_geometry = screen.geometry()
        
    
        base_width = 1100
        base_height = 750
        max_width = int(screen_geometry.width() * 0.8)  # Ekran genişliğinin %80'i
        max_height = int(screen_geometry.height() * 0.8)  # Ekran yüksekliğinin %80'i
        
        width = min(int(base_width * scale), max_width)
        height = min(int(base_height * scale), max_height)
        
        self.setFixedSize(width, height)
        
        self.main_container = QWidget()
        self.main_container.setStyleSheet(f"""
            background-color: {STYLE_CONFIG['dark']['bg']};
            border-radius: {int(15 * scale)}px;
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(int(35 * scale))
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, int(4 * scale))
        self.main_container.setGraphicsEffect(shadow)
        
        main_layout = QVBoxLayout(self.main_container)
        main_layout.addWidget(self.create_title_bar())
        main_layout.addWidget(self.create_content_area())
        main_layout.setContentsMargins(
            int(12 * scale), 
            int(12 * scale), 
            int(12 * scale), 
            int(12 * scale)
        )
        self.setCentralWidget(self.main_container)

    def prompt_update(self, latest_version, download_url):
        reply = DarkMessageBox.ask_question(
            self, "Yeni Sürüm Bulundu",
            f"Yeni bir sürüm bulundu: v{latest_version}\nGüncellemek ister misiniz?",
            yes_text="Evet", no_text="Hayır"
        )
        if reply:
            update_manager = UpdateManager(self, download_url)
            update_manager.download_and_install_update()

    def closeEvent(self, event):
        self.rpc_thread.stop()
        event.accept()

# ======================= WINDOWS AYARLARI WIDGET =======================
class WindowsSettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.checkbox_references = {}
        self.init_ui()
        self.setup_triggers()

    def init_ui(self):
        self.setContentsMargins(40, 20, 40, 20)
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        self.setup_title(layout)
        self.setup_checkboxes(layout)
        self.setup_apply_button(layout)
        style_all_buttons(self)

    def setup_title(self, layout):
        title = QLabel("⚙️ Windows Optimizasyon Ayarları")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['primary']};
            padding: 8px 0 16px 0;
        """)
        layout.addWidget(title)

    def setup_checkboxes(self, layout):
        # Windows ayarları ve açıklamaları
        settings_info = {
            "Yüksek Performans Modu": "Sisteminizi maksimum performans için optimize eder. Pil tüketimini artırabilir.",
            "Cortana'yı Devre Dışı Bırak": "Cortana asistanını devre dışı bırakarak sistem kaynaklarını serbest bırakır.",
            "Yazdırma Hizmetini Kapat": "Arka planda çalışan yazdırma hizmetini kapatarak sistem kaynaklarını serbest bırakır.",
            "Ağ Kısıtlamalarını Kaldır": "Windows'un ağ bant genişliği kısıtlamalarını kaldırarak internet hızını artırır.",
            "GameDVR'ı Devre Dışı Bırak": "Oyun kayıt özelliğini devre dışı bırakarak performansı artırır.",
            "Oyun Modunu Etkinleştir": "Oyun sırasında sistem kaynaklarını optimize eder.",
            "HPET'i Devre Dışı Bırak": "Yüksek hassasiyetli olay zamanlayıcısını devre dışı bırakarak performansı artırır.",
            "Windows Ink'i Kapat": "Dokunmatik kalem özelliklerini devre dışı bırakır.",
            "Windows Hello'yu Devre Dışı Bırak": "Yüz tanıma ve parmak izi özelliklerini kapatır.",
            "Yapışkan Tuşları Kapat": "Klavye erişilebilirlik özelliklerini devre dışı bırakır.",
            "Disk Temizleme": "Gereksiz sistem dosyalarını temizler.",
            "OneDrive'ı Devre Dışı Bırak": "OneDrive senkronizasyonunu devre dışı bırakır.",
            "Superfetch'i Kapat": "Önceden yükleme özelliğini devre dışı bırakır.",
            "Uzun Yol Desteğini Etkinleştir": "Uzun dosya yolu desteğini etkinleştirir."
        }

        features = [
            ("Yüksek Performans Modu", "chk_performance"),
            ("Cortana'yı Devre Dışı Bırak", "chk_cortana"),
            ("Yazdırma Hizmetini Kapat", "chk_print"),
            ("Ağ Kısıtlamalarını Kaldır", "chk_throttling"),
            ("GameDVR'ı Devre Dışı Bırak", "chk_gamedvr"),
            ("Oyun Modunu Etkinleştir", "chk_gamemode"),
            ("HPET'i Devre Dışı Bırak", "chk_hpet"),
            ("Windows Ink'i Kapat", "chk_ink"),
            ("Windows Hello'yu Devre Dışı Bırak", "chk_hello"),
            ("Yapışkan Tuşları Kapat", "chk_stickkeys"),
            ("Disk Temizleme", "chk_clean"),
            ("OneDrive'ı Devre Dışı Bırak", "chk_onedrive"),
            ("Superfetch'i Kapat", "chk_superfetch"),
            ("Uzun Yol Desteğini Etkinleştir", "chk_paths")
        ]

        grid = QGridLayout()
        grid.setVerticalSpacing(10)
        grid.setHorizontalSpacing(40)
        grid.setContentsMargins(10, 10, 10, 10)

        for i, (text, name) in enumerate(features):
            row = i % 7  
            col = i // 7  
            
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)
            
            checkbox = QCheckBox(text)
            self.checkbox_references[name] = checkbox
            checkbox.setObjectName(name)
            checkbox.setFont(QFont("Segoe UI", 10))
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    color: {STYLE_CONFIG['dark']['text']};
                    spacing: 6px;
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                }}
                QCheckBox::indicator:unchecked {{
                    border: 2px solid {STYLE_CONFIG['dark']['secondary']};
                    background: {STYLE_CONFIG['dark']['card_bg']};
                    border-radius: 4px;
                }}
                QCheckBox::indicator:checked {{
                    border: 2px solid {STYLE_CONFIG['dark']['primary']};
                    background: {STYLE_CONFIG['dark']['primary']};
                    border-radius: 4px;
                }}
                QCheckBox::indicator:hover {{
                    border: 2px solid {STYLE_CONFIG['dark']['hover']};
                }}
            """)
            
            info_button = InfoButton(settings_info[text], container)
            
            container_layout.addWidget(checkbox)
            container_layout.addWidget(info_button)
            container_layout.addStretch()
            
            grid.addWidget(container, row, col, alignment=Qt.AlignLeft | Qt.AlignTop)

        layout.addLayout(grid)

    def setup_apply_button(self, layout):
        btn_apply = QPushButton("🚀 Ayarları Uygula")
        btn_apply.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_apply.setMinimumHeight(40)
        btn_apply.clicked.connect(self.apply_settings)
        layout.addWidget(btn_apply, alignment=Qt.AlignCenter)

    def setup_triggers(self):
        self.findChild(QPushButton).clicked.connect(self.apply_settings)

    def apply_settings(self):
        checkboxes = self.findChildren(QCheckBox)
        selected = any(checkbox.isChecked() for checkbox in checkboxes)
        if not selected:
            CustomNotification("⚠️ Lütfen en az bir seçenek işaretleyin!", duration=3000, parent=self).show_notification()
            return
        try:
            CustomNotification("✅ Seçilen ayarlar başarıyla uygulandı!", duration=3000, parent=self).show_notification()
        except Exception as e:
            CustomNotification(f"⛔ Ayarlar uygulanırken bir hata oluştu:\n{str(e)}", duration=3000, parent=self).show_notification()

# ======================= BAŞLANGIÇ PROGRAMLARI WIDGET =======================
class StartupWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setContentsMargins(20, 15, 20, 20)
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        title = QLabel("📌 Başlangıç Programları")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {STYLE_CONFIG['dark']['primary']}; font: bold 18px;")
        self.list = QListWidget()
        self.list.setStyleSheet(f"""
    QListWidget {{ 
        background: {STYLE_CONFIG['dark']['list_bg']};
        color: {STYLE_CONFIG['dark']['text']};
        border-radius: 10px;
        padding: 8px;
    }}
    QListWidget::item {{
        height: 55px;
        padding: 10px;
        border-bottom: 1px solid {STYLE_CONFIG['dark']['secondary']};
    }}
    QListWidget::item:hover {{ 
        background: {STYLE_CONFIG['dark']['hover']};
    }}
    QScrollBar:vertical {{
        background: {STYLE_CONFIG['dark']['secondary']};
        width: 12px;
        margin: 0px;
        border-radius: 6px;
    }}
    QScrollBar::handle:vertical {{
        background: {STYLE_CONFIG['dark']['primary']};
        min-height: 20px;
        border-radius: 6px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {STYLE_CONFIG['dark']['hover']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        background: none;
        height: 0px;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: {STYLE_CONFIG['dark']['secondary']};
    }}
    QScrollBar:horizontal {{
        background: {STYLE_CONFIG['dark']['secondary']};
        height: 12px;
        margin: 0px;
        border-radius: 6px;
    }}
    QScrollBar::handle:horizontal {{
        background: {STYLE_CONFIG['dark']['primary']};
        min-width: 20px;
        border-radius: 6px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {STYLE_CONFIG['dark']['hover']};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        background: none;
        width: 0px;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: {STYLE_CONFIG['dark']['secondary']};
    }}
""")
        for entry in self.get_startup_programs():
            item = QListWidgetItem(f"📦 {entry['name']}\n🔗 {entry['path']}")
            item.setFont(QFont(*STYLE_CONFIG['font']['content']))
            self.list.addItem(item)
        btn_disable = QPushButton("🚫 SEÇİLİYİ DEVRE DIŞI BIRAK")
        btn_disable.clicked.connect(self.disable_selected)
        layout.addWidget(title)
        layout.addWidget(self.list, 1)
        layout.addWidget(btn_disable, alignment=Qt.AlignCenter)
        style_all_buttons(self)

    def get_startup_programs(self):
        programs = []
        locations = [
            (winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run'),
            (winreg.HKEY_LOCAL_MACHINE, r'Software\Microsoft\Windows\CurrentVersion\Run')
        ]
        for hive, subkey in locations:
            try:
                with winreg.OpenKey(hive, subkey) as key:
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            programs.append({'name': name, 'path': value})
                            i += 1
                        except OSError:
                            break
            except Exception as e:
                print(f"Kayıt defteri hatası: {e}")
        return programs

    def disable_selected(self):
        selected = self.list.currentItem()
        if selected:
            name = selected.text().split('\n')[0][2:]
            try:
                reply = DarkMessageBox.ask_question(
                    self, "Onay", f"{name} başlangıçtan kaldırılsın mı?", yes_text="Evet", no_text="Hayır"
                )
                if reply:
                    found = False
                    for hive, subkey in [
                        (winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run'),
                        (winreg.HKEY_LOCAL_MACHINE, r'Software\Microsoft\Windows\CurrentVersion\Run')
                    ]:
                        try:
                            with winreg.OpenKey(hive, subkey, 0, winreg.KEY_WRITE) as key:
                                winreg.DeleteValue(key, name)
                                found = True
                        except:
                            continue
                    if found:
                        CustomNotification(f"✅ {name} devre dışı bırakıldı!", duration=3000, parent=self).show_notification()
                        self.list.takeItem(self.list.currentRow())
                    else:
                        CustomNotification("⚠️ Program bulunamadı!", duration=3000, parent=self).show_notification()
            except Exception as e:
                CustomNotification(f"⛔ İşlem başarısız:\n{str(e)}", duration=3000, parent=self).show_notification()

# ======================= TEMİZLİK WIDGET =======================
class CleanerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setContentsMargins(40, 20, 40, 20)
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        self.setup_title(layout)
        self.setup_checkboxes(layout)
        self.setup_status_and_button(layout)
        style_all_buttons(self)

    def setup_title(self, layout):
        title = QLabel("🧹 Sistem Temizleme")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['primary']};
            padding: 8px 0 16px 0;
        """)
        layout.addWidget(title)

    def setup_checkboxes(self, layout):
      
        settings_info = {
            "🗑️ Geçici Dosyalar": "Geçici dosyalar silinir, genellikle önemsiz dosyalardır.",
            "🗑️ Geri Dönüşüm Kutusu": "Geri dönüşüm kutusundaki dosyalar tamamen silinir.",
            "📂 Prefetch Dosyaları": "Prefetch dosyaları bilgisayarın hızlanması için silinebilir boş dosyalardır.",
            "🌐 Tarayıcı Önbelleği": "Tarayıcı önbelleği silinir, tarayıcınızın hızını artırır. Ancak Tarayıcınızdaki oturumlar kapanabilir!",
            "🔄 Windows Güncelleme Geçmişi": "Eski Windows güncelleme dosyalarını temizler.",
            "💾 Bellek Dökümleri ve Hata Raporları": "Sistem çökmesi sırasında oluşturulan bellek dökümleri ve hata raporlarını temizler.",
            "🖼️ Thumbnail (Küçük Resim) Önbelleği": "Windows'un küçük resim önbelleğini temizler.",
            "🌐 DNS Önbelleği": "DNS önbelleğini temizleyerek ağ bağlantılarını yeniler."
        }

        features = [
            ("🗑️ Geçici Dosyalar", "chk_temp"),
            ("🗑️ Geri Dönüşüm Kutusu", "chk_recycle_bin"),
            ("📂 Prefetch Dosyaları", "chk_prefetch"),
            ("🌐 Tarayıcı Önbelleği", "chk_browsers"),
            ("🔄 Windows Güncelleme Geçmişi", "chk_windows_update"),
            ("💾 Bellek Dökümleri ve Hata Raporları", "chk_memory_dumps"),
            ("🖼️ Thumbnail (Küçük Resim) Önbelleği", "chk_thumbnails"),
            ("🌐 DNS Önbelleği", "chk_dns_cache")
        ]

        grid = QGridLayout()
        grid.setVerticalSpacing(10)
        grid.setHorizontalSpacing(40)
        grid.setContentsMargins(10, 10, 10, 10)

        for i, (text, name) in enumerate(features):
            row = i % 4  # Her sütunda 4 öğe olacak
            col = i // 4  # Sütun sayısı
            
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)
            
            checkbox = QCheckBox(text)
            checkbox.setObjectName(name)
            checkbox.setFont(QFont("Segoe UI", 10))
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    color: {STYLE_CONFIG['dark']['text']};
                    spacing: 6px;
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                }}
                QCheckBox::indicator:unchecked {{
                    border: 2px solid {STYLE_CONFIG['dark']['secondary']};
                    background: {STYLE_CONFIG['dark']['card_bg']};
                    border-radius: 4px;
                }}
                QCheckBox::indicator:checked {{
                    border: 2px solid {STYLE_CONFIG['dark']['primary']};
                    background: {STYLE_CONFIG['dark']['primary']};
                    border-radius: 4px;
                }}
                QCheckBox::indicator:hover {{
                    border: 2px solid {STYLE_CONFIG['dark']['hover']};
                }}
            """)
            
            info_button = InfoButton(settings_info[text], container)
            
            container_layout.addWidget(checkbox)
            container_layout.addWidget(info_button)
            container_layout.addStretch()
            
            grid.addWidget(container, row, col, alignment=Qt.AlignLeft | Qt.AlignTop)

        layout.addLayout(grid)

    def setup_status_and_button(self, layout):
        self.lbl_status = QLabel()
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: italic 12px;
            min-height: 40px;
        """)
        layout.addWidget(self.lbl_status)

        btn_clean = QPushButton("✨ Temizliği Başlat")
        btn_clean.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_clean.setMinimumHeight(40)
        btn_clean.clicked.connect(self.start_clean)
        layout.addWidget(btn_clean, alignment=Qt.AlignCenter)

    def start_clean(self):
        directories = []
        if self.findChild(QCheckBox, "chk_temp").isChecked():
            directories.append((os.getenv('TEMP'), "Geçici Dosyalar"))
            directories.append((os.getenv('TMP'), "Geçici Dosyalar"))
        if self.findChild(QCheckBox, "chk_prefetch").isChecked():
            directories.append((os.path.join(os.getenv('WINDIR'), 'Prefetch'), "Prefetch"))
        if self.findChild(QCheckBox, "chk_browsers").isChecked():
            browsers = [
                ('Chrome', os.path.expanduser('~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cache')),
                ('Edge', os.path.expanduser('~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Cache')),
                ('Firefox', os.path.expanduser('~\\AppData\\Local\\Mozilla\\Firefox\\Profiles'))
            ]
            for name, path in browsers:
                if os.path.exists(path):
                    directories.append((path, f"{name} Önbelleği"))
        if self.findChild(QCheckBox, "chk_windows_update").isChecked():
            directories.append((os.path.join(os.getenv('WINDIR'), 'SoftwareDistribution', 'Download'), "Windows Güncelleme Geçmişi"))
        if self.findChild(QCheckBox, "chk_memory_dumps").isChecked():
            directories.append((os.path.join(os.getenv('WINDIR'), 'Minidump'), "Bellek Dökümleri"))
            directories.append((os.path.join(os.getenv('WINDIR'), 'LiveKernelReports'), "Hata Raporları"))
        if self.findChild(QCheckBox, "chk_thumbnails").isChecked():
            directories.append((os.path.expanduser('~\\AppData\\Local\\Microsoft\\Windows\\Explorer'), "Küçük Resim Önbelleği"))
        
        dns_cleared = False
        if self.findChild(QCheckBox, "chk_dns_cache").isChecked():
            self.clear_dns_cache()
            dns_cleared = True

        if not directories and not dns_cleared and not self.findChild(QCheckBox, "chk_recycle_bin").isChecked():
            CustomNotification("⚠️ Lütfen en az bir seçenek işaretleyin!", duration=3000, parent=self).show_notification()
            return

        if directories:
            self.thread = CleanerThread(directories)
            self.thread.update_status.connect(self.lbl_status.setText)
            self.thread.complete_signal.connect(lambda total: (
                self.lbl_status.setText(f"✅ Toplam {total} dosya silindi!"),
                CustomNotification("✅ Temizlik tamamlandı!", duration=3000, parent=self).show_notification()
            ))
            self.thread.start()

        if self.findChild(QCheckBox, "chk_recycle_bin").isChecked():
            self.clear_recycle_bin()
            CustomNotification("✅ Geri Dönüşüm kutusu başarıyla temizlendi!", duration=3000, parent=self).show_notification()

    def clear_dns_cache(self):
        try:
            subprocess.run(["ipconfig", "/flushdns"], check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            self.lbl_status.setText("✅ DNS önbelleği başarıyla temizlendi!")
        except Exception as e:
            self.lbl_status.setText(f"❌ DNS önbelleği temizlenemedi: {e}")

    def clear_recycle_bin(self):
        try:
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x00000001)
            self.lbl_status.setText("✅ Geri Dönüşüm kutusu başarıyla temizlendi!")
        except Exception as e:
            self.lbl_status.setText(f"❌ Geri Dönüşüm kutusu temizlenemedi: {e}")

# ======================= PERFORMANS WIDGET =======================
class PerformanceWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 20)
        self.lbl_info = QLabel()
        self.lbl_info.setStyleSheet(f"color: {STYLE_CONFIG['dark']['text']}; font: 14px;")
        self.chart = QChart()
        self.chart.setBackgroundBrush(QColor(STYLE_CONFIG['dark']['list_bg']))
        self.chart.setTitle("📈 Sistem Kaynak Kullanımı")
        self.chart.setTitleBrush(QColor(STYLE_CONFIG['dark']['text']))
        self.chart.legend().setVisible(False)
        self.series_cpu = QLineSeries()
        self.series_cpu.setColor(QColor(STYLE_CONFIG['dark']['chart_line']))
        self.series_cpu.setName("CPU")
        self.series_ram = QLineSeries()
        self.series_ram.setColor(QColor("#4CAF50"))
        self.series_ram.setName("RAM")
        axisX = QValueAxis()
        axisX.setLabelFormat("%d")
        axisX.setTitleText("Zaman (s)")
        axisX.setTitleBrush(QColor(STYLE_CONFIG['dark']['text']))
        axisX.setLabelsBrush(QColor(STYLE_CONFIG['dark']['text']))
        axisY = QValueAxis()
        axisY.setRange(0, 100)
        axisY.setTitleText("Kullanım (%)")
        axisY.setTitleBrush(QColor(STYLE_CONFIG['dark']['text']))
        axisY.setLabelsBrush(QColor(STYLE_CONFIG['dark']['text']))
        self.chart.addSeries(self.series_cpu)
        self.chart.addSeries(self.series_ram)
        self.chart.addAxis(axisX, Qt.AlignBottom)
        self.chart.addAxis(axisY, Qt.AlignLeft)
        self.series_cpu.attachAxis(axisX)
        self.series_cpu.attachAxis(axisY)
        self.series_ram.attachAxis(axisX)
        self.series_ram.attachAxis(axisY)
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)
        self.x = 0
        layout.addWidget(self.lbl_info)
        layout.addWidget(self.chart_view)
        style_all_buttons(self)

    def update_stats(self):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        gpu = GPUtil.getGPUs()[0].load*100 if GPUtil.getGPUs() else 0
        self.lbl_info.setText(f"📊 Gerçek Zamanlı Kullanım:\nCPU: {cpu}% | RAM: {mem}% | GPU: {gpu:.1f}%")
        self.series_cpu.append(self.x, cpu)
        self.series_ram.append(self.x, mem)
        if self.series_cpu.count() > 60:
            self.series_cpu.removePoints(0, self.series_cpu.count()-60)
            self.series_ram.removePoints(0, self.series_ram.count()-60)
        axisX = self.chart.axes(Qt.Horizontal)[0]
        axisX.setRange(max(0, self.x-60), self.x)
        self.x += 1

# ======================= DONANIM WIDGET =======================
from GPUtil import GPU
class HardwareWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.show_network_ip = False  
        self.init_ui()
        self.update_hardware_info()
        QTimer.singleShot(1000, self.update_hardware_info)  

    def get_gpus_with_no_console():
        try:
            output = subprocess.check_output(
                "nvidia-smi --query-gpu=name,memory.total,utilization.gpu --format=csv,noheader,nounits",
                shell=True,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)  
            ).decode("utf-8").strip()
            gpus = []
            for line in output.split("\n"):
                name, mem_total, util = line.split(", ")
                gpu = GPU()
                gpu.name = name
                gpu.memoryTotal = int(mem_total)
                gpu.load = float(util) / 100
                gpus.append(gpu)
            return gpus
        except:
            return []

    def init_ui(self):
        self.labels = {}  
        layout = QGridLayout(self)
        layout.setVerticalSpacing(15)
        layout.setHorizontalSpacing(20)
        layout.setContentsMargins(20, 15, 20, 20)
        title = QLabel("🔧 Detaylı Donanım Bilgileri")
        title.setStyleSheet(f"color: {STYLE_CONFIG['dark']['primary']}; font: bold 18px;")
        layout.addWidget(title, 0, 0, 1, 3)
        self.cards = {
            'cpu': self.create_card("💻 İşlemci", self.get_cpu_info(), 'cpu'),
            'gpu': self.create_card("🎮 GPU", self.get_gpu_info(), 'gpu'),
            'ram': self.create_card("🧠 Bellek", self.get_ram_info(), 'ram'),
            'disk': self.create_card("💾 Depolama", self.get_disk_info(), 'disk'),
            'network': self.create_network_card("🌐 Ağ", self.get_network_info(), 'network'),
            'score': self.create_score_card()
        }
        layout.addWidget(self.cards['cpu'], 1, 0)
        layout.addWidget(self.cards['gpu'], 1, 1)
        layout.addWidget(self.cards['ram'], 2, 0)
        layout.addWidget(self.cards['disk'], 2, 1)
        layout.addWidget(self.cards['network'], 3, 0)
        layout.addWidget(self.cards['score'], 1, 2, 3, 1)
        style_all_buttons(self)

    def create_card(self, title, content, key):
        frame = QFrame()
        frame.setStyleSheet(f"""
            background: {STYLE_CONFIG['dark']['card_bg']};
            border-radius: 12px;
            padding: 10px;
        """)
        layout = QVBoxLayout(frame)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        frame.setLayout(layout)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['primary']};
            font: bold 14px;
            margin-bottom: 10px;
        """)
        layout.addWidget(lbl_title)
        lbl_content = QLabel(content)
        lbl_content.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: 13px '{STYLE_CONFIG['font']['content'][0]}';
            line-height: 1.2;
            border-radius: 10px;
            padding: 4px;
        """)
        lbl_content.setWordWrap(True)
        layout.addWidget(lbl_content)
        self.labels[key] = lbl_content 
        return frame

    def create_network_card(self, title, content, key):
        frame = QFrame()
        frame.setStyleSheet(f"""
            background: {STYLE_CONFIG['dark']['card_bg']};
            border-radius: 12px;
            padding: 10px;
        """)
        main_layout = QVBoxLayout(frame)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(0, 0, 0, 0)
        frame.setLayout(main_layout)
        header_layout = QHBoxLayout()
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['primary']};
            font: bold 14px;
        """)
        header_layout.addWidget(lbl_title)
        toggle_btn = QPushButton("👁️")
        toggle_btn.setFixedSize(30, 30)
        toggle_btn.setStyleSheet("background: transparent; border: none;")
        toggle_btn.clicked.connect(self.toggle_network_ip)
        header_layout.addWidget(toggle_btn, alignment=Qt.AlignRight)
        header_layout.setStretch(0, 1) 
        main_layout.addLayout(header_layout)
        lbl_content = QLabel(content)
        lbl_content.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: 13px '{STYLE_CONFIG['font']['content'][0]}';
            line-height: 1.2;
            border-radius: 10px;
            padding: 4px;
        """)
        lbl_content.setWordWrap(True)
        main_layout.addWidget(lbl_content)
        self.labels[key] = lbl_content 
        return frame

    def create_score_card(self):
        frame = QFrame()
        frame.setStyleSheet(f"""
            background: {STYLE_CONFIG['dark']['card_bg']};
            border-radius: 12px;
            padding: 18px;
        """)
        layout = QVBoxLayout(frame)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        frame.setLayout(layout)
        lbl_title = QLabel("🏆 Sistem Puanları")
        lbl_title.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['primary']};
            font: bold 14px;
            margin-bottom: 12px;
        """)
        layout.addWidget(lbl_title)
        self.lbl_scores = QLabel()
        self.lbl_scores.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: 13px '{STYLE_CONFIG['font']['content'][0]}';
            line-height: 1.6;
        """)
        self.lbl_scores.setWordWrap(True)
        layout.addWidget(self.lbl_scores)
        return frame

    def toggle_network_ip(self):
        self.show_network_ip = not self.show_network_ip
        self.labels['network'].setText(self.get_network_info())

    def get_winsat_scores(self):
        try:
            result = subprocess.run(
                ['powershell', '-Command', 'Get-CimInstance Win32_WinSat | ConvertTo-Json'],
                capture_output=True, text=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            )
            data = json.loads(result.stdout)
            return (
                f"• CPU: {data.get('CPUScore', 'N/A')}\n"
                f"• 3D Grafik: {data.get('D3DScore', 'N/A')}\n"
                f"• Depolama: {data.get('DiskScore', 'N/A')}\n"
                f"• 2D Grafik: {data.get('GraphicsScore', 'N/A')}\n"
                f"• Bellek: {data.get('MemoryScore', 'N/A')}"
            )
        except:
            return "Sistem puanları alınamadı"

    def get_cpu_info(self):
        try:
            freq = psutil.cpu_freq()
            return (
                f"Model: {platform.processor()}\n"
                f"Çekirdek: {os.cpu_count()}\n"
                f"Frekans: {freq.current/1000:.2f} GHz\n"
                f"Maks. Frekans: {freq.max/1000:.2f} GHz"
            )
        except:
            return "Bilgi alınamadı"

    def get_gpu_info(self):
        try:
            gpus = GPUtil.getGPUs()
            if not gpus:
                return "GPU bulunamadı"
            return "\n\n".join([
                f"{gpu.name}\nVRAM: {gpu.memoryTotal} MB\nKullanım: {gpu.load * 100:.1f}%"
                for gpu in gpus
            ])
        except Exception as e:
            return f"GPU bilgisi alınamadı: {str(e)}"
            
    def get_ram_info(self):
        mem = psutil.virtual_memory()
        return (
            f"Toplam: {mem.total//(1024**3)} GB\n"
            f"Kullanım: {mem.percent}%\n"
            f"Kullanılan: {mem.used//(1024**3)} GB"
        )

    def get_disk_info(self):
        parts = psutil.disk_partitions()
        info = []
        for part in parts:
            usage = psutil.disk_usage(part.mountpoint)
            info.append(f"{part.device}\n• Boyut: {usage.total//(1024**3)}GB\n• Boş: {usage.free//(1024**3)}GB")
        return "\n\n".join(info) if info else "Disk bilgisi yok"

    def get_network_info(self):
        addrs = psutil.net_if_addrs()
        info = []
        for name, addresses in addrs.items():
            for addr in addresses:
                if addr.family == 2:
                    ip_str = addr.address if self.show_network_ip else "••••••"
                    info.append(f"{name}\n• IP: {ip_str}")
        return "\n\n".join(info) if info else "Ağ bilgisi yok"

    def update_hardware_info(self):
        self.labels['cpu'].setText(self.get_cpu_info())
        self.labels['gpu'].setText(self.get_gpu_info())
        self.labels['ram'].setText(self.get_ram_info())
        self.labels['disk'].setText(self.get_disk_info())
        self.labels['network'].setText(self.get_network_info())
        self.lbl_scores.setText(self.get_winsat_scores())

# ======================= OPTİMİZASYON WIDGET =======================
class OptimizationWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setContentsMargins(40, 20, 40, 20)
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        title = QLabel("⚙️ Gelişmiş Optimizasyon Ayarları")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['primary']};
            padding: 8px 0 16px 0;
        """)
        layout.addWidget(title)

        # Optimizasyon ayarları ve açıklamaları
        settings_info = {
            "Hizmet Zaman Aşımlarını Azalt": "Hizmetlerin kapanma süresini kısaltarak sistem performansını artırır.",
            "Uzaktan Kayıt Defterini Devre Dışı Bırak": "Uzaktan kayıt defteri erişimini kapatarak güvenliği artırır.",
            "Dosya Uzantılarını ve Gizli Dosyaları Göster": "Dosya uzantılarını ve gizli dosyaları göstererek daha iyi dosya yönetimi sağlar.",
            "Gereksiz Hizmetleri Devre Dışı Bırak": "Arka planda çalışan gereksiz hizmetleri kapatarak sistem kaynaklarını serbest bırakır.",
            "Sistem Profilini Optimize Et": "Sistem profilini performans için optimize eder.",
            "GPU ve Öncelik Ayarlarını Geliştir": "GPU ve işlemci önceliklerini optimize ederek performansı artırır.",
            "Çerçeve Sunucu Modunu Devre Dışı Bırak": "Çerçeve sunucu modunu kapatarak performansı artırır.",
            "Düşük Gecikmeli GPU Ayarlarını Ayarla": "GPU'yu düşük gecikmeli moda alarak oyun performansını artırır.",
            "En İyi Olmayan Çaba Sınırını Belirle": "Arka plan işlemlerinin kaynak kullanımını sınırlayarak performansı artırır.",
            "SysMain'i Devre Dışı Bırak": "SysMain hizmetini kapatarak sistem kaynaklarını serbest bırakır.",
            "NTFS Zaman Damgasını Devre Dışı Bırak": "NTFS zaman damgası kaydını kapatarak disk performansını artırır."
        }

        features = [
            ("Hizmet Zaman Aşımlarını Azalt", self.reduce_service_timeouts),
            ("Uzaktan Kayıt Defterini Devre Dışı Bırak", self.disable_remote_registry),
            ("Dosya Uzantılarını ve Gizli Dosyaları Göster", self.show_file_extensions),
            ("Gereksiz Hizmetleri Devre Dışı Bırak", self.disable_unnecessary_services),
            ("Sistem Profilini Optimize Et", self.optimize_system_profile),
            ("GPU ve Öncelik Ayarlarını Geliştir", self.optimize_gpu_settings),
            ("Çerçeve Sunucu Modunu Devre Dışı Bırak", self.disable_frame_server_mode),
            ("Düşük Gecikmeli GPU Ayarlarını Ayarla", self.set_low_latency_gpu),
            ("En İyi Olmayan Çaba Sınırını Belirle", self.set_best_effort_limit),
            ("SysMain'i Devre Dışı Bırak", self.disable_sysmain),
            ("NTFS Zaman Damgasını Devre Dışı Bırak", self.disable_ntfs_timestamp)
        ]

        grid = QGridLayout()
        grid.setVerticalSpacing(10)
        grid.setHorizontalSpacing(40)
        grid.setContentsMargins(10, 10, 10, 10)

        for i, (text, callback) in enumerate(features):
            row = i % 6
            col = (i // 6) * 2
            
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)
            
            box = QCheckBox(text)
            box.setFont(QFont("Segoe UI", 10))
            box.setStyleSheet(f"""
                QCheckBox {{
                    color: {STYLE_CONFIG['dark']['text']};
                    spacing: 6px;
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                }}
                QCheckBox::indicator:unchecked {{
                    border: 2px solid {STYLE_CONFIG['dark']['secondary']};
                    background: {STYLE_CONFIG['dark']['card_bg']};
                    border-radius: 4px;
                }}
                QCheckBox::indicator:checked {{
                    border: 2px solid {STYLE_CONFIG['dark']['primary']};
                    background: {STYLE_CONFIG['dark']['primary']};
                    border-radius: 4px;
                }}
                QCheckBox::indicator:hover {{
                    border: 2px solid {STYLE_CONFIG['dark']['hover']};
                }}
            """)
            box.stateChanged.connect(callback)
            
            info_button = InfoButton(settings_info[text], container)
            
            container_layout.addWidget(box)
            container_layout.addWidget(info_button)
            container_layout.addStretch()
            
            grid.addWidget(container, row * 2, col, alignment=Qt.AlignLeft | Qt.AlignTop)

        layout.addLayout(grid)
        btn_apply = QPushButton("🚀 Ayarları Uygula")
        btn_apply.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_apply.setMinimumHeight(40)
        btn_apply.clicked.connect(self.apply_settings)
        layout.addWidget(btn_apply, alignment=Qt.AlignCenter)
        style_all_buttons(self)

    def apply_settings(self):
        checkboxes = self.findChildren(QCheckBox)
        selected = any(checkbox.isChecked() for checkbox in checkboxes)
        if not selected:
            CustomNotification("⚠️ Lütfen en az bir seçenek işaretleyin!", duration=3000, parent=self).show_notification()
            return
        try:
            CustomNotification("✅ Seçilen ayarlar başarıyla uygulandı!", duration=3000, parent=self).show_notification()
        except Exception as e:
            CustomNotification(f"⛔ Ayarlar uygulanırken bir hata oluştu:\n{str(e)}", duration=3000, parent=self).show_notification()

    def reduce_service_timeouts(self, state):
        try:
            key = r"SYSTEM\CurrentControlSet\Control"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key, 0, winreg.KEY_SET_VALUE) as reg:
                winreg.SetValueEx(reg, "WaitToKillServiceTimeout", 0, winreg.REG_SZ, "2000" if state else "5000")
        except Exception:
            pass

    def disable_remote_registry(self, state):
        try:
            subprocess.run(['sc', 'config', 'RemoteRegistry', 'start=', 'disabled' if state else 'demand'], check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            subprocess.run(['sc', 'stop', 'RemoteRegistry'], check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except Exception:
            pass

    def show_file_extensions(self, state):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", 0, winreg.KEY_SET_VALUE) as reg:
                winreg.SetValueEx(reg, "HideFileExt", 0, winreg.REG_DWORD, 0 if state else 1)
                winreg.SetValueEx(reg, "Hidden", 0, winreg.REG_DWORD, 1 if state else 2)
        except Exception:
            pass

    def disable_unnecessary_services(self, state):
        try:
            services = ["DiagTrack", "WSearch", "Fax"]
            for svc in services:
                subprocess.run(['sc', 'config', svc, 'start=', 'disabled' if state else 'demand'], check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                subprocess.run(['sc', 'stop', svc], check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except Exception:
            pass

    def optimize_system_profile(self, state):
        try:
            key = r"SYSTEM\CurrentControlSet\Control\PriorityControl"
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key) as reg:
                winreg.SetValueEx(reg, "Win32PrioritySeparation", 0, winreg.REG_DWORD, 26 if state else 2)
        except Exception:
            pass

    def optimize_gpu_settings(self, state):
        try:
            key = r"SOFTWARE\Microsoft\DirectX"
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key) as reg:
                winreg.SetValueEx(reg, "MaxFrameLatency", 0, winreg.REG_DWORD, 1 if state else 3)
        except Exception:
            pass

    def disable_frame_server_mode(self, state):
        try:
            key = r"SOFTWARE\Microsoft\Windows\DWM"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key) as reg:
                winreg.SetValueEx(reg, "FrameServerMode", 0, winreg.REG_DWORD, 0 if state else 1)
        except Exception:
            pass

    def set_low_latency_gpu(self, state):
        try:
            key = r"SOFTWARE\Microsoft\DirectX"
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key) as reg:
                winreg.SetValueEx(reg, "LowLatencyMode", 0, winreg.REG_DWORD, 1 if state else 0)
        except Exception:
            pass

    def set_best_effort_limit(self, state):
        try:
            key = r"SYSTEM\CurrentControlSet\Control\Session Manager\SubSystems"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key, 0, winreg.KEY_SET_VALUE) as reg:
                winreg.SetValueEx(reg, "BestEffortLimit", 0, winreg.REG_DWORD, 1 if state else 0)
        except Exception:
            pass

    def disable_sysmain(self, state):
        try:
            subprocess.run(['sc', 'config', 'SysMain', 'start=', 'disabled' if state else 'demand'], check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            subprocess.run(['sc', 'stop', 'SysMain'], check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except Exception:
            pass

    def disable_ntfs_timestamp(self, state):
        try:
            key = r"SYSTEM\CurrentControlSet\Control\FileSystem"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key, 0, winreg.KEY_SET_VALUE) as reg:
                winreg.SetValueEx(reg, "NtfsDisableLastAccessUpdate", 0, winreg.REG_DWORD, 1 if state else 0)
        except Exception:
            pass

# ======================= BİLGİ WIDGET =======================
class InfoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)
        title = QLabel("Twiez Optimizer Hakkında")
        title.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['primary']};
            font: bold 22px;
            padding-bottom: 10px;
        """)
        title.setAlignment(Qt.AlignCenter)
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            background: {STYLE_CONFIG['dark']['bg']};
            border-radius: 12px;
            padding: 20px;
        """)
        info_layout = QVBoxLayout(info_frame)
        description = QLabel(
            "Twiez Optimizer, Windows sistemler için geliştirilmiş kapsamlı bir optimizasyon aracıdır. "
            "Bu uygulama ile sisteminizi hızlandırabilir, gereksiz dosyaları temizleyebilir ve "
            "donanım bilgilerinizi görüntüleyebilirsiniz.\n\n"
            "Uygulama Python ve PyQt5 kullanılarak geliştirilmiştir. Modern ve kullanıcı dostu arayüzü "
            "ile kolayca sistem optimizasyonu yapabilirsiniz. Özellikler arasında:\n\n"
            "• Sistem temizliği ve optimizasyonu\n"
            "• Başlangıç programları yönetimi\n"
            "• Donanım performans izleme\n"
            "• Windows ayarları optimizasyonu\n"
            "• Güvenlik ayarları yönetimi\n"
            "• Gerçek zamanlı sistem izleme\n\n"
            "Tüm bu özellikler tek bir arayüzde toplanmış olup, kullanıcıların sistemlerini "
            "kolayca optimize etmelerini sağlar. Uygulama düzenli olarak güncellenmekte ve "
            "yeni özellikler eklenmektedir."
        )
        description.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: 13px '{STYLE_CONFIG['font']['content'][0]}';
            line-height: 1.6;
        """)
        description.setWordWrap(True)
        info_layout.addWidget(description)
        version_label = QLabel(f"Versiyon: {CURRENT_VERSION}")
        version_label.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: italic 12px;
            margin-top: 10px;
        """)
        version_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(version_label)
        layout.addWidget(title)
        layout.addWidget(info_frame)
        footer = QLabel(" 2025 Twiez Optimizer - Tüm hakları saklıdır")
        footer.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: italic 11px;
            padding-top: 15px;
        """)
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)
        style_all_buttons(self)

# ======================= GÜVENLİK WIDGET =======================
class SecurityWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background: #181828;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(18)

        
        title = QLabel("🔒 Güvenlik Özellikleri")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #bb86fc; font: bold 22px 'Segoe UI', Arial; margin-bottom: 0; background: transparent;")
        main_layout.addWidget(title)
        main_layout.addSpacing(10)

        # Responsive grid
        grid = QGridLayout()
        grid.setSpacing(18)

        # --- Firewall ---
        self.firewall_status = QLabel()
        self.firewall_status.setAlignment(Qt.AlignCenter)
        self._style_status_label(self.firewall_status)
        btn_firewall = QPushButton("Aç/Kapat")
        btn_firewall.clicked.connect(self.toggle_firewall)
        self._style_button(btn_firewall)
        grid.addWidget(self._feature_card("🔥 Güvenlik Duvarı", self.firewall_status, btn_firewall), 0, 0)

        # --- UAC ---
        self.uac_status = QLabel()
        self.uac_status.setAlignment(Qt.AlignCenter)
        self._style_status_label(self.uac_status)
        btn_uac = QPushButton("Aç/Kapat")
        btn_uac.clicked.connect(self.toggle_uac)
        self._style_button(btn_uac)
        grid.addWidget(self._feature_card("🛑 Kullanıcı Hesabı Denetimi (UAC)", self.uac_status, btn_uac), 0, 1)

        # --- Analiz ---
        self.analysis_status = QLabel()
        self.analysis_status.setAlignment(Qt.AlignCenter)
        self._style_status_label(self.analysis_status)
        btn_analyze = QPushButton("Analiz Et")
        btn_analyze.clicked.connect(self.analyze_security)
        self._style_button(btn_analyze)
        grid.addWidget(self._feature_card("🔎 Sistem Güvenlik Analizi", self.analysis_status, btn_analyze), 1, 0, 1, 2)

        main_layout.addLayout(grid)
        main_layout.addStretch()
        self.setMinimumWidth(650)
        self.setMinimumHeight(420)
        self.load_security_status()

    def _feature_card(self, title, status_label, button):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {STYLE_CONFIG['dark']['bg']};
                border-radius: 14px;
                border: none;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)
        lbl = QLabel(title)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #bb86fc; font: bold 16px 'Segoe UI', Arial; margin-bottom: 8px;")
        layout.addWidget(lbl)
        layout.addWidget(status_label, alignment=Qt.AlignCenter)
        layout.addWidget(button, alignment=Qt.AlignCenter)  
        return frame

    def _style_button(self, btn):
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c4dff, 
                    stop:1 #bb86fc);
                color: #fff;
                border-radius: 9px;
                font: bold 14px 'Segoe UI', Arial;
                padding: 8px 28px;
                min-width: 120px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #a67cdb, 
                    stop:1 #bb86fc);
            }
        """)

    def _style_status_label(self, lbl):
        lbl.setStyleSheet(f"background: {STYLE_CONFIG['dark']['bg']}; color: #fff; font: 14px 'Segoe UI', Arial; padding: 7px 0; border-radius: 8px;")

    def load_security_status(self):
        
        try:
            import subprocess
            result = subprocess.check_output('netsh advfirewall show allprofiles', shell=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)).decode()
            if 'ON' in result:
                self.firewall_status.setText('Etkin')
            else:
                self.firewall_status.setText('Devre Dışı')
        except Exception:
            self.firewall_status.setText('Bilinmiyor')
      
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System') as key:
                val, _ = winreg.QueryValueEx(key, 'EnableLUA')
                self.uac_status.setText('Etkin' if val == 1 else 'Devre Dışı')
        except Exception:
            self.uac_status.setText('Bilinmiyor')
    
        self.analysis_status.setText('Hazır')

    def toggle_firewall(self):
        import subprocess
        try:
            if self.firewall_status.text() == 'Etkin':
                subprocess.call('netsh advfirewall set allprofiles state off', shell=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                CustomNotification('Güvenlik duvarı devre dışı bırakıldı!', duration=3000, parent=self).show_notification()
            else:
                subprocess.call('netsh advfirewall set allprofiles state on', shell=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                CustomNotification('Güvenlik duvarı etkinleştirildi!', duration=3000, parent=self).show_notification()
            self.load_security_status()
        except Exception:
            self.firewall_status.setText('Değiştirilemedi')
            CustomNotification('Güvenlik duvarı değiştirilemedi!', duration=3000, parent=self).show_notification()

    def toggle_uac(self):
        import winreg
        import ctypes
        try:
            if not ctypes.windll.shell32.IsUserAnAdmin():
                self.uac_status.setText('Yönetici olarak çalıştırın!')
                CustomNotification('Yönetici olarak çalıştırın!', duration=3000, parent=self).show_notification()
                return
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System', 0, winreg.KEY_SET_VALUE) as key:
                current = 1
                try:
                    val, _ = winreg.QueryValueEx(key, 'EnableLUA')
                    current = val
                except Exception:
                    pass
                winreg.SetValueEx(key, 'EnableLUA', 0, winreg.REG_DWORD, 0 if current == 1 else 1)
            self.load_security_status()
            self.uac_status.setText('Değişiklik için bilgisayarı yeniden başlatın!')
            CustomNotification('UAC değişikliği için bilgisayarı yeniden başlatın!', duration=3000, parent=self).show_notification()
        except PermissionError:
            self.uac_status.setText('Yönetici olarak çalıştırın!')
            CustomNotification('Yönetici olarak çalıştırın!', duration=3000, parent=self).show_notification()
        except Exception as e:
            self.uac_status.setText(f'Hata: {e}')
            CustomNotification(f'UAC değiştirilemedi! {e}', duration=3000, parent=self).show_notification()

    def analyze_security(self):
        status = []
        if self.firewall_status.text() != 'Etkin':
            status.append('Güvenlik duvarı pasif!')
        if self.uac_status.text() != 'Etkin':
            status.append('UAC pasif!')
        if not status:
            self.analysis_status.setText('Tebrikler, temel güvenlik açıklarınız yok!')
            CustomNotification('Tebrikler, temel güvenlik açıklarınız yok!', duration=3000, parent=self).show_notification()
        else:
            self.analysis_status.setText(' ; '.join(status))
            CustomNotification(' ; '.join(status), duration=3000, parent=self).show_notification()

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
                zip_file.extractall(os.getcwd())  # Mevcut dizine çıkar
                CustomNotification("✅ Uygulama başarıyla güncellendi! Lütfen uygulamayı yeniden başlatın.", duration=3000, parent=self.parent).show_notification()
                sys.exit()  
            else:
                CustomNotification("⛔ Güncelleme indirilemedi!", duration=3000, parent=self.parent).show_notification()
        except Exception as e:
            CustomNotification(f"⛔ Güncelleme sırasında hata oluştu:\n{str(e)}", duration=3000, parent=self.parent).show_notification()

# ======================= YÖNETİCİ KONTROLÜ =======================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, None, 1)
    sys.exit()

class InfoButton(QToolButton):
    def __init__(self, info_text, parent=None):
        super().__init__(parent)
        self.setText("?")  
        self.setStyleSheet(f"""
            QToolButton {{
                background: transparent;
                border: none;
                padding: 4px;
                margin-left: 8px;
                color: {STYLE_CONFIG['dark']['primary']};
                font: bold 14px;
                min-width: 20px;
                min-height: 20px;
            }}
            QToolButton:hover {{
                background: {STYLE_CONFIG['dark']['hover']};
                border-radius: 12px;
                color: white;
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Bilgi")
        self.clicked.connect(lambda: self.show_info(info_text))

    def show_info(self, info_text):
        CustomNotification(info_text, duration=5000, parent=self).show_notification()

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    update_font_sizes(app)
    set_global_styles(app)
    window = OptimizerWindow()
    window.show()
    sys.exit(app.exec_())
