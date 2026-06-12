import os
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from config import STYLE_CONFIG, style_all_buttons
from utils.i18n import tr
from ui.components import InfoButton, ToggleSwitch
from utils import settings_manager as sm
from ui.custom_dialogs import DarkMessageBox
from utils.system_restore import create_restore_point

class DebloaterThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    restore_status = pyqtSignal(str)

    def __init__(self, run_bloatware, run_telemetry):
        super().__init__()
        self.run_bloatware = run_bloatware
        self.run_telemetry = run_telemetry

    def run(self):
        try:
            # First, attempt to create a restore point
            self.restore_status.emit("creating")
            success, msg = create_restore_point("Twiez Optimizer Debloat")
            
            if not success:
                if msg == "DISABLED":
                    self.restore_status.emit("disabled")
                else:
                    self.restore_status.emit(f"failed|{msg}")
                # Wait for user input from UI (we'll implement this via a flag)
                # But to keep it simple, if restore fails, we'll abort the thread and let UI ask the user.
                # Actually, the UI will handle the prompt. We will just pause here or return failure.
                return
            else:
                self.restore_status.emit("success")

            errors = []
            
            if self.run_bloatware:
                self.progress.emit(tr("debloat_bloatware", "Removing Bloatware..."))
                apps = [
                    "Microsoft.ZuneVideo", "Microsoft.ZuneMusic", 
                    "Microsoft.BingWeather", "Microsoft.Microsoft3DViewer",
                    "Microsoft.WindowsFeedbackHub", "Microsoft.GetHelp",
                    "Microsoft.YourPhone", "king.com.CandyCrushSaga",
                    "Microsoft.XboxApp", "Microsoft.XboxGamingOverlay",
                    "Microsoft.MixedReality.Portal", "Microsoft.549981C3F5F10" # Cortana
                ]
                for app in apps:
                    cmd = f"Get-AppxPackage *{app}* | Remove-AppxPackage"
                    subprocess.run(["powershell", "-Command", cmd], creationflags=subprocess.CREATE_NO_WINDOW)
            
            if self.run_telemetry:
                self.progress.emit(tr("debloat_telemetry", "Disabling Telemetry..."))
                # DiagTrack and dmwappushservice
                services = ["DiagTrack", "dmwappushservice"]
                for svc in services:
                    cmd = f"Stop-Service -Name {svc} -Force; Set-Service -Name {svc} -StartupType Disabled"
                    subprocess.run(["powershell", "-Command", cmd], creationflags=subprocess.CREATE_NO_WINDOW)
                
                # Registry entries for telemetry
                reg_cmd = (
                    "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection' -Name 'AllowTelemetry' -Value 0 -Type DWord -Force; "
                    "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection' -Name 'MaxTelemetryAllowed' -Value 0 -Type DWord -Force"
                )
                subprocess.run(["powershell", "-Command", reg_cmd], creationflags=subprocess.CREATE_NO_WINDOW)

            if errors:
                self.finished.emit(False, "\n".join(errors))
            else:
                self.finished.emit(True, "")
        except Exception as e:
            self.finished.emit(False, str(e))

class DebloaterWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(20)

        self.setup_title(layout)
        self.setup_options(layout)
        self.setup_action_button(layout)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        style_all_buttons(self)

    def setup_title(self, layout):
        title = QLabel(tr("debloater_title", "🧽 System Debloater & Privacy"))
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont(*STYLE_CONFIG['font']['title']))
        title.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['primary']};
            padding: 8px 0 16px 0;
        """)
        layout.addWidget(title)

    def setup_options(self, layout):
        options = [
            ("chk_bloatware", tr("debloat_bloatware", "Gereksiz Yüklü Uygulamaları Kaldır"), tr("debloat_bloatware_desc", "Açıklama")),
            ("chk_telemetry", tr("debloat_telemetry", "Windows Telemetrisini Devre Dışı Bırak"), tr("debloat_telemetry_desc", "Açıklama"))
        ]

        self.toggles = {}
        
        for name, title, desc in options:
            container = QFrame()
            container.setStyleSheet(f"""
                QFrame {{
                    background: {STYLE_CONFIG['dark']['list_bg']};
                    border-radius: 10px;
                    border: 1px solid {STYLE_CONFIG['dark']['primary']};
                }}
            """)
            cont_layout = QHBoxLayout(container)
            cont_layout.setContentsMargins(15, 15, 15, 15)

            lbl = QLabel(title)
            lbl.setFont(QFont(*STYLE_CONFIG['font']['content']))
            lbl.setStyleSheet(f"color: {STYLE_CONFIG['dark']['text']}; background: transparent; border: none;")
            
            info_btn = InfoButton(desc, container)
            
            toggle = ToggleSwitch(container)
            toggle.setObjectName(name)
            toggle.blockSignals(True)
            toggle.setChecked(bool(sm.get("debloater", name, False)))
            toggle.blockSignals(False)
            toggle.stateChanged.connect(lambda state, n=name: sm.set_value("debloater", n, state))

            self.toggles[name] = toggle

            cont_layout.addWidget(lbl)
            cont_layout.addWidget(info_btn)
            cont_layout.addStretch()
            cont_layout.addWidget(toggle)

            layout.addWidget(container)

    def setup_action_button(self, layout):
        action_layout = QHBoxLayout()
        self.btn_apply = QPushButton(tr("debloat_btn_apply", "Arındırmayı Başlat"))
        self.btn_apply.setCursor(Qt.PointingHandCursor)
        self.btn_apply.clicked.connect(self.start_debloat)
        action_layout.addStretch()
        action_layout.addWidget(self.btn_apply)
        action_layout.addStretch()
        layout.addWidget(self.btn_apply)
        
        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet(f"color: {STYLE_CONFIG['dark']['text']}; font: 12px 'Segoe UI';")
        layout.addWidget(self.status_lbl)
        layout.addStretch()

    def start_debloat(self):
        run_bloatware = self.toggles["chk_bloatware"].isChecked()
        run_telemetry = self.toggles["chk_telemetry"].isChecked()

        if not run_bloatware and not run_telemetry:
            DarkMessageBox.show_warning(self, tr("sec_error", "Hata"), tr("msg_select_one", "Lütfen en az bir seçenek işaretleyin!"))
            return

        self.btn_apply.setEnabled(False)
        self.thread = DebloaterThread(run_bloatware, run_telemetry)
        self.thread.restore_status.connect(self.handle_restore_status)
        self.thread.progress.connect(self.handle_progress)
        self.thread.finished.connect(self.handle_finished)
        self.thread.start()

    def handle_restore_status(self, status):
        if status == "creating":
            self.status_lbl.setText(tr("msg_restore_creating", "Sistem geri yükleme noktası oluşturuluyor..."))
        elif status == "success":
            self.status_lbl.setText(tr("msg_restore_success", "Geri yükleme noktası başarıyla oluşturuldu. Arındırma işlemi başlatılıyor..."))
        elif status == "disabled":
            self.thread.terminate() # Durdur ve sor
            reply = DarkMessageBox.ask_question(
                self, 
                "System Restore", 
                tr("msg_restore_disabled", "Sistem Geri Yükleme kapalı. Devam edilsin mi?")
            )
            if reply:
                self.force_run_debloat()
            else:
                self.reset_ui()
        elif status.startswith("failed|"):
            self.thread.terminate() # Durdur ve sor
            err = status.split("|")[1]
            # Truncate error message to avoid breaking UI
            if len(err) > 100:
                err = err[:100] + "..."
            reply = DarkMessageBox.ask_question(
                self, 
                "System Restore Error", 
                tr("msg_restore_failed", "Geri yükleme noktası oluşturulamadı. Devam edilsin mi?\nHata: {}").format(err)
            )
            if reply:
                self.force_run_debloat()
            else:
                self.reset_ui()

    def force_run_debloat(self):
        # Restore işlemini atla, doğrudan komutları çalıştır
        run_bloatware = self.toggles["chk_bloatware"].isChecked()
        run_telemetry = self.toggles["chk_telemetry"].isChecked()
        
        # DebloaterThread class'ını modifiye edebiliriz ya da yeni bir thread açabiliriz.
        # Kolaylık için yeni bir is_force_run argümanı eklemedim, direk aynı theadi bir daha başlatamam.
        # Bu yüzden burada mini bir thread daha yapıyorum:
        class ForceDebloaterThread(QThread):
            finished = pyqtSignal(bool, str)
            def run(self_thr):
                try:
                    if run_bloatware:
                        apps = ["Microsoft.ZuneVideo", "Microsoft.BingWeather", "Microsoft.Microsoft3DViewer", "Microsoft.WindowsFeedbackHub", "Microsoft.GetHelp", "Microsoft.YourPhone", "king.com.CandyCrushSaga", "Microsoft.XboxApp", "Microsoft.XboxGamingOverlay", "Microsoft.MixedReality.Portal", "Microsoft.549981C3F5F10"]
                        for app in apps:
                            subprocess.run(["powershell", "-Command", f"Get-AppxPackage *{app}* | Remove-AppxPackage"], creationflags=subprocess.CREATE_NO_WINDOW)
                    if run_telemetry:
                        for svc in ["DiagTrack", "dmwappushservice"]:
                            subprocess.run(["powershell", "-Command", f"Stop-Service -Name {svc} -Force; Set-Service -Name {svc} -StartupType Disabled"], creationflags=subprocess.CREATE_NO_WINDOW)
                    self_thr.finished.emit(True, "")
                except Exception as e:
                    self_thr.finished.emit(False, str(e))
        
        self.force_thread = ForceDebloaterThread()
        self.force_thread.finished.connect(self.handle_finished)
        self.status_lbl.setText(tr("debloat_btn_apply", "Arındırılıyor..."))
        self.force_thread.start()

    def handle_progress(self, msg):
        self.status_lbl.setText(msg)

    def handle_finished(self, success, err_msg):
        self.reset_ui()
        if success:
            DarkMessageBox.show_info(self, tr("sec_ready", "Hazır"), tr("msg_debloat_success", "Arındırma işlemi başarıyla tamamlandı!"))
        else:
            DarkMessageBox.show_error(self, tr("sec_error", "Hata"), tr("msg_debloat_failed", "Arındırma işleminde hatalar oluştu: {}").format(err_msg))

    def reset_ui(self):
        self.btn_apply.setEnabled(True)
        self.status_lbl.setText("")
