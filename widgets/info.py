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

# ======================= BİLGİ WIDGET =======================
class InfoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)
        title = QLabel(tr("info_about_title", "Twiez Optimizer Hakkında"))
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
            tr("info_about_desc", "Twiez Optimizer, Windows sistemler için geliştirilmiş kapsamlı bir optimizasyon aracıdır. Bu uygulama ile sisteminizi hızlandırabilir, ağınızı optimize edebilir ve gereksiz dosyaları temizleyebilirsiniz.\n\nUygulama Python ve PyQt5 kullanılarak geliştirilmiştir. Modern ve kullanıcı dostu arayüzü ile kolayca sistem optimizasyonu yapabilirsiniz. Özellikler arasında:\n\n• Sistem temizliği ve optimizasyonu\n• Windows Arındırıcı (Debloater) ve Telemetri Kapatma\n• Ağ ve DNS Optimizasyonu (Hızlı DNS ve Bağlantı Onarımı)\n• Başlangıç programları yönetimi\n• Windows ayarları optimizasyonu\n• Otomatik Sistem Geri Yükleme Noktası\n\nTüm bu özellikler tek bir arayüzde toplanmış olup, sisteminizin en yüksek performansta ve güvende çalışmasını sağlar.")
        )
        description.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: 13px '{STYLE_CONFIG['font']['content'][0]}';
            line-height: 1.6;
        """)
        description.setWordWrap(True)
        info_layout.addWidget(description)
        version_label = QLabel(tr("info_version_label", "Versiyon: {}").format(CURRENT_VERSION))
        version_label.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: italic 12px;
            margin-top: 10px;
        """)
        version_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(version_label)
        # GitHub Button
        github_btn = QPushButton(tr("info_github_btn", "💻 GitHub'da Görüntüle"))
        github_btn.setCursor(Qt.PointingHandCursor)
        github_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {STYLE_CONFIG['dark']['hover']};
                color: {STYLE_CONFIG['dark']['text']};
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font: bold 13px;
                max-width: 200px;
            }}
            QPushButton:hover {{
                background-color: {STYLE_CONFIG['dark']['primary']};
            }}
        """)
        github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/twiez/twiez-optimizer")))
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(github_btn)
        btn_layout.addStretch()
        
        layout.addWidget(title)
        layout.addWidget(info_frame)
        layout.addLayout(btn_layout)
        
        footer = QLabel(tr("info_footer", "© 2026 Twiez Optimizer - Tüm hakları saklıdır"))
        footer.setStyleSheet(f"""
            color: {STYLE_CONFIG['dark']['text']};
            font: italic 11px;
            padding-top: 15px;
        """)
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)
        style_all_buttons(self)

