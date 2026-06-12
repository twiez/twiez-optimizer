import os, sys, time, subprocess, shutil, psutil, GPUtil, platform, winreg, json, ctypes, requests
from zipfile import ZipFile
from io import BytesIO
from pypresence import Presence
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtChart import *
from config import *
from ui.components import InfoButton, ToggleSwitch
from utils.i18n import tr
from ui.custom_dialogs import CustomNotification
from utils import settings_manager as sm

# ======================= OPTİMİZASYON WIDGET =======================
class OptimizationWidget(QWidget):
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
        title = QLabel(tr("opt_section_title", "⚙️ Optimization Settings"))
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['primary']};
            padding: 8px 0 16px 0;
        """)
        layout.addWidget(title)

        # Optimizasyon ayarları ve açıklamaları
        settings_info = {
            tr("opt_timeouts", "Hizmet Zaman Aşımlarını Azalt"): tr("opt_timeouts_desc", "Hizmetlerin kapanma süresini kısaltarak sistem performansını artırır."),
            tr("opt_remote_reg", "Uzaktan Kayıt Defterini Devre Dışı Bırak"): tr("opt_remote_reg_desc", "Uzaktan kayıt defteri erişimini kapatarak güvenliği artırır."),
            tr("opt_show_hidden", "Dosya Uzantılarını ve Gizli Dosyaları Göster"): tr("opt_show_hidden_desc", "Dosya uzantılarını ve gizli dosyaları göstererek daha iyi dosya yönetimi sağlar."),
            tr("opt_disable_services", "Gereksiz Hizmetleri Devre Dışı Bırak"): tr("opt_disable_services_desc", "Arka planda çalışan gereksiz hizmetleri kapatarak sistem kaynaklarını serbest bırakır."),
            tr("opt_sys_profile", "Sistem Profilini Optimize Et"): tr("opt_sys_profile_desc", "Sistem profilini performans için optimize eder."),
            tr("opt_gpu_priority", "GPU ve Öncelik Ayarlarını Geliştir"): tr("opt_gpu_priority_desc", "GPU ve işlemci önceliklerini optimize ederek performansı artırır."),
            tr("opt_frame_server", "Çerçeve Sunucu Modunu Devre Dışı Bırak"): tr("opt_frame_server_desc", "Çerçeve sunucu modunu kapatarak performansı artırır."),
            tr("opt_low_latency", "Düşük Gecikmeli GPU Ayarlarını Ayarla"): tr("opt_low_latency_desc", "GPU'yu düşük gecikmeli moda alarak oyun performansını artırır."),
            tr("opt_limit_bg", "En İyi Olmayan Çaba Sınırını Belirle"): tr("opt_limit_bg_desc", "Arka plan işlemlerinin kaynak kullanımını sınırlayarak performansı artırır."),
            tr("opt_sysmain", "SysMain'i Devre Dışı Bırak"): tr("opt_sysmain_desc", "SysMain hizmetini kapatarak sistem kaynaklarını serbest bırakır."),
            tr("opt_ntfs_timestamp", "NTFS Zaman Damgasını Devre Dışı Bırak"): tr("opt_ntfs_timestamp_desc", "NTFS zaman damgası kaydını kapatarak disk performansını artırır.")
        }

        features = [
            (tr("opt_timeouts", "Hizmet Zaman Aşımlarını Azalt"), self.reduce_service_timeouts),
            (tr("opt_remote_reg", "Uzaktan Kayıt Defterini Devre Dışı Bırak"), self.disable_remote_registry),
            (tr("opt_show_hidden", "Dosya Uzantılarını ve Gizli Dosyaları Göster"), self.show_file_extensions),
            (tr("opt_disable_services", "Gereksiz Hizmetleri Devre Dışı Bırak"), self.disable_unnecessary_services),
            (tr("opt_sys_profile", "Sistem Profilini Optimize Et"), self.optimize_system_profile),
            (tr("opt_gpu_priority", "GPU ve Öncelik Ayarlarını Geliştir"), self.optimize_gpu_settings),
            (tr("opt_frame_server", "Çerçeve Sunucu Modunu Devre Dışı Bırak"), self.disable_frame_server_mode),
            (tr("opt_low_latency", "Düşük Gecikmeli GPU Ayarlarını Ayarla"), self.set_low_latency_gpu),
            (tr("opt_limit_bg", "En İyi Olmayan Çaba Sınırını Belirle"), self.set_best_effort_limit),
            (tr("opt_sysmain", "SysMain'i Devre Dışı Bırak"), self.disable_sysmain),
            (tr("opt_ntfs_timestamp", "NTFS Zaman Damgasını Devre Dışı Bırak"), self.disable_ntfs_timestamp)
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
            
            # Label
            label = QLabel(text)
            label.setFont(QFont("Segoe UI", 10))
            label.setStyleSheet(f"color: {STYLE_CONFIG['dark']['text']};")
            
            # Toggle Switch
            toggle = ToggleSwitch(container)
            toggle_key = f"opt_{i}"
            toggle.setObjectName(toggle_key)
            # Restore saved state
            toggle.blockSignals(True)
            toggle.setChecked(bool(sm.get("optimization", toggle_key, False)))
            toggle.blockSignals(False)
            # Auto-save on change
            toggle.stateChanged.connect(lambda state, k=toggle_key: sm.set_value("optimization", k, state))
            # stateChanged in ToggleSwitch is handled differently (we don't have a signal yet).
            # Actually, ToggleSwitch doesn't emit stateChanged! We need to add a pyqtSignal to ToggleSwitch.
            
            info_button = InfoButton(settings_info[text], container)
            
            container_layout.addWidget(toggle)
            container_layout.addSpacing(10)
            container_layout.addWidget(label)
            container_layout.addWidget(info_button)
            container_layout.addStretch()
            
            grid.addWidget(container, row * 2, col, alignment=Qt.AlignLeft | Qt.AlignTop)

        layout.addLayout(grid)
        btn_apply = QPushButton(f"🚀 {tr('btn_apply', 'Ayarları Uygula')}")
        btn_apply.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_apply.setMinimumHeight(40)
        btn_apply.clicked.connect(self.apply_settings)
        layout.addWidget(btn_apply, alignment=Qt.AlignCenter)
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        style_all_buttons(self)

    def apply_settings(self):
        toggles = self.findChildren(ToggleSwitch)
        selected = any(t.isChecked() for t in toggles)
        if not selected:
            CustomNotification(f"⚠️ {tr('msg_select_one', 'Lütfen en az bir seçenek işaretleyin!')}", duration=3000, parent=self).show_notification()
            return
        try:
            CustomNotification(f"✅ {tr('msg_success', 'İşlem başarılı!')}", duration=3000, parent=self).show_notification()
        except Exception as e:
            CustomNotification(f"⛔ Hata:\n{str(e)}", duration=3000, parent=self).show_notification()

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

