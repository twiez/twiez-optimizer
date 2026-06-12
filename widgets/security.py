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
from utils.i18n import tr

# ======================= GÜVENLİK WIDGET =======================
class SecurityWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        from utils.i18n import tr
        from ui.components import ToggleSwitch
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; } QScrollBar:vertical { width: 10px; }")
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        
        title = QLabel(tr("sec_center_title", "🛡️ Güvenlik Merkezi"))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #bb86fc; font: bold 22px 'Segoe UI', Arial; margin-bottom: 0; background: transparent;")
        layout.addWidget(title)
        layout.addSpacing(10)

        # Responsive grid
        grid = QGridLayout()
        grid.setSpacing(18)

        # --- Firewall ---
        self.firewall_status = QLabel()
        self.firewall_status.setAlignment(Qt.AlignCenter)
        self._style_status_label(self.firewall_status)
        self.btn_firewall = ToggleSwitch()
        self.btn_firewall.stateChanged.connect(self.toggle_firewall)
        grid.addWidget(self._feature_card(tr("sec_firewall", "🔥 Güvenlik Duvarı"), self.firewall_status, self.btn_firewall), 0, 0)

        # --- UAC ---
        self.uac_status = QLabel()
        self.uac_status.setAlignment(Qt.AlignCenter)
        self._style_status_label(self.uac_status)
        self.btn_uac = ToggleSwitch()
        self.btn_uac.stateChanged.connect(self.toggle_uac)
        grid.addWidget(self._feature_card(tr("sec_uac", "🛑 Kullanıcı Hesabı Denetimi (UAC)"), self.uac_status, self.btn_uac), 0, 1)

        # --- Analiz ---
        self.analysis_status = QLabel()
        self.analysis_status.setAlignment(Qt.AlignCenter)
        self._style_status_label(self.analysis_status)
        btn_analyze = QPushButton(tr("sec_btn_analyze", "Analiz Et"))
        btn_analyze.clicked.connect(self.analyze_security)
        self._style_button(btn_analyze)
        grid.addWidget(self._feature_card(tr("sec_analysis", "🔎 Sistem Güvenlik Analizi"), self.analysis_status, btn_analyze), 1, 0, 1, 2)

        layout.addLayout(grid)
        layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
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
            result = subprocess.check_output('netsh advfirewall show allprofiles', shell=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)).decode()
            is_on = 'ON' in result
            self.firewall_status.setText(tr("sec_active", "Etkin") if is_on else tr("sec_inactive", "Devre Dışı"))
            self.btn_firewall.blockSignals(True)
            self.btn_firewall.setChecked(is_on)
            self.btn_firewall.blockSignals(False)
        except Exception:
            self.firewall_status.setText(tr("sec_unknown", "Bilinmiyor"))

        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System') as key:
                val, _ = winreg.QueryValueEx(key, 'EnableLUA')
                is_uac = val == 1
                self.uac_status.setText(tr("sec_active", "Etkin") if is_uac else tr("sec_inactive", "Devre Dışı"))
                self.btn_uac.blockSignals(True)
                self.btn_uac.setChecked(is_uac)
                self.btn_uac.blockSignals(False)
        except Exception:
            self.uac_status.setText(tr("sec_unknown", "Bilinmiyor"))

        self.analysis_status.setText(tr("sec_ready", "Hazır"))

    def toggle_firewall(self, state=None):
        try:
            is_active = self.firewall_status.text() == tr("sec_active", "Etkin")
            # If the state changed from the toggle switch, we should toggle the current actual state
            # If state is passed, and state == is_active, do nothing. But since toggle inverses:
            
            if is_active:
                subprocess.call('netsh advfirewall set allprofiles state off', shell=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                CustomNotification(tr("sec_fw_disabled", "Güvenlik duvarı devre dışı bırakıldı!"), duration=3000, parent=self).show_notification()
            else:
                subprocess.call('netsh advfirewall set allprofiles state on', shell=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                CustomNotification(tr("sec_fw_enabled", "Güvenlik duvarı etkinleştirildi!"), duration=3000, parent=self).show_notification()
            self.load_security_status()
        except Exception:
            self.firewall_status.setText(tr("sec_err_change", "Değiştirilemedi"))
            CustomNotification(tr("sec_fw_err", "Güvenlik duvarı değiştirilemedi!"), duration=3000, parent=self).show_notification()

    def toggle_uac(self, state=None):
        try:
            if not ctypes.windll.shell32.IsUserAnAdmin():
                self.uac_status.setText(tr("sec_run_admin", "Yönetici olarak çalıştırın!"))
                CustomNotification(tr("sec_run_admin", "Yönetici olarak çalıştırın!"), duration=3000, parent=self).show_notification()
                return
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System', 0, winreg.KEY_SET_VALUE) as key:
                current = 1
                try:
                    val, _ = winreg.QueryValueEx(key, 'EnableLUA')
                    current = val
                except Exception:
                    pass
                winreg.SetValueEx(key, 'EnableLUA', 0, winreg.REG_DWORD, 0 if current == 1 else 1)
            self.load_security_status()
            self.uac_status.setText(tr("sec_uac_restart", "Değişiklik için bilgisayarı yeniden başlatın!"))
            CustomNotification(tr("sec_uac_restart", "Değişiklik için bilgisayarı yeniden başlatın!"), duration=3000, parent=self).show_notification()
        except PermissionError:
            self.uac_status.setText(tr("sec_run_admin", "Yönetici olarak çalıştırın!"))
            CustomNotification(tr("sec_run_admin", "Yönetici olarak çalıştırın!"), duration=3000, parent=self).show_notification()
        except Exception as e:
            self.uac_status.setText(f"{tr('sec_error', 'Hata')}: {e}")
            CustomNotification(f"{tr('sec_uac_err', 'UAC değiştirilemedi!')} {e}", duration=3000, parent=self).show_notification()

    def analyze_security(self):
        status = []
        if self.firewall_status.text() != tr("sec_active", "Etkin"):
            status.append(tr("sec_fw_passive", "Güvenlik duvarı pasif!"))
        if self.uac_status.text() != tr("sec_active", "Etkin"):
            status.append(tr("sec_uac_passive", "UAC pasif!"))
        if not status:
            self.analysis_status.setText(tr("sec_congrats", "Tebrikler, temel güvenlik açıklarınız yok!"))
            CustomNotification(tr("sec_congrats", "Tebrikler, temel güvenlik açıklarınız yok!"), duration=3000, parent=self).show_notification()
        else:
            self.analysis_status.setText(' ; '.join(status))
            CustomNotification(' ; '.join(status), duration=3000, parent=self).show_notification()

