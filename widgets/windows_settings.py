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

# ======================= WINDOWS AYARLARI WIDGET =======================
class WindowsSettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.checkbox_references = {}
        self.init_ui()
        self.setup_triggers()
        self._restore_states()

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
        self.setup_apply_button(layout)
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        style_all_buttons(self)

    def setup_title(self, layout):
        title = QLabel(tr("win_section_title", "⚙️ Windows Optimization Settings"))
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
            tr("chk_performance", "Yüksek Performans Modu"): tr("chk_performance_desc", "Sisteminizi maksimum performans için optimize eder. Pil tüketimini artırabilir."),
            tr("chk_cortana", "Cortana'yı Devre Dışı Bırak"): tr("chk_cortana_desc", "Cortana asistanını devre dışı bırakarak sistem kaynaklarını serbest bırakır."),
            tr("chk_print", "Yazdırma Hizmetini Kapat"): tr("chk_print_desc", "Arka planda çalışan yazdırma hizmetini kapatarak sistem kaynaklarını serbest bırakır."),
            tr("chk_throttling", "Ağ Kısıtlamalarını Kaldır"): tr("chk_throttling_desc", "Windows'un ağ bant genişliği kısıtlamalarını kaldırarak internet hızını artırır."),
            tr("chk_gamedvr", "GameDVR'ı Devre Dışı Bırak"): tr("chk_gamedvr_desc", "Oyun kayıt özelliğini devre dışı bırakarak performansı artırır."),
            tr("chk_gamemode", "Oyun Modunu Etkinleştir"): tr("chk_gamemode_desc", "Oyun sırasında sistem kaynaklarını optimize eder."),
            tr("chk_hpet", "HPET'i Devre Dışı Bırak"): tr("chk_hpet_desc", "Yüksek hassasiyetli olay zamanlayıcısını devre dışı bırakarak performansı artırır."),
            tr("chk_ink", "Windows Ink'i Kapat"): tr("chk_ink_desc", "Dokunmatik kalem özelliklerini devre dışı bırakır."),
            tr("chk_hello", "Windows Hello'yu Devre Dışı Bırak"): tr("chk_hello_desc", "Yüz tanıma ve parmak izi özelliklerini kapatır."),
            tr("chk_stickkeys", "Yapışkan Tuşları Kapat"): tr("chk_stickkeys_desc", "Klavye erişilebilirlik özelliklerini devre dışı bırakır."),
            tr("chk_clean", "Disk Temizleme"): tr("chk_clean_desc", "Gereksiz sistem dosyalarını temizler."),
            tr("chk_onedrive", "OneDrive'ı Devre Dışı Bırak"): tr("chk_onedrive_desc", "OneDrive senkronizasyonunu devre dışı bırakır."),
            tr("chk_superfetch", "Superfetch'i Kapat"): tr("chk_superfetch_desc", "Önceden yükleme özelliğini devre dışı bırakır."),
            tr("chk_paths", "Uzun Yol Desteğini Etkinleştir"): tr("chk_paths_desc", "Uzun dosya yolu desteğini etkinleştirir.")
        }

        features = [
            (tr("chk_performance", "Yüksek Performans Modu"), "chk_performance"),
            (tr("chk_cortana", "Cortana'yı Devre Dışı Bırak"), "chk_cortana"),
            (tr("chk_print", "Yazdırma Hizmetini Kapat"), "chk_print"),
            (tr("chk_throttling", "Ağ Kısıtlamalarını Kaldır"), "chk_throttling"),
            (tr("chk_gamedvr", "GameDVR'ı Devre Dışı Bırak"), "chk_gamedvr"),
            (tr("chk_gamemode", "Oyun Modunu Etkinleştir"), "chk_gamemode"),
            (tr("chk_hpet", "HPET'i Devre Dışı Bırak"), "chk_hpet"),
            (tr("chk_ink", "Windows Ink'i Kapat"), "chk_ink"),
            (tr("chk_hello", "Windows Hello'yu Devre Dışı Bırak"), "chk_hello"),
            (tr("chk_stickkeys", "Yapışkan Tuşları Kapat"), "chk_stickkeys"),
            (tr("chk_clean", "Disk Temizleme"), "chk_clean"),
            (tr("chk_onedrive", "OneDrive'ı Devre Dışı Bırak"), "chk_onedrive"),
            (tr("chk_superfetch", "Superfetch'i Kapat"), "chk_superfetch"),
            (tr("chk_paths", "Uzun Yol Desteğini Etkinleştir"), "chk_paths")
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
            
            
            # Label
            label = QLabel(text)
            label.setFont(QFont("Segoe UI", 10))
            label.setStyleSheet(f"color: {STYLE_CONFIG['dark']['text']};")
            
            # Toggle Switch
            toggle = ToggleSwitch(container)
            self.checkbox_references[name] = toggle
            toggle.setObjectName(name)
            # Restore saved state (silent, no signal)
            saved = sm.get("windows", name, False)
            toggle.blockSignals(True)
            toggle.setChecked(bool(saved))
            toggle.blockSignals(False)
            # Auto-save on change
            toggle.stateChanged.connect(lambda state, n=name: sm.set_value("windows", n, state))
            
            info_button = InfoButton(settings_info[text], container)
            container_layout.addWidget(toggle)
            container_layout.addSpacing(10)
            container_layout.addWidget(label)
            container_layout.addWidget(info_button)
            container_layout.addStretch()
            
            grid.addWidget(container, row, col, alignment=Qt.AlignLeft | Qt.AlignTop)

        layout.addLayout(grid)

    def setup_apply_button(self, layout):
        btn_apply = QPushButton(f"🚀 {tr('btn_apply', 'Ayarları Uygula')}")
        btn_apply.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_apply.setMinimumHeight(40)
        btn_apply.clicked.connect(self.apply_settings)
        layout.addWidget(btn_apply, alignment=Qt.AlignCenter)

    def setup_triggers(self):
        pass  # triggers are set up per-toggle in setup_checkboxes

    def _restore_states(self):
        """Restore saved toggle states from settings.json."""
        saved = sm.get_section("windows")
        for name, toggle in self.checkbox_references.items():
            if name in saved:
                toggle.blockSignals(True)
                toggle.setChecked(bool(saved[name]))
                toggle.blockSignals(False)

    def apply_settings(self):
        toggles = self.checkbox_references.values()
        selected = any(t.isChecked() for t in toggles)
        if not selected:
            CustomNotification(f"⚠️ {tr('msg_select_one', 'Lütfen en az bir seçenek işaretleyin!')}", duration=3000, parent=self).show_notification()
            return
        
        errors = []
        applied = 0
        
        try:
            # Yüksek Performans Modu
            if self.checkbox_references.get("chk_performance") and self.checkbox_references["chk_performance"].isChecked():
                try:
                    subprocess.run(['powercfg', '/setactive', '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'], 
                                   check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                    applied += 1
                except Exception as e:
                    errors.append(f"Yüksek Performans: {e}")
            
            # Cortana'yı Devre Dışı Bırak
            if self.checkbox_references.get("chk_cortana") and self.checkbox_references["chk_cortana"].isChecked():
                try:
                    key = r"SOFTWARE\Policies\Microsoft\Windows\Windows Search"
                    with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key) as reg:
                        winreg.SetValueEx(reg, "AllowCortana", 0, winreg.REG_DWORD, 0)
                    applied += 1
                except Exception as e:
                    errors.append(f"Cortana: {e}")
            
            # Yazdırma Hizmetini Kapat
            if self.checkbox_references.get("chk_print") and self.checkbox_references["chk_print"].isChecked():
                try:
                    subprocess.run(['sc', 'config', 'Spooler', 'start=', 'disabled'], 
                                   check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                    subprocess.run(['sc', 'stop', 'Spooler'], 
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                    applied += 1
                except Exception as e:
                    errors.append(f"Yazdırma: {e}")
            
            # Ağ Kısıtlamalarını Kaldır
            if self.checkbox_references.get("chk_throttling") and self.checkbox_references["chk_throttling"].isChecked():
                try:
                    key = r"SOFTWARE\Policies\Microsoft\Windows\Psched"
                    with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key) as reg:
                        winreg.SetValueEx(reg, "NonBestEffortLimit", 0, winreg.REG_DWORD, 0)
                    applied += 1
                except Exception as e:
                    errors.append(f"Ağ Kısıtlamaları: {e}")
            
            # GameDVR'ı Devre Dışı Bırak
            if self.checkbox_references.get("chk_gamedvr") and self.checkbox_references["chk_gamedvr"].isChecked():
                try:
                    key = r"SOFTWARE\Microsoft\PolicyManager\default\ApplicationManagement\AllowGameDVR"
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key) as reg:
                        winreg.SetValueEx(reg, "value", 0, winreg.REG_DWORD, 0)
                    key2 = r"System\GameConfigStore"
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key2) as reg:
                        winreg.SetValueEx(reg, "GameDVR_Enabled", 0, winreg.REG_DWORD, 0)
                    applied += 1
                except Exception as e:
                    errors.append(f"GameDVR: {e}")
            
            # Oyun Modunu Etkinleştir
            if self.checkbox_references.get("chk_gamemode") and self.checkbox_references["chk_gamemode"].isChecked():
                try:
                    key = r"Software\Microsoft\GameBar"
                    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key) as reg:
                        winreg.SetValueEx(reg, "AutoGameModeEnabled", 0, winreg.REG_DWORD, 1)
                    applied += 1
                except Exception as e:
                    errors.append(f"Oyun Modu: {e}")
            
            # HPET'i Devre Dışı Bırak
            if self.checkbox_references.get("chk_hpet") and self.checkbox_references["chk_hpet"].isChecked():
                try:
                    subprocess.run(['bcdedit', '/set', 'useplatformclock', 'false'], 
                                   check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                    applied += 1
                except Exception as e:
                    errors.append(f"HPET: {e}")
            
            # Windows Ink'i Kapat
            if self.checkbox_references.get("chk_ink") and self.checkbox_references["chk_ink"].isChecked():
                try:
                    key = r"SOFTWARE\Policies\Microsoft\WindowsInkWorkspace"
                    with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key) as reg:
                        winreg.SetValueEx(reg, "AllowWindowsInkWorkspace", 0, winreg.REG_DWORD, 0)
                    applied += 1
                except Exception as e:
                    errors.append(f"Windows Ink: {e}")
            
            # Windows Hello'yu Devre Dışı Bırak
            if self.checkbox_references.get("chk_hello") and self.checkbox_references["chk_hello"].isChecked():
                try:
                    key = r"SOFTWARE\Policies\Microsoft\PassportForWork"
                    with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key) as reg:
                        winreg.SetValueEx(reg, "Enabled", 0, winreg.REG_DWORD, 0)
                    applied += 1
                except Exception as e:
                    errors.append(f"Windows Hello: {e}")
            
            # Yapışkan Tuşları Kapat
            if self.checkbox_references.get("chk_stickkeys") and self.checkbox_references["chk_stickkeys"].isChecked():
                try:
                    key = r"Control Panel\Accessibility\StickyKeys"
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_SET_VALUE) as reg:
                        winreg.SetValueEx(reg, "Flags", 0, winreg.REG_SZ, "506")
                    applied += 1
                except Exception as e:
                    errors.append(f"Yapışkan Tuşlar: {e}")
            
            # Disk Temizleme
            if self.checkbox_references.get("chk_clean") and self.checkbox_references["chk_clean"].isChecked():
                try:
                    subprocess.Popen(['cleanmgr', '/sagerun:1'], 
                                     creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                    applied += 1
                except Exception as e:
                    errors.append(f"Disk Temizleme: {e}")
            
            # OneDrive'ı Devre Dışı Bırak
            if self.checkbox_references.get("chk_onedrive") and self.checkbox_references["chk_onedrive"].isChecked():
                try:
                    key = r"SOFTWARE\Policies\Microsoft\Windows\OneDrive"
                    with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key) as reg:
                        winreg.SetValueEx(reg, "DisableFileSyncNGSC", 0, winreg.REG_DWORD, 1)
                    applied += 1
                except Exception as e:
                    errors.append(f"OneDrive: {e}")
            
            # Superfetch'i Kapat
            if self.checkbox_references.get("chk_superfetch") and self.checkbox_references["chk_superfetch"].isChecked():
                try:
                    subprocess.run(['sc', 'config', 'SysMain', 'start=', 'disabled'], 
                                   check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                    subprocess.run(['sc', 'stop', 'SysMain'], 
                                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                    applied += 1
                except Exception as e:
                    errors.append(f"Superfetch: {e}")
            
            # Uzun Yol Desteğini Etkinleştir
            if self.checkbox_references.get("chk_paths") and self.checkbox_references["chk_paths"].isChecked():
                try:
                    key = r"SYSTEM\CurrentControlSet\Control\FileSystem"
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key, 0, winreg.KEY_SET_VALUE) as reg:
                        winreg.SetValueEx(reg, "LongPathsEnabled", 0, winreg.REG_DWORD, 1)
                    applied += 1
                except Exception as e:
                    errors.append(f"Uzun Yol: {e}")
            
            # Sonuç bildirimi
            if errors:
                error_msg = "\n".join(errors[:3])
                CustomNotification(f"⚠️ {applied} ayar uygulandı, {len(errors)} hata oluştu:\n{error_msg}", duration=5000, parent=self).show_notification()
            else:
                CustomNotification(f"✅ {tr('msg_success', 'İşlem başarılı!')}", duration=3000, parent=self).show_notification()
        except Exception as e:
            CustomNotification(f"⛔ Hata:\n{str(e)}", duration=3000, parent=self).show_notification()

