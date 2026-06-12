import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from config import STYLE_CONFIG, style_all_buttons
from utils.i18n import tr
from ui.components import InfoButton
from ui.custom_dialogs import DarkMessageBox, CustomNotification
from utils import settings_manager as sm

class NetworkThread(QThread):
    finished = pyqtSignal(bool, str)
    
    def __init__(self, dns_primary, dns_secondary, is_dhcp=False):
        super().__init__()
        self.dns_primary = dns_primary
        self.dns_secondary = dns_secondary
        self.is_dhcp = is_dhcp

    def run(self):
        try:
            # Get active network interface name via wmic
            wmic_cmd = 'wmic nic where "netenabled=true" get netconnectionid'
            result = subprocess.run(wmic_cmd, capture_output=True, text=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Parse output
            lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            adapter_name = None
            if len(lines) >= 2:
                adapter_name = lines[1] # First line is header "NetConnectionID"
            
            if not adapter_name:
                self.finished.emit(False, tr("msg_net_no_adapter", "Aktif bir ağ bağdaştırıcısı bulunamadı!"))
                return
                
            if self.is_dhcp:
                # Set to DHCP
                cmd = f'netsh interface ipv4 set dns name="{adapter_name}" dhcp'
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                # Set static DNS
                cmd1 = f'netsh interface ipv4 set dns name="{adapter_name}" static {self.dns_primary}'
                cmd2 = f'netsh interface ipv4 add dns name="{adapter_name}" {self.dns_secondary} index=2'
                subprocess.run(cmd1, shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                res = subprocess.run(cmd2, shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            # if netsh command fails, it usually still returns 0, so we check if there are explicit errors
            # but usually it succeeds if run as admin.
            self.finished.emit(True, adapter_name)
            
        except Exception as e:
            self.finished.emit(False, str(e))

class ToolsThread(QThread):
    finished = pyqtSignal(bool, str, str) # success, msg, tool_type
    
    def __init__(self, tool_type):
        super().__init__()
        self.tool_type = tool_type # 'flush' or 'winsock'

    def run(self):
        try:
            if self.tool_type == 'flush':
                cmd = "ipconfig /flushdns"
            else:
                cmd = "netsh winsock reset"
                
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if res.returncode == 0:
                self.finished.emit(True, "", self.tool_type)
            else:
                self.finished.emit(False, res.stderr.strip() or res.stdout.strip(), self.tool_type)
        except Exception as e:
            self.finished.emit(False, str(e), self.tool_type)

class NetworkWidget(QWidget):
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
        self.setup_dns_section(layout)
        self.setup_tools_section(layout)
        
        layout.addStretch()

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        style_all_buttons(self)

    def setup_title(self, layout):
        title = QLabel(tr("net_title", "🌐 Ağ & DNS Optimizatörü"))
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont(*STYLE_CONFIG['font']['title']))
        title.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['primary']};
            padding: 8px 0 16px 0;
        """)
        layout.addWidget(title)

    def create_card_container(self, title_text, desc_text=None):
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: {STYLE_CONFIG['dark']['list_bg']};
                border-radius: 10px;
                border: 1px solid {STYLE_CONFIG['dark']['primary']};
            }}
        """)
        cont_layout = QVBoxLayout(container)
        cont_layout.setContentsMargins(20, 20, 20, 20)
        cont_layout.setSpacing(15)

        title_lbl = QLabel(title_text)
        title_lbl.setFont(QFont(*STYLE_CONFIG['font']['title']))
        title_lbl.setStyleSheet(f"color: {STYLE_CONFIG['dark']['primary']}; background: transparent; border: none; font-size: 16px;")
        cont_layout.addWidget(title_lbl)

        if desc_text:
            desc_lbl = QLabel(desc_text)
            desc_lbl.setStyleSheet(f"color: {STYLE_CONFIG['dark']['text']}; background: transparent; border: none; font-size: 12px;")
            desc_lbl.setWordWrap(True)
            cont_layout.addWidget(desc_lbl)
            
        return container, cont_layout

    def setup_dns_section(self, layout):
        container, cont_layout = self.create_card_container(
            tr("net_dns_title", "DNS Sunucu Ayarları"),
            tr("net_dns_desc", "İnternet hızınızı artırmak ve pingi düşürmek için bir DNS sunucusu seçin.")
        )

        # Radio buttons
        self.dns_group = QButtonGroup(self)
        
        options = [
            ("cloudflare", tr("net_dns_cloudflare", "Cloudflare (1.1.1.1) - En Hızlısı")),
            ("google", tr("net_dns_google", "Google (8.8.8.8) - Güvenilir")),
            ("quad9", tr("net_dns_quad9", "Quad9 (9.9.9.9) - Güvenlik Odaklı")),
            ("dhcp", tr("net_dns_default", "Varsayılan (DHCP) - Sıfırla"))
        ]
        
        self.radio_buttons = {}
        saved_dns = sm.get("network", "dns_provider", "dhcp")
        
        for i, (key, label) in enumerate(options):
            rb = QRadioButton(label)
            rb.setStyleSheet(f"""
                QRadioButton {{
                    color: {STYLE_CONFIG['dark']['text']};
                    background: transparent;
                    border: none;
                    font: 13px 'Segoe UI';
                }}
                QRadioButton::indicator {{
                    width: 16px;
                    height: 16px;
                    border-radius: 8px;
                    border: 2px solid {STYLE_CONFIG['dark']['primary']};
                }}
                QRadioButton::indicator:checked {{
                    background-color: {STYLE_CONFIG['dark']['primary']};
                    border: 2px solid {STYLE_CONFIG['dark']['text']};
                }}
            """)
            self.dns_group.addButton(rb, i)
            self.radio_buttons[key] = rb
            cont_layout.addWidget(rb)
            
            if key == saved_dns:
                rb.setChecked(True)

        self.dns_group.buttonClicked.connect(self.save_dns_selection)

        btn_layout = QHBoxLayout()
        self.btn_apply_dns = QPushButton(tr("net_btn_apply_dns", "DNS'i Uygula"))
        self.btn_apply_dns.setCursor(Qt.PointingHandCursor)
        self.btn_apply_dns.clicked.connect(self.apply_dns)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_apply_dns)
        
        cont_layout.addLayout(btn_layout)
        layout.addWidget(container)

    def save_dns_selection(self, button):
        for key, rb in self.radio_buttons.items():
            if rb.isChecked():
                sm.set_value("network", "dns_provider", key)
                break

    def apply_dns(self):
        selected_key = sm.get("network", "dns_provider", "dhcp")
        
        is_dhcp = False
        primary = ""
        secondary = ""
        
        if selected_key == "cloudflare":
            primary, secondary = "1.1.1.1", "1.0.0.1"
        elif selected_key == "google":
            primary, secondary = "8.8.8.8", "8.8.4.4"
        elif selected_key == "quad9":
            primary, secondary = "9.9.9.9", "149.112.112.112"
        else:
            is_dhcp = True

        self.btn_apply_dns.setEnabled(False)
        self.btn_apply_dns.setText(tr("msg_net_detecting", "Aktif ağ bağdaştırıcısı aranıyor..."))
        
        self.thread_dns = NetworkThread(primary, secondary, is_dhcp)
        self.thread_dns.finished.connect(self.handle_dns_finished)
        self.thread_dns.start()

    def handle_dns_finished(self, success, result_msg):
        self.btn_apply_dns.setEnabled(True)
        self.btn_apply_dns.setText(tr("net_btn_apply_dns", "DNS'i Uygula"))
        
        if success:
            DarkMessageBox.show_success(self, "DNS", tr("msg_net_dns_success", "DNS ayarları '{}' bağdaştırıcısına başarıyla uygulandı!").format(result_msg))
        else:
            DarkMessageBox.show_error(self, "DNS Error", tr("msg_net_dns_failed", "DNS ayarları değiştirilirken hata oluştu: {}").format(result_msg))

    def setup_tools_section(self, layout):
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background: {STYLE_CONFIG['dark']['list_bg']};
                border-radius: 10px;
                border: 1px solid {STYLE_CONFIG['dark']['primary']};
            }}
        """)
        cont_layout = QVBoxLayout(container)
        cont_layout.setContentsMargins(20, 20, 20, 20)
        cont_layout.setSpacing(18)

        # Section title
        title_lbl = QLabel(tr("net_tools_title", "Hızlı Ağ Araçları"))
        title_lbl.setFont(QFont(*STYLE_CONFIG['font']['title']))
        title_lbl.setStyleSheet(f"color: {STYLE_CONFIG['dark']['primary']}; background: transparent; border: none; font-size: 16px;")
        cont_layout.addWidget(title_lbl)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"color: {STYLE_CONFIG['dark']['primary']}; background: {STYLE_CONFIG['dark']['primary']}; border: none; max-height: 1px; opacity: 0.3;")
        cont_layout.addWidget(divider)

        tools = [
            ("flush", tr("net_flush_dns", "DNS Önbelleğini Temizle"), tr("net_flush_desc", "Ağ önbelleğini sıfırlar. Yüklenmeyen siteleri ve bağlantı hatalarını çözer.")),
            ("winsock", tr("net_winsock", "Ağı Tamamen Sıfırla (Winsock)"), tr("net_winsock_desc", "Ağ bağdaştırıcılarını fabrika ayarlarına döndürür. Yeniden başlatma gerektirir."))
        ]
        
        self.tool_btns = {}
        for idx, (key, title, desc) in enumerate(tools):
            row_widget = QWidget()
            row_widget.setStyleSheet("background: transparent; border: none;")
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            # Title label
            lbl_title = QLabel(title)
            lbl_title.setFont(QFont(*STYLE_CONFIG['font']['content']))
            lbl_title.setStyleSheet(
                f"color: {STYLE_CONFIG['dark']['text']}; background: transparent; border: none; font-size: 14px;"
            )

            # Info (?) button
            info_btn = InfoButton(desc, row_widget)

            # Execute button
            btn_exec = QPushButton(tr("net_btn_execute", "Çalıştır"))
            btn_exec.setCursor(Qt.PointingHandCursor)
            btn_exec.setFixedWidth(110)
            btn_exec.clicked.connect(lambda _, k=key: self.run_tool(k))
            self.tool_btns[key] = btn_exec

            row_layout.addWidget(lbl_title)
            row_layout.addWidget(info_btn)
            row_layout.addStretch()
            row_layout.addWidget(btn_exec)

            cont_layout.addWidget(row_widget)

            # Add subtle separator between rows (not after last)
            if idx < len(tools) - 1:
                sep = QFrame()
                sep.setFrameShape(QFrame.HLine)
                sep.setStyleSheet(f"background: rgba(103, 58, 183, 0.2); border: none; max-height: 1px;")
                cont_layout.addWidget(sep)

        layout.addWidget(container)

    def run_tool(self, key):
        self.tool_btns[key].setEnabled(False)
        self.thread_tool = ToolsThread(key)
        self.thread_tool.finished.connect(self.handle_tool_finished)
        self.thread_tool.start()

    def handle_tool_finished(self, success, msg, tool_type):
        self.tool_btns[tool_type].setEnabled(True)
        
        if success:
            if tool_type == "flush":
                notif_msg = tr("msg_net_flush_success", "DNS önbelleği başarıyla temizlendi!")
            else:
                notif_msg = tr("msg_net_winsock_success", "Ağ başarıyla sıfırlandı. Lütfen bilgisayarınızı yeniden başlatın!")
            CustomNotification(f"✅ {notif_msg}", duration=5000, parent=self).show_notification()
        else:
            DarkMessageBox.show_error(self, tr("sec_error", "Hata"), msg)
