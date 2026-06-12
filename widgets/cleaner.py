import os, sys, time, subprocess, shutil, psutil, GPUtil, platform, winreg, json, ctypes, requests
from zipfile import ZipFile
from io import BytesIO
from pypresence import Presence
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtChart import *
from config import *
from ui.custom_dialogs import CustomConfirmation, CustomNotification
from threads.cleaner_thread import CleanerThread
from ui.components import InfoButton, ToggleSwitch
from utils.i18n import tr
from utils import settings_manager as sm

# ======================= TEMİZLİK WIDGET =======================
class CleanerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Ana layout (ScrollArea için)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; } QScrollBar:vertical { width: 10px; }")

        # İçerik Widget'ı
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(18)
        
        self.setup_title(layout)
        self.setup_checkboxes(layout)
        self.setup_status_and_button(layout)
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        style_all_buttons(self)

    def setup_title(self, layout):
        title = QLabel(tr("cleaner_title", "🧹 Sistem Temizleme"))
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['primary']};
            padding: 8px 0 16px 0;
        """)
        layout.addWidget(title)

    def setup_checkboxes(self, layout):
      
        settings_info = {
            tr("chk_temp", "🗑️ Geçici Dosyalar"): tr("chk_temp_desc", "Geçici dosyalar silinir, genellikle önemsiz dosyalardır."),
            tr("chk_recycle_bin", "🗑️ Geri Dönüşüm Kutusu"): tr("chk_recycle_bin_desc", "Geri dönüşüm kutusundaki dosyalar tamamen silinir."),
            tr("chk_prefetch", "📂 Prefetch Dosyaları"): tr("chk_prefetch_desc", "Prefetch dosyaları bilgisayarın hızlanması için silinebilir boş dosyalardır."),
            tr("chk_browsers", "🌐 Tarayıcı Önbelleği"): tr("chk_browsers_desc", "Tarayıcı önbelleği silinir, tarayıcınızın hızını artırır. Ancak Tarayıcınızdaki oturumlar kapanabilir!"),
            tr("chk_windows_update", "🔄 Windows Güncelleme Geçmişi"): tr("chk_windows_update_desc", "Eski Windows güncelleme dosyalarını temizler."),
            tr("chk_memory_dumps", "💾 Bellek Dökümleri ve Hata Raporları"): tr("chk_memory_dumps_desc", "Sistem çökmesi sırasında oluşturulan bellek dökümleri ve hata raporlarını temizler."),
            tr("chk_thumbnails", "🖼️ Thumbnail (Küçük Resim) Önbelleği"): tr("chk_thumbnails_desc", "Windows'un küçük resim önbelleğini temizler."),
            tr("chk_dns_cache", "🌐 DNS Önbelleği"): tr("chk_dns_cache_desc", "DNS önbelleğini temizleyerek ağ bağlantılarını yeniler.")
        }

        features = [
            (tr("chk_temp", "🗑️ Geçici Dosyalar"), "chk_temp"),
            (tr("chk_recycle_bin", "🗑️ Geri Dönüşüm Kutusu"), "chk_recycle_bin"),
            (tr("chk_prefetch", "📂 Prefetch Dosyaları"), "chk_prefetch"),
            (tr("chk_browsers", "🌐 Tarayıcı Önbelleği"), "chk_browsers"),
            (tr("chk_windows_update", "🔄 Windows Güncelleme Geçmişi"), "chk_windows_update"),
            (tr("chk_memory_dumps", "💾 Bellek Dökümleri ve Hata Raporları"), "chk_memory_dumps"),
            (tr("chk_thumbnails", "🖼️ Thumbnail (Küçük Resim) Önbelleği"), "chk_thumbnails"),
            (tr("chk_dns_cache", "🌐 DNS Önbelleği"), "chk_dns_cache")
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
            
            # Label
            label = QLabel(text)
            label.setFont(QFont("Segoe UI", 10))
            label.setStyleSheet(f"color: {STYLE_CONFIG['dark']['text']};")
            
            # Toggle Switch
            toggle = ToggleSwitch(container)
            toggle.setObjectName(name)
            # Restore saved state
            toggle.blockSignals(True)
            toggle.setChecked(bool(sm.get("cleaner", name, False)))
            toggle.blockSignals(False)
            # Auto-save on change
            toggle.stateChanged.connect(lambda state, n=name: sm.set_value("cleaner", n, state))
            
            info_button = InfoButton(settings_info[text], container)
            
            container_layout.addWidget(toggle)
            container_layout.addSpacing(10)
            container_layout.addWidget(label)
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

        btn_clean = QPushButton(f"✨ {tr('btn_clean', 'Temizliği Başlat')}")
        btn_clean.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_clean.setMinimumHeight(40)
        btn_clean.clicked.connect(self.start_clean)
        layout.addWidget(btn_clean, alignment=Qt.AlignCenter)

    def start_clean(self):
        directories = []
        if self.findChild(ToggleSwitch, "chk_temp") and self.findChild(ToggleSwitch, "chk_temp").isChecked():
            directories.append((os.getenv('TEMP'), tr("dir_temp", "Geçici Dosyalar")))
            directories.append((os.getenv('TMP'), tr("dir_temp", "Geçici Dosyalar")))
        if self.findChild(ToggleSwitch, "chk_prefetch") and self.findChild(ToggleSwitch, "chk_prefetch").isChecked():
            directories.append((os.path.join(os.getenv('WINDIR'), 'Prefetch'), tr("dir_prefetch", "Prefetch")))
        if self.findChild(ToggleSwitch, "chk_browsers") and self.findChild(ToggleSwitch, "chk_browsers").isChecked():
            browsers = [
                ('Chrome', os.path.expanduser('~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cache')),
                ('Edge', os.path.expanduser('~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Cache')),
                ('Firefox', os.path.expanduser('~\\AppData\\Local\\Mozilla\\Firefox\\Profiles'))
            ]
            for name, path in browsers:
                if os.path.exists(path):
                    directories.append((path, tr("dir_browser_cache", "{} Cache").format(name)))
        if self.findChild(ToggleSwitch, "chk_windows_update") and self.findChild(ToggleSwitch, "chk_windows_update").isChecked():
            directories.append((os.path.join(os.getenv('WINDIR'), 'SoftwareDistribution', 'Download'), tr("dir_win_update", "Windows Update History")))
        if self.findChild(ToggleSwitch, "chk_memory_dumps") and self.findChild(ToggleSwitch, "chk_memory_dumps").isChecked():
            directories.append((os.path.join(os.getenv('WINDIR'), 'Minidump'), tr("dir_memory_dumps", "Memory Dumps")))
            directories.append((os.path.join(os.getenv('WINDIR'), 'LiveKernelReports'), tr("dir_error_reports", "Error Reports")))
        if self.findChild(ToggleSwitch, "chk_thumbnails") and self.findChild(ToggleSwitch, "chk_thumbnails").isChecked():
            directories.append((os.path.expanduser('~\\AppData\\Local\\Microsoft\\Windows\\Explorer'), tr("dir_thumbnails", "Thumbnail Cache")))
        
        dns_cleared = False
        if self.findChild(ToggleSwitch, "chk_dns_cache") and self.findChild(ToggleSwitch, "chk_dns_cache").isChecked():
            self.clear_dns_cache()
            dns_cleared = True

        if not directories and not dns_cleared and (not self.findChild(ToggleSwitch, "chk_recycle_bin") or not self.findChild(ToggleSwitch, "chk_recycle_bin").isChecked()):
            CustomNotification(f"⚠️ {tr('msg_select_one', 'Lütfen en az bir seçenek işaretleyin!')}", duration=3000, parent=self).show_notification()
            return

        if directories:
            self.thread = CleanerThread(directories)
            self.thread.update_status.connect(self._on_clean_progress)
            self.thread.complete_signal.connect(self._on_clean_complete)
            self.thread.start()

        if self.findChild(ToggleSwitch, "chk_recycle_bin") and self.findChild(ToggleSwitch, "chk_recycle_bin").isChecked():
            self.clear_recycle_bin()
            CustomNotification(tr("msg_success", "✅ İşlem başarılı!"), duration=3000, parent=self).show_notification()

    def _on_clean_progress(self, count_str):
        self.lbl_status.setText(tr("clean_progress", "🗑️ {} files deleted...").format(count_str))

    def _on_clean_complete(self, total):
        self.lbl_status.setText(tr("clean_complete", "✅ Cleaning complete! {} files deleted.").format(total))
        CustomNotification(tr("clean_done_notif", "✅ Cleaning complete!"), duration=3000, parent=self).show_notification()

    def clear_dns_cache(self):
        try:
            subprocess.run(["ipconfig", "/flushdns"], check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            self.lbl_status.setText(tr("clean_dns_ok", "✅ DNS önbelleği başarıyla temizlendi!"))
        except Exception as e:
            self.lbl_status.setText(tr("clean_dns_err", "❌ DNS önbelleği temizlenemedi: {}").format(e))

    def clear_recycle_bin(self):
        try:
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x00000001)
            self.lbl_status.setText(tr("clean_bin_ok", "✅ Geri Dönüşüm kutusu başarıyla temizlendi!"))
        except Exception as e:
            self.lbl_status.setText(tr("clean_bin_err", "❌ Geri Dönüşüm kutusu temizlenemedi: {}").format(e))

